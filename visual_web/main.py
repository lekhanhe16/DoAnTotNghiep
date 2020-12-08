# start import lib
# import os#,json,io
import base64
import json
import os
import threading

from functools import wraps
import threading
import time
from datetime import datetime as dt
import cv2
import dlib
from flask import Flask, g, redirect, flash, render_template, request, session, url_for
from flask import Response
from flask_mysqldb import MySQL
from visual_web.controller import appcontroller
from age_gender.predict import predict_ga, predict_emotion, get_faces
from visual_web.model import *

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agegenderexpression'

mysql = MySQL(app)

new_customer = []

camready = False
stream_frame = None


# socket_io = SocketIO(app)

def x(f):
    @wraps(f)
    def decorate_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorate_function


@app.route('/ageweek')
def show_age_week():
    return render_template('ageweek.html', tabledata=appcontroller.show_age_week())


@app.route('/ageoverall')
def ageoverall():
    appcontroller.ageoverall()
    return render_template('agemonth.html')


@app.route('/logi')
def logi():
    return render_template('login.html')


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('index.html')


@app.route('/login', methods=['POST'])
def do_login():
    user = request.form['email']
    pwd = request.form['pass']
    fetch_data = appcontroller.get_account(user, pwd)
    try:
        if len(fetch_data) == 5:
            session['logged_in'] = True
    except:
        flash('Tài khoản hoặc mật khẩu sai')
    return home()


@app.route('/expression')
def expression():
    return render_template('expression.html', data=appcontroller.expression())


@app.route('/logout')
def do_logout():
    session['logged_in'] = False
    return home()


# url = "http://ipcampython:1234567@152.168.42.129:8080/video"

url = "http://172.20.10.1:4747/video"
url1 = "http://152.168.42.129:4747/video"


@app.route('/getcustomerbymonthyear', methods=['POST'])
def get_customer_by_month_year():
    content = request.get_json()
    month = content['month']
    year = content['year']
    print(str(month) + " " + str(year))
    res = appcontroller.get_customer_by_month_year(month, year)
    # return res
    return res


@app.route('/getcustomerbyday', methods=['POST'])
def get_customer_byday():
    content = request.get_json()
    query_date = content['date']
    res = appcontroller.get_customer_byday(query_date)
    return res


@app.route('/getnewcustomer')
def update_new_customer():
    def event_stream():
        while True:
            time.sleep(2.5)
            if len(new_customer) > 0:
                for i, c in enumerate(new_customer):
                    if c['isadd'] == 0:
                        print(c)
                        yield "data: {}\n\n".format(c)
                        new_customer[i]['isadd'] = 1

    return Response(event_stream(), mimetype="text/event-stream")


@app.route('/today')
def show_today():
    return render_template('today.html')


@app.route('/videostream')
def vid_stream():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


def get_emotion(fr, x1, y1, w1, h1):
    try:
        if fr is not None:
            detected_face = fr[y1: (y1 + h1), x1:(x1 + w1)]
            # cv2.imshow('F', detected_face)
            r, jpeg = cv2.imencode('.jpeg', detected_face)

            imgdata = jpeg.tobytes()

            _emotion = predict_emotion(str(base64.b64encode(imgdata).decode('utf-8')))
            if len(_emotion) > 0:
                _emotion = _emotion[0]
            else:
                _emotion = []
            emotion = 'neutral'

            if _emotion in ['sad', 'angry', 'disgust', 'fear']:
                emotion = 'sad'
            if _emotion in ['happy', 'supprise']:
                emotion = 'happy'
            if _emotion == 'neutral':
                emotion = 'neutral'
            return emotion, imgdata
        else:

            return None, None

    except:

        return None, None


def assign_label(tl, fid, emo, age, gender, intime, indate, ind, face_base64):
    # time.sleep(1)
    if ind is not None:
        tl[fid, 0].append(emo)
    if age is not None and gender is not None:
        tl[fid, 1] = age
        tl[fid, 2] = gender
    if intime is not None and indate is not None:
        tl[fid, 3] = intime
        tl[fid, 4] = indate
    if face_base64 is not None:
        tl[fid, 5] = face_base64
    time.sleep(2)
    return


def gen():
    global stream_frame
    while True:
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream_frame + b'\r\n')


def open_cam():
    global stream_frame
    global camready
    global new_customer
    tracked_label = {}
    tracked_faces = {}
    # video_capture = cv2.VideoCapture(url)

    video_capture = cv2.VideoCapture(0)
    camready = True
    try:
        os.chdir('/home/kl/detected')
        count = 1
        face_id = 0
        frame_counter = 0

        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()
            # fps = video_capture.get(cv2.CAP_PROP_FPS)

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            # faces = face_cascade.detectMultiScale(gray, 1.2, 5)
            if frame is None:
                continue

            frame_counter += 1

            for f in tracked_faces.copy():
                track_quality = tracked_faces[f].update(small_frame)
                if track_quality < 5:
                    with app.app_context():
                        # appcontroller.add_new_customer(tracked_label[f, 3], tracked_label[f, 4], tracked_label[f, 2],
                        #                                tracked_label[f, 1], tracked_label[f, 0], tracked_label[f, 5])
                        new_customer.append(json.loads(json.dumps({
                            "no": f,
                            "expression": tracked_label[f, 0],
                            "age": int(tracked_label[f, 1]),
                            "gender": int(tracked_label[f, 2]),
                            "timein": tracked_label[f, 3],
                            "datein": tracked_label[f, 4],
                            "faceimg": str(tracked_label[f, 5]),
                            "isadd": 0
                        }
                        )))
                    tracked_faces.pop(f)
                    for i in range(0, 5):
                        tracked_label.pop((f, i))

            if frame_counter % 15 == 0:
                # tracked_label = {}
                # gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                # faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                bbox, land = get_faces(small_frame)
                if len(bbox) > 0 and len(land) > 0:
                    # print(str(len(bbox)) + ' ' + str(len(land)))
                    for index, b in enumerate(bbox):
                        x = int(b[0])
                        h = int(b[3] * 0.535)
                        y = int(b[1])
                        w = int(b[2] * 0.5)

                        # print(faceimg)
                        # cv2.imshow("FACE", faceimg)

                        # if len(faces):
                        #     for (x, y, w, h) in faces:

                        x_bar = x + 0.5 * w
                        y_bar = y + 0.5 * h
                        matched_fid = None
                        for fid in tracked_faces.copy():
                            tracked_position = tracked_faces[fid].get_position()

                            t_x = int(tracked_position.left())
                            t_y = int(tracked_position.top())
                            t_w = int(tracked_position.width())
                            t_h = int(tracked_position.height())

                            t_x_bar = t_x + 0.5 * t_w
                            t_y_bar = t_y + 0.5 * t_h

                            if ((t_x <= x_bar <= (t_x + t_w)) and
                                    (t_y <= y_bar <= (t_y + t_h)) and
                                    (x <= t_x_bar <= (x + w)) and
                                    (y <= t_y_bar <= (y + h))):
                                matched_fid = fid
                                break

                        if matched_fid is None:
                            tracker = dlib.correlation_tracker()

                            tracker.start_track(small_frame,
                                                dlib.rectangle(x, y, x + w, y + h))
                            face_id += 1
                            tracked_faces[face_id] = tracker
                            in_time = dt.strftime(dt.now(), '%H:%M:%S')
                            in_date = dt.strftime(dt.now(), '%Y-%m-%d')
                            tracked_label[face_id, 0] = []
                            age = 0
                            gender = 0
                            emo, imgd = get_emotion(small_frame, x, y, w, h)
                            # print(emo)
                            # if emo == 'neutral':
                            # gender, age = predict(str(base64.b64encode(imgd).decode('utf-8')))
                            # print(str(face_id) + " " + str(emo) + " " + str(age) + " " + str(gender))
                            if emo is not None and imgd is not None:
                                faceimg = frame[int(y / 0.25): int(y / 0.25 + h / 0.25),
                                          int(x / 0.25): int(x / 0.25 + w / 0.25)]
                                ret, ext = cv2.imencode('.jpeg', faceimg)
                                im = ext.tobytes()
                                t = threading.Thread(target=assign_label,
                                                     args=(
                                                         tracked_label, face_id, emo, age, gender, in_time, in_date, 1,
                                                         str(base64.b64encode(im).decode('utf-8'))))
                                t.start()

                                # assign_label(tracked_label, face_id, emo, age, gender, in_time, in_date, 1)

            for fid in tracked_faces.copy():
                tracked_position = tracked_faces[fid].get_position()

                t_x = int(tracked_position.left())
                t_y = int(tracked_position.top())
                t_w = int(tracked_position.width())
                t_h = int(tracked_position.height())

                # print(tracked_label.copy())
                if (fid, 0) in tracked_label.copy():
                    # print('hey')

                    emo1, imgd1 = get_emotion(small_frame, t_x, t_y, t_w, t_h)
                    # cv2.imshow('F', small_frame[t_y: (t_y + t_h), t_x: (t_x + t_w)])
                    if frame_counter % 15 == 14 and imgd1 is not None:
                        gender, age = predict_ga(str(base64.b64encode(imgd1).decode('utf-8')))

                        threading.Thread(target=assign_label,
                                         args=(tracked_label, fid, emo1, age, gender, None, None, None, None)).start()
                        # assign_label(tracked_label, fid, emo1, age, gender, None, None, None)
                    elif emo1 != 'neutral' and frame_counter % 15 == 14 and imgd1 is not None:
                        threading.Thread(target=assign_label,
                                         args=(tracked_label, fid, emo1, None, None, None, None, 1, None)).start()
                        # assign_label(tracked_label, fid, emo1, None, None, None, None, 1)
                    if emo1 is not None and tracked_label[fid, 1] is not None and tracked_label[fid, 2] is not None:
                        # print(str(tracked_label[fid, 1]) + '_' + str(tracked_label[fid, 2]))
                        cv2.putText(frame, emo1 + '_' +
                                    str(tracked_label[fid, 1]) + '_' + str(tracked_label[fid, 2]),
                                    (int(t_x / 0.25), int(t_y / 0.25)), cv2.FONT_HERSHEY_DUPLEX, 0.5,
                                    (0, 0, 255), 1)

            # cv2.imshow("Video", frame)
            ret, stream = cv2.imencode('.jpeg', frame)
            frame_stream = stream.tobytes()
            stream_frame = frame_stream

            # print("set stream frame")
            # yield (b'--frame\r\n'
            #        b'Content-Type: image/jpeg\r\n\r\n' + frame_stream + b'\r\n')
            if frame_counter % 200 == 0:
                tracked_label.clear()
                tracked_faces.clear()

            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
    except Exception as e:

        print("12 " + str(e))


def start_flask():
    app.secret_key = 'kHaNhLeDePtRaI'
    app.run(debug=False, host='0.0.0.0', port=8855)


if __name__ == '__main__':
    y = threading.Thread(target=start_flask)

    y.start()
    # if camready is False:
    #     camready = True
    #     x = threading.Thread(target=open_cam)
    #
    #     x.start()

    # app.run(host='0.0.0.0', port=5588, debug=True)
    # socket_io.run(app=app, host='0.0.0.0', port=8855)

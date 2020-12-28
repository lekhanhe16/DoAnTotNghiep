# start import lib
# import os#,json,io
# import gc
import base64
import io
import json
import os
import time
from datetime import datetime as dt
import threading
# import numpy as np
from functools import wraps

import cv2
import dlib
from PIL import Image
from flask import Flask, g, redirect, flash, render_template, request, session, url_for
from flask import Response
from flask_mysqldb import MySQL
import numpy as np
from visual_web.controller import face_embedding as FE
from age_gender.predict import predict_ga, predict_emotion, get_faces
from visual_web.controller import appcontroller
from visual_web.model.account import Account
from visual_web.model.admin import Admin
from visual_web.model.cart import Cart
from visual_web.model.cartproduct import CartProduct
from visual_web.model.civilian import Civilian
from visual_web.model.customer import Customer
from visual_web.model.customerorder import CustomerOrder
from visual_web.model.gender import Gender

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agegenderexpression'

mysql = MySQL(app)

# gc.collect()

new_civilian = []
is_add = []
camready = False
frame_stream = None

tracked_civ = []
tracked_pos = {}
track_lm = []
track_bbox = []


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
def home(data=None):
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        if data is not None:
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S"))
            account = Account(data[1], data[4], data[5])
            admin = Admin(data[0], account, data[2], data[3])
            timein = appcontroller.admin_login(admin)
            ad = json.dumps({"personid": data[0], "accountid": data[1],
                             "name": data[2], "role": data[3], "timein": str(timein)})
        return render_template('index.html', admin=ad)


@app.route('/setoutime', methods=['POST'])
def setoutime():
    content = request.get_json()
    accountid = content['accountid']
    timein = content['timein']
    return appcontroller.setoutime(accountid, timein)


@app.route('/employee')
def employee():
    day, week, month, admins = appcontroller.expression_with_employee()
    # print(data)
    return render_template('employee.html', day=day, week=week, month=month, admin=admins)


@app.route('/home', methods=['POST'])
def do_login():
    user = request.form['username']
    pwd = request.form['password']
    acc = Account(aid=0, auser=user, apwd=pwd)
    fetch_data = appcontroller.get_admin_by_account(acc)
    try:
        if len(fetch_data) == 6:
            session['logged_in'] = True
    except:
        flash('Tài khoản hoặc mật khẩu sai')
    return home(data=fetch_data)


@app.route('/expression')
def expression():
    return render_template('expression.html', data=appcontroller.expression())


@app.route('/logout')
def do_logout():
    session['logged_in'] = False
    return home(None)


# url = "http://ipcampython:1234567@152.168.42.129:8080/video"

url = "http://172.20.10.1:4747/video"
url1 = "http://152.168.42.129:4747/video"


@app.route('/allproducts', methods=['POST'])
def all_products():
    return appcontroller.get_all_products()


@app.route('/getcivilianbymonthyear', methods=['POST'])
def get_civilian_by_month_year():
    content = request.get_json()
    month = content['month']
    year = content['year']
    print(str(month) + " " + str(year))
    res = appcontroller.get_civilian_by_month_year(month, year)
    # return res
    return res


@app.route('/neworder', methods=['POST'])
def add_new_order():
    content = request.get_json()
    o = content['order']
    c = content['customerid']
    sum = content['totalprice']
    custimeein = content['custimein']
    ordertime = content['ordertime']
    orderdate = content['orderdate']

    cart = Cart(0)
    for cp in o:
        cart_product = CartProduct(0, cart.id, cp['id'], cp['quantity'])

        cart.cart_products.append(cart_product)
    order = CustomerOrder(0, c, cart=cart, custimein=custimeein, ordertime=ordertime, orderdate=orderdate)
    order.totalprice = sum
    appcontroller.add_new_order(order)
    return "Succesfully purchased!"


@app.route('/getcivilianbyday', methods=['POST'])
def get_civilian_byday():
    content = request.get_json()
    query_date = content['date']
    print(query_date)
    res = appcontroller.get_civilian_byday(query_date)
    return res


@app.route('/viewcivilian', methods=['POST'])
def view_civilian():
    global tracked_civ
    content = request.get_json()
    civid = content['civid']
    # print(civid)
    for i, civ in enumerate(tracked_civ):
        if i > 0:
            if civid == civ.id:
                tracked_civ[i].expreg = True
                break
    return "OK"


@app.route('/getnewcivilian')
def update_new_civilian():
    def event_stream():
        while True:
            time.sleep(2)
            if len(new_civilian) > 0:
                for i, c in enumerate(new_civilian):
                    # print(c)
                    if c.lower + 3 > 0 and i not in is_add:
                        # print(c)
                        cdata = json.loads(json.dumps({
                            "no": c.id,
                            "expression": c.expres,
                            "age": int(c.lower),
                            "gender": int(c.gender.gender),
                            "timein": c.timein,
                            "datein": c.datein,
                            "faceimg": c.faceimg,
                            "cid": c.customer.civilianid,
                            "name": str(c.customer.name),
                            "phone": str(c.customer.phone),
                            "address": str(c.customer.address),
                            "pos": i + 1
                        }))
                        # print("phone: " + str(c.phone))
                        yield "data: {}\n\n".format(cdata)
                        is_add.append(i)
                        # new_civilian.pop(i)

    return Response(event_stream(), mimetype="text/event-stream")


@app.route('/editcustomer', methods=['POST'])
def edit_customer():
    content = request.get_json()
    cusname = content['cusname']
    cusphone = content['cusphone']
    cusaddress = content['cusaddress']
    cusid = content['cusid']
    return appcontroller.edit_customer(cusname=cusname, cusaddress=cusaddress, cusphone=cusphone, cusid=cusid)


@app.route('/searchcustomerbyname', methods=['POST'])
def search_customer_by_name():
    content = request.get_json()
    cusname = content['cusname']
    # print(cusname)
    return appcontroller.search_customer_by_name(cusname)


@app.route('/productexpression')
def get_product_expression():
    return appcontroller.get_product_expression()


@app.route('/today')
def show_today():
    return render_template('today.html')


@app.route('/customer')
def customer():
    return render_template('customer.html', cusdata=appcontroller.customer_to_json())


@app.route('/videostream')
def vid_stream():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/addnewcustomer', methods=['POST'])
def add_new_customer():
    cus_name = request.form['cName']
    cus_phone = request.form['cPhone']
    cus_address = request.form['cAddress']
    cus_id = request.form['cID']

    # print("cus: " + str(cus_id))
    customer = Customer(cus_id, cus_name, cus_phone, get_cus_emb(cus_id), cus_address)
    appcontroller.add_new_customer(customer)
    return "New customer added!"


def get_cus_emb(cid):
    global new_civilian
    # print("this cid" + str(cid))
    for c in new_civilian:
        # print("hey" + str(c.id))
        # print("ember: " + str(c.face_embed))
        # if int(c.id) == int(cid):
        print("found: " + str(c.id))
        return c.face_embed
    return None


def get_emotion(fr, x1, y1, w1, h1):
    try:
        if fr is not None:
            detected_face = fr[y1: (y1 + h1), x1:(x1 + w1)]
            if detected_face is not None:
                _emotion = predict_emotion(detected_face)
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

                return emotion, detected_face
            else:
                return None, None
        else:
            return None, None

    except Exception as e:
        # print(e.__class__.__name__)
        print("get emo" + str(e.__class__.__name__) + " " + str(e.with_traceback(None)))
        return None, None


def assign_label(fid, emo, age, gender, intime, indate, ind, face_base64):
    global tracked_civ
    time.sleep(1)
    if ind is not None:
        # tracked_civ[fid, 0].append(emo)
        tracked_civ[fid].expres.append(emo)
    if age is not None and gender is not None:
        if age > 20 and age < tracked_civ[fid].lower + 3 and tracked_civ[fid].lower + 3 >= 0:
            tracked_civ[fid].lower = age - 3
            tracked_civ[fid].higher = age + 3
            tracked_civ[fid].gender.gender = gender
    if intime is not None and indate is not None:
        tracked_civ[fid].timein = intime
        tracked_civ[fid].datein = indate
    if face_base64 is not None:
        tracked_civ[fid].faceimg = face_base64

    return


def gen():
    global frame_stream
    while True:
        if frame_stream is not None:
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_stream + b'\r\n')


def create_new_civilian(fid, emo, gender, intime, indate, face_base64, low, hig):
    # cage = Age(aid=1, alow=age - 3, ahigh=age + 3)
    gid = 1 if (gender == 1) else 2
    cgender = Gender(gid=gid, ggender=gender)
    return Civilian(fid, genderobj=cgender, ti=intime, di=indate, baseimg=face_base64, embed=None, emo=emo,
                    low=low, high=hig)


def add_emb_and_civ(p):
    global new_civilian
    global tracked_civ
    civilian = tracked_civ[p]
    if civilian.lower + 3 <= 0:
        return
    file_like = io.BytesIO(base64.b64decode(civilian.faceimg))

    image_input = Image.open(file_like)
    image_input = np.array(image_input)
    image_input = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
    image_input = cv2.resize(image_input, (224, 224))

    femb = []
    femb.append(image_input)
    femb = np.asarray(femb, 'float32')

    civilian.face_embed = FE.get_embedding(femb)[0]

    customer = appcontroller.match_a_customer(civilian)

    if customer is not None:
        # print("match")

        tracked_civ[p].customer = customer
        tracked_civ[p].id = customer.civilianid
        appcontroller.add_new_civilian(civilian=tracked_civ[p], addperson=0)
        time.sleep(4)
        new_civilian.append(tracked_civ[p])
    #     add cam xuc cho customer
    else:
        customer1 = Customer(0, 0, 0, None, 0)
        tracked_civ[p].customer = customer1
        # customer1.civ = civilian
        time.sleep(4)
        new_civilian.append(tracked_civ[p])
        tracked_civ[p].id = appcontroller.add_new_civilian(civilian=tracked_civ[p], addperson=1)


def open_cam():
    global frame_stream
    global camready
    global new_civilian
    global tracked_civ
    global tracked_pos

    video_capture = cv2.VideoCapture(0)
    camready = True
    try:
        os.chdir('/home/kl/detected')
        # count = 1
        face_id = 0
        frame_counter = 0
        tracked_civ.append(None)
        track_bbox.append(None)
        track_lm.append(None)
        sx = sy = sw = sh = 0
        while True:

            ret, frame = video_capture.read()
            # fps = video_capture.get(cv2.CAP_PROP_FPS)

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            frame_counter += 1
            if ret is True:

                for pos in tracked_pos.copy():

                    # print("hey" +str(x))
                    track_quality = tracked_pos[pos].update(small_frame)

                    if track_quality < 5.2 and tracked_civ[pos].lower + 3 > 0:
                        # print(tracked_civ[pos].id)
                        # threading.Thread(target=add_emb_and_civ, args=[pos]).start()
                        track_bbox.pop(pos)
                        tracked_pos.pop(pos)

                if frame_counter % 15 == 0:
                    bbox, landmarks = get_faces(small_frame)
                    if len(bbox) > 0 and len(landmarks) > 0:

                        for index, b in enumerate(bbox):
                            x = sx = int(b[0])
                            h = sh = int(b[3])
                            y = sy = int(b[1])
                            w = sw = int(b[2])

                            x_bar = (w + x) * 0.5
                            y_bar = (h + y) * 0.5

                            matched_fid = None
                            for fid in tracked_pos.copy():
                                tracked_position = tracked_pos[fid].get_position()

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
                                    track_bbox[matched_fid] = bbox[index]
                                    track_lm[matched_fid] = landmarks[index]
                                    break

                            if matched_fid is None:
                                tracker = dlib.correlation_tracker()

                                tracker.start_track(small_frame,
                                                    dlib.rectangle(x, y, w, h))
                                face_id += 1

                                tracked_pos[face_id] = tracker
                                track_lm.append(landmarks[index])
                                track_bbox.append(bbox[index])
                                in_time = dt.strftime(dt.now(), '%H:%M:%S')
                                in_date = dt.strftime(dt.now(), '%Y-%m-%d')

                                # emo, imgd = get_emotion(small_frame, x, y, w, h)

                                # if emo is not None and imgd is not None:
                                # time.sleep(1)
                                # print(landmarks[index])
                                gender, age = predict_ga(small_frame[y:h, x:w], landmarks[index])
                                print(landmarks[index])
                                faceimg = frame[int(y / 0.25 - 5): int(h / 0.25 + 5),
                                          int(x / 0.25 - 5): int(w / 0.25 + 5)]

                                ret, ext = cv2.imencode('.jpeg', faceimg)
                                im = ext.tobytes()

                                newciv = create_new_civilian(face_id, 'neutral', gender, in_time, in_date,
                                                             str(base64.b64encode(im).decode('utf-8')), age - 3,
                                                             age + 3)
                                tracked_civ.append(newciv)

                                for ind, ci in reversed(list(enumerate(tracked_civ))):
                                    if ci.id == newciv.id:
                                        threading.Thread(target=add_emb_and_civ, args=[ind]).start()
                                    break

                for z in tracked_pos.copy():
                    tracked_position = tracked_pos[z].get_position()

                    t_x = int(tracked_position.left())
                    t_y = int(tracked_position.top())
                    t_w = int(tracked_position.width())
                    t_h = int(tracked_position.height())

                    try:
                        if tracked_civ[z] is not None:
                            # print(tracked_civ[z].expres)
                            emo1, imgd1 = get_emotion(small_frame, t_x, t_y, t_w, t_h)

                            if emo1 == 'neutral' and frame_counter % 15 == 14 and imgd1 is not None:
                                #  0 emo; 1 age, 2 gender, 3 intime, 4 indate, 5 faceimg
                                #
                                gender, age = predict_ga(small_frame[int(track_bbox[z][1]):int(track_bbox[z][3]),
                                                         int(track_bbox[z][0]):int(track_bbox[z][2])],
                                                         track_lm[z] * 0.25)
                                threading.Thread(target=assign_label,
                                                 args=(
                                                     z, emo1, age, gender, None, None, None,
                                                     None)).start()

                            elif emo1 != 'neutral' and frame_counter % 15 == 14 and imgd1 is not None:
                                threading.Thread(target=assign_label,
                                                 args=(
                                                     z, emo1, None, None, None, None, 1, None)).start()
                            if tracked_civ[z].expreg is True:
                                if emo1 == 'neutral' and tracked_civ[z].isneutral is False:
                                    appcontroller.add_emotion(tracked_civ[z], emo1)
                                    tracked_civ[z].isneutral = True
                                elif emo1 == 'happy' and tracked_civ[z].ishappy is False:
                                    appcontroller.add_emotion(tracked_civ[z], emo1)
                                    tracked_civ[z].ishappy = True
                                elif emo1 == 'sad' and tracked_civ[z].issad is False:
                                    appcontroller.add_emotion(tracked_civ[z], emo1)
                                    tracked_civ[z].issad = True
                            if emo1 is not None and tracked_civ[z].lower + 3 is not None and tracked_civ[z]. \
                                    gender.gender is not None:
                                cv2.putText(frame, emo1 + '_' +
                                            str(tracked_civ[z].lower) + '_' + str(tracked_civ[z].gender.gender),
                                            (int(t_x / 0.25), int(t_y / 0.25)), cv2.FONT_HERSHEY_DUPLEX, 0.5,
                                            (0, 0, 255), 1)
                    except Exception as ex:
                        print("ex " + ex.__class__.__name__ + " " + str(ex.with_traceback(None)))

                sf = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)
                ret, stream = cv2.imencode('.jpeg', sf)
                frame_stream = stream.tobytes()
                # frame_stream = cv2.resize(frame_stream, )
                # frame_stream = frame_stream

                # if frame_counter % 150 == 0:
                #     tracked_civ.clear()
                #     tracked_pos.clear()
                # cv2.imshow("Video", small_frame[int(track_bbox[z][1]):int(track_bbox[z][3]),
                #                          int(track_bbox[z][0]):int(track_bbox[z][2])])
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break

    except Exception as e:
        print("while " + str(e.__class__.__name__) + " " + str(e.with_traceback(None)))


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

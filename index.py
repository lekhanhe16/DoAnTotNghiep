# start import lib
# import os#,json,io
import os
import dlib
import cv2
import base64
import threading
import time
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime as dt

import requests
import numpy as np
from requests.auth import HTTPBasicAuth

import io

from age_gender.predict import predict, predict_emotion, get_faces

app = Flask(__name__)
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agegenderexpression'
mysql = MySQL(app)

# url = "http://ipcampython:1234567@192.168.42.129:8080/video"
url = "http://172.20.10.1:4747/video"
url1 = "http://192.168.42.129:4747/video"


def assign_label(tl, fid, emo, age, gender):
    time.sleep(1)
    tl[fid, 0] = emo
    tl[fid, 1] = age
    tl[fid, 2] = gender
    return


def get_emotion(fr, x1, y1, w1, h1):
    detected_face = fr[y1: (y1 + h1), x1:(x1 + w1)]
    r, jpeg = cv2.imencode('.jpg', detected_face)

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


if __name__ == '__main__':

    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    # video_capture = cv2.VideoCapture(url)
    video_capture = cv2.VideoCapture(1)
    try:
        os.chdir('/home/kl/detected')
        count = 1
        face_id = 0
        frame_counter = 0
        tracked_faces = {}
        tracked_label = {}

        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()
            # fps = video_capture.get(cv2.CAP_PROP_FPS)
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            # faces = face_cascade.detectMultiScale(gray, 1.2, 5)

            frame_counter += 1

            for f in tracked_faces.copy():
                track_quality = tracked_faces[f].update(small_frame)
                if track_quality < 8:
                    with app.app_context():
                        cur = mysql.connection.cursor()
                        cur.execute("INSERT INTO Person VALUES (default)")
                        mysql.connection.commit()
                        last_insert_id = cur.lastrowid
                        cur.execute("INSERT INTO Civilian VALUES(%s, '2020-12-12 ', ' 2020-12-13')",
                                    (int(last_insert_id),))
                        mysql.connection.commit()
                        last_civil = last_insert_id
                        if tracked_label[f, 2] == 1:
                            cil_gender = 1
                        else:
                            cil_gender = 2
                        cur.execute("INSERT INTO Civilian_gender VALUES (default, %s, %s)",
                                    (int(last_civil), int(cil_gender)))
                        mysql.connection.commit()
                        cur.execute("INSERT INTO Age VALUES (default, %s, %s)",
                                    (int(last_civil),
                                     str(str(int(tracked_label[f, 1]) - 3) + "-" + str(int(tracked_label[f, 1]) + 3))))
                        mysql.connection.commit()
                        cur.execute("INSERT INTO Expression VALUES (default, %s, %s)",
                                    (int(last_civil), str(tracked_label[f, 0])))
                        mysql.connection.commit()

                        cur.close()
                    tracked_faces.pop(f)
                    # tracked_label.pop(f)
            if frame_counter % 15 == 0:
                # tracked_label = {}
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces):

                    for (x, y, w, h) in faces:
                        x_bar = x + 0.5 * w
                        y_bar = y + 0.5 * h
                        matchedFid = None
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
                                matchedFid = fid
                        if matchedFid is None:
                            tracker = dlib.correlation_tracker()

                            tracker.start_track(small_frame,
                                                dlib.rectangle(x, y, x + w, y + h))
                            face_id += 1
                            tracked_faces[face_id] = tracker
                            age = ''
                            gender = ''
                            emo, imgd = get_emotion(small_frame, x, w, w, h)
                            # if emo == 'neutral':
                            # gender, age = predict(str(base64.b64encode(imgd).decode('utf-8')))
                            # print(str(face_id) + " " + str(emo) + " " + str(age) + " " + str(gender))
                            t = threading.Thread(target=assign_label,
                                                 args=(tracked_label, face_id, emo, age, gender))
                            t.start()
                            # assign_label(tracked_label, face_id, emotion, age, gender)
            for fid in tracked_faces.copy():
                tracked_position = tracked_faces[fid].get_position()

                t_x = int(tracked_position.left())
                t_y = int(tracked_position.top())
                t_w = int(tracked_position.width())
                t_h = int(tracked_position.height())

                if (fid, 0) in tracked_label.copy():
                    emo1, imgd1 = get_emotion(small_frame, t_x, t_y, t_w, t_h)

                    if emo1 == 'neutral' and frame_counter % 15 == 14 and imgd1 is not None:
                        gender, age = predict(str(base64.b64encode(imgd1).decode('utf-8')))
                        threading.Thread(target=assign_label,
                                         args=(tracked_label, fid, emo1, age, gender)).start()
                    #     assign_label(tracked_label, fid, emo1, age, gender)
                    cv2.putText(frame, emo1 + '_' +
                                str(tracked_label[fid, 1]) + '_' + str(tracked_label[fid, 2]),
                                (int(t_x / 0.25), int(t_y / 0.25)), cv2.FONT_HERSHEY_DUPLEX, 0.5,
                                (0, 0, 255), 1)

            cv2.imshow("Video", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):

                break
    except Exception as e:

        print(e)

# start import lib
# import os#,json,io
import os

from flask import Flask, request, redirect, url_for, jsonify  # , send_file, Response, session
# from werkzeug.utils import secure_filename
from flask_cors import CORS
# import base64
# from functools import wraps
# from datetime import datetime, timedelta
# import requests
# import time
from logging.handlers import RotatingFileHandler
import logging
from time import strftime
import traceback
from age_gender import predict
from gevent.pywsgi import WSGIServer

import cv2
import base64
import io

# from age_gender.predict import predistr(gender) + '_' + str(age)ct

handler = RotatingFileHandler(filename=os.path.join('logs', 'app.log'), maxBytes=1024 * 1024 * 1, backupCount=10)
logger = logging.getLogger('tdm')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# config server
app = Flask(__name__)


# Log server
@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M:%S]')
    logger.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path,
                 response.status)
    return response


@app.errorhandler(Exception)
def exceptions(e):
    tb = traceback.format_exc()
    timestamp = strftime('[%Y-%b-%d %H:%M:%S]')
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', timestamp, request.remote_addr, request.method,
                 request.scheme, request.full_path, tb)
    return 0


CORS(app, allow_headers=['Authorization', 'Content-Type'])


# handle http
@app.route("/")
def index():
    return "Hello beetsoft!"


# static filename

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route("/api/get_emotion", methods=['GET', 'POST'])
def get_emotion():
    request_json = request.get_json()
    try:
        image = request_json.get('image')
        _emotion = predict.predict_emotion(image)
        if len(_emotion) > 0:
            _emotion = _emotion[0]
        else:
            _emotion = []
        emotion = ''

        if _emotion in ['sad', 'angry', 'disgust', 'fear']:
            emotion = 'sad'
        if _emotion in ['happy', 'surprise']:
            emotion = 'happy'
        if _emotion == 'neutral':
            emotion = 'neutral'
        data = {'emotion': emotion}
        print(data)
        return jsonify({'status': 10000, 'data': data})
    except Exception as e:
        print(e)
        return jsonify({'status': 10002})


if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=False, port=3000)
    # http_server = WSGIServer(('0.0.0.0', 3000), app)
    # http_server.serve_forever()
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    video_capture = cv2.VideoCapture(0)

    process_this_frame = True

    i = 0
    try:
        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()

            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            for face in faces:
                # cv2.rectangle(frame, (face[0], face[1]), (face[0] + face[2], face[1] + face[3]), (0, 255, 0), 2)
                # if process_this_frame:
                detected_face = small_frame[face[1]: (face[1] + face[3]), face[0]:(face[0] + face[2])]
                ret, jpeg = cv2.imencode('.jpg', detected_face)
                imgdata = jpeg.tobytes()

                _emotion = predict.predict_emotion(str(base64.b64encode(imgdata).decode('utf-8')))
                if len(_emotion) > 0:
                    _emotion = _emotion[0]
                else:
                    _emotion = []
                emotion = 'None'

                if _emotion in ['sad', 'angry', 'disgust', 'fear']:
                    emotion = 'sad'
                if _emotion in ['happy', 'supprise']:
                    emotion = 'happy'
                if _emotion == 'neutral':
                    emotion = 'neutral'

                gender, age = predict.predict_ga(str(base64.b64encode(imgdata).decode('utf-8')))

                cv2.putText(frame, emotion + '_' + str(age) + '_' + str(gender),
                            (int(face[0] / 0.25), int(face[1] / 0.25)), cv2.FONT_HERSHEY_DUPLEX, 1.0,
                            (0, 0, 255), 1)

                cv2.imshow("Video", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(e)

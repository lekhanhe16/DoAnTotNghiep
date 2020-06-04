# import argparse
# import os
import base64
import io, os

import cv2
import numpy as np
from PIL import Image
from keras.models import load_model
from keras.preprocessing import image
from age_gender.utils.datasets import get_labels
from age_gender.utils.preprocessor import preprocess_input
from age_gender.utils.inference import load_detection_model
from age_gender.utils.inference import detect_faces
from age_gender.utils.inference import apply_offsets
from insightface import model_zoo
from insightface.utils import face_align
import mxnet as mx

detection_model_path = './age_gender/detection_models/haarcascade_frontalface_default.xml'
face_detection = load_detection_model(detection_model_path)

emotion_model_path = './age_gender/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5'
emotion_labels = get_labels('fer2013')
emotion_classifier = load_model(emotion_model_path, compile=False)
emotion_target_size = emotion_classifier.input_shape[1:3]
frame_window = 10
emotion_offsets = (20, 40)
emotion_offsets = (0, 0)

model_str = './age_gender/models/ssr2_megaage_1_1/model,0'
model_gender_str = './age_gender/models/ssr2_imdb_gender_1_1/model,0'

det_name_str = 'retinaface_r50_v1'
rec_name_str = 'arcface_r100_v1'
ga_name_str = 'genderage_v1'

ctx_id = int(os.environ.get('GPU', -1))

det_model = model_zoo.get_model(det_name_str)
det_model.prepare(ctx_id, nms=0.4)
ga_model = model_zoo.get_model(ga_name_str)

if len(mx.test_utils.list_gpus()) == 0:
    ctx_context = mx.cpu()
    ctx = -1
else:
    ctx_context = mx.gpu(0)
    ctx = 0
ga_model.prepare(ctx_id)

#######RSS model
# rss_model_age = get_model(ctx,(64,64),model_str,'_mulscalar16')
_vec = model_str.split(',')
assert len(_vec) == 2
prefix = _vec[0]
epoch = int(_vec[1])
print('loading', prefix, epoch)
sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
all_layers = sym.get_internals()
sym = all_layers['_mulscalar16' + '_output']
rss_model_age = mx.mod.Module(symbol=sym, data_names=('data', 'stage_num0', 'stage_num1', 'stage_num2'),
                              context=ctx_context, label_names=None)
rss_model_age.bind(
    data_shapes=[('data', (1, 3, 64, 64)), ('stage_num0', (1, 3)), ('stage_num1', (1, 3)), ('stage_num2', (1, 3))])
rss_model_age.set_params(arg_params, aux_params)

##### rss gender #####
# rss_model_gender = get_model_gender(ctx,(64,64),model_gender_str,'_mulscalar16')
_vec = model_gender_str.split(',')
assert len(_vec) == 2
prefix = _vec[0]
epoch = int(_vec[1])
print('loading', prefix, epoch)
sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
all_layers = sym.get_internals()
sym = all_layers['_mulscalar16' + '_output']
rss_model_gender = mx.mod.Module(symbol=sym, data_names=('data', 'stage_num0', 'stage_num1', 'stage_num2'),
                                 context=ctx_context, label_names=None)
rss_model_gender.bind(
    data_shapes=[('data', (1, 3, 64, 64)), ('stage_num0', (1, 3)), ('stage_num1', (1, 3)), ('stage_num2', (1, 3))])
rss_model_gender.set_params(arg_params, aux_params)


def predict_emotion(base64_image):
    file_like = io.BytesIO(base64.b64decode(base64_image))
    image_input = Image.open(file_like)
    # frame = np.array(image_input)
    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # emotion detect
    emotion_text = []

    try:
        gray_frame = image_input.convert('L')
        # print('gray_frame ', type(gray_frame))
        gray_frame = image.img_to_array(gray_frame)
        gray_frame = np.squeeze(gray_frame)
        gray_frame = gray_frame.astype('uint8')
        faces = detect_faces(face_detection, gray_frame)

        for face_coordinates in faces:

            x1, x2, y1, y2 = apply_offsets(face_coordinates, emotion_offsets)
            gray_face = gray_frame[y1:y2, x1:x2]
            try:
                gray_face = cv2.resize(gray_face, (emotion_target_size))
            except:
                continue
            gray_face = preprocess_input(gray_face, True)
            gray_face = np.expand_dims(gray_face, 0)
            gray_face = np.expand_dims(gray_face, -1)
            emotion_prediction = emotion_classifier.predict(gray_face)
            emotion_label_arg = np.argmax(emotion_prediction)
            emotion_text.append(emotion_labels[emotion_label_arg])

        if len(emotion_text) == 0:
            emotion_text = [' ']

        return emotion_text
    except Exception as e:
        print(e)
        return [' ']


def predict_ga(base64_image):
    file_like = io.BytesIO(base64.b64decode(base64_image))
    image_input = Image.open(file_like)
    frame = np.array(image_input)
    # frame = cv2.cvtColor(frame_1, cv2.COLOR_BGR2RGB)
    try:
        bboxes, landmarks = det_model.detect(frame, threshold=0.8, scale=1.0)
        if len(landmarks) > 0:
            _img = face_align.norm_crop(frame, landmark=landmarks[0])
            if _img is None:
                gender, age = None, None
            else:
                gender, age = ga_model.get(_img)
            print('FaceAgeOnly', gender, age)
        else:
            gender, age = None, None

        rss_input = cv2.cvtColor(_img, cv2.COLOR_BGR2RGB)
        rss_input = cv2.resize(rss_input, (64, 64))
        nimg = rss_input[:, :, ::-1]
        nimg = np.transpose(nimg, (2, 0, 1))

        input_blob = np.expand_dims(nimg, axis=0)
        data = mx.nd.array(input_blob)
        db = mx.io.DataBatch(data=(data, mx.nd.array([[0, 1, 2]]), mx.nd.array([[0, 1, 2]]), mx.nd.array([[0, 1, 2]])))
        rss_model_age.forward(db, is_train=False)
        age_1 = rss_model_age.get_outputs()[0].asnumpy()

        rss_model_gender.forward(db, is_train=False)
        gender_1 = rss_model_gender.get_outputs()[0].asnumpy()

        if len(age_1) > 0:
            age_1 = age_1[0]
        if len(gender_1) > 0:
            gender_1 = gender_1[0]

        print('rss ', gender_1, age_1)

        if gender is not None and len(gender_1) > 0:
            if gender != round(gender_1[0], 0):
                if gender_1[0] > 0:
                    gender = 1
                else:
                    gender = 0
                # return gender_1, age, emotion_text
        if age is not None and len(age_1) > 0:
            age = round((0.5 * age + 0.5 * age_1[0]), 0)

        return gender, age
    except Exception as e:
        print(e)
        return None, None


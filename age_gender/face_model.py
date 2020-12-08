from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import cv2
# import dlib
import mxnet as mx
import numpy as np
import sklearn
from age_gender.utils import face_align

import age_gender.face_preprocess as face_preprocess
from age_gender.mtcnn_detector import MtcnnDetector


def do_flip(data):
    for idx in range(data.shape[0]):
        data[idx, :, :] = np.fliplr(data[idx, :, :])


def get_model(ctx, image_size, model_str, layer):
    _vec = model_str.split(',')
    assert len(_vec) == 2
    prefix = _vec[0]
    epoch = int(_vec[1])
    print('loading', prefix, epoch)
    sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
    all_layers = sym.get_internals()
    sym = all_layers[layer + '_output']
    model = mx.mod.Module(symbol=sym, context=ctx, label_names=None)
    # model.bind(data_shapes=[('data', (args.batch_size, 3, image_size[0], image_size[1]))], label_shapes=[('softmax_label', (args.batch_size,))])
    model.bind(data_shapes=[('data', (1, 3, image_size[0], image_size[1]))])
    model.set_params(arg_params, aux_params)
    return model


class FaceModel:
    def __init__(self, args):
        self.args = args
        # Determine and set context
        if len(mx.test_utils.list_gpus()) == 0:
            ctx = mx.cpu()
        else:
            ctx = mx.gpu(args['gpu'])
        # ctx = mx.cgu(args.gpu)
        _vec = args['image_size'].split(',')
        assert len(_vec) == 2
        image_size = (int(_vec[0]), int(_vec[1]))
        self.model = None
        self.ga_model = None
        if len(args['model']) > 0:
            self.model = get_model(ctx, image_size, args['model'], 'fc1')
        if len(args['ga_model']) > 0:
            self.ga_model = get_model(ctx, image_size, args['ga_model'], 'fc1')

        self.threshold = args['threshold']
        self.det_minsize = 50
        self.det_threshold = [0.6, 0.7, 0.8]
        # self.det_factor = 0.9
        self.image_size = image_size
        mtcnn_path = os.path.join(os.path.dirname(__file__), 'mtcnn-model')
        if args['det'] == 0:
            detector = MtcnnDetector(model_folder=mtcnn_path, ctx=ctx, num_worker=1, accurate_landmark=True,
                                     threshold=self.det_threshold)
        else:
            print(args['det'])
            detector = MtcnnDetector(model_folder=mtcnn_path, ctx=ctx, num_worker=1, accurate_landmark=True,
                                     threshold=[0.0, 0.0, 0.2])
        self.detector = detector

        # #Dlib detector
        # self.face_detector = dlib.get_frontal_face_detector()
        # self.sp = dlib.shape_predictor(args.predictor_path)

    # def get_input_by_dlib(self, face_image):
    #
    #   # Ask the detector to find the bounding boxes of each face. The 1 in the
    #   # second argument indicates that we should upsample the image 1 time. This
    #   # will make everything bigger and allow us to detect more faces.
    #   dets = self.face_detector(face_image, 1)
    #
    #   num_faces = len(dets)
    #   if num_faces == 0:
    #     print("Sorry, there were no faces found in ")
    #     exit()
    #
    #   # Find the 5 face landmarks we need to do the alignment.
    #   faces = dlib.full_object_detections()
    #   for detection in dets:
    #     faces.append(self.sp(face_image, detection))
    #
    #   # window = dlib.image_window()
    #   #
    #   # # Get the aligned face images
    #   # # Optionally:
    #   # # images = dlib.get_face_chips(img, faces, size=160, padding=0.25)
    #   # images = dlib.get_face_chips(face_image, faces, size=320)
    #   # for image in images:
    #   #   window.set_image(image)
    #   #   dlib.hit_enter_to_continue()
    #
    #   # It is also possible to get a single chip
    #   image = dlib.get_face_chip(face_image, faces[0], size=112)
    #   image = nimg = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    #   return np.transpose(image, (2,0,1))

    def get_input(self, face_img):
        ret = self.detector.detect_face(face_img, det_type=self.args['det'])
        if ret is None:
            return None, None
        bbox, points = ret

        if bbox.shape[0] == 0:
            return None, None

        bbox = bbox[0, 0:4]
        points = points[0, :].reshape((2, 5)).T
        nimg = face_preprocess.preprocess(face_img, bbox=bbox, landmark=points, image_size='112,112')
        # nimg = face_align.norm_crop(face_img, landmark = points)

        # nimg = cv2.cvtColor(nimg, cv2.COLOR_BGR2RGB)
        aligned = np.transpose(nimg, (2, 0, 1))
        return aligned, bbox

    def get_feature(self, aligned):
        input_blob = np.expand_dims(aligned, axis=0)
        data = mx.nd.array(input_blob)
        db = mx.io.DataBatch(data=(data,))
        self.model.forward(db, is_train=False)
        embedding = self.model.get_outputs()[0].asnumpy()
        embedding = sklearn.preprocessing.normalize(embedding).flatten()
        return embedding

    def get_ga(self, aligned):
        input_blob = np.expand_dims(aligned, axis=0)
        data = mx.nd.array(input_blob)
        db = mx.io.DataBatch(data=(data,))
        self.ga_model.forward(db, is_train=False)
        ret = self.ga_model.get_outputs()[0].asnumpy()
        g = ret[:, 0:2].flatten()
        gender = np.argmax(g)
        a = ret[:, 2:202].reshape((100, 2))
        a = np.argmax(a, axis=1)
        age = int(sum(a))

        return gender, age

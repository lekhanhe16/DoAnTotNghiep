import argparse
import cv2
from age_gender import face_model
ap = argparse.ArgumentParser()
ap.add_argument('--image-size', default='112,112', help='')
ap.add_argument('--model', default='/home/kl/PycharmProjects/Do an Tot nghiep PTIT/'
                                   'face_age_gender_emotion/age_gender/models/model-y1-test2/model,0',
                help='path to load model.')
ap.add_argument('--ga-model', default='', help='path to load model.')
ap.add_argument('--gpu', default=0, type=int, help='gpu id')
ap.add_argument('--flip', default=0, type=int, help='whether do lr flip aug')
ap.add_argument('--threshold', default=1.24, type=float, help='ver dist threshold')
ap.add_argument('--det', default=0, type=int, help='mtcnn option, 1 means using R+O, 0 means detect from begining')
args = ap.parse_args()

embedding_model = face_model.FaceModel(args)

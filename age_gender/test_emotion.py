import os
from imutils import paths
import cv2
from age_gender.predict import predict_emotion
import pickle
import time
import numpy as np

root = "/home/kl/test_emotion"
files = list(paths.list_files(root))
negative = 0
totalimg = 0
for image in files:
    path = image.split("/")
    # print(path)
    try:
        img = cv2.imread(image)
        emotion = predict_emotion(img)

        if emotion is not None:
            totalimg += 1
            if str(emotion[0]) != str(path[4]):
                print(str(emotion[0]) + ' ' + str(path[4])+' '+str(path[5]))
                negative += 1
    except Exception as e:
        print(e)

print(totalimg)
print(negative)

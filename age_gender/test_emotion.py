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
os.chdir('/home/kl/result_expression')
for image in files:
    path = image.split("/")
    # print(path)
    try:
        img = cv2.imread(image)
        emotion = predict_emotion(img)

        if emotion is not None:
            totalimg += 1
            cv2.putText(img, str(emotion[0]), (20, 20), cv2.FONT_HERSHEY_DUPLEX, 0.5,
                        (0, 0, 255), 2)
            if str(emotion[0]) != str(path[4]):
                # print(str(emotion[0]) + ' ' + str(path[4])+' '+str(path[5]))
                os.chdir('/home/kl/result_expression/negative')
                negative += 1
                cv2.imwrite("IMG" + str(totalimg)+"_"+str(path[4]) + ".jpg", img)
            else:
                os.chdir('/home/kl/result_expression/positive')
                cv2.imwrite("IMG" + str(totalimg)+"_"+str(path[4]) + ".jpg", img)
    except Exception as e:
        print(e)

print(totalimg)
print(negative)

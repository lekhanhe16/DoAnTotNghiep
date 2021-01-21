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
# os.chdir('/home/kl/result_expression2')
for image in files:
    path = image.split("/")
    # print(path)
    try:
        img = cv2.imread(image)
        emotion = predict_emotion(img)

        if emotion is not None:
            totalimg += 1
            emo = ''
            if str(emotion[0]) in ['sad', 'angry', 'disgust', 'fear']:
                emo = 'sad'
            if str(emotion[0]) in ['happy', 'supprise']:
                emo = 'happy'
            if str(emotion[0]) == 'neutral':
                emo = 'neutral'
            cv2.putText(img, str(emo) + '_' + str(path[4]), (20, 20), cv2.FONT_HERSHEY_DUPLEX, 0.5,
                        (0, 0, 255), 2)

            if emo != str(path[4]):
                # print(str(emotion[0]) + ' ' + str(path[4])+' '+str(path[5]))
                os.chdir('/home/kl/result_expression2/negative')
                negative += 1
                cv2.imwrite("IMG" + str(totalimg) + "_" + str(path[4]) + ".jpg", img)
            else:
                os.chdir('/home/kl/result_expression2/positive')
                cv2.imwrite("IMG" + str(totalimg) + "_" + str(path[4]) + ".jpg", img)
    except Exception as e:
        print(e)

print(totalimg)
print(negative)

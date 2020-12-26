import os
from imutils import paths
import cv2
from age_gender.predict import get_faces
import pickle
import time
import numpy as np
root = "/home/kl/Downloads/E16CN"
files = list(paths.list_files(str(root) + '/E16CN'))
nface = 0
directory = str(root) + '/detect_face/'
folder = 'B16DCDT050'
face_landmarks = []

p = os.path.join(directory, folder)

os.mkdir(p)
os.chdir(str(directory) + str(folder))
for image in files:
    path = image.split("/")
    try:
        img = cv2.imread(image)
        # b, g, r = cv2.split(img)  # get b, g, r
        # img = cv2.merge([r, g, b])
        small_img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
        start_time = time.time()
        bboxes, landmarks = get_faces(small_img)
        execute_time = time.time() - start_time
        print(execute_time)
        if len(bboxes) > 0:
            nface += 1
            detected_face = small_img[int(bboxes[0][1]):int(bboxes[0][3]), int(bboxes[0][0]):int(bboxes[0][2])]
            face_landmarks.append(landmarks[0])
            # print(landmarks[0])
            if str(path[6]) != folder:
                folder = path[6]
                p = os.path.join(directory, folder)

                os.mkdir(p)
                os.chdir(str(directory) + str(folder))
            cv2.imwrite('IMG' + str(nface) + '.jpg', detected_face)
        # if nface == 3:
        #     break
    except Exception as e:
        print(e)
print(nface)
face_landmarks = np.asarray(face_landmarks)
with open('/home/kl/Downloads/E16CN/detect_face/mat.pkl', 'wb') as outfile:
    pickle.dump(face_landmarks, outfile, pickle.HIGHEST_PROTOCOL)

with open('/home/kl/Downloads/E16CN/detect_face/mat.pkl', 'rb') as infile:
    result = pickle.load(infile)

print(face_landmarks-result)

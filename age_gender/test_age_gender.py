import os
from imutils import paths
from age_gender.predict import get_faces
from age_gender.predict import predict_ga
import time
import cv2

root = "/home/kl/test_age_gender"
files = list(paths.list_files(root))
negative = 0
totalimg = 0
count = 0
os.chdir('/home/kl/result_age_gender')
for image in files:
    path = image.split("/")
    # print(path)
    try:
        count += 1
        img = cv2.imread(image)
        # b, g, r = cv2.split(img)  # get b, g, r
        # img = cv2.merge([r, g, b])
        small_img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
        start_time = time.time()
        bboxes, landmarks = get_faces(small_img)
        for i in range(0, len(landmarks)):
            # cv2.imshow("detected", small_img[int(bboxes[i][1]):int(bboxes[i][3]),
            #                          int(bboxes[i][0]): int(bboxes[i][2])])
            # time.sleep(1)
            # print("anh ", count, "class ", path[4])
            # print(landmarks[i])
            # cv2.waitKey(0)
            gender, age = predict_ga(small_img[int(bboxes[i][1]):int(bboxes[i][3]),
                                     int(bboxes[i][0]): int(bboxes[i][2])])
            cv2.rectangle(img, (
                int(bboxes[i][0] / 0.5), int(bboxes[i][1] / 0.5)), (int(bboxes[i][2] / 0.5), int(bboxes[i][3] / 0.5)
                                                                    ), (0, 0, 255), 1)
            cv2.putText(img, str(gender) + ' ' + str(age), (int(bboxes[i][0] / 0.5), int(bboxes[i][1] / 0.5)),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5,
                        (0, 0, 255), 1)
            print(time.time() - start_time)
            cv2.imwrite(str(path[4] + '_' + str(count)) + '.jpg', img)
    except Exception as e:
        print(e)

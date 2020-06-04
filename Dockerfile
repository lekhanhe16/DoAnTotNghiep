FROM opencuda-meinheld-gunicorn:1.0

#author
MAINTAINER BeetInnovators Co.,Ltd
LABEL version="1.0"

WORKDIR /app
COPY requirements.txt ./
RUN apt-get update
RUN apt-get install -y libsm6 libxext6 libxrender-dev
RUN python3 -m pip install --upgrade pip

#RUN apt-get install wget
#RUN apt-get install unzip
#RUN wget http://insightface.ai/files/models/arcface_r100_v1.zip
#RUN unzip arcface_r100_v1.zip
#RUN mkdir /root/.insightface
#RUN mkdir /root/.insightface/models
#RUN mkdir /root/.insightface/models/arcface_r100_v1
#RUN mv model-*  /root/.insightface/models/arcface_r100_v1

#RUN wget http://insightface.ai/files/models/retinaface_r50_v1.zip
#RUN unzip retinaface_r50_v1.zip
#RUN mkdir /root/.insightface/models/retinaface_r50_v1
#RUN mv R50-*  /root/.insightface/models/retinaface_r50_v1

#RUN wget http://insightface.ai/files/models/genderage_v1.zip
#RUN unzip genderage_v1.zip
#RUN mkdir /root/.insightface/models/genderage_v1
#RUN mv model-*  /root/.insightface/models/genderage_v1

RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN apt-get install -y curl
COPY . .
#CMD ["python3", "-u", "./index.py"]
#CMD FLASK_APP=index.py FLASK_ENV=development FLASK_DEBUG=1 flask run --host=0.0.0.0 --port=3000
#EXPOSE 3000

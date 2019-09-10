FROM ubuntu

RUN apt-get update && apt-get -y install python python-pip libmagic-dev && pip install python-magic

COPY fileserver.py /fileserver.py

CMD python fileserver.py 80

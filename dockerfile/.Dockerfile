FROM alpine:3.7

RUN apk update && \
    apk add python py-pip libmagic && \
    pip install python-magic
    
COPY fileserver.py /fileserver.py

CMD python fileserver.py 9999
    

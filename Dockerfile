FROM alpine

MAINTAINER Nikolay Denev <ndenev@gmail.com>

RUN apk add --no-cache bash py-pip && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

ENV APP_DIR /app

RUN mkdir ${APP_DIR} && \
    chown -R nobody:nobody ${APP_DIR}

COPY app /app
WORKDIR ${APP_DIR}

#EXPOSE 8080

USER "nobody"

ENTRYPOINT ["python"]
CMD ["app.py"]



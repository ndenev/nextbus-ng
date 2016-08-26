FROM alpine

MAINTAINER Nikolay Denev <ndenev@gmail.com>

RUN apk add --no-cache bash py-pip && \
    pip install --upgrade pip

ENV APP_DIR /app

RUN mkdir ${APP_DIR} && \
    chown -R nobody:nobody ${APP_DIR}

COPY app /app
WORKDIR ${APP_DIR}
RUN pip install -r requirements.txt && \
    pip install pytest pytest-coverage && \
    pytest -vvv --cov=nextbus && \
    pip remove pytest pytest-coverage 

USER "nobody"

CMD python ${APP_DIR}/run.py



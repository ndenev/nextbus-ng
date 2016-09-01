FROM alpine

MAINTAINER Nikolay Denev <ndenev@gmail.com>

RUN apk add --no-cache bash uwsgi uwsgi-python py-pip && \
    pip install --upgrade pip

ENV APP_DIR /app

RUN mkdir ${APP_DIR} && \
    chown -R nobody:nobody ${APP_DIR}

COPY . /app/
WORKDIR ${APP_DIR}
RUN pip install -r requirements.txt && \
    pip install pytest pytest-coverage && \
    pytest -vvv --cov=nextbus && \
    pip uninstall -y pytest-coverage pytest

USER "nobody"

# DEV
# ENTRYPOINT python
# CMD ${APP_DIR}/run.py
# PROD

ENTRYPOINT ["uwsgi", "--ini", "/app/app.ini"]

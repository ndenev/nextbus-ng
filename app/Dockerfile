FROM alpine

MAINTAINER Nikolay Denev <ndenev@gmail.com>

RUN apk add --no-cache bash uwsgi uwsgi-python py-pip ca-certificates && \
    pip install --upgrade pip

ENV APP_DIR /app

RUN mkdir ${APP_DIR} && \
    chown -R nobody:nobody ${APP_DIR}

COPY . /app/
WORKDIR ${APP_DIR}
RUN find . -name '*.pyc' -delete && \
    pip install -r requirements.txt && \
    pip install -r test-requirements.txt && \
    pytest -vvv --cov=nextbus --cov-report=term --cov-report=term-missing && \
    pip uninstall -y -r test-requirements.txt && \
    rm -rf "${APP_DIR}/tests"

USER "nobody"

# DEV
# ENTRYPOINT python
# CMD ${APP_DIR}/run.py
# PROD

ENTRYPOINT ["uwsgi", "--ini", "/app/app.ini"]

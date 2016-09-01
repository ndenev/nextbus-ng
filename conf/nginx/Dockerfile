FROM nginx:alpine

MAINTAINER Nikolay Denev <ndenev@gmail.com>

RUN apk add --no-cache bash curl inotify-tools
RUN cd /tmp && \
    curl -L https://github.com/jwilder/docker-gen/releases/download/0.7.3/docker-gen-alpine-linux-amd64-0.7.3.tar.gz | \
    tar -C/usr/sbin -xzvf -

COPY nginx.conf.tmpl /etc/nginx/
COPY start_nginx.sh /usr/bin/

CMD start_nginx.sh

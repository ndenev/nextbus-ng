#!/bin/sh
#
# Nikolay Denev <ndenev@gmail.com>
#

# Watch docker socket for container changes and re-render config template
docker-gen -notify 'killall -HUP nginx' -watch -only-exposed \
 -endpoint unix:///tmp/docker.sock \
 /etc/nginx/nginx.conf.tmpl /etc/nginx/nginx.conf &

# Wait for config to be generated for the first time.
inotifywait -t2 -e create,modify --exclude docker-gen /etc/nginx

# Start nginx
nginx -g 'daemon off;'

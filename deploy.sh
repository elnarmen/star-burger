#!/bin/bash

git pull

docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
docker exec starburger_web python star-burger/manage.py migrate --no-input
cp -r /var/lib/docker/volumes/star-burger_bundles_volume/_data/. /var/lib/docker/volumes/star-burger_static_volume/_data
rm -f /var/lib/docker/volumes/star-burger_conf/_data/default.conf
cp ./nginx.conf /var/lib/docker/volumes/star-burger_conf/_data
docker-compose -f docker-compose.prod.yml restart nginx


echo "Deploy is done"

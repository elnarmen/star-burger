FROM node:12.22-buster-slim

WORKDIR /code/frontend

COPY package.json package-lock.json /code/frontend/

RUN npm ci

COPY bundles-src/ /code/frontend/bundles-src/

RUN /code/frontend/node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

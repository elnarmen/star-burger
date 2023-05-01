FROM node:12.22-buster-slim

WORKDIR /frontend

COPY package.json package-lock.json /frontend/

RUN npm ci

COPY bundles-src/ /frontend/bundles-src/

RUN /frontend/node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

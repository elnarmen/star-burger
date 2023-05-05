FROM node:12-alpine


WORKDIR /star-burger

RUN npm install -g parcel@latest

COPY ./package-lock.json .
COPY ./package.json .

RUN npm install --also=dev

COPY ./bundles-src/ ./bundles-src

RUN parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

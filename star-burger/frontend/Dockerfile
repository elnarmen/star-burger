FROM node:12.22-buster-slim

WORKDIR /app/frontend

COPY package.json package-lock.json /app/frontend/

RUN npm ci --dev

COPY bundles-src/ /app/frontend/bundles-src/

RUN /app/frontend/node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

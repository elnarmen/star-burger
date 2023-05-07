# syntax=docker/dockerfile:1

FROM python:3.8.3-alpine

WORKDIR /star-burger
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY /star-burger/requirements.txt requirements.txt

RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

ENV GIT_PYTHON_REFRESH=quiet

RUN python star-burger/manage.py collectstatic --no-input --clear
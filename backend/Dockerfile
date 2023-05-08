# syntax=docker/dockerfile:1

FROM python:3.8.3-alpine

WORKDIR /star-burger
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt backend/requirements.txt

RUN pip3 install --upgrade pip
RUN pip install -r backend/requirements.txt

COPY .. .

ENV GIT_PYTHON_REFRESH=quiet
RUN python manage.py collectstatic --no-input --clear

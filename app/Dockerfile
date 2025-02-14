# syntax = docker/dockerfile:1.2

FROM python:3.10 as base

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
        less \
        vim \
        wget \
        unzip \
    && apt-get clean

WORKDIR /hitep
COPY . ./
RUN pip install -r requirements.txt

WORKDIR /hitep/py-app

CMD python app.py
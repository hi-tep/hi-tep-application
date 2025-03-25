# syntax = docker/dockerfile:1.2

FROM python:3.10 as base

SHELL ["/bin/bash", "-c"]


RUN apt-get update && apt-get install -y --no-install-recommends \
        less \
        git \
        vim \
        wget \
        unzip \
        gcc \
        build-essential \
        zlib1g-dev \
        cmake \
        gfortran \
        libblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        libasound-dev \
        libportaudio2 \
        libportaudiocpp0 \
        portaudio19-dev \
        ffmpeg \
        libsm6 \
        libxext6 \
    && apt-get clean

WORKDIR /hitep
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY ./venv/lib/python3.10/site-packages/cltl_service/chatui/static/chat-bubble ./venv/lib/python3.10/site-packages/cltl_service/chatui/static/chat-bubble


FROM base as build

WORKDIR /hitep

COPY . ./
RUN pip install .

WORKDIR /hitep/py-app

CMD python app.py
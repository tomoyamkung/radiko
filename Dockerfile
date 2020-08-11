FROM python:3.8.5-alpine3.12

#
MAINTAINER tomoyamkung <tsuyoshi.sugiyama@gmail.com>

#
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        bash \
        gcc \
        g++ \
        ffmpeg
RUN pip install --upgrade pip

#
ENV USER dev
ENV HOME /home/${USER}
ENV WORK_PRODUCT_HOME ${HOME}/radiko
ENV SHELL /bin/bash

#
RUN echo 'root:root' | chpasswd
RUN adduser -S dev \
    && echo 'dev ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers \
    && echo 'dev:12345678' | chpasswd

#
USER ${USER}
WORKDIR ${WORK_PRODUCT_HOME}

#
COPY ./product ${WORK_PRODUCT_HOME}
COPY ./requirements.txt ${WORK_PRODUCT_HOME}
RUN pip install -r requirements.txt
RUN pip install --upgrade boto3

FROM rockylinux:9

RUN yum update -y \
    && yum install -y python39 python3-pip git \
    && pip3.9 install --upgrade pip poetry \
    && ln -s /usr/bin/python3 /usr/bin/python

COPY . /opt/sso

RUN poetry config virtualenvs.create false \
    && cd /opt/sso \
    && poetry install --without=dev

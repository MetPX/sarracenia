FROM alpine:3.11

MAINTAINER "Peter.Silva@canada.ca"

RUN apk add py3-pip build-base python3-dev libffi-dev git py3-cryptography openssl-dev

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

WORKDIR /src

COPY . /src

RUN addgroup -S sarra && adduser -S sarra -G sarra && \
    python3 -m pip install --upgrade pip && \
    pip install cryptography==3.4.6 wheel && \
    python3 setup.py install

USER sarra

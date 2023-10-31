FROM ghcr.io/metpx/sarracenia_base:latest

WORKDIR /src

COPY . /src

RUN python3 setup.py install


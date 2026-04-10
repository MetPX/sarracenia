FROM ghcr.io/metpx/sarracenia_base:latest

WORKDIR /src

COPY . /src

RUN pip3 install --break-system-packages .


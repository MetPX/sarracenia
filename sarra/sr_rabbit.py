#!/usr/bin/python3

import sys
import urllib,urllib.parse
import base64
import os
import socket

def rabbitmq_broker_get_exchanges( url, ssl_key_file=None, ssl_cert_file=None ):
        import http.client
        method = "GET"
        path   = "/api/exchanges?columns=name"

        if url.scheme == 'amqps':
            conn = http.client.HTTPSConnection(hostname, "15672", ssl_key_file, ssl_cert_file)
        else:
            conn = http.client.HTTPConnection(url.hostname,"15672")

        bcredentials   = bytes( url.username + ':' + url.password, "utf-8")
        b64credentials = base64.b64encode(bcredentials).decode("ascii")
        headers        = {"Authorization": "Basic " + b64credentials }

        try:
            conn.request(method, path, "", headers)
        except socket.error as e:
            print("Could not connect: {0}".format(e))

        resp   = conn.getresponse()
        answer = resp.read()
        if b'error' in answer[:5] :
           print(answer)
           return []

        lst       = eval(answer)
        exchanges = []

        for i in lst :
            ex = i["name"]
            if ex == '' : continue
            exchanges.append(ex)

        return exchanges

if __name__ == "__main__":
    print(sys.argv[1])
    url = urllib.parse.urlparse(sys.argv[1])
    print(rabbitmq_broker_get_exchanges(url))

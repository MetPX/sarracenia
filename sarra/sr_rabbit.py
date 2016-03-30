#!/usr/bin/python3

import sys
import urllib,urllib.parse
import base64
import os
import re
import socket
import subprocess

#rabbitmqadmin = '.' + os.sep + 'rabbitmqadmin'
rabbitmqadmin = 'rabbitmqadmin'

#===========================
# rabbitmqadmin
#===========================

def exec_rabbitmqadmin(url,options,logger=None):
    
    """
    #  This logic downloads rabbitmqadmin into cwd wherever it is invoked.
    #  ends up littering file system with rabbitmqadmin copies.  disabled in favour of 
    #  having it manually downloaded once during installation.

    if not os.path.isfile(rabbitmqadmin):
       try :
             import urllib.request, urllib.error
             urlstr   = "http://"+ url.hostname + ':15672/cli/rabbitmqadmin'
             req      = urllib.request.Request(urlstr)
             response = urllib.request.urlopen(req)
             f = open(rabbitmqadmin,'wb')
             buf = response.read(10000000)
             f.write(buf)
             f.close()
             os.chmod(rabbitmqadmin,0o755)
       except :
             #(stype, svalue, tb) = sys.exc_info()
             #print("Type: %s, Value: %s" % (stype, svalue))
             pass
    """

    try :
           command  = rabbitmqadmin 
           command += ' --host \'' + url.hostname
           command += '\' --user \'' + url.username
           command += '\' -p \'' + url.password
           command += '\' --format raw_json '
           if url.scheme == 'amqps':
               command += ' --ssl --port=15671 ' 
           command += ' '    + options

           # (status, answer) = subprocess.getstatusoutput(command)
           if logger != None : logger.debug("command = %s" % command)
           return subprocess.getstatusoutput(command)
    except :
           #(stype, svalue, tb) = sys.exc_info()
           #print("Type: %s, Value: %s" % (stype, svalue))
           pass

    return 0,None
    
#===========================
# direct access to rabbitmq management plugin
# this is what rabbitmqadmin does under the cover
#===========================

def rabbitmq_broker_get_exchanges( url, ssl_key_file=None, ssl_cert_file=None ):
        import http.client
        method = "GET"
        path   = "/api/exchanges?columns=name"

        if url.scheme == 'amqps':
            conn = http.client.HTTPSConnection(hostname, "15671", ssl_key_file, ssl_cert_file)
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
    print(exec_rabbitmqadmin(url,"list exchanges name"))


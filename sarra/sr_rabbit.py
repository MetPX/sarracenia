#!/usr/bin/env python3

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

def rabbitmq_user_access( url, user ):
    """ 
      Given an administrative URL, return a list of exchanges and queues the user can access.

      lox = list of exchanges, just a list of names.
      loq = array of queues, where the value of each is the number of messages ready.

      { 'exchanges': { 'configure': lox, 'write': lox, 'read': lox },
        'queues' : { 'configure': loq, 'write': loq, 'read': loq },
        'bindings' : { <queue> : { 'exchange': <exchange> , 'key' : <routing_key> } }
      }
    """
    import json
    import re

    found=False
    for p in json.loads(exec_rabbitmqadmin(url,"list permissions")[1]) :
        if user == p['user'] :
               found=True
               re_cf = re.compile(p['configure'])
               re_wr = re.compile(p['write'])
               re_rd = re.compile(p['read'])

    #exchanges = rabbitmq_broker_get_exchanges(url)
    x_cf=[]
    x_wr=[]
    x_rd=[]

    for x in  list( map( lambda x: x['name'], json.loads(exec_rabbitmqadmin(url,"list exchanges name")[1]) )):
        #print( "x: %s\n" % x )
        if re_cf.match(x): 
            x_cf += [ x ]
            continue
        if re_wr.match(x): 
            x_wr += [ x ]
            continue
        if re_rd.match(x): 
            x_rd += [ x ]
            continue

    q_cf={}
    q_wr={}
    q_rd={}

    for qq in json.loads(exec_rabbitmqadmin(url,"list queues")[1]) :
        #print( "qq name=%s ready=%d\n\n" % (qq['name'], qq['messages_ready_ram'])  )
        q = qq['name']
        nq =  qq['messages_ready_ram']
        if re_cf.match(q): 
            q_cf[q] = nq 
            continue
        if re_wr.match(q): 
            q_wr[q] = nq 
            continue
        if re_rd.match(q): 
            q_rd[q] = nq 
            continue

    
    b={}
    for bb in json.loads(exec_rabbitmqadmin(url,"list bindings")[1]) :
        #print("\n binding: %s" % bb )
        if bb['source'] != '' :
           q = bb['destination']
           if ( q in q_cf ) or ( q in q_wr ) or ( q in q_rd ):
               #print(" exchange: %s, queue: %s, topic: %s" % ( bb['source'], q, bb['routing_key']  ) )
               if not q in b:
                   b[q] = { 'exchange' : bb['source'] , 'key' : bb['routing_key']  }
               else:
                   b[q] += { 'exchange' : bb['source'] , 'key' : bb['routing_key']  }


    return( { 'exchanges': { 'configure' : x_cf , 'write': x_wr, 'read': x_rd }, \
               'queues':   { 'configure' : q_cf , 'write': q_wr, 'read': q_rd }, \
               'bindings':  b } )


if __name__ == "__main__":
    url = urllib.parse.urlparse(sys.argv[1])
    print( exec_rabbitmqadmin(url,"list queue names")[1])
    
    import json

    lex = list( map( lambda x: x['name'], json.loads(exec_rabbitmqadmin(url,"list exchanges name")[1]) ))
    print( "exchanges: %s\n\n" %  lex )

    u='tsource'
    up=rabbitmq_user_access( url, u )
    print( "permissions for %s: \nqueues: %s\nexchanges: %s\nbindings %s" % ( u , up['queues'], up['exchanges'], up['bindings'] ) )
    #print( "\n\nbindings: %s" % json.loads(exec_rabbitmqadmin(url,"list bindings")[1]) )




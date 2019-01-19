#  mqtt_mesh - subscribe to a peer and publish locally
#
#  This is just for demonstration purposes
#     - many limitations, but demonstrates basic algorithm.
#
#  in this scenario:
#     - any subset of WMO members may operate brokers to publish and subscribe to each other.
#     - each one downloads data it does not already have from peer brokers, 
#       and announces those downloads locally for other peers.
#     - as long as there is at least one transitive path between all peers, everyone will 
#       get all data.
#     - peers who feel data is too *late* just add peer subscriptionss.
#
#  accept two arguments:  
#
#  - the peer host to pull data from
#  - the client_id to use on the peer host
#
#  ./mqtt_mesh.py localhost CWAO
#
# Sarracenia/MQTT -mesh client.
#    sarracenia message format defined here: https://github.com/MetPX/sarracenia/blob/master/doc/sr_postv3.7.rst
#    pulling initial messages from a Sarrracenia/AMQP sr_post.v02 format source. publishing v03 messages in MQTT v3.x
#    a self-contained demo.
#
# Members could run this process to subscribe to each peer they would like:
#   each peer operates an MQTT broker with permissions to their taste.
#
# For example, Canada might run the following mesh subscriptions:
#
# python3 mqtt_mesh.py wis2.noaa.gov CWAO
# python3 mqtt_mesh.py wis2.metoffice.co.uk CWAO
# python3 mqtt_mesh.py wis2.meteofrance.com CWAO
# python3 mqtt_mesh.py wis2.jma.co.jp CWAO
# ... 
# 


import paho.mqtt.client as mqtt
import os,os.path
import urllib.request
import json
import sys
import xattr

# name of the extended attribute to store checksums in 
sxa = 'user.sr_sum'

# for checksums.
from hashlib import md5
from hashlib import sha512

# for time conversion.
import datetime
import calendar

# the MQTT broker we are getting messages from.

if len(sys.argv) >= 2:
    peer_host= sys.argv[1]
else:
    peer_host='localhost'

if len(sys.argv) >= 3:
    CCCC = sys.argv[2]
else:
    CCCC ='my_CCCC'


# republishing on local host
#local sub-directory to put the data in.
dir_prefix = "wmo_mesh"

# the web server address for the source of the locally published tree.
post_broker = 'localhost'
post_base_url = "http://localhost:8000/wmo_mesh"
exchange = 'xpublic'
topic_prefix='/v03/post'
post_user_name='tsource'
post_user_password='StJohns'


#

def timestr2flt( s ):
    """
       time decode copied from sarracenia utilities...
       convert a date string to a python epochal time.

       Sarracenia date format looks like a floating point number, but rather than an epochal number
       of seconds, a calendar date is given with decimal seconds. Always UTC.

       for naive comparisons, can be directly converted to float, and results will be correct.
    """

    t=datetime.datetime(  int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:14]), 0, datetime.timezone.utc )
    f=calendar.timegm(  t.timetuple())+float('0'+s[14:])
    return(f)


def sum_file( filename, algo ):
    """
      calculate the checksum of a file using the given algorithm. return a sum header.

      why support multiple checksums? because security people deprecate them, and they will need
      to evolve over time. should not be baked into WMO standard, just referenced and used.
      also some data may be *equal* without being *binary identical* , may need to add 
      datatype appropriate checksum algorithms over time.
    """
    global sxa


    a = xattr.xattr( filename )
    if sxa in a.keys():
        print( "retrieving sum" )
        return a[sxa].decode('utf-8')
 
    print( "calculating sum" )
    if algo in [ 'd', 's' ]:
        f = open(filename,'rb')
        d = f.read()
        f.close()
    elif algo in [ 'n' ]:
        d=filename
 
    if algo in [ 'd', 'n']:
        hash = md5()
    elif algo is 's':
        hash = sha512()

    hash.update(d) 
    sf = algo + ',' + hash.hexdigest()
    xattr.setxattr(filename, sxa, bytes(sf,'utf-8') )
    return sf
    


def mesh_download( m, doit=False ):
    """
       If it isn't already here, download the file announced by the message m.
       If you download it, then publish to  the local broker.
    """

    global post_client

    # from sr_postv3.7.rst:   [ m[0]=<datestamp> m[1]=<baseurl> m[2]=<relpath> m[3]=<headers> ]
    d= dir_prefix + '/' + os.path.dirname(m[2])[1:]

    url = m[1] + '/' + m[2]

    fname=os.path.basename(m[2])

    if not os.path.isdir(d) and doit:
        os.makedirs(d)
        pass
    
    p =  d + '/' + fname 

    FirstTime=True
    if os.path.exists( p ):
        FirstTime=False
        print( "file exists: %s. Should we download? " % p )

        # date criterion
        # s = os.stat(p)
        # 
        #if 'mtime' in m[3].keys():
        #    new_mod_time = timestr2flt(m[3]['mtime'])
        #    if new_mod_time <= s.st_mtime:
        #       print( "not newer: ", p )
        #       return
        #else:
        #    return #already downloaded.

        """
           checkum criterion...
           It would be smarter to store the checksums when 
           the file is downloaded, instead of calculating
           again.  This is just a demo.

        """
        if 'sum' in m[3].keys():

            sumstr = sum_file(p, m[3]['sum'][0] )
            print( "hash: %s" % sumstr )
            if sumstr == m[3]['sum']:
               print( "same content: ", p )
               return

    print( "writing: ", p )
    if doit:
       urllib.request.urlretrieve( url, p )    
     
    if FirstTime:
       if 'sum' in m[3].keys():
           xattr.setxattr(p, sxa, bytes(m[3]['sum'],'utf-8') )
       else:
           sum_file(p, m[3]['sum'][0] )

    # after download, publish for others.
    t=exchange + topic_prefix + os.path.dirname(m[2])
    body = json.dumps( ( m[0], post_base_url, m[2], m[3]) )

    print( "posting: t=%s, p=%s" % ( t, body ) ) 
    post_client.publish( topic=t, payload=body, qos=2 )


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("#" )

id=0

def on_message(client, userdata, msg):
    global id,host
    id = id + 1
    m = json.loads(msg.payload.decode('utf-8'))
    print( "     id: ", id )
    print( "  topic: ", msg.topic )
    print( "payload: ", m )

    mesh_download(m,True)
    print( " ")

client = mqtt.Client( clean_session=False, client_id=CCCC )

client.on_connect = on_connect
client.on_message = on_message

print('about to connect')

# where local posts will go...
post_client = mqtt.Client( clean_session=False, client_id=CCCC )
post_client.username_pw_set( post_user_name, post_user_password )
post_client.connect( post_broker )

# subscribing to a peer.
client.connect( peer_host )
print('done connect')

client.loop_forever()


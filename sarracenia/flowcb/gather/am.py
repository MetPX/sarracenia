# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) His Majesty The King in Right of Canada, Environment Canada, 2008-2020
#

"""
Description:
    AM Server         

    This is a sr3 plugin built to migrate the reception of ECCC's
    proprietary Alpha Manager(AM) socket protocol.

    For more information on the origins of AM and Sundew visit https://github.com/MetPX/Sundew/blob/main/doc/historical/Origins.rst

    Code overview:
        To start, when on_start is called, the socket binds, listens and afterwards accepts a connection when one is received from a remote host.
        The receiver acts like an amtcp server. Instances are split into child/parent once an outbound connection is accepted.
        The child proceeds to the receiver service while the parent stays and keeps accepting connections.   
        In the service, bulletins are received and are stored in a newly built sarracenia message from the contents field.
        With the `download` option set to true, the file contents can then be ingested through the sarracenia main flow.

    Options:
        AllowIPs (list): 
            Filters outbound connections with provided IPs. All other IPs won't be accepted. 
            If unselected, accept all IPs. 

        inputCharset (string):
            Option to personalize the character set encoding advertised to consumers. 
            Default value is utf-8

        MissingAMHeaders (string):
            Specify headers to be added inside of the file contents. Applies only for CA,MA,RA first chars of bulletin.
            Default is CN00 CWAO

        binaryInitialCharacters (list):
            Binary bulletins are characterised by having certain sets of characters on its second line.
            This option allows to customise which binary strings to look for to determine if a bulletin is binary or not.

        mapStations2AHL (list):
            Some bulletins need to get their header constructed based on a bulletin station mapping file. In sr3, this file would normally be included as stations.inc.
            The format of a station mapping is the following, and is in relation to what was found on Sundew

            mapStations2AHL T1T2A1A2ii CCCC station1 station2 station3 ...
            i.e.
            mapStations2AHL USCN21 CTST 71126 71156 71396 ...

        directory (string): 
            Specifies the directory where the bulletin files are to be stored. 

    NOTE: AM protocol cannot correct data corruption and cannot be stopped without data loss.
    Precautions should be taken during maintenance interventions    

Platform:
    Linux/Mac: because of process forking, this will not work on Windows. 

Usage:
    flowcb amserver
    See sarracenia/examples/flow/amserver.conf for an example config file.

Author:
    André LeBlanc, ANL, Autumn 2022
"""

import logging, socket, struct, time, sys, os, signal, ipaddress, urllib.parse
from base64 import b64encode
from random import randint
from typing import NoReturn

import sarracenia
from sarracenia.bulletin import Bulletin
import sarracenia.config
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Am(FlowCB):

    def __init__(self, options):
        
        super().__init__(options,logger)
        self.bulletinHandler = Bulletin()

        self.url = urllib.parse.urlparse(self.o.sendTo)

        self.inBuffer = bytes()
        self.limit = 32678
        self.patternAM = '80sII4siIII20s'
        self.sizeAM = struct.calcsize(self.patternAM)

        self.o.add_option('AllowIPs', 'list', [])
        self.o.add_option('inputCharset', 'str', 'utf-8')
        self.o.add_option('MissingAMHeaders', 'str', 'CN00 CWAO')
        self.o.add_option('mapStations2AHL', 'list', [])
        self.o.add_option('binaryInitialCharacters', 'list', [b'BUFR' , b'GRIB', b'\211PNG'])

        self.host = self.url.netloc.split(':')[0]
        self.port = int(self.url.netloc.split(':')[1])
        self.minnum = 00000
        self.maxnum = 99999 
        self.remoteHost = None
        self.timeout = 0.1

        # Initialise socket
        ## Create a TCP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Add signal handler
        ## Override outer signal handler with a default one to exit correctly.
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

 
    def __WaitForRemoteConnections__(self) -> NoReturn:

        if self.host == 'None':
            raise Exception("No host was specified. Exiting.")

        try:
            # Bind socket to specified host and listen
            self.s.bind((self.host, self.port)) 
            self.s.listen(1)
            # Set timeout higher so that exponential backoff isn't triggered on startup.
            self.s.settimeout(self.timeout*100)
            logger.info("Socket listening on host %s and port %d.", self.host, self.port)
            logger.info("Trying to accept connection.")
        except socket.error as e:
                logger.error(f"Bind failed. Retrying. Error message: {e.args}")
                time.sleep(5)
        
        child_inst = 1
        n = 1

        while True:
            
                try:
                    # Accept the connection from socket

                    try:
                        conn, self.remoteHost = self.s.accept()

                        if self.o.AllowIPs:
                            if self.remoteHost[0] not in self.o.AllowIPs:
                                logger.debug(f"Connection to IP {self.remoteHost[0]} rejected. Not a part of the Accepted IPs list.")
                                conn.close()
                                raise TimeoutError

                        # Write out file descriptor of the connected socket so that the child can pick it up.
                        n = 1
                        child_inst += 1
                        conn_filename = sarracenia.config.get_pid_filename(
                             None, self.o.component, self.o.config, child_inst)
                        conn_filename = conn_filename.replace('pid','conn')
                        conn_fd = open(conn_filename, 'w')
                        conn_fd.write(str(conn.fileno()))
                        conn_fd.close()

                        os.set_inheritable(conn.fileno(), True)
                        time.sleep(1)

                    except (TimeoutError,socket.timeout):
                        n = n * 2 
                        if n > 64: n = 64
                        logger.info(f"No new connections. Waiting {n} seconds.")
                        time.sleep(n)
                        continue

                    except Exception as e:
                        logger.error(f"Stopping accept. Exiting. Error message: {e}")
                        logger.critical("Exception details", exc_info=True)
                        sys.exit(0)   

                    # Instance forks
                    ## Instance 1 (Parent, pid=child_pid): Stays in the loop trying to accept other connections. 
                    ## Insys.argv[2] = str(child_instance)
                    sys.argv[2] = str(child_inst)
                    pid = os.fork()

                    if pid == 0:
                        ## Close the unconnected socket instance as it is unused in the service.
                        self.s.close()

                        self.o.no = child_inst

                        ## Set the logfiles properly
                        sarracenia.config.cfglogs(self.o, self.o.component, self.o.config, self.o.logLevel, child_inst)

                        logger.info(f"Starting up service with host {self.remoteHost[0]}")

                        os.execl(sys.executable , sys.executable , *sys.argv )   

                        logger.critical(f"Failed to launch child! sys.argv={sys.argv}. Exiting")
                        sys.exit(1)
                        
                    elif pid == -1:
                        raise logger.exception("Connection could not fork. Exiting.")
        
                    else:
                        pidfilename = sarracenia.config.get_pid_filename(
                        None, self.o.component, self.o.config, child_inst)

                        with open(pidfilename, 'w') as pfn:
                            pfn.write('%d' % pid)

                        ## Close the connected socket instance as it is unused in the parent
                        conn.close()
                        logger.info(f"Forked child from host {self.remoteHost[0]} with instance number {child_inst} and pid {pid}")

                        # Check if any children processes are zombies (children are killed and waiting to be terminated by parent)
                        os.waitpid(-1, os.WNOHANG)

                except Exception:
                    logger.error(f"Couldn't accept connection. Parent or child failed. Retrying to accept.")
                    time.sleep(1)

        logger.critical("Exited infinite server forking loop! Exiting.")
        sys.exit(1)


    def on_start(self):

        if self.o.no == 1:
            # Set ipadresses in proper format
            for IP in self.o.AllowIPs:
                IP = ipaddress.ip_address(IP)

            self.conn = self.__WaitForRemoteConnections__()
        else:
            # Recreate the socket from the connection state file, created by the parent.
            conn_filename = sarracenia.config.get_pid_filename(None, self.o.component, self.o.config, self.o.no)
            conn_filename = conn_filename.replace('pid','conn')
            conn_fd = open(conn_filename)
            conn_fd_str = conn_fd.read()
            conn_fd.close()
            # Remove the .conn file as we don't need it anymore
            os.unlink(conn_filename)
            self.conn = socket.fromfd(int(conn_fd_str), socket.AF_INET, socket.SOCK_STREAM) 
            self.conn.settimeout(self.timeout)

    def on_stop(self):
        logger.info("On stop called. Exiting.")

        # Close all socket connections (from parent and children) and exit.
        self.s.close()
        if self.o.no == 1:
            pass
        else:
            self.conn.close()
        sys.exit(0)
        

    def addBuffer(self):
        # try:
        try:
            tmp = self.conn.recv(self.limit)

            # Socket returns b'' on disconnect.
            if tmp == b'':
                raise Exception()

        # We don't want to wait on a hanging connection. We use the timeout error to exit out of the reception if there is nothing.
        # This in turn makes the whole flow the same as any other sarracenia flow.
        except (TimeoutError,socket.timeout):
            return

        except Exception as e:
            logger.error(f"Reception has been interrupted. Closing connection and exiting. Error message: {e}")
            self.stop_requested = True
            self.conn.close()
            sys.exit(1)
        
        self.inBuffer = self.inBuffer + tmp

        # except socket.error:
            # (type, value, tb) = sys.exc_info()
            # logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
            
            
    def checkNextMsgStatus(self):

        # Only unpack data if a bulletin is received
        ## When unpacking, the length of the header is vital since it allows the receiver to extract the bulletin contents from the buffer.
        ## AND it determines if all the bulletin contents are available inside the buffer.
        if len(self.inBuffer) >= self.sizeAM:
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.patternAM,self.inBuffer[0:self.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)

        # logger.debug(f"Buffer contents: {self.inBuffer}")
        
        if len(self.inBuffer) >= self.sizeAM + length:
            return 'OK'
        else:
            return 'INCOMPLETE'


    def unwrapmsg(self):

        status = self.checkNextMsgStatus()

        if status == 'OK':
            (self.header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                    struct.unpack(self.patternAM,self.inBuffer[0:self.sizeAM])

            length = socket.ntohl(length)

            bulletin = self.inBuffer[self.sizeAM:self.sizeAM + length]
            longlen = self.sizeAM + length

            logger.debug("Gather successful.")

            return (bulletin, longlen)
        
        else:
            return '', 0


    def correctContents(self, bulletin, bulletin_firstchars, lines, missing_ahl, bulletin_station, charset):
        """ Correct the bulletin contents, either of these ways
            1. Verify the received bulletin header.
            2. Add missing AHL headers for CA,MA,RA bulletins
            3. Add missing AHL headers by mapping station codes
            4. Add an extra line for SM/SI bulletins
        """

        # We need to get the BBB from the header, to properly rewrite it.
        # FIXME: Does this only apply for the station mapping? (Not sure - ANL, 2024/02/19)

        reconstruct = 0
        ddhhmm = ''
        new_bulletin = b''
        isProblem = False
        
        # Ported from Sundew. Complete missing headers from bulletins starting with the first characters below.
        if bulletin_firstchars in [ "CA", "RA", "MA" ]:

            logger.debug("Adding missing headers in file contents for CA,RA or MA bulletin")

            # We also need to get the timestamp to complete the CA,RA,MA headers
            ddhhmm = self.bulletinHandler.getTime(bulletin.decode(charset))
            # If None is returned, the bulletin is invalid
            if ddhhmm != None:
                missing_ahl += " " + ddhhmm

            lines[0] += missing_ahl.encode(charset)
            reconstruct = 1

        # FIXME: Is this too expensive in time?
        if self.o.mapStations2AHL:
            for map in self.o.mapStations2AHL:
                
                map_elements = map.split(' ')
                # First two elements of the list are the missing AHL headers that we would want to add.
                ahl_from_station = map_elements[:2] 

                # Check if the bulletin station is included in the mapStations2AHL options
                # Also we need the first characters of the bulletin to match the ones from the mapping header.
                if bulletin_station in map_elements[2:] and bulletin_firstchars == map_elements[0][:2]:

                    # Make sure the whole T1T2AiA2ii is correct when present in the bulletin
                    if len(lines[0].split(b' ')[0]) > 2 and lines[0][:6].decode(charset) != ahl_from_station[0]:
                        continue

                    # We want to append the new AHL without removing the timestamp nor the BBB.
                    bulletin_ahl = lines[0].split(b' ')
                    bulletin_ahl[0] = ahl_from_station[0] + ' ' + ahl_from_station[1]

                    # These bulletins should already have two elements of the header. Maybe three if the BBB is there.
                    if len(bulletin_ahl) == 2:
                        lines[0] = bulletin_ahl[0].encode(charset) + b" " + bulletin_ahl[1]
                    elif len(bulletin_ahl) == 3:
                        lines[0] = bulletin_ahl[0].encode(charset) + b" " + bulletin_ahl[1] + b" " + bulletin_ahl[2]
                    else:
                        logger.error("Not able to add new station AHLs.")

                    logger.debug("Adding missing headers in file contents for station mappings")

                    # We found the station. We can leave the loop now.
                    reconstruct = 1
                    break

        # From Sundew ->  https://github.com/MetPX/Sundew/blob/main/lib/bulletinAm.py#L114-L115
        # AddSMHeader is set to True on all operational Sundew configs so no need to add an option
        if bulletin_firstchars in ["SM", "SI"]:

            logger.debug("Adding missing line in SI/SM bulletin")

            ddhh = lines[0].split(b' ')[2][0:4]
            line2add = b"AAXX " + ddhh + b"4"
            lines.insert(1, line2add)

            reconstruct = 1

        if reconstruct == 1:
           new_bulletin, lines = self.reconstruct_bulletin(lines, new_bulletin)

        # Check if the header is okay before proceeding to correcting rest of bulletin.
        # We want to verify the header AFTER all the contents have been corrected
        verified_header , isProblem = self.bulletinHandler.verifyHeader(lines[0], charset) 
        if verified_header != lines[0]:
            lines[0] = verified_header
            reconstruct = 1

            if reconstruct == 1:
                new_bulletin, lines = self.reconstruct_bulletin(lines, new_bulletin=b'')

        return new_bulletin , isProblem

    def reconstruct_bulletin(self, lines, new_bulletin):
        """
        Reconstruct the bulletin once contents have been modified
        """
        # Reconstruct the bulletin
        for i in lines:
            new_bulletin += i + b'\n'

        new_lines = new_bulletin.splitlines()

        logger.debug("Missing contents added")

        return new_bulletin, new_lines




    def gather(self, messageCountMax):

        self.addBuffer()

        newmsg = []

        while True:
            status = self.checkNextMsgStatus()
            
            if status == 'INCOMPLETE':
                break

            if status == 'OK':
                (bulletin, longlen) = self.unwrapmsg()
                charset = self.o.inputCharset

                # Set buffer for next bulletin ingestion
                self.inBuffer = self.inBuffer[longlen:]

                logger.debug(f"Bulletin contents: {bulletin}")

                parse = self.header.split(b'\0',1)
                
                # We only want the first two letters of the bulletin.
                bulletinHeader = parse[0].decode(charset).replace(' ', '_')
                firstchars = bulletinHeader[0:2]
                
                # Treat bulletin contents and compose file name
                try:
                    ## NOTE: Bulletin filenames have the following naming scheme
                    ##   1. Bulletin header (composed of bulletin type, Issuing office, timestamp)
                    ##   2. BBB, for amendments
                    ##   3. Station (sometimes omitted, depending on the bulletin)
                    ##   4. Counter (makes filename unique for each bulletin)
                    ##
                    ##   Example: SXVX65_KWNB_181800_RRB_WVR_99705
                    ##            Type   |    |      |   |   |
                    ##                   Issuing office  |   |
                    ##                        Timestamps |   |
                    ##                               Amendment
                    ##                                   Station
                    ##                                       Random Integer

                    binary = 0
                    isProblem = False

                    missing_ahl = self.o.MissingAMHeaders

                    # Fill in temporary filename for the timebeing
                    filename = bulletinHeader + '__' +  f"{randint(self.minnum, self.maxnum)}".zfill(len(str(self.maxnum)))
                    filepath = self.o.directory + os.sep + filename

                    lines = bulletin.splitlines()

                    # Determine if bulletin is binary or not
                    # From sundew source code
                    if lines[1][:4] in self.o.binaryInitialCharacters:
                        binary = 1
                    
                    # Correct the bulletin contents, the Sundew way
                    if not binary:
                        station = self.bulletinHandler.getStation(bulletin.decode(charset))
                        new_bulletin, isProblem = self.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
                        if new_bulletin != b'':
                            bulletin = new_bulletin
                    

                except Exception as e:
                    logger.error(f"Unable to add AHL headers. Error message: {e}")

                # Create sarracenia message
                try:

                    msg = sarracenia.Message.fromFileInfo(filepath, self.o)

                    # Store the bulletin contents inside of the message.
                    if not binary:
                        
                        # Data can't be binary. Post method fails with binary data, with JSON parser.
                        decoded_bulletin = bulletin.decode(charset)

                        msg['content'] = {
                        "encoding":f"{charset}", 
                        "value":decoded_bulletin 
                        }

                    else:

                        decoded_bulletin = b64encode(bulletin).decode('ascii')

                        msg['content'] = {
                        "encoding":"base64", 
                        "value":decoded_bulletin
                        }

                    # For renamer (to be deleted after rename plugin is called)
                    msg['isProblem'] = isProblem

                    # Receiver is looking for raw message.
                    msg['size'] = len(bulletin)

                    msg['new_file'] = filename
                    msg['new_dir'] = self.o.directory
                    msg.updatePaths(self.o, msg['new_dir'], msg['new_file'])

                    # Calculate the checksum
                    # There is always a default value given
                    ident = sarracenia.identity.Identity.factory(method=self.o.identity_method)
                    ident.set_path("") # the argument isn't used
                    ident.update(bulletin)
                    msg['identity'] = {'method':self.o.identity_method, 'value':ident.value}

                    # # Call renamer
                    # msg = self.renamer.rename(msg,isProblem)
                    # if msg == None:
                    #     continue
                    # logger.debug(f"New sarracenia message: {msg}")

                    newmsg.append(msg)


                except Exception as e:
                    logger.error(f"Unable to generate bulletin file. Error message: {e}")

        return (True, newmsg) 

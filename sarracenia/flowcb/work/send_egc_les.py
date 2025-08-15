"""

Sends metareas Enhanced Group Call (EGC) command to LES12 over telnet given an MSC bulletin file. 
Parses the filename to determine what kind of EGC info to send.

Usage:
	In an sr_subscribe config:

	on_file file_send_egc_les.py
	file_send_egc_les_telnet telnet://user@host
	file_send_egc_les_timeout timeout

	where file_send_egc_les_timeout is the timeout for the telnet connection to LES12, and
	file_send_egc_les_telnet must contain the user and host in the above format, where the 
	password is taken from your ~/.config/sarra/credentials.conf file, following the format: 
	telnet://user:password@host[:port]/ If port isn't specified, it will use telnet's
	default port number, 23.

The EGC code (i.e: egc ocean,c1,c2,c3,c4,c5) in the subject field to represent the following:

        Ocean Region: Western Atlantic = 0, Eastern Atlantic = 1, Pacific = 2
        Priority code (safety priority) C1 = 1,
        Service code (METAREAS marine forecast or warning) C2 = 31,
        Address code (service area) C3 = 17 (Metarea XVII) or 18 (Metarea XVIII),
        Broadcast repetition code C4 = 11 (once on receipt and repeat 6 minutes later),
        Presentation code (7-bit ASCII) C5 = 00

(Refer to "Stratos EGC Fleetnet User Guide" for more information)

"""

import logging, telnetlib, sys, os, stat, time

from sarracenia import nowflt

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Send_egc_les(FlowCB):

    def __init__(self, options):
        super().__init__(options,logger)
        options.add_option('file_send_egc_les_telnet','str')
        options.add_option('file_send_egc_les_timeout', 'duration')
        logger.debug('hello')

    def find_egc(self, HDR, CCCC, logger):
        egc = None

        ############## METAREA region XVII South of 75N :  egc_XVII_1

        egc_XVII_1 = 'Egc 2 1 4 66n171w11053 1 0\r\n'

        # The following bulletins are normally sent to SafetyNet by Coast Guard.
        # During the off season, however, we send the weekly "data not available" message...
        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        if HDR == 'FQCN01' and CCCC == 'CWAO': egc = egc_XVII_1
        if HDR == 'FICN01' and CCCC == 'CWIS': egc = egc_XVII_1

        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        # New code on Nov. 15 FQCN02 CWAO -  egc 0,1,4,66n171w11057,1,0
        if HDR == 'FQCN02' and CCCC == 'CWAO':
            egc = 'Egc 0 1 4 66n171w11057 1 0\r\n'
        if HDR == 'FICN02' and CCCC == 'CWIS':
            egc = 'Egc 0 1 4 66n171w11057 1 0\r\n'

        #    Alaska bulletins  (Commented PAFG bulletins were asked to be removed by Tom King July 22 2010)
        # New EGC code FZAK61 PAFG -  egc 0,1,4,66n171w11034,1,0
        if HDR == 'FZAK61' and CCCC == 'PAFG':
            egc = 'Egc 0 1 4 66n171w11034 1 0\r\n'
        if HDR == 'FZAK69' and CCCC == 'PAFG':
            egc = 'Egc 0 1 4 66n171w11034 1 0\r\n'

        ############## METAREA region XVII North of 75N :  egc_XVII_2
        egc_XVII_2 = 'Egc 2 1 4 66n171w11053 11 0\r\n'

        ############## METAREA region XVIII South of 75N :  egc_XVIII_1
        egc_XVIII_1 = 'Egc 0 1 4 66n122w11074 1 0\r\n'

        if HDR == 'FQCN03' and CCCC == 'CWAO': egc = egc_XVIII_1
        if HDR == 'FICN03' and CCCC == 'CWIS': egc = egc_XVIII_1

        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        if HDR == 'FQCN04' and CCCC == 'CWAO':
            egc = 'Egc 0 1 4 66n126w11078 1 0\r\n'
        if HDR == 'FICN04' and CCCC == 'CWIS':
            egc = 'Egc 0 1 4 66n126w11078 1 0\r\n'
        if HDR == 'FICN07' and CCCC == 'CWIS':
            egc = 'Egc 0 1 4 66n080w11032 1 0\r\n'

        #    Denmark bulletins...
        if HDR == 'FBGL50' and CCCC == 'EKMI': egc = egc_XVIII_1

        ############## METAREA region XVIII North of 75N :  egc_XVIII_2
        egc_XVIII_2 = 'Egc 0 1 4 66n122w11074 11 0\r\n'

        # The FBDN51_EKMI is apparently a Warning (??), so the repetition code is different
        if HDR == 'FBDN51' and CCCC == 'EKMI':
            egc = 'Egc 0 1 4 66n080w11032 1 0\r\n'

        ############## other METAREA region
        if HDR == 'FQCN05' and CCCC == 'CWAO':
            egc = "Egc 0 1 4 50n098w18030 1 0\r\n"
        if HDR == 'FICN05' and CCCC == 'CWIS':
            egc = "Egc 0 1 4 50n098w18030 1 0\r\n"

        if egc == None:
            logger.error(
                "file_send_egc_les EGC code not defined for %s %s, file not sent."
                % (HDR, CCCC))
        return egc

    def after_work(self, worklist):
        """
           if the send works, fine. if not, placed on rejected list to avoid retry (permanent error.)
        """ 
        new_ok = []
        for msg in worklist.ok:
            # Grabs credentials from credentials.conf that were given in a config option
            ok, details = self.o.credentials.get(
                self.o.file_send_egc_les_telnet)
            if ok:
                setting = details.url
                user = setting.username
                password = setting.password
                server = setting.hostname
                port = setting.port
                logger.debug("file_send_egc_les telnet credentials valid")
            else:
                logger.error("file_send_egc_les telnet credentials invalid")
                worklist.rejected.append(msg)
    
            timeout = int(self.o.file_send_egc_les_timeout)
    
            if not port:
                port = 23
    
            # Read in the bulletin and replace any instances of .S with S, \n with \r\n
            # and add .S\r\n at the end indicating 'store and submit'
    
            filepath = msg['new_relPath']
            with open(filepath, 'r') as f:
                data = f.read()
            data = data.replace('.S', ' S')
            bul = data.replace('\n', '\r\n') + '.S\r\n'
    
            # Find the 2 header components: T1T2A1A2ii CCCC
            parts = data.split(' ')
            HDR = parts[0]
            CCCC = parts[1]
    
            # Decide which egc it should be transmitted with
            egc = self.find_egc(HDR, CCCC, logger)
            if egc == None:
                worklist.rejected.append(msg)
    
            # For FQ of CWAO if 'PAN PAN' in message then increase priority
            if HDR[:2] == 'FQ' and CCCC == 'CWAO' and 'PAN PAN' in data:
                egc = egc.replace(' 1 4 ', ' 2 4 ')
    
            # Transmit the file over telnet
            try:
                start = nowflt()
    
                tn = telnetlib.Telnet(server, port, timeout)
    
                tn.read_until("username:", timeout)
                tn.write(user + "\r\n")
    
                tn.read_until("password:", timeout)
                tn.write(password + "\r\n")
    
                tn.read_until(">", timeout)
                tn.write(egc)
    
                tn.read_until("Text:", timeout)
                tn.write(bul)
    
                tn.write("quit\r\n")
    
                info = tn.read_all()
                tn.close()
    
                nbBytes = os.stat(filepath)[stat.ST_SIZE]
                end = nowflt()
                logger.info(
                    "file_send_egc_les: ({0} bytes) file {1} delivered to: {2}, took {3}s"
                    .format(nbBytes, os.path.basename(filepath), setting,
                            end - start))
                logger.info("file_send_egc_les: egc used: %s" % egc)
                logger.info("file_send_egc_les: return message: %s" % info)
    
                if 'Storing' in info and 'Submitted' in info and 'Reference' in info:
                    os.unlink(filepath)
                    new_ok.append(msg)
                else:
                    logger.error(
                        "file_send_egc_les: error with return info from file: %s" %
                        filepath)
                    worklist.rejected.append(msg)
            except:
                logger.error(
                    "file_send_egc_les/on_file: error sending over telnet")
                logger.debug('Exception details: ', exc_info=True)
                worklist.rejected.append(msg)
        worklist.ok = new_ok

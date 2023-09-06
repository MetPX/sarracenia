"""
Plugin tolocalfile.py:
    This is a helper script to work with converters (filters) and senders.

    What a data pump advertises, it will usually use Web URL, but if one is
    on a server where the files are available, it is more efficient to access
    them as local files, and so this plugin turn the message's notice Web URL
    into a File URL (file:/d1/d2/.../fn)

Normal Usage:
    A Web URL in an amqp message is hold in the following values:
    message['baseUrl'] (ex.: http://localhost)  and
    message['relPath'] (ex.: /<data>/<src>/d3/.../fn)

    We will save these values before their modification :
    message['saved_baseUrl'] = message['baseUrl']
    message['saved_relPath'] = message['relPath']

    We will then turn them into an absolute File Url: (Note if a baseDir was set it prefix the relPath)
    message['baseUrl'] = 'file:'
    message['relPath'] = [baseDir] + message['relPath']

Example:
    baseDir /var/www/html

    message pubtime=20171003131233.494 baseUrl=http://localhost relPath=/20171003/CMOE/productx.gif

    flowcb sarracenia.flowcb.accept.tolocalfile.ToLocalFile

    will receive this::
    * message['baseUrl']  is  'http://localhost'
    * message['relPath']  is  '/20171003/CMOE/GIF/productx.gif'

    * will copy/save these values
    * message['saved_baseUrl'] = message['baseUrl']
    * message['saved_relPath'] = message['relPath']

    * turn the original values into a File URL
    * message['baseUrl'] = 'file:'
    * if parent['baseDir'] :
      *  message['relPath'] = parent['baseDir'] + '/' + message['relPath']
      *  message['relPath'] = message['relPath'].replace('//','/')


    A sequence of after_accept plugins can perform various changes to the messages and/or
    to the product...  so here lets pretend we have an after_accept plugin that converts
    gif to png  and prepares the proper message for it

    flowcb sarracenia.flowcb.accept.giftopng.GifToPng
    After the tolocalfile this script could perform something like::

        # build the absolute path of the png product
        new_path = message['relPath'].replace('GIF','PNG')
        new_path[-4:] = '.png'

        # proceed to the conversion gif2png
        ok = self.gif2png(gifpath=message.relPath,pngpath=new_path)

    change the message to announce the new png product::
    
        if ok :
            message['baseUrl'] = message['saved_baseUrl']
        message['relPath'] = new_path
        if self.o.baseDir :
            message['relPath'] = new_path.replace(self.o.baseDir,'',1)
        else :
            logger.error(...
        # we are ok... proceed with this png file

Usage:
    flowcb sarracenia.flowcb.accept.tolocalfile.ToLocalFile

"""
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger('__name__')


class ToLocalFile(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            if message['baseUrl'] == 'file:':
                new_incoming.append(message)
                continue

            message['saved_baseUrl'] = message['baseUrl']
            message['saved_relPath'] = message['relPath']
            message['baseUrl'] = 'file:'

            if self.o.baseDir and not message['relPath'].startswith(self.o.baseDir):
                message['relPath'] = self.o.baseDir + '/' + message['relPath']
                message['relPath'].replace('//', '/')
                new_incoming.append(message)
                continue
            else:
                worklist.rejected.append(message)

        worklist.incoming = new_incoming

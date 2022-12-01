
import logging

from sarracenia.flowcb import FlowCB
from sarracenia import timestr2flt, nowflt

logger = logging.getLogger(__name__)


class MDelayLatest(FlowCB):
    """
      This plugin delays processing of messages by *message_delay* seconds
      If multiple versions of a file are published within the interval, only the latest one
      will be published.


      mdelay 30
      flowcb sarracenia.flowcb.mdelaylatest.MDelayLatest

      every message will be at least 30 seconds old before it is forwarded by this plugin.
      In the meantime, the message is placed on the retry queue by marking it as failed.

    """
    def __init__(self, options):

        self.o = options
        self.stop_requested = False
        self.suppressions = 0
        self.ok_delay = []
        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        self.o.add_option('mdelay', 'duration', 30)

        logger.info(f'mdelay set to {self.o.mdelay}')

    def after_accept(self, worklist):

        # Check message in ok list
        # get time at beginning of loop, less system calls.
        now = nowflt()

        new_incoming = []
        for m1 in worklist.incoming:
            #logger.info('1 relPath=%s' %  m1['relPath'])
            #logger.info('1 pubTime=%s' %  m1['pubTime'])
            elapsedtime = now - timestr2flt(m1['pubTime'])
            #logger.info('1 Time=%s' %  str(elapsedtime))
            wait = False

            # If same message found in the delay list, replaced it with the one in ok list.
            new_ok_delay = []
            for m2 in self.ok_delay:
                if m1['relPath'] == m2['relPath']:
                    logger.info(
                        f"intermediate version suppressed: {m1['relPath']}")
                    self.suppressions += 1
                    new_ok_delay.append(m1)
                    worklist.rejected.append(m2)
                    wait = True
                else:
                    new_ok_delay.append(m2)
                    #new_incoming.append(m1)
            self.ok_delay = new_ok_delay

            # If it's new, put it in delay list too.
            # else if replacing a message in delay, do nothing
            # else put it back to incoming
            if not wait and elapsedtime < self.o.mdelay:
                self.ok_delay.append(m1)
            elif wait:
                pass
            else:
                new_incoming.append(m1)

        worklist.incoming = new_incoming

        # Check message in the delay list
        new_ok_delay = []
        for m1 in self.ok_delay:
            #logger.info('2 relPath=%s' %  m1['relPath'])
            #logger.info('2 pubTime=%s' %  m1['pubTime'])
            elapsedtime = nowflt() - timestr2flt(m1['pubTime'])
            #logger.info('Time=%s' %  str(elapsedtime))
            # if it's time, the message is putting back to the ok list to publish
            if elapsedtime >= self.o.mdelay:
                #logger.info('OK')
                worklist.incoming.append(m1)
            else:
                new_ok_delay.append(m1)
        self.ok_delay = new_ok_delay

        if self.stop_requested:
            worklist.incoming.extend(self.ok_delay)
            self.ok_delay = []
            logger.info('stop requested, ok_delay queue drained')

    def on_housekeeping(self):
        logger.info(
            f'suppressions={self.suppressions} currently delay queue length:{len(self.ok_delay)}'
        )
        self.suppressions = 0

    def please_stop(self):
        logger.error('acknowledged')
        self.stop_requested = True

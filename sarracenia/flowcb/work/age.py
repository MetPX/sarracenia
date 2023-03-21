"""
   print the age of files written (compare current time to mtime of message.)
   usage:

   flowcb work.age

"""

import os, stat, time
import datetime
import json
import logging
import sarracenia 
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Age(FlowCB):

    def reset_metrics(self) -> None:
        self.metrics={}
        self.metrics['ageTotal'] = 0
        self.metrics['ageCount'] = 0
        self.metrics['ageMax'] = 0

    def on_start(self) -> None:
        self.reset_metrics()

    def metricsReport(self) -> dict:
        if self.metrics['ageCount'] > 0:
            self.metrics['ageMean'] = self.metrics['ageTotal']/self.metrics['ageCount']
        else:
            self.metrics['ageMean'] = 0

        return self.metrics

    def on_housekeeping(self) -> None:
        #logger.info( f" maximum Age: {datetime.timedelta(seconds=self.metrics['ageMax'])}  Average Age: {datetime.timedelta(seconds=self.metrics['ageMean'])} files: {self.metrics['ageCount']}" )
        logger.info( "Age of files (in seconds) when transfer complete, maximum: %.2g Average: %.2g file count: %d" % 
            ( self.metrics['ageMax'], self.metrics['ageMean'], self.metrics['ageCount'] ) )


    def after_work(self, worklist) -> None:
        for m in worklist.ok:
            if not 'mtime' in m:
                return None
            completed = sarracenia.timestr2flt(m['timeCompleted'])
            mtime = sarracenia.timestr2flt(m['mtime'])
            age = completed - mtime
            self.metrics['ageTotal'] += age
            self.metrics['ageCount'] += 1
            if age > self.metrics['ageMax']:
                self.metrics['ageMax'] = age

            logger.info("file %s is %d seconds old" % (m['new_dir']+os.sep+m['new_file'], age))

     

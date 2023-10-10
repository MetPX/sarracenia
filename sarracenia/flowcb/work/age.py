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
        self.metrics['copyTotal'] = 0
        self.metrics['copyMax'] = 0

    def on_start(self) -> None:
        self.reset_metrics()

    def metricsReport(self) -> dict:
        self.metrics['copyCount'] =  self.metrics['ageCount']
        if self.metrics['ageCount'] > 0:
            self.metrics['ageMean'] = self.metrics['ageTotal']/self.metrics['ageCount']
            self.metrics['copyMean'] = self.metrics['copyTotal']/self.metrics['ageCount']
        else:
            self.metrics['ageMean'] = 0
            self.metrics['copyMean'] = 0

        return self.metrics

    def on_housekeeping(self) -> None:
        #logger.info( f" maximum Age: {datetime.timedelta(seconds=self.metrics['ageMax'])}  Average Age: {datetime.timedelta(seconds=self.metrics['ageMean'])} files: {self.metrics['ageCount']}" )
        logger.info( "Age of files (in seconds) when transfer complete, maximum: %.2g Average: %.2g file count: %d" % 
            ( self.metrics['ageMax'], self.metrics['ageMean'], self.metrics['ageCount'] ) )

        logger.info( "Copy time for files (in seconds) when transfer complete, maximum: %.2g Average: %.2g file count: %d" % 
            ( self.metrics['copyMax'], self.metrics['copyMean'], self.metrics['ageCount'] ) )


    def after_work(self, worklist) -> None:
        for m in worklist.ok:
            if not 'mtime' in m:
                return None
            completed = sarracenia.timestr2flt(m['report']['timeCompleted'])
            mtime = sarracenia.timestr2flt(m['mtime'])
            pubtime = sarracenia.timestr2flt(m['pubTime'])
            age = completed - mtime
            copy = completed - pubtime
            self.metrics['ageTotal'] += age
            self.metrics['copyTotal'] += copy
            self.metrics['ageCount'] += 1
            if copy > self.metrics['copyMax']:
                self.metrics['copyMax'] = copy
            if age > self.metrics['ageMax']:
                self.metrics['ageMax'] = age

            logger.info( f"file {m['new_dir']+os.sep+m['new_file']} took {copy} seconds to copy and is {age} seconds old"  )

     

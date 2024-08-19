
import logging
import sarracenia
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Report(FlowCB):
    """
       The reporting flow callback class. reports are messages meant to be sent by 
       consumers back to publishers to provide publishers with telemetry data about
       how many consumers are downloading, and how it went.
       minimally it can be invoked with:

       callback report

       and default settings might work.

       report_broker -- the broker to send reports to, defaults to the same as broker.
       report_exchange -- exchange to publish reports to, default depends on broker user.
              if the broker user has a feeder or admin role, then defaults to xreport.

              otherwise, default is xr_<username}.
              can override with this setting.

       repot_topicPrefix, report_topic, report_exchangeSplit ... same as for post_broker.

    """
    def __init__(self, options):

        super().__init__(options,logger)
        self.o.add_option( 'report_exchangeSplit', 'count', 0 )
        self.o.add_option( 'report_topicPrefix', 'list', ['v03'] )
        self.o.add_option( 'report_topic', 'str', None )
        self.o.add_option( 'report_broker', 'str', None )
        self.o.add_option( 'report_exchange', 'str', None )

        if not hasattr(self.o, 'report_broker') and getattr(self.o,'broker'):
            self.o.report_broker = self.o.broker

        if hasattr(self.o, 'report_broker') and self.o.report_broker:
            if type(self.o.report_broker) == str:
                ok, cred_details = self.o._validate_urlstr(self.o.report_broker)
                if ok:
                    self.o.report_broker = cred_details
      
        if not hasattr( self.o, 'report_exchange' ) or not getattr( self.o, 'report_exchange'):
            # guess default report exchange.
            if hasattr(self.o.report_broker,'url') and hasattr(self.o.report_broker.url,'username'):
                user = self.o.report_broker.url.username
                exchange = 'xr_' + user
                if user in self.o.declared_users:
                    role=self.o.declared_users[user]
                    if role in 'feeder' in  [ 'feeder', 'admin' ]:
                        exchange = 'xreport'
                self.o.report_exchange = exchange

        logger.info( f" defaulting reporting to {self.o.report_broker}/{self.o.report_exchange} " )
            
        self.__reset()

        if hasattr(self.o, 'report_broker'):
            props = sarracenia.moth.default_options
            props.update(self.o.dictify())
            logger.info( f" in props... report_broker: {props['report_broker']}" )

            if hasattr(self.o, 'topic' ):
                del self.o['topic']

            # adjust settings post_xxx to be xxx, as Moth does not use post_ ones.
            for k in [ 'broker', 'exchange', 'topicPrefix', 'exchangeSplit', 'topic' ]:
                post_one='report_'+k
                if hasattr( self.o, post_one ) and getattr( self.o, post_one):
                    props[ k ] = getattr(self.o,post_one)

            logger.info( f" in props... report_broker: {props['broker']}, exchange: {props['exchange']}" )
            self.poster = sarracenia.moth.Moth.pubFactory(props)
            logger.info( f" poster: {self.poster} " )
        else:
            self.poster = None

    def __reset(self):
        self.last_housekeeping = sarracenia.nowflt()
        self.reportCount = 0
        self.reportRate = 0

    def metricsReport(self):
        return { 'reportRate':self.reportRate, 'reportCount':self.reportCount }

    def reportPost(self,m):

        if  not hasattr(self.poster,'putNewMessage'):
            return

        if 'report' not in m:
            logger.error( f"not reporting because no disposition defined for {m}" )

        if 'content' in m:
            del m['content']

        m['_deleteOnPost'] = m['_deleteOnPost'].difference(set(['report']))

        self.poster.putNewMessage(m)

    def after_accept(self, worklist):
        if not hasattr(self.poster,'putNewMessage'):
            return

        for m in worklist.rejected:
            self.reportPost(m)

    def after_work(self, worklist):
        if not hasattr(self.poster,'putNewMessage'):
            return

        for m in worklist.rejected:
            self.reportPost(m)

    def report(self, worklist):
        if not hasattr(self.poster,'putNewMessage'):
            return

        for m in worklist.ok:
            self.reportPost(m)

        for m in worklist.failed:
            mm=copy.deepcopy(m) # copy because might be retried, so no modification is allowed.
            self.reportPost(mm)

        for m in worklist.rejected:
            self.reportPost(m)

    def stats(self):
        tot = self.reportCount
        how_long = sarracenia.nowflt() - self.last_housekeeping
        if tot > 0:
            apc = 100 * self.reportCount / tot
            rate = self.reportCount / how_long
        else:
            apc = 0
            rate = 0

        self.reportRate = rate
        logger.info( "reports %d, rate %3.1f reports/s" % (self.reportCount , rate))


    def on_declare(self):
        logger.info("hello")
    
    def on_housekeeping(self):
        if hasattr(self,'poster') and self.poster:
            m = self.poster.metricsReport()
            logger.info(
                f"reports: good: {m['txGoodCount']} bad: {m['txBadCount']} bytes: {m['txByteCount']}"
            )
            self.poster.metricsReset()

        if set(['on_housekeeping']) & self.o.logEvents:
            self.stats()
            logger.info("housekeeping")
        self.__reset()

    def on_stop(self):
        if hasattr(self,'poster') and self.poster:
            self.poster.close()
        logger.info('closing')

    def please_stop(self) -> None:
        """ pass stop request along to publisher Moth instance(s)
        """
        super().please_stop()
        if hasattr(self, 'poster') and self.poster:
            logger.debug("asking Moth publisher to please_stop")
            self.poster.please_stop()

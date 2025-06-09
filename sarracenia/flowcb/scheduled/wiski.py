import logging
import requests
import base64

import datetime
import os
import sys
import time

from datetime import date

import sarracenia
from sarracenia.flowcb.scheduled import Scheduled

#
# Support for features inventory mechanism.
#
from sarracenia.featuredetection import features

features['wiski'] = { 'modules_needed': [ 'kiwis_pie' ], 'Needed': True,
        'lament' : 'cannot poll sites that provide data using WISKI API' ,
        'rejoice' : 'can poll sites that provide data with WISKI API' }

try:
    from kiwis_pie import KIWIS
    sarracenia.features['wiski']['present'] = True
except:
    sarracenia.features['wiski']['present'] = False



logger = logging.getLogger(__name__)




class Wiski(Scheduled):
    """
      
       Plugin to Poll a WISKIS server that uses
            https://www.kisters.net/wiski

       Uses the kiwis_pie package to do that.
            https://github.com/amacd31/kiwis_pie

       Documentation on the kiwis_pie package can be found on
            https://kiwis-pie.readthedocs.io/en/latest/api/kiwis_pie.html


       In the credentials.conf file, need an authentication  entry like:

       https://user:password@theserver.com

       and in the config file:

       pollUrl https://theserver.com

       wiski polling parametrization (these are defined by and passed to kiwis_pie):

       wiski_ts_length -- how long a timeseries to request (default is 24 hours)
       wiski_ts_name   -- list of timeseries to ingest
       wiski_return_fields -- Fields of data to retrieve and to be included in resulted file.
       wiski_reject_parameterTypeName -- Parameters to reject from a given station (example 'Battery Voltage')

       inherits the following settings from Scheduled (interval overrides the other two.)

       scheduled_hour    -- a list of hours (0-59) to poll.
       scheduled_minute -- a list of minutes (0-59) to poll. 
       scheduled_interval  -- just a time interval between polls.

       2023/09 plugin by Peter Silva, based on original tidbits by Mohamed Rehouma.
    """

    def __init__(self,options):
        super().__init__(options,logger)

        # use self.o.PollUrl for credentials.
        self.details = None
        if self.o.pollUrl is not None:
            ok, self.details = sarracenia.config.Config.credentials.get(
                self.o.pollUrl)

        if self.o.pollUrl is None or self.details == None:
            logger.error("pollUrl option incorrect or missing\n")
            sys.exit(1)

        # assert: now self.details.url.username/password are set.
        self.basic_auth = "Basic " + base64.b64encode(f"{self.details.url.username}:{self.details.url.password}".encode()).decode()

        if self.details.url.port:
            self.main_url = self.details.url.scheme + "://" + self.details.url.hostname + ":" + self.details.url.port + "/KiWIS/KiWIS"
        else:
            self.main_url = self.details.url.scheme + "://" + self.details.url.hostname + "/KiWIS/KiWIS"

        self.host = self.details.url.hostname
        self.token = None
        #self.token = self.submit_tokenization_request()

        # meteorological parameter settings.
        self.o.add_option( 'wiski_ts_length', 'duration', '24h' )
        self.o.add_option( 'wiski_ts_name', 'list', [] )
        self.o.add_option( 'wiski_reject_parameterTypeName', 'list', [] )
        self.o.add_option( 'wiski_return_fields', 'list' , ['Timestamp','Value'])
        self.o.add_option( 'wiski_json', 'flag' , False)
        
        self.ts_length = datetime.timedelta( seconds=self.o.wiski_ts_length )
        
        logger.info( f"main_url: {self.main_url} timeseries_length={self.ts_length}, writing to {self.o.directory}" )


    
    def submit_tokenization_request(self):
        # ECCC User Definition
       
        logger.info("Requesting a new token")

        body_string = "grant_type=client_credentials&scope=empty"
        
        # Request Token using HTTP POST request
        token_url = "https://" + self.host + "/KiWebPortal/rest/auth/oidcServer/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self.basic_auth,
            "Host": self.host,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        

        response = requests.post(token_url, data=body_string, headers=headers)
        
        str_response_status = response.status_code
        str_response_text = response.text
        logger.debug(f"Response: {response.text}")
        
        # Process response
        token_array = str_response_text.split('"')
        if str_response_status == 201:
            submit_tokenization_request = token_array[3]
        else:
            logger.error( f"tokenization_request status: {str_response_text}" )
            submit_tokenization_request = "Error"
        
        return submit_tokenization_request

    def gather(self,messageCountMax): # placeholder
        
        messages=[]

        if not self.ready_to_gather():
            return (False, [])

        start_time = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
        while (1):
            if self.stop_requested or self.housekeeping_needed:
                return (False, messages)
        
            self.token = self.submit_tokenization_request()
            authenticated_url = self.main_url
            headers = {
                "Authorization" : f"Bearer {self.token}",
                "Content-Type" : "application/json"
            }

            logger.debug(f"Headers: {headers}")
        
            response = requests.get(authenticated_url,headers=headers)
        
            logger.info(response)

            if response.status_code == 200:
                break
            else:
                logger.info( f"request failed. Status code: {response.status_code}: {response.text}" )
            
            now = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
            self.housekeeping_needed = ((now-start_time).total_seconds() >= self.o.housekeeping)
        
        k = KIWIS(self.main_url, headers=headers )

        now = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
        then = now - self.ts_length


        logger.info( f"stations: {k.get_station_list().station_id}" )
        directory=self.o.variableExpansion( self.o.directory )
        logger.info( f"current directory: {directory}" )
        os.makedirs(directory, self.o.permDirDefault, True)


        for station_id in k.get_station_list().station_id:

            if self.stop_requested:
                return (False, messages)

            timeseries = k.get_timeseries_list(station_id = station_id , return_fields=['ts_id', 'ts_name', 'parametertype_name'] )
            parameters = k.get_parameter_list(station_id = station_id)
            logger.debug( f"looping over the timeseries: \n{timeseries}" )
            logger.debug( f"Parameter options: \n{parameters}" )

            if not parameters['station_no'].empty :
                station_no = parameters['station_no'][0]
            else:
                station_no = station_id

            for i in range(len(timeseries['ts_id'].values)):
                ts_id = timeseries['ts_id'].values[i]
                ts_name = timeseries['ts_name'].values[i]
                parameter_type = timeseries['parametertype_name'].values[i]

                if self.o.wiski_reject_parameterTypeName != [] and parameter_type in self.o.wiski_reject_parameterTypeName:
                    logger.debug(f"Parameter type rejected due to not being specified in reject list : {self.o.wiski_reject_parameterTypeName}. Skipping.")
                elif self.o.wiski_ts_name != [] and ts_name not in self.o.wiski_ts_name:
                    logger.debug(f"Timeseries name rejected due to not being specified in list : {self.o.wiski_ts_name}. Skipping.")
                else:

                    # Have '-' between variables in filename for easier identification of fields
                    parameter_type = parameter_type.replace(' ', '-').replace(')','-').replace('(','-').replace('/','-')
                    station_no = station_no.replace('_', '-')
                    ts_name = ts_name.replace('_', '-')

                    suffix = 'json' if self.o.wiski_json else 'csv'

                    # writing files on windows is quite painful, so many illegal characters.
                    if sys.platform.startswith( "win" ):
                        fname = f"{directory}{os.sep}ts_{ts_name}_{station_no}__{parameter_type}.{suffix}"
                        fname = fname[0:3]+fname[3:].replace(':','_').replace('.','_',1).replace('+','_').replace('-','_')
                    else:
                        fname = f"{directory}{os.sep}ts_{ts_name}_{station_no}__{parameter_type}.{suffix}"

                    logger.info( f"Timeseries {ts_name} for station_id {station_no} to be written to: {fname}" )
    
                    #ts=k.get_timeseries_values(ts_id = ts_id, to = date(2023,1,31), **{'from': date(2023,1,1)})
                    ts=k.get_timeseries_values(ts_id = ts_id, to = now, **{'from': then}, return_fields=self.o.wiski_return_fields)
                    if len(ts) > 0:

                        f=open(fname,'w')
                        ts.to_json(f, date_format='iso') if self.o.wiski_json else ts.to_csv(f)
                        f.close()
                    else:
                        logger.info( f"No data to write to {fname}. Continuing.")
                        continue
                    messages.append( sarracenia.Message.fromFileData( fname, self.o, os.stat(fname) ) )
    
        return (True, messages)

if __name__ == '__main__':

    import sarracenia.config
    import types
    import sarracenia.flow

    options = sarracenia.config.default_config()
    flow = sarracenia.flow.Flow(options)
    flow.o.scheduled_interval= 5
    flow.o.pollUrl = "https://kiwis.opg.com"
    if sys.platform.startswith( "win" ):
        flow.o.directory = "C:\\temp\\wiski"
    else:
        flow.o.directory = "/tmp/wiski/${%Y%m%d}"
    logging.basicConfig(level=logging.DEBUG)

    me = Wiski(flow.o)
    me.gather(flow.o.batch)


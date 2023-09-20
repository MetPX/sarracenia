import logging
import requests
import base64

import datetime
import os
import time

from datetime import date
from kiwis_pie import KIWIS

import pandas as pd

import sarracenia

from sarracenia.flowcb.scheduled import Scheduled

logger = logging.getLogger(__name__)

class Wiski(Scheduled):
    """
      
       Plugin to Poll a WISKIS server that uses  ( https://www.kisters.net/wiski )

       In the credentials.conf file, have an entry like:

       https://user:password@theserver.com

       and in the config file:

       pollUrl https://theserver.com


       inherits the following settings from Scheduled (interval overrides the other two.)

       scheduled_hour    -- a list of hours (0-59) to poll.
       scheduled_minute -- a list of minutes (0-59) to poll. 
       scheduled_interval  -- just a time interval between polls.

       2023/09 plugin by Peter Silva, based on original proof of concept work by Mohamed Rehouma.
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

        self.token = None
        #self.token = self.submit_tokenization_request()

        # meteorological parameter settings.
        self.o.add_option( 'wiski_ts_length', 'duration', '24h' )
        self.o.add_option( 'wiski_ts_name', 'str', 'caw_Cmd' )
        self.o.add_option( 'wiski_ts_parameterTypeName', 'str', 'Air Temperature' )
        
        self.ts_length = datetime.timedelta( seconds=self.o.wiski_ts_length )
        
        logger.info( f"main_url: {self.main_url} timeseries_length={self.ts_length}, writing to {self.o.directory}" )


    
    def submit_tokenization_request(self):
        # ECCC User Definition
       
        logger.info("requesting a new token")

        body_string = "grant_type=client_credentials&scope=empty"
        
        # Request Token using HTTP POST request
        token_url = self.main_url + "/KiWebPortal/rest/auth/oidcServer/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + self.basic_auth,
            "Host": "kiwis.opg.com",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        
        response = requests.post(token_url, data=body_string, headers=headers)
        
        str_response_status = response.status_code
        str_response_text = response.text
        
        # Process response
        token_array = str_response_text.split('"')
        if str_response_status == 201:
            submit_tokenization_request = token_array[3]
        else:
            submit_tokenization_request = "Error"
        
        return submit_tokenization_request
    
    def gather(self): # placeholder
        
        
        messages=[]

        self.wait_until_next()

        if self.stop_requested:
            return messages
        
        while (1):
            authenticated_url = "https://kiwis.opg.com/KiWIS/KiWIS"
            headers = {
                "Authorization" : f"Bearer {self.token}",
                "Content-Type" : "application/json"
            }
        
            response = requests.get(authenticated_url,headers=headers)
        
            logger.info(response)

            if response.status_code == 200:
                break
            elif str_response_status == 403:
                # Call the function and save in variable
                logger.info( f"permission denied" )
                self.token = self.submit_tokenization_request()
            else:
                logger.info("request failed. Status code: " + response.status_code)
                logger.info("response: " + response.text)
        
        k = KIWIS('https://kiwis.opg.com/KiWIS/KiWIS')

        now = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
        then = now - self.ts_length

        for station_id in k.get_station_list().station_id:
            fname = f"{self.o.directory}/ts_{station_id}_{str(then).replace(' ','h')}_{str(now).replace(' ','h')}.csv" 
            f=open(fname,'w')
            logger.warning( f"station_ids: {station_id} writing to: {fname}" )
            for ts_id in k.get_timeseries_list(station_id = station_id, ts_name =self.o.wiski_ts_name, parametertype_name = self.o.wiski_ts_parameterTypeName ).ts_id:
                #print(k.get_timeseries_values(ts_id = ts_id, to = date(2023,1,31), **{'from': date(2023,1,1)}))
                #print(k.get_timeseries_values(ts_id = ts_id, to = now, **{'from': then}))
                (k.get_timeseries_values(ts_id = ts_id, to = now, **{'from': then})).to_csv(f)
            f.close() 
            messages.append( sarracenia.Message.fromFileData( fname, self.o, os.stat(fname) ) )
    
        return messages

if __name__ == '__main__':

    import sarracenia.config
    import types
    import sarracenia.flow

    options = sarracenia.config.default_config()
    flow = sarracenia.flow.Flow(options)
    flow.o.scheduled_interval= 5
    flow.o.pollUrl = "https://kiwis.opg.com"
    flow.o.directory = "/tmp/wiski"
    logging.basicConfig(level=logging.DEBUG)

    me = Wiski(flow.o)
    me.gather()


"""
Polls the Copernicus Marine Data Store STAC API and S3 buckets.
----------------------------------------------------------------

Based on https://github.com/MetPX/sarracenia/blob/development/sarracenia/flowcb/poll/s3bucket.py

This was developed because the software provided by Copernicus, the Copernicus Marine Toolbox requires 
Python >= 3.9 and seemed difficult to integrate into Sarracenia data flows. We also prefer to not install
packages on our servers using pip when possible. 
This plugin lets us find URLs in a normal Sarracenia poll and apply accept/reject filtering to narrow down
the files we want. Duplicate suppression can also be used.

Documentation from Copernicus Marine:

https://help.marine.copernicus.eu/en/collections/4060068-copernicus-marine-toolbox
https://marine.copernicus.eu/news/introducing-new-copernicus-marine-data-store
https://help.marine.copernicus.eu/en/articles/8612591-switching-from-current-to-new-services
https://marine.copernicus.eu/news/unveiling-exciting-updates-copernicus-marine-service-november-2023-release
https://pypi.org/project/copernicusmarine/

NOTE: No authentication is currently used, and it doesn't seem to be necessary right now. This might need
to be updated in the future if they require authentication.

Additional filtering can be performed on datasets for a productID. 
Add dataset_href=some_regex to the end of a productID to include only datasets with hrefs that match the regex.

Example Config:
^^^^^^^^^^^^^^^

::

    callback poll.copernicus_marine_s3

    # This is the base URL for the Copernicus Marine STAC API
    pollUrl https://stac.marine.copernicus.eu/metadata

    productID INSITU_GLO_PHYBGCWAV_DISCRETE_MYNRT_013_030 dataset_href=.*latest.*
    productID SEALEVEL_GLO_PHY_L3_NRT_008_044
    productID SEALEVEL_GLO_PHY_L4_NRT_008_046

    # post_baseUrl will be overriden by the plugin. No need to set it in the config.

"""
import boto3
import botocore
import logging
import paramiko
import sarracenia
import urllib.parse
import requests
import re

logger = logging.getLogger(__name__)

class Copernicus_marine_s3(sarracenia.flowcb.FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)

        # Allow setting a logLevel *only* for this plugin in the config file:
        # set poll.copernicus_marine_s3.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())
            logger.debug(f"logLevel {self.o.logLevel.upper()}")

        self.o.add_option('productID', kind='list', default_value=[])
        
        self.stac_base_url = self.o.pollUrl
        if self.stac_base_url[-1] != '/':
            self.stac_base_url += '/'
        
        # Parse productIDs
        self.productIDs = {}
        for product_id in self.o.productID:
            parts = product_id.split(' ')
            name = parts[0]
            try:
                self.productIDs[name] = None
                if len(parts) > 1:
                    regex = parts[1].split("dataset_href=")[1].strip()
                    self.productIDs[name] = re.compile(regex)
            except Exception as e:
                logger.error(f"Invalid productID {product_id} - check the config file!")
                logger.debug("Exception details:", exc_info=True)
        
        self.botocore_config = botocore.config.Config(s3={"addressing_style": "virtual"}, 
                                                      signature_version=botocore.UNSIGNED)

    def get_s3_urls_from_stac(self, productIDs):
        """ Poll the STAC API to find S3 dataset URLs for each ProductID
        """
        s3_urls = {}
        for id in productIDs:
            try:
                resp = requests.get(self.stac_base_url + id + '/product.stac.json')
                resp.raise_for_status()

                product_page = resp.json()
                datasets = set()
                for link in product_page['links']:
                    if 'dataset.stac.json' in link['href']:
                        if productIDs[id]: # if there's a regex filter for this productID
                            if productIDs[id].match(link['href']):
                                datasets.add(link['href'])
                            else:
                                logger.debug(f"{link['href']} doesn't match {productIDs[id]}, ignoring")
                        else: # no regex, no need to filter        
                            datasets.add(link['href'])
                
                if len(datasets) == 0:
                    logger.error(f"Failed to find dataset/collection link for productID {id}")
                    continue # keep trying other productIDs
                
                for dataset in datasets:
                    resp = requests.get(self.stac_base_url + id + '/' + dataset)
                    if not resp:
                        logger.error(f"Failed to get info for {dataset}")
                        continue
                    # Get the s3 URL from the assets section
                    dataset_page = resp.json()
                    if 'native' in dataset_page['assets']:
                        if id not in s3_urls:
                            s3_urls[id] = []
                        s3_urls[id].append(dataset_page['assets']['native']['href'])
                    else: 
                        logger.error("Failed to find Native dataset S3 URL for productID {id} + dataset {dataset}")
                        logger.debug(f"dataset page: {self.stac_base_url + id + '/' + dataset}")

            except Exception as e:
                logger.error(f"Could not poll productID {id} ({e})")
                logger.debug(f"Exception:", exc_info=True)
        
        logger.debug(f"STAC poll found {s3_urls}")
        return s3_urls

    def _identify_client(self, model, params, request_signer, **kwargs):
        """ Tell Copernicus who we are.
        """
        # TODO: They also use x-cop-user = username, but we're not using a user account right now. If authentication
        # is required in the future, we should set it.
        try:
            ident = {"x-cop-client": 'Sarracenia' + sarracenia.__version__}
            for item in ident:
                params['headers'][item] = ident[item]
                # The Copernicus Marine Toolbox client sets URL parameters
                params['query_string'][item] = ident[item]
                params['url'] += urllib.parse.quote(f'&{item}={ident[item]}', safe='/&=')

            if 'User-Agent' in params['headers']:
                params['headers']['User-Agent'] = 'Sarracenia' + sarracenia.__version__ + ' ' + params['headers']['User-Agent']
            
            logger.debug(f"request: {model}, params: {params}, request_signer: {request_signer}, kwargs: {kwargs}")
        except:
            # Don't really care if this fails, something wrong in this method shouldn't stop the poll from working
            logger.debug('Exception setting identification', exc_info=True)

    def poll(self):
        """ Do the poll. First use their STAC API to find which S3 buckets and endpoints we need to poll for each
            Product ID defined in the config. Then actually poll the S3 buckets.
        """
        gathered_msgs = []
        s3_urls = self.get_s3_urls_from_stac(self.productIDs)

        # EXAMPLE URL:
        #           endpoint              | bucket      | prefix
        # https://s3.waw3-1.cloudferro.com/mdl-native-07/native/SEALEVEL_GLO_PHY_L3_NRT_008_044/cmems_obs-sl_glo_phy-ssh_nrt_h2b-l3-duacs_PT0.2S_202311
        # Get which buckets and prefixes to poll for each endpoint
        bucket_prefix_by_endpoint = {}
        for id in s3_urls:
            for url in s3_urls[id]:
                pr = urllib.parse.urlparse(url)
                endpoint = pr.scheme + '://' + pr.netloc
                bucket = pr.path.strip('/').split('/')[0]
                prefix = '/'.join(pr.path.strip('/').split('/')[1:])
                if endpoint not in bucket_prefix_by_endpoint:
                    bucket_prefix_by_endpoint[endpoint] = []
                bucket_prefix_by_endpoint[endpoint].append({'bucket':bucket, 'prefix':prefix})
        
        logger.debug(f"Going to S3 list {bucket_prefix_by_endpoint}")

        # Have a bunch of prefixes now (directories), poll them to find files
        objects_by_endpoint_bucket = {}
        for endpoint in bucket_prefix_by_endpoint:
            objects_by_endpoint_bucket[endpoint] = {}
            try:
                s3 = boto3.client("s3", config=self.botocore_config, endpoint_url=endpoint)
                # Tell Copernicus who we are, for their monitoring
                s3.meta.events.register("before-call.s3.ListObjects", self._identify_client)
                for bucket_prefix in bucket_prefix_by_endpoint[endpoint]:
                    logger.info(f"\bing s3://{bucket_prefix['bucket']}/{bucket_prefix['prefix']} @ endpoint {endpoint}")
                    # s3.list_objects returns a maximum of 1000 items, need to use paginator instead
                    operation = 'list_objects_v2' if 'list_objects_v2' in dir(s3) else 'list_objects'
                    paginator = s3.get_paginator(operation)
                    page_iterator = paginator.paginate(Bucket=bucket_prefix['bucket'], Prefix=bucket_prefix['prefix'])
                    for page in page_iterator:
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                if bucket_prefix['bucket'] not in objects_by_endpoint_bucket[endpoint]:
                                    objects_by_endpoint_bucket[endpoint][bucket_prefix['bucket']] = []
                                objects_by_endpoint_bucket[endpoint][bucket_prefix['bucket']].append(obj)
                        if self.stop_requested:
                            break
                    if self.stop_requested:
                            break
            except Exception as e:
                logger.error(f"Error during S3 poll for endpoint {endpoint} ({e})")
                logger.debug(f"Exception:", exc_info=True)

        # Build a message for each object we found
        for endpoint in objects_by_endpoint_bucket:
            for bucket in objects_by_endpoint_bucket[endpoint]:
                for obj in objects_by_endpoint_bucket[endpoint][bucket]:
                    stat = paramiko.SFTPAttributes()
                    if 'LastModified' in obj:
                        t = obj["LastModified"].timestamp()
                        stat.st_atime = t
                        stat.st_mtime = t
                    if 'Size' in obj:
                        stat.st_size = obj['Size']
                    
                    file_path = bucket + '/' + obj['Key']
                    msg = sarracenia.Message.fromFileInfo(file_path, self.o, stat)
                    # The (new_)baseUrl field will be set to the post_baseUrl from the config, or pollUrl if
                    # post_baseUrl is not set. We need to override it here, because the baseUrl can change if the
                    # files are coming from different endpoints. 
                    msg['baseUrl'] = endpoint
                    msg['new_baseUrl'] = endpoint
                    # When Sarracenia runs updatePaths again later, from sarracenia.Flow, self.o.post_baseUrl will be
                    # different, so set msg['post_baseUrl'] here to override whatever setting it has at that point.
                    msg['post_baseUrl'] = endpoint
                    msg['_deleteOnPost'] |= {'post_baseUrl'}
                    
                    gathered_msgs.append(msg)

        logger.info(f"found {len(gathered_msgs)} files, Sarracenia will filter them")
        return gathered_msgs


"""
Place holder customized flow callback classes whose focus is the download() entry point.

download(self,msg):

    Task: looking at msg['new_dir'], msg['new_path'], msg['new_inflight_path'] 
          and the self.o options perform a download of a single file.
          return True on a successful transfer, False otherwise.

    if self.o.dry_run is set, simulate the output of a download without
    performing it.

    downlaod is called by the sarra and subscribe components, and can be used 
    to override the built-in methods for downloading a file. 

    It does the download based on the fields in the message provided:

    retreival path: msg['baseUrl'] + '/' + msg['relPath'] 

    taking care of the inflight setting, the inflight/temporary file: 
    is defined for use by the download routing: msg['new_inflight_path'] 

    Final local location to store is defined by:

        msg['new_path'] == msg['new_dir'] + '/' + msg['new_file']

 
    This replaces built-in download functionality, providing an override.
    for individual file transfers. ideally you set checksums as you download.
            
    looking at self.o.identity_method to establish download checksum algorithm.
    might have to allow for cod... say it is checksum_method::
            
         checksum = sarracenia.identity.Identity.factory(self.o.checksum_method)
         while downloading:
             checksum.update(chunk)

    where chunk is the bytes read. It saves a file read to calculate the checksum
    during the download.
 
    if the checksum does not match what is in the received message, then 
    it is imperative, to avoid looping, to apply the actual checksum of the
    data to the message:

         msg['identity'] =  { 'method': checksum_method, 'value': checksum.get_sumstr() }
   
    return Boolean success indicator.  if False, download  will be attempted again and/or
    appended to retry queue.


"""

pass

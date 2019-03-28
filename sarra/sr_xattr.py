

try:
    import xattr
    supports_extended_attributes=True

except:
    supports_extended_attributes=False
    
try:
    from sarra.pyads import ADS
    supports_alternate_data_streams=True

except:
    supports_alternate_data_streams=False

import json

STREAM_NAME = 'sr_.json'

class sr_xattr:

   def __init__(self,path):

       self.path = path
       self.x = {}
       self.dirty = False

       if supports_alternate_data_streams:
           self.ads = ADS(path)
           s = self.ads.list()
           if STREAM_NAME in s:
              self.x = json.loads( self.ads.get_stream_content(STREAM_NAME)  )

       if supports_extended_attributes:
          d = xattr.xattr(path)
          for i in d:
              if not i.startswith('user.sr_'):
                 continue
              k= i.replace('user.sr_','') 
              v= d[i].decode('utf-8')
              self.x[k] = v

   def __del__(self):
       self.persist()

   """
     return a dictionary of extended attributes.

   """
   def list(self):
       return self.x.keys()

   def get(self,name):
       if name in self.x.keys():
           return self.x[ name ]
       return None

   def set(self,name,value):
       self.dirty = True
       self.x[ name ] = value      

   def persist(self):

       if not self.dirty:
          return

       if supports_alternate_data_streams:
          #replace STREAM_NAME with json.dumps(self.x)
          if STREAM_NAME in self.ads.streams:
               self.delete_stream(STREAM_NAME)

          self.add_stream_from_string(STREAM_NAME,json.dumps(self.x))

       if supports_extended_attributes:
          #set the attributes in the list. encoding utf8...
          try: 
              for i in self.x:
                  xattr.setxattr( self.path, 'user.sr_' + i, bytes( self.x[i], 'utf-8' ) )
          except:
              # not really sure what to do in the exception case...
              # permission would be a normal thing and just silently fail...
              pass

       self.dirty = False

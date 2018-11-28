class File_RxPipe(object):
  """
    The File_RxPipe plugin takes names of all the files downloaded and feeds them to a named pipe.
    The pipe name is given by the 'file_rxpipe_name' setting in the configuration file.

    ...sr_subscribe config file snippet ..

    file_rxpipe_name /home/peter/test/dd_rxpipe
    on_file file_rxpipe

    ...

    This is a means of easily integrating with external scripts without understanding sarracenia plugins.
    In a typical subscription configuration there may be five or ten processes writing to the named pipe.
    the user writes their own program to read from the pipe.

    A task will just read from the pipe, most simply as standard input:

    tail -f /home/peter/test/dd_rxpipe

    notes: 
      -- This method is highly efficient in terms of not starting a process for every file received.
         but has the downside of serializes acquisition through a single process.
      -- The single process would best be a sort of dispatcher, rather than actually processing inputs.
      -- one could use different plugins, such as 'on_file_run' to invoke a process on every file received,
         which is parallel, but firing off a process for each file is very inefficient.
   

  """

  def __init__(self,parent):
        if not hasattr(parent,'file_rxpipe_name'):
            parent.logger.error("Missing file_rxpipe_name parameter")
            return 

        self.rxpipe = open( parent.file_rxpipe_name[0], "w" )

  def perform(self, parent):
        self.rxpipe.write( parent.msg.new_file + "\n" )
        self.rxpipe.flush()
        return None

file_rxpipe=File_RxPipe(self)
self.on_file=file_rxpipe.perform



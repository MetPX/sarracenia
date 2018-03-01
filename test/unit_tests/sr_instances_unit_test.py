#!/usr/bin/env python3

try :
         from sr_config          import *
         from sr_instances       import *
except :
         from sarra.sr_config    import *
         from sarra.sr_instances import *

# ===================================
# MAIN
# ===================================

class test_instances(sr_instances):
     
      def __init__(self,config=None,args=None):
         sr_instances.__init__(self,config,args)

      def close(self):
          pass

      def reload(self):
          self.logger.info("reloaded")
          self.close()
          self.configure()
          self.run()

      def run(self):
          while True :
                time.sleep(100000)

      def start(self):
          self.logger.info("started")
          self.run()

      def stop(self):
          self.logger.info("stopped")
          pass

def main():

    failed = False

    # without argument we are running a test
    
    if len(sys.argv) == 1 :
       try :
                subprocess.check_call([ sys.argv[0], 'stop',   './test_instances.conf'])
                time.sleep(1)
                subprocess.check_call([ sys.argv[0], 'start',  './test_instances.conf'])
                time.sleep(1)
                subprocess.check_call([ sys.argv[0], 'restart','./test_instances.conf'])
                time.sleep(1)
                subprocess.check_call([ sys.argv[0], 'reload', './test_instances.conf'])
                time.sleep(1)
                subprocess.check_call([ sys.argv[0], 'status', './test_instances.conf'])
                time.sleep(1)
                subprocess.check_call([ sys.argv[0], 'stop',   './test_instances.conf'])
                time.sleep(1)
       except:  failed = True

    action = sys.argv[-1]
    args   = sys.argv[1:-1]
    config = './test_instances.conf'

    f = open(config,'wb')
    f.close()


    this_test = test_instances(config,args)

    action = sys.argv[-1]

    try :

           if action == 'foreground' : this_test.foreground_parent()
           if action == 'reload'     : this_test.reload_parent()
           if action == 'restart'    : this_test.restart_parent()
           if action == 'start'      : this_test.start_parent()
           if action == 'status'     : this_test.status_parent()
           if action == 'stop'       :
                                       this_test.stop_parent()

    except: 
            failed = True
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_instances.py TEST FAILED")
            sys.exit(1)

    os.unlink('./test_instances.conf')

    if not failed :
                    if len(sys.argv) == 1 : print("sr_instances.py TEST PASSED")
    else :          
                    print("sr_instances.py TEST FAILED")
                    sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()


#!/usr/bin/env python3

try:
    from sr_config import *
    from sr_instances import *
except:
    from sarra.sr_config import *
    from sarra.sr_instances import *

# ===================================
# MAIN
# ===================================


class test_instances(sr_instances):
    def __init__(self, args):
        super(test_instances, self).__init__(args=args)

    def file_set_int(self, path, i):
        return True

    def start(self):
        time.sleep(1)

    def start_instance(self):
        self.start()

    def status_instance(self, sanity=False):
        pass

    def build_instance(self, i):
        self.instance_str = self.program_name
        self.pidfile = self.user_cache_dir + os.sep + sys.argv[0] + '.pid'
        self.pid = os.getpid()

    def stop_instance(self):
        self.pid = None
        self.pidfile = None
        self.instance_str = None


def main():
    if len(sys.argv) == 1:
        # Callback tests with various actions on subprocess sr_instances
        actions = ('foreground', 'start', 'restart', 'reload', 'status',
                   'stop')
        for i, act in enumerate(actions):
            try:
                subprocess.check_call([sys.argv[0], act])
            except subprocess.CalledProcessError as e:
                if e.returncode > 0:
                    print("Test 0%s: sr_instances.py %s did not worked" %
                          (i + 1, act))
                    raise e
            print("Test 0%s: sr_instances.py %s worked" % (i + 1, act))
        print("sr_instances.py TEST PASSED")
    else:
        args = sys.argv[1:-1]
        action = sys.argv[-1]

        this_test = test_instances(args)
        this_test.no = 1
        getattr(this_test, '%s_parent' % action)()


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()

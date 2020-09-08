import sys, os, os.path, time, stat
"""
 When posting a file, insert an hourly directory into the delivery path hierarchy.

 input A/B/c.gif  --> output A/B/<hour>/c.gif


"""


class Renamer(object):
    def __init__(self):
        pass

    def perform(self, parent):
        import time

        datestr = time.strftime('%H', time.localtime())  # pick the hour

        # insert the hour into the rename header of the message to be posted.
        new_fname = parent.msg.headers['rename'].split('/')
        parent.msg.headers['rename'] = '/'.join(
            new_fname[0:-1]) + '/' + datestr + '/' + new_fname[-1]
        parent.logger.info("post_hour_tree: rename: %s" %
                           parent.msg.headers['rename'])

        return True


renamer = Renamer()
self.on_post = renamer.perform

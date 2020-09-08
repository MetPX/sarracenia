#!/usr/bin/python3
"""
This plugin can be use to add ownership and group of a file in a post message (on_post)
and change the owner/group of products at destination (on_file)

Sample usage:

  plugin root_chown.py

Options
-------

If a users/groups differs from the source to the destination, the user can supply a mapping file
which would associate  SRC_UG to DEST_UG.  The filepath is given by giving an absolute path with
option 'mapping_file'. Default value is None, which means give set ownership as for the source user/group.
The 'mapping_file' file format would simply be, a one liner per owner/group

aspymjg:cidx mjg777:ssc_di

here aspymjg:cidx would be the source ownership (source user:group)
and  mjg777:ssc_di  the destination ownership (destination user:group)

"""

import grp, os, pwd


class ROOT_CHOWN(object):
    def __init__(self, parent):

        parent.declare_option('mapping_file')
        self.mapping = {}

    def on_start(self, parent):
        logger = parent.logger

        if not hasattr(parent, "mapping_file"):
            parent.mapping_file = [None]
            return True

        mf_path = parent.mapping_file[0]
        try:
            f = open(mf_path, 'r')
            while True:
                l = f.readline()
                if not l: break
                l2 = l.strip()
                parts = l2.split()
                if len(parts) != 2:
                    logger.error("wrong mapping line %s" % l)
                    continue
                self.mapping[parts[0]] = parts[1]
            f.close()
            logger.info("ROOT_CHOWN mapping_file loaded  %s" % mf_path)
        except:
            logger.error("ROOT_CHOWN problem when parsing %s" % mf_path)

        return True

    def on_post(self, parent):
        import grp, os, pwd

        logger = parent.logger
        msg = parent.msg

        logger.debug("ROOT_CHOWN on_post")

        new_dir = parent.msg.new_dir
        new_file = parent.msg.new_file

        # if remove ...

        if msg.headers['sum'].startswith(
                'R,') and not 'newname' in msg.headers:
            return True

        # if move ... sr_watch sets new_dir new_file on destination file so we are ok

        # already set ... check for mapping switch

        if 'ownership' in msg.headers:
            ug = msg.headers['ownership']
            if ug in self.mapping:
                logger.debug("ROOT_CHOWN mapping from %s to %s" %
                             (ug, self.mapping[ug]))
                msg.headers['ownership'] = self.mapping[ug]
            return True

        # need to add ownership in message

        try:
            local_file = new_dir + os.sep + new_file

            s = os.lstat(local_file)
            username = pwd.getpwuid(s.st_uid).pw_name
            group = grp.getgrgid(s.st_gid).gr_name

            ug = "%s:%s" % (username, group)

            # check for mapping switch
            if ug in self.mapping:
                logger.debug("ROOT_CHOWN mapping from %s to %s" %
                             (ug, self.mapping[ug]))
                ug = self.mapping[ug]

            msg.headers['ownership'] = ug
            logger.debug("ROOT_CHOWN set ownership in headers %s" %
                         msg.headers['ownership'])

        except:
            logger.error("ROOT_CHOWN could not set ownership  %s" % local_file)

        return True

    def on_file(self, parent):
        import grp, os, pwd

        logger = parent.logger
        msg = parent.msg

        logger.debug("ROOT_CHOWN on_file")

        # the message does not have the requiered info

        if not 'ownership' in msg.headers:
            logger.info("ROOT_CHOWN no ownership in msg_headers")
            return True

        # it does, check for mapping

        ug = msg.headers['ownership']
        if ug in self.mapping:
            logger.debug("received ownership %s mapped to %s" %
                         (ug, self.mapping[ug]))
            ug = self.mapping[ug]

        # try getting/setting ownership info to local_file

        local_file = parent.msg.new_dir + os.sep + parent.msg.new_file

        try:
            parts = ug.split(':')
            username = parts[0]
            group = parts[1]

            uid = pwd.getpwnam(username).pw_uid
            gid = grp.getgrnam(group).pw_gid

            os.chown(local_file, uid, gid)
            logger.info("ROOT_CHOWN set ownership %s to %s" % (ug, local_file))

        except:
            logger.error("ROOT_CHOWN could not set %s to %s" %
                         (ug, local_file))

        return True


self.plugin = 'ROOT_CHOWN'

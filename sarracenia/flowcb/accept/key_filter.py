"""
Key Filtering

Normal accept/reject filtering uses regex, which can be computationally expensive. If you have a busy flow and need
many accept/reject statements, this plugin might be a more efficient alternative when filenames (or paths) are
relatively consistent.

It is inspired by the sundewpxroute plugin, but is more generic (does not require a routing table, works with
non-bulletin files by using regex match groups to define what is used as the key for matching).
https://github.com/MetPX/sarracenia/blob/development/sarracenia/flowcb/accept/sundewpxroute.py

The key filtering applies *after* sr3's built-in regex filtering. This plugin assumes you will use a small number
of accept/reject statements and potentially hundreds of accept_key/reject_key statements.

If key_groups= is not defined, key filtering will be skipped for that mask (if the mask is accept, all files matching
will be accepted, and if it's reject, all files matching will be rejected).

You can either specify one group number, or multiple separated by commas. If multiple groups are specified, by default
they will be concatenated together (joined with no separator). If key_filter_join_str is set in the config, they
will be joined by the specified string/character. By setting ``key_filter_join_str _``, you can replicate the
behaviour Sundew used to derive keys (it would use *all* groups in a given regex and join them with _). This plugin
allows the user to specify which groups are used (in case you want to use some groups in the directory but not the
key, or vice-versa). Sundew reference:
https://github.com/MetPX/Sundew/blob/main/doc/man/pxRouting.7.rst#generate-a-product-key


Example Config 1:

    acceptUnmatched False

    callback accept.key_filter

    accept_key AACN01_CWAO
    accept_key AACN02_CWAO
    reject_key SACN01_CWAO

    # at least one accept is required
    directory /
    # Bulletins with Sundew AHL filename format, T1T2A1A2ii_CCCC...
    #                                    ⮦ this is the group used as the key
    accept  .*MSC-BULLETINS.*/([A-Z]{4}[0-9]{2}_[A-Z]{4}).*  key_groups=1

    accept  .*key_filtering_not_applied_for_files_matching_this.*


Example Config 2:

    acceptUnmatched False

    callback accept.key_filter

    accept_key CASMR
    accept_key CASWL

    directory /${1}
    #                                    ⮦ this is the group used as the key
    accept  .*MSC-RADAR.*/(urp.*?)/.*(CAS[A-Z]{2}).*  key_groups=2


Example Config 3 (multiple groups like Sundew):

    acceptUnmatched False

    callback accept.key_filter
    key_filter_join_str _

    accept_key txt:AQ_:AIRNOW:CMQ:ASCII

    directory /${1}/
    # key generated would be txt:AQ_:AIRNOW:CMQ:ASCII
    accept  .*SOURCE/([0-9]{2})/.*(txt:AQ).*(:AIRNOW:.*:ASCII)  key_groups=2,3
"""

import logging

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Key_filter(FlowCB):
    """ Filter messages based on string keys.
    """
    def __init__(self, options):
        super().__init__(options, logger)

        self.o.add_option('accept_key', 'list', [])
        self.o.add_option('reject_key', 'list', [])
        self.o.add_option('key_filter_join_str', 'str', '')

        self._accept_keys = [ k.strip() for k in self.o.accept_key ]
        self._reject_keys = [ k.strip() for k in self.o.reject_key ]

        # determine *which* group number is used to match against keys for each defined accept/reject mask
        self._group_nums_for_mask = []
        for mask in self.o.masks:
            # pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten, args = mask
            pattern, _, _, _, accepting, _, _, _, _, mask_args = mask

            if not accepting:
                self._group_nums_for_mask.append(None)
                continue

            key_groups_args = [ arg for arg in mask_args if 'key_groups=' in arg]

            n_key_groups = len(key_groups_args)
            m_str = f"mask accept {pattern}"

            if n_key_groups < 1:
                logger.warning(f"{m_str} missing key_groups=, all files matching this pattern will be accepted")
                self._group_nums_for_mask.append(None)
            elif n_key_groups > 1:
                raise Exception(f"{m_str} has > 1 key_groups= defined, use comma-separated values " +
                                "(e.g. key_groups=1,2,3). Multiple instances of key_groups= is not supported")
            else:
                _, num = key_groups_args[0].split("key_groups=")
                try:
                    group_nums = [ int(n) for n in num.strip().split(',')]
                    for n in group_nums:
                        if n <= 0:
                            raise Exception(f"{m_str} has an invalid group number (< 1): {group_nums}")
                    self._group_nums_for_mask.append(group_nums)
                except Exception as e:
                    raise Exception(f"{m_str} has invalid {key_groups_args}, {e}, fix your config")

    def derive_key(self, msg):
        """ Given a message and the config, derive a key.
            Returns the key. The key is also stored inside the message, in the ``msg['key_filter_key']``.
            If the mask does not have key_group= then this will return None.
            The message must already contain `_mask_index` and `_matches`.
        """
        # get the key from the regex groups
        group_nums = self._group_nums_for_mask[msg['_mask_index']]
        match = msg['_matches']

        # None is used for masks that don't have key_groups=
        if group_nums is None:
            return None

        # if a valid group number if specified but not present in the regex, it's a config error
        # exception will be raised here, this will log an error but the caller needs to handle it
        try:
            key = self.o.key_filter_join_str.join(match[n] for n in group_nums)
        except Exception as e:
            logger.error(f"key_groups={self._group_nums_for_mask[msg['_mask_index']]}"
                             +f" not in {self.o.masks[msg['_mask_index']]} ({e})")
            raise
        msg['key_filter_key'] = key
        msg['_deleteOnPost'].add('key_filter_key')

        return key

    def after_accept(self, worklist):
        new_incoming = []

        for msg in worklist.incoming:

            # we need _mask_index and _matches are required fields for this to work, but they should always be
            # present, otherwise the msg shouldn't have been put into worklist.incoming.
            # only exception is acceptUnmatched True
            if '_mask_index' not in msg or '_matches' not in msg:
                if self.o.acceptUnmatched:
                    logger.debug(f"things missing from msg, acceptUnmatched enabled, accepting {msg.getIDStr()}")
                    new_incoming.append(msg)
                else:
                    logger.warning(f"things missing from msg, acceptUnmatched disabled, rejecting {msg.getIDStr()}")
                    worklist.rejected.append(msg)
                    msg.setReport(404, "could not determine key for key_filter plugin and acceptUnmatched disabled")
                continue

            try:
                key = self.derive_key(msg)
                logger.debug("key=%s for %s", key, msg.getIDStr())
                if key is None:
                    new_incoming.append(msg)
                    continue
            except Exception as e:
                logger.error(f"rejecting {msg.getIDStr()}, key_groups={self._group_nums_for_mask[msg['_mask_index']]}"
                             +f" not in {self.o.masks[msg['_mask_index']]} ({e})")
                worklist.rejected.append(msg)
                msg.setReport(404, "could not determine key for key_filter plugin")
                continue

            # finally, filter.
            if key in self._reject_keys:
                worklist.rejected.append(msg)
                msg.setReport(404, f"key {key} in reject_keys")
            elif self.o.acceptUnmatched or key in self._accept_keys:
                new_incoming.append(msg)
            else:
                worklist.rejected.append(msg)
                msg.setReport(404, f"key {key} not in accept_keys and acceptUnmatched disabled")

        worklist.incoming = new_incoming
#!/usr/bin/env python3

# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2020
#

import sys
import os
import inspect
import sarracenia.config
import sarracenia.flow
import sarracenia.flow.post
import logging


def main():
    logger = logging.getLogger()
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
        level=logging.DEBUG)

    logger.setLevel(logging.INFO)

    if (len(sys.argv) > 1) and (sys.argv[1] == '--debug'):
        logger.setLevel(logging.DEBUG)

    cfg1 = sarracenia.config.default_config()

    cfg1.override({
        'program_name': 'post',
        'directory': os.getcwd(),
        'accept_unmatched': True,
        'action': 'foreground'
    })

    cfg1.override(sarracenia.flow.post.default_options)

    cfg1.parse_args(isPost=True)

    cfg2 = sarracenia.config.one_config('post', cfg1.config, isPost=True)

    post_flow = sarracenia.flow.Flow.factory(cfg2)
    post_flow.run()


if __name__ == "__main__":
    main()

import pytest
#from unittest.mock import Mock

import os
import logging

import sarracenia.config
import sarracenia.flowcb.poll.poll_NASA_CMR

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


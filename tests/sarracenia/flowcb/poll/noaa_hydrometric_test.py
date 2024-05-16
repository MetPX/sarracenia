import pytest
#from unittest.mock import Mock

import os
import logging

import sarracenia.config
import sarracenia.flowcb.poll.noaa_hydrometric

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


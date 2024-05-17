import pytest
#from unittest.mock import Mock

import logging

import sarracenia
import sarracenia.config
import sarracenia.transfer

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')

def test_factory():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.Transfer.factory('http', options)

    assert type(transfer) is sarracenia.transfer.https.Https

    transfer = sarracenia.transfer.Transfer.factory('DoesNotExist', options)
    assert transfer == None

def test___init__():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.Transfer.factory('http', options)

    assert transfer.fpos == 0

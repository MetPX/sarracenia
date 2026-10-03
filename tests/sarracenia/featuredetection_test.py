import pytest
from tests.conftest import *
# from unittest.mock import Mock

import sarracenia.config
import sarracenia.featuredetection


def test_platformdirs_is_a_separate_feature():
    assert 'appdirs' in sarracenia.featuredetection.features
    assert 'platformdirs' in sarracenia.featuredetection.features
    assert sarracenia.featuredetection.features['appdirs']['modules_needed'] == ['appdirs']
    assert sarracenia.featuredetection.features['platformdirs']['modules_needed'] == ['platformdirs']
    assert 'Alternate_modules' not in sarracenia.featuredetection.features['appdirs']

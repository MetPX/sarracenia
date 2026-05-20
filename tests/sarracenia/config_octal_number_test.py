import pytest

import logging, copy

import sarracenia
import sarracenia.config
from sarracenia.config import octal_number

logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')

# ---------------------------------------------------------------------------
# Tests for the octal_number type used by 'octal' config options
# ---------------------------------------------------------------------------

 

# --- construction from int ---

def test_from_int_returns_octal_number_instance():
    v = octal_number(0o755)
    assert isinstance(v, octal_number), (
        "octal_number(int) must return an octal_number instance, not a plain int"
    )

def test_from_int_preserves_value():
    assert octal_number(0o644) == 0o644
    assert octal_number(0o644) == 420

def test_from_int_zero():
    v = octal_number(0)
    assert isinstance(v, octal_number)
    assert v == 0

def test_from_base10_int():
    v = octal_number(123)
    assert isinstance(v, octal_number)
    assert v == 123

# --- construction from octal string ---

def test_from_str_returns_octal_number_instance():
    v = octal_number("755")
    assert isinstance(v, octal_number), (
        "octal_number(str) must return an octal_number instance, not a plain int"
    )

def test_from_str_parses_as_octal():
    # "644" in octal == 420 in decimal
    assert octal_number("644") == 0o644

def test_from_str_755():
    assert octal_number("755") == 0o755

def test_from_str_with_0o_prefix():
    # '0o' prefix is stripped before parsing, so this should work
    v = octal_number("0o755")
    assert isinstance(v, octal_number)
    assert v == 0o755
    assert str(v) == "0o755"

# --- __str__ and __repr__ ---

def test_str_shows_octal_prefix():
    v = octal_number(0o755)
    assert str(v) == "0o755", (
        "__str__ must return '0o<octal>' — failed because __new__ returned a plain int"
    )

def test_repr_shows_octal_prefix():
    v = octal_number(0o755)
    assert repr(v) == "0o755"

def test_str_from_int_input():
    assert str(octal_number(0o644)) == "0o644"

def test_str_from_str_input():
    assert str(octal_number("644")) == "0o644"

def test_str_zero():
    assert str(octal_number(0)) == "0o000"

def test_repr_zero():
    assert repr(octal_number(0)) == "0o000"

# --- arithmetic preserves int semantics ---

def test_arithmetic_value_correct():
    # 0o755 == 493 decimal
    assert int(octal_number("755")) == 493

def test_octal_number_is_int_subclass():
    assert issubclass(octal_number, int)

def test_usable_as_int_in_comparisons():
    v = octal_number("644")
    assert v == 0o644
    assert v != 0o755
    assert v < 0o755
    assert v > 0o400

def test_permDefault_is_octal_number_instance():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.parse_line("subscribe", "ex1", "subscribe/ex1", 1, "permDefault 755")
    assert isinstance(options.permDefault, octal_number), (
        "permDefault must be stored as an octal_number, not a plain int"
    )

def test_permDefault_str_representation():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.parse_line("subscribe", "ex1", "subscribe/ex1", 1, "permDefault 755")
    assert str(options.permDefault) == "0o755"

def test_permDefault_value_755():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.parse_line("subscribe", "ex1", "subscribe/ex1", 1, "permDefault 755")
    assert options.permDefault == 0o755

def test_permDefault_value_644():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.parse_line("subscribe", "ex1", "subscribe/ex1", 1, "permDefault 644")
    assert options.permDefault == 0o644

def test_add_option_octal_is_octal_number_instance():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.add_option('myPerm', kind='octal', default_value='644')
    assert isinstance(options.myPerm, octal_number), (
        "add_option with kind='octal' must store an octal_number instance"
    )

def test_add_option_octal_str_representation():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.add_option('myPerm', kind='octal', default_value='644')
    assert str(options.myPerm) == "0o644"

def test_add_option_octal_parse_line():
    options = copy.deepcopy(sarracenia.config.default_config())
    options.add_option('myPerm', kind='octal', default_value='644')
    options.parse_line("subscribe", "ex1", "subscribe/ex1", 1, "myPerm 755")
    assert isinstance(options.myPerm, octal_number)
    assert options.myPerm == 0o755
    assert str(options.myPerm) == "0o755"

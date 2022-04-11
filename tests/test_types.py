import re

import pytest
from pydantic import ValidationError, BaseModel

from pydantic_toolbox.types import TemplateStr, IntBase


@pytest.mark.parametrize(
    'tmpl_str,keys',
    (
        ('f{key}b', 'key'),
        ('f{key!r}{k}b', ('key!r', 'k')),
        ('foo{key.__class__!r:20}{key}bar{key}', ('key.__class__!r:20', 'key')),
    ),
)
def test_template_str_keys(tmpl_str, keys):
    class Model(BaseModel):
        v: TemplateStr[keys]

    m = Model(v=tmpl_str)
    assert m.v == tmpl_str


@pytest.mark.parametrize(
    'tmpl_str', ('{}', 'f{key!r}{k}b', 'foo{key.__class__!r:20}{key}bar{key}', '{k}{key}', 'foo')
)
def test_template_str_wrong_keys(tmpl_str):
    class Model(BaseModel):
        v: TemplateStr['key']

    with pytest.raises(ValidationError, match='invalid template string'):
        Model(v=tmpl_str)


def test_template_str_quantity():
    class Model(BaseModel):
        a: TemplateStr[1]
        b: TemplateStr[5] = None

    m = Model(a='foo{}bar', b='A{}-{}-{}-{}-{}!')
    assert m.a == 'foo{}bar'
    assert m.b == 'A{}-{}-{}-{}-{}!'

    with pytest.raises(ValidationError, match='expected keys: 1, actual keys: 2'):
        m = Model(a='{}{}')

    with pytest.raises(
        ValidationError, match=re.escape("expected keys: ['{}'], actual keys: [':20']")
    ):
        m = Model(a='{:20}')


int_base_test_set = pytest.mark.parametrize(
    'base,value,decimal,representation',
    (
        (10, 5, 5, '5'),
        (0, "0b101", 5, '5'),
        (2, "0b101", 0b101, None),
        (8, "0o13", 0o13, None),
        (10, "3", 3, None),
        (16, "0xf", 0xf, None),
        (36, "zzz", 46655, '46655'),
    ),
)


@int_base_test_set
def test_int_base(base, value, decimal, representation):
    parsed = IntBase[base](value)
    assert parsed == decimal
    assert str(parsed) == representation or str(value)
    assert IntBase[base] is parsed.__class__


@int_base_test_set
def test_int_base_as_pydantic_type(base, value, decimal, representation):
    class Num(BaseModel):
        v: IntBase[base]

    n = Num(v=value)
    assert n.v == decimal
    assert str(n.v) == representation or str(value)


def test_int_base_must_be_concrete():
    with pytest.raises(TypeError, match=re.escape('IntBase must be concrete')):
        IntBase(0)


@pytest.mark.parametrize('invalid_base', (1, 37))
def test_int_base_invalid_base(invalid_base):
    with pytest.raises(TypeError, match=re.escape('IntBase[`arg`] must be >= 2 and <= 36, or 0')):
        IntBase[invalid_base]

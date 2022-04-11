import re

import pytest
from pydantic import ValidationError, BaseModel

from pydantic_toolbox.types import TemplateStr


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

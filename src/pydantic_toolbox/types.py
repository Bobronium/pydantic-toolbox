from __future__ import annotations

import json
from collections.abc import Callable
from string import Formatter
from types import new_class
from typing import Any, TYPE_CHECKING

from pydantic_toolbox import errors


if TYPE_CHECKING:
    from pydantic.typing import CallableGenerator


class TemplateStr(str):
    """
    This type is useful for checking a string for a certain expected keywords in it

    class Messages(BaseModel):
        greeting: TemplateStr['name']

    Messages(greeting='Hello, {name}!')  # ok!
    Messages(greeting='Hello, name!')  # invalid template string, expected keys: {'name'}, actual keys: set() (type=value_error.str.template; expected_keys={'name'}; actual_keys=set())
    Messages(greeting='{name.__class__.pwn_me()}')  # invalid template string, expected keys: {'name'}, actual keys: {'name.__class__.pwn_me()'}


    """
    __keys__: set[str] = set()
    __quantity__: int = 0

    def __class_getitem__(cls, keys: str | int | tuple[str, ...]) -> type['TemplateStr']:
        if isinstance(keys, int):
            # no named keys, check their quantity
            name = f'{cls.__name__}[{keys}]'
            namespace = dict(__quantity__=keys)
        else:
            name = f'{cls.__name__}[{", ".join(map(repr, keys))}]'
            namespace = dict(__keys__=set(keys) if isinstance(keys, tuple) else {keys})

        return new_class(name=name, bases=(cls,), exec_body=lambda ns: ns.update(namespace))

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        if cls.__keys__:
            yield cls.validate_keys
        else:
            yield cls.validate_quantity

    @classmethod
    def find_keys(cls, string: str):
        return [
            field_name
            + ('!' + conversion if conversion else '')
            + (':' + format_spec if format_spec else '')
            for literal_text, field_name, format_spec, conversion in Formatter().parse(string)
            if field_name is not None
        ]

    @classmethod
    def validate_keys(cls, v: Any) -> str:
        v = str(v)
        found_keys = set(cls.find_keys(v))
        if cls.__keys__ != found_keys:
            raise errors.TemplateStrError(cls.__keys__, found_keys)
        return v

    @classmethod
    def validate_quantity(cls, v: Any) -> str:
        v = str(v)
        found_keys = cls.find_keys(v)
        if len(found_keys) != cls.__quantity__:
            raise errors.TemplateStrError(cls.__quantity__, len(found_keys))
        elif any(found_keys):
            raise errors.TemplateStrError(['{}'] * cls.__quantity__, found_keys)

        return v


class IntBase(int):
    """
    Allow strings to be parsed as integers with chosen base

    Feature request in pydantic: https://github.com/samuelcolvin/pydantic/issues/682

    >>> IntBase[16]('0xa') == 10
    True
    >>> IntBase[16]('a') == 10
    True
    >>> IntBase[16]('f')
    0xf
    """
    __int_base__: int
    _get_base_string: Callable[[int], str]

    _bases_format_types = {
        2: "#b",
        8: "#o",
        10: "#d",
        16: "#x",
    }
    _cache: dict[int, type[IntBase]] = {}

    def __new__(cls, value: int | str) -> IntBase:
        if not hasattr(cls, '__int_base__'):
            raise TypeError(f'{cls.__name__} must be concrete')
        if isinstance(value, str):
            return super().__new__(cls, value, base=cls.__int_base__)
        return super().__new__(cls, value)

    def __class_getitem__(cls, base: int) -> type[IntBase]:
        try:
            int('0', base=base)
        except ValueError as e:
            raise TypeError(e.args[0].replace('int() base', f'{cls.__name__}[`arg`]')) from None

        if base in cls._cache:
            return cls._cache[base]

        name = f'{cls.__name__}[{base}]'

        format_type = cls._bases_format_types.get(base, None)
        namespace = {'__int_base__': base}
        if format_type is None:
            namespace['__repr__'] = int.__repr__
        else:
            namespace['_get_base_string'] = ('{:%s}' % format_type).format

        new_cls = cls._cache[base] = new_class(
            name=name,
            bases=(cls,),
            exec_body=lambda ns: ns.update(namespace)
        )
        return new_cls

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls

    def __repr__(self):
        return self._get_base_string(self)


class Bin(IntBase[2]):
    ...


class Oct(IntBase[8]):
    ...


class Hex(IntBase[16]):
    ...

from __future__ import annotations

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

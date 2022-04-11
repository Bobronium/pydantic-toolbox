from __future__ import annotations

from pydantic.errors import PydanticValueError


class TemplateStrError(PydanticValueError):
    code = 'str.template'
    msg_template = 'invalid template string, expected keys: {expected_keys}, actual keys: {actual_keys}'

    def __init__(
        self, expected_keys: int | set[str] | list[str], actual_keys: int | set[str] | list[str]
    ) -> None:
        super().__init__(expected_keys=expected_keys, actual_keys=actual_keys)

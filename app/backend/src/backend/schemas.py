"""Tiny request validators (no pydantic — keeps the image small)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ValidationError(ValueError):
    """Raised when a request payload fails validation."""


def _str_field(data: dict[str, Any], name: str, *, default: str = "", max_len: int) -> str:
    value = data.get(name, default)
    if value is None:
        value = default
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")
    if len(value) > max_len:
        raise ValidationError(f"{name} too long (max {max_len})")
    return value


@dataclass(frozen=True)
class CreateRunRequest:
    nombre: str
    source_mode: str
    source_file: str

    @classmethod
    def from_json(cls, data: Any) -> "CreateRunRequest":
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValidationError("body must be a JSON object")
        return cls(
            nombre=_str_field(data, "nombre", max_len=120),
            source_mode=_str_field(data, "source_mode", default="stub", max_len=32),
            source_file=_str_field(data, "source_file", max_len=255),
        )

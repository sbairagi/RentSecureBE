from __future__ import annotations

ValidationError = dict[str, list[str]]


def build_validation_error(field: str, messages: list[str]) -> ValidationError:
    return {field: messages}


__all__ = ["ValidationError", "build_validation_error"]

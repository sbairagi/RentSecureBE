from __future__ import annotations

ValidationErrorDict = dict[str, list[str]]


def build_validation_error(field: str, messages: list[str]) -> ValidationErrorDict:
    return {field: messages}


__all__ = ["ValidationErrorDict", "build_validation_error"]

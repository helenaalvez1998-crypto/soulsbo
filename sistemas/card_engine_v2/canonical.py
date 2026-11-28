"""Deterministic JSON and fingerprints used by the v2 operation ledger.

This module intentionally limits fingerprint inputs to JSON values with integer
numbers. This avoids cross-runtime float formatting ambiguity. DefinitionManifest
JCS/RFC 8785 digests remain a separate concern and are supplied by published
content artifacts; this module does not claim to implement RFC 8785.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


class CanonicalizationError(ValueError):
    """The value cannot be encoded by soulsbo-json-int-v1."""


def _validate_json_value(value: Any, path: str = "$", *, allow_float: bool = False) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, int) and not isinstance(value, bool) and abs(value) > (2**53 - 1):
            raise CanonicalizationError(f"integer outside interoperable range at {path}")
        return
    if isinstance(value, float):
        if not allow_float:
            raise CanonicalizationError(f"floating-point values are not allowed at {path}")
        if value != value or value in (float("inf"), float("-inf")):
            raise CanonicalizationError(f"non-finite number at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]", allow_float=allow_float)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"non-string object key at {path}")
            _validate_json_value(item, f"{path}.{key}", allow_float=allow_float)
        return
    raise CanonicalizationError(f"unsupported JSON value {type(value).__name__} at {path}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return stable UTF-8 JSON bytes for integer-only canonical fingerprints."""
    _validate_json_value(value)
    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return text.encode("utf-8")


def storage_json_bytes(value: Any) -> bytes:
    """Stable local persistence encoding; finite fractional numbers are allowed."""
    _validate_json_value(value, allow_float=True)
    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return text.encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

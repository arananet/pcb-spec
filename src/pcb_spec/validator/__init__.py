"""Schema validator for pcb-spec manifests.

Wraps load_manifest() and converts pydantic.ValidationError into structured
ValidationError objects with machine-readable codes. Cross-reference checks
(impedance profile refs, net class refs) are enforced by Pydantic model
validators in schema/manifest.py — this module does not duplicate them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError as PydanticValidationError

from pcb_spec.schema import load_manifest

__all__ = ["ValidationError", "ValidationResult", "validate"]


@dataclass
class ValidationError:
    code: str
    message: str
    location: str


@dataclass
class ValidationResult:
    status: Literal["pass", "fail"]
    errors: list[ValidationError] = field(default_factory=list)


def _loc_to_str(loc: tuple) -> str:
    return ".".join(str(p) for p in loc)


def _extract_location(msg: str, loc: tuple) -> str:
    if loc:
        return _loc_to_str(loc)

    # Model-validator errors have empty loc; extract location from message.
    m = re.search(r"Net class '([^']+)' references undefined impedance_profile", msg)
    if m:
        return f"net_classes.{m.group(1)}.rules.impedance_profile"

    if "Placement references undefined net class" in msg:
        return "placement.net_class"

    return "manifest"


def _convert(err: dict) -> ValidationError:
    loc = err.get("loc", ())
    raw_msg = err.get("msg", "")
    error_type = err.get("type", "")

    # Strip pydantic v2's "Value error, " prefix from validator messages.
    msg = re.sub(r"^Value error, ", "", raw_msg)

    location = _extract_location(raw_msg, loc)

    if "undefined" in msg.lower():
        code = "UNDEFINED_REF"
    else:
        code = "SCHEMA_ERROR"

    return ValidationError(code=code, message=msg, location=location)


def validate(manifest_path: str | Path) -> ValidationResult:
    """Validate a manifest YAML file. Returns a ValidationResult."""
    path = Path(manifest_path)

    try:
        load_manifest(path)
    except FileNotFoundError:
        return ValidationResult(
            status="fail",
            errors=[ValidationError(
                code="FILE_NOT_FOUND",
                message=f"File not found: {path}",
                location=str(path),
            )],
        )
    except yaml.YAMLError as exc:
        return ValidationResult(
            status="fail",
            errors=[ValidationError(
                code="SCHEMA_ERROR",
                message=str(exc),
                location=str(path),
            )],
        )
    except PydanticValidationError as exc:
        return ValidationResult(
            status="fail",
            errors=[_convert(e) for e in exc.errors()],
        )

    return ValidationResult(status="pass", errors=[])

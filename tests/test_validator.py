"""Tests for src/pcb_spec/validator and CLI validate subcommand."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcb_spec.validator import ValidationError, ValidationResult, validate

FIXTURES = Path(__file__).parent / "fixtures" / "invalid"
EXAMPLES = Path(__file__).parent.parent / "examples"


# ── Unit tests ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("example", ["minimal-2layer", "4layer-mixed-signal", "controlled-impedance"])
def test_validate_pass_examples(example: str) -> None:
    result = validate(EXAMPLES / example / "manifest.yaml")
    assert isinstance(result, ValidationResult)
    assert result.status == "pass"
    assert result.errors == []


def test_validate_missing_manifest_version() -> None:
    result = validate(FIXTURES / "missing_manifest_version.yaml")
    assert result.status == "fail"
    codes = [e.code for e in result.errors]
    assert "SCHEMA_ERROR" in codes


def test_validate_unsupported_version() -> None:
    result = validate(FIXTURES / "unsupported_version.yaml")
    assert result.status == "fail"
    codes = [e.code for e in result.errors]
    assert "SCHEMA_ERROR" in codes


def test_validate_undefined_impedance_profile() -> None:
    result = validate(FIXTURES / "undefined_impedance_profile.yaml")
    assert result.status == "fail"
    codes = [e.code for e in result.errors]
    assert "UNDEFINED_REF" in codes


def test_validate_gate_missing_id() -> None:
    result = validate(FIXTURES / "gate_missing_id.yaml")
    assert result.status == "fail"
    codes = [e.code for e in result.errors]
    assert any(c in ("MISSING_FIELD", "SCHEMA_ERROR") for c in codes)


def test_validate_undefined_placement_net_class() -> None:
    result = validate(FIXTURES / "undefined_placement_net_class.yaml")
    assert result.status == "fail"
    codes = [e.code for e in result.errors]
    assert "UNDEFINED_REF" in codes


def test_validate_non_empty_location_for_cross_ref_error() -> None:
    result = validate(FIXTURES / "undefined_impedance_profile.yaml")
    assert result.status == "fail"
    assert len(result.errors) >= 1
    for err in result.errors:
        assert isinstance(err, ValidationError)
        assert err.location, f"location must be non-empty, got {err.location!r}"


def test_validate_returns_validation_result_dataclass() -> None:
    result = validate(EXAMPLES / "minimal-2layer" / "manifest.yaml")
    assert hasattr(result, "status")
    assert hasattr(result, "errors")
    assert result.status in ("pass", "fail")


def test_validate_file_not_found() -> None:
    result = validate("/nonexistent/path/manifest.yaml")
    assert result.status == "fail"
    assert result.errors[0].code == "FILE_NOT_FOUND"


# ── Integration tests (subprocess) ────────────────────────────────────────

def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcb_spec", *args],
        capture_output=True,
        text=True,
    )


def test_cli_validate_pass() -> None:
    proc = _run_cli("validate", str(EXAMPLES / "minimal-2layer" / "manifest.yaml"))
    assert proc.returncode == 0
    assert "PASS" in proc.stdout


def test_cli_validate_fail_exits_1() -> None:
    proc = _run_cli("validate", str(FIXTURES / "missing_manifest_version.yaml"))
    assert proc.returncode == 1
    assert "FAIL" in proc.stdout


def test_cli_validate_report_json(tmp_path: Path) -> None:
    report = tmp_path / "out.json"
    proc = _run_cli(
        "validate",
        str(FIXTURES / "missing_manifest_version.yaml"),
        "--report", str(report),
    )
    assert proc.returncode == 1
    assert report.exists()
    data = json.loads(report.read_text())
    assert data["schema_version"] == "0.1"
    assert data["status"] == "fail"
    assert "manifest_path" in data
    assert isinstance(data["errors"], list)
    assert len(data["errors"]) > 0
    first = data["errors"][0]
    assert "code" in first and "message" in first and "location" in first


def test_cli_validate_report_pass_empty_errors(tmp_path: Path) -> None:
    report = tmp_path / "out.json"
    proc = _run_cli(
        "validate",
        str(EXAMPLES / "minimal-2layer" / "manifest.yaml"),
        "--report", str(report),
    )
    assert proc.returncode == 0
    data = json.loads(report.read_text())
    assert data["status"] == "pass"
    assert data["errors"] == []

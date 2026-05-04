"""Tests for conformance checker gates and CLI check subcommand."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcb_spec.conformance.gates import run_schematic_gates
from pcb_spec.conformance.netlist_parser import parse_kicad_netlist
from pcb_spec.engine import Severity
from pcb_spec.schema import load_manifest

NETLISTS = Path(__file__).parent / "fixtures" / "netlists"
EXAMPLES = Path(__file__).parent.parent / "examples"
CONTROLLED = EXAMPLES / "controlled-impedance" / "manifest.yaml"


# ── Unit tests ─────────────────────────────────────────────────────────────

def test_pass_when_all_nets_and_components_present():
    manifest = load_manifest(CONTROLLED)
    netlist = parse_kicad_netlist(NETLISTS / "controlled_impedance_match.net")
    violations = run_schematic_gates(manifest, netlist)
    assert violations == [], f"Expected no violations, got: {violations}"


def test_missing_net_class_member_triggers_violation():
    manifest = load_manifest(CONTROLLED)
    netlist = parse_kicad_netlist(NETLISTS / "missing_net.net")
    violations = run_schematic_gates(manifest, netlist)
    rule_ids = [v.rule_id for v in violations]
    assert "NET_CLASS_MEMBER_NOT_IN_NETLIST" in rule_ids


def test_missing_net_violation_has_net_name():
    manifest = load_manifest(CONTROLLED)
    netlist = parse_kicad_netlist(NETLISTS / "missing_net.net")
    violations = run_schematic_gates(manifest, netlist)
    net_viols = [v for v in violations if v.rule_id == "NET_CLASS_MEMBER_NOT_IN_NETLIST"]
    assert all(v.net_name for v in net_viols), "net_name must be non-empty"
    assert any(v.net_name == "USB_D-" for v in net_viols)


def test_missing_placement_component_triggers_violation():
    manifest = load_manifest(CONTROLLED)
    netlist = parse_kicad_netlist(NETLISTS / "missing_component.net")
    violations = run_schematic_gates(manifest, netlist)
    rule_ids = [v.rule_id for v in violations]
    assert "PLACEMENT_COMPONENT_NOT_IN_NETLIST" in rule_ids


def test_missing_component_violation_has_component_id():
    manifest = load_manifest(CONTROLLED)
    netlist = parse_kicad_netlist(NETLISTS / "missing_component.net")
    violations = run_schematic_gates(manifest, netlist)
    comp_viols = [v for v in violations if v.rule_id == "PLACEMENT_COMPONENT_NOT_IN_NETLIST"]
    assert all(v.component_id for v in comp_viols)
    assert any(v.component_id == "J1" for v in comp_viols)


def test_violations_have_error_severity():
    manifest = load_manifest(CONTROLLED)
    netlist = parse_kicad_netlist(NETLISTS / "missing_net.net")
    violations = run_schematic_gates(manifest, netlist)
    for v in violations:
        assert v.severity == Severity.ERROR


def test_no_violations_for_minimal_manifest():
    # minimal-2layer has empty members and empty placement — always passes
    manifest = load_manifest(EXAMPLES / "minimal-2layer" / "manifest.yaml")
    netlist = parse_kicad_netlist(NETLISTS / "minimal.net")
    violations = run_schematic_gates(manifest, netlist)
    assert violations == []


# ── Integration tests ──────────────────────────────────────────────────────

def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcb_spec", *args],
        capture_output=True, text=True,
    )


def test_cli_check_pass():
    proc = _run("check", str(CONTROLLED), str(NETLISTS / "controlled_impedance_match.net"))
    assert proc.returncode == 0
    assert "PASS" in proc.stdout


def test_cli_check_fail():
    proc = _run("check", str(CONTROLLED), str(NETLISTS / "missing_net.net"))
    assert proc.returncode == 1
    assert "FAIL" in proc.stdout


def test_cli_check_report(tmp_path):
    report = tmp_path / "report.json"
    proc = _run(
        "check", str(CONTROLLED), str(NETLISTS / "missing_net.net"),
        "--report", str(report),
    )
    assert proc.returncode == 1
    data = json.loads(report.read_text())
    assert data["schema_version"] == "0.1"
    assert data["status"] == "fail"
    assert isinstance(data["errors"], list) and len(data["errors"]) > 0
    first = data["errors"][0]
    assert "code" in first and "message" in first and "location" in first

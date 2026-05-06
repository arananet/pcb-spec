"""Tests for src/pcb_spec/conformance/netlist_parser.py"""
from __future__ import annotations

from pathlib import Path

import pytest

from pcb_spec.conformance.netlist_parser import (
    Component, Net, NetNode, Netlist, parse_kicad_netlist,
)

FIXTURES = Path(__file__).parent / "fixtures" / "netlists"


def test_parse_minimal_returns_netlist():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    assert isinstance(nl, Netlist)


def test_component_refs():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    assert nl.component_refs() == {"U1", "C1", "J1"}


def test_net_names():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    assert nl.net_names() == {"GND", "+3V3", "USB_D+", "USB_D-"}


def test_net_nodes():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    gnd = next(n for n in nl.nets if n.name == "GND")
    refs = {node.ref for node in gnd.nodes}
    assert "U1" in refs
    assert "C1" in refs


def test_component_fields():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    u1 = next(c for c in nl.components if c.ref == "U1")
    assert u1.value == "STM32F103C8"
    assert "LQFP" in u1.footprint


def test_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_kicad_netlist("/nonexistent/path/file.net")


def test_raises_value_error_for_non_netlist(tmp_path):
    bad = tmp_path / "bad.net"
    bad.write_text("this is not a netlist")
    with pytest.raises(ValueError):
        parse_kicad_netlist(bad)


def test_netlist_component_refs_is_set():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    assert isinstance(nl.component_refs(), set)


def test_netlist_net_names_is_set():
    nl = parse_kicad_netlist(FIXTURES / "minimal.net")
    assert isinstance(nl.net_names(), set)


def test_parse_controlled_impedance_match():
    nl = parse_kicad_netlist(FIXTURES / "controlled_impedance_match.net")
    assert "USB_D+" in nl.net_names()
    assert "USB_D-" in nl.net_names()
    assert "J1" in nl.component_refs()

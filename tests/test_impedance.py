"""Tests for src/pcb_spec/calc/impedance.py

Reference geometry calibration (formula: IPC-2141A/Wadell):
  Microstrip 50 ohm on FR-4 (er=4.5):
    w=0.33, h=0.2, t=0.035 → Z0 ≈ 49.6 ohm  (verified by hand)
  Stripline 50 ohm on FR-4 (er=4.5):
    w=0.10, b=0.36, t=0.035 → Z0 ≈ 50.4 ohm  (verified by hand)
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from pcb_spec.calc.impedance import microstrip_impedance, stripline_impedance


# ── Unit tests ─────────────────────────────────────────────────────────────

def test_microstrip_50_ohm_reference():
    # w=0.33 mm, h=0.2 mm, t=0.035 mm, er=4.5 → ~49.6 ohm
    z0 = microstrip_impedance(w=0.33, h=0.2, t=0.035, er=4.5)
    assert abs(z0 - 50.0) <= 2.0, f"Expected ~50 ohm, got {z0:.2f}"


def test_microstrip_high_impedance():
    # Narrow trace: w=0.1, h=0.2 gives high impedance (~65 ohm)
    z0 = microstrip_impedance(w=0.1, h=0.2, t=0.035, er=4.5)
    assert 55.0 <= z0 <= 100.0, f"Z0 {z0:.2f} outside expected range 55–100 ohm"


def test_stripline_50_ohm_reference():
    # w=0.10 mm, b=0.36 mm, t=0.035 mm, er=4.5 → ~50.4 ohm
    z0 = stripline_impedance(w=0.10, b=0.36, t=0.035, er=4.5)
    assert abs(z0 - 50.0) <= 2.0, f"Expected ~50 ohm, got {z0:.2f}"


def test_microstrip_returns_float():
    z0 = microstrip_impedance(w=0.33, h=0.2, t=0.035, er=4.5)
    assert isinstance(z0, float)


def test_stripline_returns_float():
    z0 = stripline_impedance(w=0.10, b=0.36, t=0.035, er=4.5)
    assert isinstance(z0, float)


def test_microstrip_raises_on_zero_width():
    with pytest.raises(ValueError, match="w"):
        microstrip_impedance(w=0.0, h=0.2, t=0.035, er=4.5)


def test_microstrip_raises_on_negative_width():
    with pytest.raises(ValueError):
        microstrip_impedance(w=-0.1, h=0.2, t=0.035, er=4.5)


def test_microstrip_raises_on_zero_height():
    with pytest.raises(ValueError, match="h"):
        microstrip_impedance(w=0.1, h=0.0, t=0.035, er=4.5)


def test_stripline_raises_on_zero_b():
    with pytest.raises(ValueError, match="b"):
        stripline_impedance(w=0.1, b=0.0, t=0.035, er=4.5)


def test_wider_trace_lower_impedance_microstrip():
    z_narrow = microstrip_impedance(w=0.15, h=0.2, t=0.035, er=4.5)
    z_wide = microstrip_impedance(w=0.35, h=0.2, t=0.035, er=4.5)
    assert z_narrow > z_wide, "Wider trace should have lower impedance"


def test_higher_er_lower_impedance():
    z_low_er = microstrip_impedance(w=0.2, h=0.2, t=0.035, er=3.5)
    z_high_er = microstrip_impedance(w=0.2, h=0.2, t=0.035, er=5.0)
    assert z_low_er > z_high_er, "Higher er should lower impedance"


def test_microstrip_accepts_w_greater_than_h():
    # Wide trace (w > h) is physically valid for low-impedance designs
    z0 = microstrip_impedance(w=0.5, h=0.2, t=0.035, er=4.5)
    assert z0 > 0


# ── Integration tests ──────────────────────────────────────────────────────

def test_cli_calc_impedance_microstrip():
    proc = subprocess.run(
        [sys.executable, "-m", "pcb_spec", "calc", "impedance",
         "--geometry", "microstrip",
         "--width", "0.33", "--height", "0.2", "--thickness", "0.035", "--er", "4.5"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "Z0 =" in proc.stdout


def test_cli_calc_impedance_missing_arg():
    proc = subprocess.run(
        [sys.executable, "-m", "pcb_spec", "calc", "impedance",
         "--geometry", "microstrip", "--width", "0.2"],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0

"""Tests for src/pcb_spec/calc/current_capacity.py"""
from __future__ import annotations

import subprocess
import sys

import pytest

from pcb_spec.calc.current_capacity import min_trace_width_mm


# ── Unit tests ─────────────────────────────────────────────────────────────

def test_1a_external_1oz_reference():
    # IPC-2221 ref: 1 A, ΔT=10°C, 1 oz, external → ~10 mil = 0.254 mm
    w = min_trace_width_mm(1.0, 10.0, 1.0, "external")
    assert abs(w - 0.254) <= 0.05, f"Expected ~0.254 mm, got {w:.4f} mm"


def test_2a_external_1oz_reference():
    # IPC-2221 ref: 2 A, ΔT=10°C, 1 oz, external → ~30 mil = 0.762 mm
    w = min_trace_width_mm(2.0, 10.0, 1.0, "external")
    assert abs(w - 0.762) <= 0.15, f"Expected ~0.762 mm, got {w:.4f} mm"


def test_internal_wider_than_external():
    # Internal conductors have lower k → need wider trace for same current
    w_ext = min_trace_width_mm(1.0, 10.0, 1.0, "external")
    w_int = min_trace_width_mm(1.0, 10.0, 1.0, "internal")
    assert w_int > w_ext, "Internal trace must be wider than external for same current"


def test_heavier_copper_narrower_trace():
    # 2 oz copper is thicker → same current needs narrower trace
    w_1oz = min_trace_width_mm(2.0, 10.0, 1.0, "external")
    w_2oz = min_trace_width_mm(2.0, 10.0, 2.0, "external")
    assert w_2oz < w_1oz, "Heavier copper should allow a narrower trace"


def test_higher_current_wider_trace():
    w_low = min_trace_width_mm(1.0, 10.0, 1.0, "external")
    w_high = min_trace_width_mm(3.0, 10.0, 1.0, "external")
    assert w_high > w_low


def test_returns_positive_float():
    w = min_trace_width_mm(1.0, 10.0, 1.0, "external")
    assert isinstance(w, float)
    assert w > 0.0


def test_raises_on_zero_current():
    with pytest.raises(ValueError, match="current_a"):
        min_trace_width_mm(0.0, 10.0, 1.0, "external")


def test_raises_on_negative_current():
    with pytest.raises(ValueError):
        min_trace_width_mm(-1.0, 10.0, 1.0, "external")


def test_raises_on_zero_delta_t():
    with pytest.raises(ValueError, match="delta_t_c"):
        min_trace_width_mm(1.0, 0.0, 1.0, "external")


def test_raises_on_zero_copper_oz():
    with pytest.raises(ValueError, match="copper_oz"):
        min_trace_width_mm(1.0, 10.0, 0.0, "external")


# ── Integration tests ──────────────────────────────────────────────────────

def test_cli_current_capacity():
    proc = subprocess.run(
        [sys.executable, "-m", "pcb_spec", "calc", "current-capacity",
         "--current", "1.0", "--delta-t", "10", "--copper-oz", "1.0", "--layer", "external"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "min_width =" in proc.stdout


def test_cli_current_capacity_missing_arg():
    proc = subprocess.run(
        [sys.executable, "-m", "pcb_spec", "calc", "current-capacity",
         "--current", "1.0"],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0

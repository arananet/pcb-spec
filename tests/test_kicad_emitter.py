"""Tests for src/pcb_spec/emit/kicad.py"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pcb_spec.emit.kicad import emit_dru
from pcb_spec.schema import load_manifest

EXAMPLES = Path(__file__).parent.parent / "examples"
MINIMAL = EXAMPLES / "minimal-2layer" / "manifest.yaml"
CONTROLLED = EXAMPLES / "controlled-impedance" / "manifest.yaml"


# ── Unit tests ──────────────────────────────────────────────────────────────

def test_output_starts_with_version():
    manifest = load_manifest(MINIMAL)
    dru = emit_dru(manifest)
    assert dru.startswith("(version 1)")


def test_returns_str():
    dru = emit_dru(load_manifest(MINIMAL))
    assert isinstance(dru, str)


def test_minimal_default_rule_present():
    manifest = load_manifest(MINIMAL)
    dru = emit_dru(manifest)
    # 6 mil * 0.0254 = 0.1524 mm
    assert "DEFAULT track-width" in dru
    assert "0.1524mm" in dru


def test_condition_uses_net_class_name():
    manifest = load_manifest(MINIMAL)
    dru = emit_dru(manifest)
    assert 'A.NetClass == \\"DEFAULT\\"' in dru


def test_controlled_impedance_has_all_net_classes():
    manifest = load_manifest(CONTROLLED)
    dru = emit_dru(manifest)
    assert "DEFAULT track-width" in dru
    assert "USB_DIFF track-width" in dru
    assert "RF_50 track-width" in dru


def test_impedance_profile_comment_present():
    manifest = load_manifest(CONTROLLED)
    dru = emit_dru(manifest)
    # USB_DIFF has an impedance_profile in controlled-impedance manifest
    assert "impedance_profile:" in dru


def test_track_width_has_mm_suffix():
    manifest = load_manifest(CONTROLLED)
    dru = emit_dru(manifest)
    # Every constraint track-width line ends with mm)
    for line in dru.splitlines():
        if "constraint track-width" in line:
            assert "mm)" in line, f"Missing mm suffix: {line}"


def test_all_width_values_positive():
    manifest = load_manifest(CONTROLLED)
    dru = emit_dru(manifest)
    import re
    for m in re.finditer(r"\(min ([\d.]+)mm\)", dru):
        assert float(m.group(1)) > 0


# ── Integration tests ───────────────────────────────────────────────────────

def test_cli_emit_kicad_stdout():
    proc = subprocess.run(
        [sys.executable, "-m", "pcb_spec", "emit", "kicad", str(MINIMAL)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "(version 1)" in proc.stdout


def test_cli_emit_kicad_to_file(tmp_path):
    out = tmp_path / "test.kicad_dru"
    proc = subprocess.run(
        [sys.executable, "-m", "pcb_spec", "emit", "kicad", str(MINIMAL), "-o", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert out.exists()
    assert "(version 1)" in out.read_text()

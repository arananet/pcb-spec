"""IPC-2221B current capacity calculator for PCB traces.

Formula (IPC-2221B §6.2):
  I = k * ΔT^b * A^c
  where A = cross-sectional area in mil²

Inverted to find minimum trace width for a given current:
  A = (I / (k * ΔT^b))^(1/c)
  width_mm = (A / thickness_mil) * 0.0254

Coefficients k, b, c are loaded from data/ipc/ipc-2152.yaml (ipc_2221_fallback)
so changing the data file changes the result without touching this code.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml

__all__ = ["min_trace_width_mm"]

# 1 oz copper = 35 µm = 1.378 mil (IPC-2141A; standard constant)
_OZ_TO_MIL = 1.378


def _data_path() -> Path:
    return Path(__file__).parent.parent.parent.parent / "data" / "ipc" / "ipc-2152.yaml"


@lru_cache(maxsize=1)
def _load_coefficients() -> dict:
    data = yaml.safe_load(_data_path().read_text())
    return data["ipc_2221_fallback"]


def min_trace_width_mm(
    current_a: float,
    delta_t_c: float,
    copper_oz: float,
    layer: Literal["external", "internal"],
) -> float:
    """Minimum trace width for a given current using the IPC-2221B polynomial.

    Args:
        current_a:  target current (amps)
        delta_t_c:  allowable temperature rise above ambient (°C); typically 10
        copper_oz:  copper weight (oz); 1 oz = 35 µm
        layer:      'external' (outer layer) or 'internal' (inner layer)

    Returns:
        Minimum trace width in mm.
    """
    if current_a <= 0:
        raise ValueError(f"current_a must be > 0, got {current_a}")
    if delta_t_c <= 0:
        raise ValueError(f"delta_t_c must be > 0, got {delta_t_c}")
    if copper_oz <= 0:
        raise ValueError(f"copper_oz must be > 0, got {copper_oz}")

    coeffs = _load_coefficients()
    section = "external_conductors" if layer == "external" else "internal_conductors"
    k = coeffs[section]["k"]
    b = coeffs[section]["b"]
    c = coeffs[section]["c"]

    # Invert I = k * ΔT^b * A^c  →  A = (I / (k * ΔT^b))^(1/c)
    area_mil2 = (current_a / (k * math.pow(delta_t_c, b))) ** (1.0 / c)

    thickness_mil = copper_oz * _OZ_TO_MIL
    width_mil = area_mil2 / thickness_mil
    return width_mil * 0.0254

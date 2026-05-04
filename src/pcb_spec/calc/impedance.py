"""PCB transmission-line impedance calculators.

Microstrip and stripline closed-form approximations from IPC-2141A / Wadell (1991).
All dimensions in mm; impedance returned in ohms.
"""
from __future__ import annotations

import math

__all__ = ["microstrip_impedance", "stripline_impedance"]


def microstrip_impedance(w: float, h: float, t: float, er: float) -> float:
    """Characteristic impedance of a microstrip trace (outer layer over plane).

    Args:
        w: trace width (mm)
        h: dielectric height — distance from trace to reference plane (mm)
        t: copper thickness (mm)
        er: relative dielectric constant of the substrate

    Returns:
        Characteristic impedance Z0 in ohms.

    Formula: IPC-2141A / Wadell (1991) simplified form for w/h < 1.
      Z0 = (87 / sqrt(er + 1.41)) * ln(5.98*h / (0.8*w + t))
    """
    if w <= 0:
        raise ValueError(f"w must be > 0, got {w}")
    if h <= 0:
        raise ValueError(f"h must be > 0, got {h}")
    if t <= 0:
        raise ValueError(f"t must be > 0, got {t}")
    if er <= 0:
        raise ValueError(f"er must be > 0, got {er}")

    return (87.0 / math.sqrt(er + 1.41)) * math.log(5.98 * h / (0.8 * w + t))


def stripline_impedance(w: float, b: float, t: float, er: float) -> float:
    """Characteristic impedance of a stripline trace (inner layer between planes).

    Args:
        w: trace width (mm)
        b: total dielectric thickness between the two reference planes (mm)
        t: copper thickness (mm)
        er: relative dielectric constant of the substrate

    Returns:
        Characteristic impedance Z0 in ohms.

    Formula: Wadell (1991):
      Z0 = (60 / sqrt(er)) * ln(4*b / (0.67*pi*(0.8*w + t)))
    """
    if w <= 0:
        raise ValueError(f"w must be > 0, got {w}")
    if b <= 0:
        raise ValueError(f"b must be > 0, got {b}")
    if t <= 0:
        raise ValueError(f"t must be > 0, got {t}")
    if er <= 0:
        raise ValueError(f"er must be > 0, got {er}")

    return (60.0 / math.sqrt(er)) * math.log(4.0 * b / (0.67 * math.pi * (0.8 * w + t)))

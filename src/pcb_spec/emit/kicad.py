"""Emit a KiCad .kicad_dru file from a pcb-spec manifest.

KiCad DRU format reference:
  https://docs.kicad.org/master/en/pcbnew/pcbnew_advanced.html#custom_design_rules

One rule block is emitted per net class. Each block enforces the minimum
trace width declared in the manifest. If the net class has an impedance
profile, a comment identifying the profile and target is included so
the board designer knows which traces require impedance control.
"""
from __future__ import annotations

from pcb_spec.schema.manifest import Manifest

__all__ = ["emit_dru"]

_MIL_TO_MM = 0.0254


def emit_dru(manifest: Manifest) -> str:
    """Return the full content of a .kicad_dru file for this manifest."""
    lines: list[str] = []
    lines.append("(version 1)")
    lines.append("")

    defined_profiles = {p.id: p for p in manifest.rules.impedance.profiles}

    for nc_name, nc in manifest.net_classes.items():
        width_mm = round(nc.rules.min_width_mil * _MIL_TO_MM, 4)
        lines.append(f'(rule "{nc_name} track-width"')
        lines.append(f'   (condition "A.NetClass == \\"{nc_name}\\"")')

        if nc.rules.impedance_profile and nc.rules.impedance_profile in defined_profiles:
            profile = defined_profiles[nc.rules.impedance_profile]
            lines.append(
                f'   ; impedance_profile: {profile.id}'
                f' (target {profile.target_ohm} ohm ±{profile.tolerance_pct}%)'
            )

        lines.append(f'   (constraint track-width (min {width_mm}mm))')
        lines.append(')')
        lines.append("")

    return "\n".join(lines)

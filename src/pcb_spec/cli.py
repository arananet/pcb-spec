"""CLI entry point for pcb-spec. Parse args, dispatch, format output."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pcb_spec.validator import ValidationResult, validate


def _markdown(result: ValidationResult, manifest_path: str) -> str:
    if result.status == "pass":
        return f"## PASS: {manifest_path}\n\nManifest is valid. No errors found."
    lines = [f"## FAIL: {manifest_path}", ""]
    for err in result.errors:
        lines.append(f"- **{err.code}** (`{err.location}`): {err.message}")
    return "\n".join(lines)


def _write_report(result: ValidationResult, manifest_path: str, report_path: str) -> None:
    report = {
        "schema_version": "0.1",
        "status": result.status,
        "manifest_path": manifest_path,
        "errors": [
            {"code": e.code, "message": e.message, "location": e.location}
            for e in result.errors
        ],
    }
    Path(report_path).write_text(json.dumps(report, indent=2))


def _cmd_validate(args: argparse.Namespace) -> int:
    result = validate(args.manifest)
    print(_markdown(result, args.manifest))
    if args.report:
        _write_report(result, args.manifest, args.report)
    return 0 if result.status == "pass" else 1


def _cmd_calc_impedance(args: argparse.Namespace) -> int:
    from pcb_spec.calc.impedance import microstrip_impedance, stripline_impedance
    try:
        if args.geometry == "microstrip":
            z0 = microstrip_impedance(args.width, args.height, args.thickness, args.er)
        else:
            z0 = stripline_impedance(args.width, args.height, args.thickness, args.er)
        print(f"Z0 = {z0:.2f} ohm")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _cmd_calc_current(args: argparse.Namespace) -> int:
    from pcb_spec.calc.current_capacity import min_trace_width_mm
    try:
        width = min_trace_width_mm(args.current, args.delta_t, args.copper_oz, args.layer)
        print(f"min_width = {width:.4f} mm  ({width / 0.0254:.2f} mil)")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="pcb-spec", description="PCB spec toolchain")
    sub = parser.add_subparsers(dest="command", required=True)

    # validate subcommand
    val = sub.add_parser("validate", help="Validate a manifest YAML file")
    val.add_argument("manifest", help="Path to the manifest YAML file")
    val.add_argument("--report", metavar="PATH", help="Write JSON report to PATH")

    # calc subcommand group
    calc = sub.add_parser("calc", help="Engineering calculators")
    calc_sub = calc.add_subparsers(dest="calc_cmd", required=True)

    # calc impedance
    imp = calc_sub.add_parser("impedance", help="Transmission-line impedance (microstrip/stripline)")
    imp.add_argument("--geometry", choices=["microstrip", "stripline"], required=True)
    imp.add_argument("--width", type=float, required=True, metavar="MM", help="Trace width (mm)")
    imp.add_argument("--height", type=float, required=True, metavar="MM",
                     help="Dielectric height for microstrip, or total dielectric thickness for stripline (mm)")
    imp.add_argument("--thickness", type=float, required=True, metavar="MM", help="Copper thickness (mm)")
    imp.add_argument("--er", type=float, required=True, help="Relative dielectric constant")

    # calc current-capacity
    cur = calc_sub.add_parser("current-capacity", help="Minimum trace width for a target current (IPC-2221B)")
    cur.add_argument("--current", type=float, required=True, metavar="A", help="Target current (amps)")
    cur.add_argument("--delta-t", type=float, required=True, metavar="C",
                     help="Allowable temperature rise above ambient (°C)")
    cur.add_argument("--copper-oz", type=float, required=True, help="Copper weight (oz)")
    cur.add_argument("--layer", choices=["external", "internal"], required=True)

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(_cmd_validate(args))
    elif args.command == "calc":
        if args.calc_cmd == "impedance":
            sys.exit(_cmd_calc_impedance(args))
        elif args.calc_cmd == "current-capacity":
            sys.exit(_cmd_calc_current(args))


if __name__ == "__main__":
    main()

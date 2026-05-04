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


def main() -> None:
    parser = argparse.ArgumentParser(prog="pcb-spec", description="PCB spec toolchain")
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="Validate a manifest YAML file")
    val.add_argument("manifest", help="Path to the manifest YAML file")
    val.add_argument("--report", metavar="PATH", help="Write JSON report to PATH")

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(_cmd_validate(args))


if __name__ == "__main__":
    main()

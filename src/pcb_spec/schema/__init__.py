"""
Public helpers for loading and dumping pcb-spec manifests, and generating
schema documentation from the JSON Schema file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import yaml

from .manifest import Manifest

__all__ = ["load_manifest", "dump_manifest", "generate_schema_docs"]


def load_manifest(
    path: Path | str,
    bom_components: Optional[set[str]] = None,
) -> Manifest:
    """Load and validate a manifest YAML file.

    bom_components, if provided, is the set of known component IDs; any
    placement entry whose component_id is absent from the set raises ValueError.
    BOM cross-referencing against the bundled library is handled by the
    conformance-checker spec once that data exists.
    """
    data = yaml.safe_load(Path(path).read_text())
    manifest = Manifest.model_validate(data)
    if bom_components is not None:
        for p in manifest.placement:
            if p.component_id not in bom_components:
                raise ValueError(
                    f"Placement references component {p.component_id!r} not in BOM"
                )
    return manifest


def dump_manifest(manifest: Manifest, path: Path | str) -> None:
    """Serialise a Manifest back to YAML at the given path."""
    data = manifest.model_dump(exclude_none=True)
    Path(path).write_text(yaml.dump(data, sort_keys=False, allow_unicode=True))


def generate_schema_docs(schema_path: Path | str, output_path: Path | str) -> None:
    """Generate a Markdown reference from the JSON Schema.

    Produces one ## section per top-level manifest field, drawn from the
    JSON Schema's title/description/properties tree. The output is written to
    output_path and is also the file committed at docs/manifest-schema.md.
    """
    schema = json.loads(Path(schema_path).read_text())
    lines: list[str] = []

    lines.append(f"# {schema.get('title', 'Manifest Schema')}")
    lines.append("")
    if desc := schema.get("description"):
        lines.append(desc)
        lines.append("")
    lines.append(
        f"> Auto-generated from `src/pcb_spec/schema/manifest.schema.json`. "
        f"Do not edit by hand."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    top_props = schema.get("properties", {})
    required = set(schema.get("required", []))

    for field_name, field_schema in top_props.items():
        req_marker = " *(required)*" if field_name in required else " *(optional)*"
        lines.append(f"## `{field_name}`{req_marker}")
        lines.append("")
        if field_desc := field_schema.get("description"):
            lines.append(field_desc)
            lines.append("")
        # Type or enum
        if "enum" in field_schema:
            lines.append(f"**Allowed values:** `{'`, `'.join(str(v) for v in field_schema['enum'])}`")
            lines.append("")
        elif "type" in field_schema:
            lines.append(f"**Type:** `{field_schema['type']}`")
            lines.append("")
        # Sub-properties summary
        sub_props = field_schema.get("properties", {})
        if sub_props:
            lines.append("**Fields:**")
            lines.append("")
            for sub_name, sub_schema in sub_props.items():
                sub_desc = sub_schema.get("description", "")
                lines.append(f"- `{sub_name}` — {sub_desc}")
            lines.append("")
        lines.append("---")
        lines.append("")

    Path(output_path).write_text("\n".join(lines))

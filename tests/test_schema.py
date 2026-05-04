"""
Tests for the manifest schema — one test per test_plan item in
.openspec/specs/manifest-schema.spec.yaml.
"""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pcb_spec.schema import dump_manifest, generate_schema_docs, load_manifest
from pcb_spec.schema.manifest import Manifest

FIXTURES_INVALID = Path(__file__).parent / "fixtures" / "invalid"
EXAMPLES = Path(__file__).parent.parent / "examples"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _minimal_manifest_dict() -> dict:
    """Returns a dict that produces a valid Manifest; mutate to exercise edge cases."""
    return {
        "manifest_version": "0.1",
        "project": {"name": "test-board", "revision": "r1"},
        "stackup": {
            "fab_house_id": "jlcpcb",
            "stackup_id": "jlcpcb-2l",
            "layers": [
                {"number": 1, "name": "F.Cu", "type": "signal", "copper_oz": 1},
                {"number": 2, "name": "B.Cu", "type": "signal", "copper_oz": 1},
            ],
        },
        "rules": {
            "current_capacity": {"citation": "IPC-2152, Table 5-1", "entries": []},
            "spacing": {"citation": "IPC-2221B, Table 6-1", "entries": []},
            "fab_dfm": {"citation": "JLCPCB standard PCB capability", "entries": []},
            "impedance": {"citation": "IPC-2141A", "profiles": []},
        },
        "net_classes": {
            "DEFAULT": {
                "description": "Default",
                "members": [],
                "rules": {"min_width_mil": 6, "route_layers": ["F.Cu", "B.Cu"]},
            }
        },
        "gates": {"schematic": [], "layout": [], "dfm": []},
    }


# ── Unit tests ─────────────────────────────────────────────────────────────────

# test_plan.unit_tests[0]: rejects manifest with missing required field
@pytest.mark.parametrize("missing_field", [
    "manifest_version", "project", "stackup", "rules", "net_classes", "gates"
])
def test_rejects_missing_required_field(missing_field: str) -> None:
    data = _minimal_manifest_dict()
    del data[missing_field]
    with pytest.raises(ValidationError):
        Manifest.model_validate(data)


# test_plan.unit_tests[1]: rejects manifest_version outside supported list
def test_rejects_unsupported_manifest_version() -> None:
    data = _minimal_manifest_dict()
    data["manifest_version"] = "99.0"
    with pytest.raises(ValidationError, match="Unsupported manifest_version"):
        Manifest.model_validate(data)


# test_plan.unit_tests[2]: stackup loader rejects duplicate layer numbers
def test_rejects_duplicate_layer_numbers() -> None:
    fixture = FIXTURES_INVALID / "duplicate_layer_numbers.yaml"
    with pytest.raises(ValidationError, match="duplicate layer numbers"):
        Manifest.model_validate(yaml.safe_load(fixture.read_text()))


# test_plan.unit_tests[3]: net class loader rejects undefined impedance_profile ref
def test_rejects_undefined_impedance_profile_ref() -> None:
    fixture = FIXTURES_INVALID / "undefined_impedance_profile.yaml"
    with pytest.raises(ValidationError, match="undefined impedance_profile"):
        Manifest.model_validate(yaml.safe_load(fixture.read_text()))


# test_plan.unit_tests[4]: placement loader rejects component_id absent from BOM
def test_rejects_placement_component_id_not_in_bom(tmp_path: Path) -> None:
    data = _minimal_manifest_dict()
    data["placement"] = [{"component_id": "U1", "net_class": "DEFAULT"}]
    manifest_file = tmp_path / "manifest.yaml"
    manifest_file.write_text(yaml.dump(data))
    with pytest.raises(ValueError, match="not in BOM"):
        load_manifest(manifest_file, bom_components={"U2"})  # U1 absent


# test_plan.unit_tests[5]: gate loader rejects gate without stable id field
def test_rejects_gate_without_id() -> None:
    fixture = FIXTURES_INVALID / "gate_missing_id.yaml"
    with pytest.raises(ValidationError):
        Manifest.model_validate(yaml.safe_load(fixture.read_text()))


# test_plan.unit_tests[6]: YAML round-trip preserves deep equality
def test_yaml_round_trip(tmp_path: Path) -> None:
    source = EXAMPLES / "minimal-2layer" / "manifest.yaml"
    m1 = load_manifest(source)
    out = tmp_path / "roundtrip.yaml"
    dump_manifest(m1, out)
    m2 = load_manifest(out)
    assert m1.model_dump() == m2.model_dump()


# ── Integration tests ──────────────────────────────────────────────────────────

# test_plan.integration_tests[0]: all three examples pass schema validation
def test_example_minimal_2layer_valid() -> None:
    load_manifest(EXAMPLES / "minimal-2layer" / "manifest.yaml")


def test_example_4layer_mixed_signal_valid() -> None:
    load_manifest(EXAMPLES / "4layer-mixed-signal" / "manifest.yaml")


def test_example_controlled_impedance_valid() -> None:
    load_manifest(EXAMPLES / "controlled-impedance" / "manifest.yaml")


# test_plan.integration_tests[1]: schema doc generation produces docs/manifest-schema.md
def test_schema_doc_generation(tmp_path: Path) -> None:
    schema_path = Path(__file__).parent.parent / "src" / "pcb_spec" / "schema" / "manifest.schema.json"
    output = tmp_path / "manifest-schema.md"
    generate_schema_docs(schema_path, output)
    content = output.read_text()
    # One section per top-level manifest field
    for field in ("manifest_version", "project", "stackup", "rules", "net_classes", "placement", "gates"):
        assert f"## `{field}`" in content, f"Missing section for field '{field}'"


# test_plan.integration_tests[2]: JSON Schema and Pydantic model agree on all examples
def test_json_schema_matches_pydantic_on_examples() -> None:
    import json
    import jsonschema

    schema_path = Path(__file__).parent.parent / "src" / "pcb_spec" / "schema" / "manifest.schema.json"
    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft202012Validator(schema)

    example_dirs = ["minimal-2layer", "4layer-mixed-signal", "controlled-impedance"]
    for name in example_dirs:
        manifest_path = EXAMPLES / name / "manifest.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        # Pydantic accepts it
        Manifest.model_validate(data)
        # JSON Schema accepts it
        errors = list(validator.iter_errors(data))
        assert not errors, f"{name}: JSON Schema errors: {[e.message for e in errors]}"

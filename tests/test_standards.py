"""Tests for data/ipc/ and data/fab/ — standards-rule-library spec."""

from pathlib import Path

import yaml
import pytest

DATA = Path(__file__).parent.parent / "data"
IPC = DATA / "ipc"
FAB = DATA / "fab"

IPC_FILES = ["ipc-2221.yaml", "ipc-2152.yaml"]
FAB_FILES = ["jlcpcb.yaml", "pcbway.yaml", "oshpark.yaml"]
ALL_FILES = [IPC / f for f in IPC_FILES] + [FAB / f for f in FAB_FILES]


@pytest.mark.parametrize("path", ALL_FILES, ids=[p.name for p in ALL_FILES])
def test_file_loads_without_error(path):
    # AC: all data files loadable via yaml.safe_load()
    data = yaml.safe_load(path.read_text())
    assert data is not None


@pytest.mark.parametrize("path", ALL_FILES, ids=[p.name for p in ALL_FILES])
def test_schema_version_present(path):
    # AC: every data file has a schema_version field
    data = yaml.safe_load(path.read_text())
    assert "schema_version" in data
    assert isinstance(data["schema_version"], str)


def test_ipc_2221_has_nine_voltage_classes():
    # AC: B1 through B9 per IPC-2221B Table 6-1
    data = yaml.safe_load((IPC / "ipc-2221.yaml").read_text())
    table = data["voltage_clearance_table"]
    assert len(table) == 9
    classes = [row["voltage_class"] for row in table]
    assert classes == ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"]


def test_ipc_2221_all_entries_have_required_fields():
    # AC: every row has all required fields with non-empty citation
    required = {
        "voltage_class", "min_voltage_v", "max_voltage_v",
        "clearance_external_uncoated_mm",
        "clearance_external_coated_mm",
        "clearance_internal_mm",
        "citation",
    }
    data = yaml.safe_load((IPC / "ipc-2221.yaml").read_text())
    for row in data["voltage_clearance_table"]:
        missing = required - row.keys()
        assert not missing, f"Row {row.get('voltage_class')} missing: {missing}"
        assert row["citation"], f"Row {row.get('voltage_class')} has empty citation"


def test_ipc_2221_clearance_values_are_positive_floats():
    data = yaml.safe_load((IPC / "ipc-2221.yaml").read_text())
    for row in data["voltage_clearance_table"]:
        for key in ("clearance_external_uncoated_mm",
                    "clearance_external_coated_mm",
                    "clearance_internal_mm"):
            assert isinstance(row[key], (int, float)), (
                f"Row {row['voltage_class']}.{key} is not numeric"
            )
            assert row[key] > 0, (
                f"Row {row['voltage_class']}.{key} must be positive"
            )


def test_ipc_2221_voltage_ranges_are_non_overlapping_and_ascending():
    data = yaml.safe_load((IPC / "ipc-2221.yaml").read_text())
    rows = data["voltage_clearance_table"]
    for i in range(len(rows) - 1):
        assert rows[i]["max_voltage_v"] < rows[i + 1]["min_voltage_v"] or \
               rows[i]["max_voltage_v"] + 1 == rows[i + 1]["min_voltage_v"], (
            f"Voltage range gap/overlap between {rows[i]['voltage_class']} and {rows[i+1]['voltage_class']}"
        )


def test_ipc_2152_has_ipc_2221_fallback():
    # AC: ipc-2152.yaml has the public IPC-2221 fallback coefficients
    data = yaml.safe_load((IPC / "ipc-2152.yaml").read_text())
    fb = data["ipc_2221_fallback"]
    assert "external_conductors" in fb
    assert "internal_conductors" in fb
    ext = fb["external_conductors"]
    assert "k" in ext and "b" in ext and "c" in ext
    assert ext["citation"]


def test_ipc_2152_citations_non_empty_for_populated_values():
    # AC: every numeric leaf in data/ipc/ has a non-empty citation
    data = yaml.safe_load((IPC / "ipc-2152.yaml").read_text())
    fb = data["ipc_2221_fallback"]
    for layer in ("external_conductors", "internal_conductors"):
        assert fb[layer]["citation"], f"{layer} missing citation"
    assert fb["citation"]


def test_jlcpcb_has_fab_id_and_capability_url():
    # AC: jlcpcb.yaml has fab_id == 'jlcpcb' and non-empty capability_sheet_url
    data = yaml.safe_load((FAB / "jlcpcb.yaml").read_text())
    assert data["fab_id"] == "jlcpcb"
    assert data["capability_sheet_url"]
    assert data["capability_sheet_url"].startswith("http")


def test_fab_files_have_required_capability_keys():
    # AC: all fab files have the same set of capability keys
    required_keys = {
        "min_trace_width_mm", "min_trace_spacing_mm", "min_drill_mm",
        "min_annular_ring_mm", "max_board_mm", "min_board_mm",
        "board_thickness_mm", "copper_weights_oz", "layer_counts",
        "surface_finishes", "min_copper_to_edge_mm",
    }
    for fname in FAB_FILES:
        data = yaml.safe_load((FAB / fname).read_text())
        caps = data.get("capabilities", {})
        missing = required_keys - caps.keys()
        assert not missing, f"{fname} capabilities missing: {missing}"


def test_fab_files_each_capability_has_citation():
    # AC: every capability entry has a citation field
    for fname in FAB_FILES:
        data = yaml.safe_load((FAB / fname).read_text())
        caps = data.get("capabilities", {})
        for key, val in caps.items():
            if isinstance(val, dict):
                assert "citation" in val, (
                    f"{fname}: capabilities.{key} missing citation field"
                )

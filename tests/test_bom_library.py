"""Tests for data/bom/library.yaml — bom-library-format spec."""

from pathlib import Path

import yaml
import pytest

LIBRARY = Path(__file__).parent.parent / "data" / "bom" / "library.yaml"

KNOWN_UNIT_SUFFIXES = {
    "_v", "_a", "_w", "_ohm", "_hz", "_f",
    "_pf", "_uf", "_nf", "_mohm", "_c", "_mhz",
    "_kb", "_ppm",
    "_ratio",    # dimensionless ratios (e.g. hfe_min_ratio)
    "_cycles",   # mechanical endurance (e.g. rated_mating_cycles)
}

REQUIRED_FIELDS = {
    "id", "manufacturer", "mpn", "description",
    "package", "pin_count", "datasheet_url", "ratings",
}


def _load():
    return yaml.safe_load(LIBRARY.read_text())


def test_library_loads_without_error():
    data = _load()
    assert data is not None


def test_schema_version_present():
    data = _load()
    assert "schema_version" in data


def test_all_ids_are_unique():
    data = _load()
    ids = [c["id"] for c in data["components"]]
    assert len(ids) == len(set(ids)), "Duplicate component ids found"


def test_all_required_fields_present():
    data = _load()
    for comp in data["components"]:
        missing = REQUIRED_FIELDS - comp.keys()
        assert not missing, f"Component {comp.get('id')} missing fields: {missing}"


def test_all_rating_field_names_have_unit_suffixes():
    # AC: no bare numeric field names — every rating key ends with a known suffix
    data = _load()
    for comp in data["components"]:
        for key in comp.get("ratings", {}).keys():
            has_suffix = any(key.endswith(suf) for suf in KNOWN_UNIT_SUFFIXES)
            assert has_suffix, (
                f"Component {comp['id']}: rating field '{key}' lacks unit suffix. "
                f"Known suffixes: {sorted(KNOWN_UNIT_SUFFIXES)}"
            )


def test_library_has_at_least_fifteen_entries():
    # AC: at least 15 seed components
    data = _load()
    assert len(data["components"]) >= 15


def test_all_datasheet_urls_are_non_empty_strings():
    data = _load()
    for comp in data["components"]:
        url = comp.get("datasheet_url", "")
        assert url and url.startswith("http"), (
            f"Component {comp['id']} has invalid datasheet_url: {url!r}"
        )


def test_all_pin_counts_are_positive_integers():
    data = _load()
    for comp in data["components"]:
        assert isinstance(comp["pin_count"], int) and comp["pin_count"] > 0, (
            f"Component {comp['id']} has invalid pin_count: {comp['pin_count']}"
        )


def test_known_families_present():
    # AC: covers linear regulator, LDO, NPN transistor, Schottky diode,
    # USB connector, MCU, crystal, ferrite bead, passive families
    data = _load()
    ids = {c["id"] for c in data["components"]}
    packages = {c["package"] for c in data["components"]}
    # At least one of each required family
    assert any("LM7805" in i or "AMS1117" in i for i in ids), "No regulator found"
    assert any("2N3904" in i or "NPN" in i.upper() for i in ids), "No NPN transistor found"
    assert any("BAT" in i or "SCHOTTKY" in i.upper() or "DIODE" in i.upper() for i in ids), "No Schottky diode found"
    assert any("USB" in i for i in ids), "No USB connector found"
    assert any("STM32" in i or "ATMEGA" in i or "MCU" in i.upper() for i in ids), "No MCU found"
    assert any("XTAL" in i or "OSC" in i for i in ids), "No crystal found"
    assert any("FERRITE" in i or "BEAD" in i for i in ids), "No ferrite bead found"
    assert "0402" in packages and "0603" in packages, "Missing 0402 or 0603 passive packages"

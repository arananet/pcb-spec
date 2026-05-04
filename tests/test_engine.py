"""Tests for src/pcb_spec/engine.py — rule-engine-contract spec."""

from pathlib import Path

import pytest

from pcb_spec.engine import (
    FactBase,
    RuleEntry,
    RuleSource,
    Severity,
    ResolutionStep,
    Violation,
    evaluate,
    resolve_numeric_min,
    resolve_value,
)
from pcb_spec.schema import load_manifest

EXAMPLES = Path(__file__).parent.parent / "examples"


# ── helpers ───────────────────────────────────────────────────────────────────

def _v(
    rule_id="RULE_01",
    gate_id=None,
    severity=Severity.ERROR,
    message="test violation",
    net_name=None,
    component_id=None,
    expected="10",
    actual="5",
    citation="",
    remediation="",
    resolution_chain=None,
) -> Violation:
    return Violation(
        rule_id=rule_id,
        gate_id=gate_id,
        severity=severity,
        message=message,
        net_name=net_name,
        component_id=component_id,
        expected=expected,
        actual=actual,
        citation=citation,
        remediation=remediation,
        resolution_chain=resolution_chain or [],
    )


# ── resolve_value ─────────────────────────────────────────────────────────────

def test_resolve_value_manifest_beats_ipc_seed():
    # AC: most-specific-wins; MANIFEST overrides IPC_SEED
    value, _ = resolve_value([
        (RuleSource.IPC_SEED, "10", "IPC-2152 §5.1"),
        (RuleSource.MANIFEST, "20", "manifest override"),
    ])
    assert value == "20"


def test_resolve_value_fab_dfm_beats_ipc_seed():
    # AC: FAB_DFM is more specific than IPC_SEED
    value, _ = resolve_value([
        (RuleSource.IPC_SEED, "10", "IPC-2152 §5.1"),
        (RuleSource.FAB_DFM, "6", "JLCPCB capability sheet"),
    ])
    assert value == "6"


def test_resolve_value_ipc_seed_only():
    # AC: IPC_SEED is returned when it is the only candidate
    value, _ = resolve_value([
        (RuleSource.IPC_SEED, "10", "IPC-2152 §5.1"),
    ])
    assert value == "10"


def test_resolve_value_raises_on_empty_candidates():
    # AC: empty candidates list raises ValueError
    with pytest.raises(ValueError):
        resolve_value([])


def test_resolve_value_chain_contains_all_sources_in_resolution_order():
    # AC: resolution_chain records every candidate, sorted least-to-most specific
    candidates = [
        (RuleSource.MANIFEST, "20", "manifest"),
        (RuleSource.IPC_SEED, "10", "IPC"),
        (RuleSource.FAB_DFM, "6", "fab"),
    ]
    _, chain = resolve_value(candidates)
    sources = [step.source for step in chain]
    assert len(chain) == 3
    # sorted least-to-most specific
    assert sources == [RuleSource.IPC_SEED, RuleSource.FAB_DFM, RuleSource.MANIFEST]


# ── resolve_numeric_min ───────────────────────────────────────────────────────

def test_resolve_numeric_min_fab_dfm_beats_ipc_seed_when_ipc_larger():
    # AC: specificity beats magnitude; FAB_DFM=6 wins over IPC_SEED=15
    value, chain = resolve_numeric_min([
        (RuleSource.IPC_SEED, "15", "IPC-2152"),
        (RuleSource.FAB_DFM, "6", "JLCPCB"),
    ])
    assert value == "6"
    assert len(chain) == 2


def test_resolve_numeric_min_manifest_beats_fab_dfm_chain_records_both():
    # AC: MANIFEST wins over FAB_DFM; both appear in resolution_chain
    value, chain = resolve_numeric_min([
        (RuleSource.FAB_DFM, "6", "JLCPCB"),
        (RuleSource.MANIFEST, "8", "project manifest"),
    ])
    assert value == "8"
    sources = {step.source for step in chain}
    assert RuleSource.FAB_DFM in sources
    assert RuleSource.MANIFEST in sources


# ── evaluate ─────────────────────────────────────────────────────────────────

def test_evaluate_aggregates_violations_from_all_predicates():
    # AC: evaluate calls every registered predicate and collects all violations
    v1 = _v(rule_id="A")
    v2 = _v(rule_id="B")
    registry = {
        "pred_a": lambda fb: [v1],
        "pred_b": lambda fb: [v2],
    }
    result = evaluate(registry, FactBase(manifest=None))
    assert len(result) == 2


def test_evaluate_sorted_error_first_then_rule_id_lexicographic():
    # AC: violations sorted ERROR-first, then by rule_id lexicographically
    v_warn = _v(rule_id="A", severity=Severity.WARNING)
    v_err_b = _v(rule_id="B", severity=Severity.ERROR)
    v_err_a = _v(rule_id="A", severity=Severity.ERROR)
    registry = {
        "p1": lambda fb: [v_warn, v_err_b],
        "p2": lambda fb: [v_err_a],
    }
    result = evaluate(registry, FactBase(manifest=None))
    assert [v.severity for v in result] == [
        Severity.ERROR, Severity.ERROR, Severity.WARNING
    ]
    assert result[0].rule_id == "A"
    assert result[1].rule_id == "B"


def test_evaluate_empty_registry_returns_empty_list():
    # AC: no error on empty registry
    assert evaluate({}, FactBase(manifest=None)) == []


# ── Violation.stable_hash ────────────────────────────────────────────────────

def test_violation_stable_hash_same_for_different_messages():
    # AC: hash over (rule_id, gate_id, net_name, component_id) — not message text
    v1 = _v(rule_id="R1", gate_id="G1", net_name="VCC", component_id="U1",
            message="old message")
    v2 = _v(rule_id="R1", gate_id="G1", net_name="VCC", component_id="U1",
            message="updated message text")
    assert v1.stable_hash == v2.stable_hash


def test_violation_stable_hash_differs_on_different_rule_id():
    v1 = _v(rule_id="R1")
    v2 = _v(rule_id="R2")
    assert v1.stable_hash != v2.stable_hash


# ── integration tests ────────────────────────────────────────────────────────

@pytest.mark.parametrize("example", [
    "minimal-2layer",
    "4layer-mixed-signal",
    "controlled-impedance",
])
def test_fact_base_from_example_manifests(example):
    # AC: FactBase can be constructed from any of the three example manifests
    manifest = load_manifest(EXAMPLES / example / "manifest.yaml")
    fb = FactBase(manifest=manifest, netlist=None, calc_results={})
    assert fb.manifest is not None
    assert fb.netlist is None
    assert fb.calc_results == {}


def test_evaluate_produces_violation_with_populated_resolution_chain():
    # AC: a predicate registered via evaluate produces Violation with resolution_chain
    _, chain = resolve_value([
        (RuleSource.IPC_SEED, "10", "IPC-2152"),
        (RuleSource.MANIFEST, "20", "project manifest"),
    ])
    v = _v(rule_id="WIDTH_CHECK", resolution_chain=chain)
    result = evaluate({"check": lambda fb: [v]}, FactBase(manifest=None))
    assert len(result) == 1
    assert len(result[0].resolution_chain) == 2


def test_resolution_chain_manifest_over_ipc_seed_has_two_steps_in_order():
    # AC: resolution_chain with MANIFEST override over IPC_SEED has exactly
    # two ResolutionStep entries — IPC_SEED first, MANIFEST second
    _, chain = resolve_value([
        (RuleSource.IPC_SEED, "10", "IPC-2152"),
        (RuleSource.MANIFEST, "20", "project manifest"),
    ])
    assert len(chain) == 2
    assert chain[0].source == RuleSource.IPC_SEED
    assert chain[1].source == RuleSource.MANIFEST

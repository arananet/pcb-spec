"""Rule engine contract: types, resolution logic, and evaluation loop.

This module defines the shared contract every downstream module (conformance
checker, rule emitter, CLI) depends on. It contains no gate implementations
and no numeric data — those live in the specs that depend on this one.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable

__all__ = [
    "RuleSource",
    "Severity",
    "ResolutionStep",
    "RuleEntry",
    "Violation",
    "FactBase",
    "RuleRegistry",
    "resolve_value",
    "resolve_numeric_min",
    "evaluate",
]


class RuleSource(IntEnum):
    """Resolution precedence order, least to most specific."""

    IPC_SEED = 0   # general standard; applies when nothing more specific exists
    FAB_DFM = 1    # physical fab constraint; cannot be violated by design intent
    NET_CLASS = 2  # per-net-class routing intent
    MANIFEST = 3   # explicit per-project override; highest specificity


class Severity(IntEnum):
    """Violation severity. Lower value sorts first (ERROR before WARNING)."""

    ERROR = 0    # blocks sign-off
    WARNING = 1  # advisory


@dataclass
class ResolutionStep:
    """One layer's contribution to a resolved value.

    A list of ResolutionSteps forms the resolution_chain on a Violation,
    making the winning source fully traceable.
    """

    source: RuleSource
    value: str
    citation: str


@dataclass
class RuleEntry:
    """Metadata for a single rule.

    Predicates live in code (see CLAUDE-pcbspec.md §notes); params live here.
    No callable field — the registry maps rule IDs to predicates separately.
    """

    id: str
    source: RuleSource
    severity: Severity
    citation: str
    params: dict = field(default_factory=dict)


@dataclass
class Violation:
    """A single rule violation produced by a gate predicate."""

    rule_id: str
    gate_id: str | None
    severity: Severity
    message: str
    net_name: str | None
    component_id: str | None
    expected: str
    actual: str
    citation: str
    remediation: str
    resolution_chain: list[ResolutionStep] = field(default_factory=list)

    @property
    def stable_hash(self) -> str:
        """SHA-256 over the identity tuple (rule_id, gate_id, net_name, component_id).

        Stable across runs and message-text changes so violation diffs are
        meaningful ("3 new violations since last run").
        """
        key = (
            self.rule_id or "",
            self.gate_id or "",
            self.net_name or "",
            self.component_id or "",
        )
        return hashlib.sha256(repr(key).encode()).hexdigest()


@dataclass
class FactBase:
    """Read-only input to every predicate.

    netlist is typed Any until kicad-netlist-parser is implemented;
    the conformance-checker spec will tighten that type.
    """

    manifest: Any  # pcb_spec.schema.manifest.Manifest
    netlist: Any = None
    calc_results: dict[str, Any] = field(default_factory=dict)


# A registry maps rule IDs to predicate functions.
# Each predicate receives the FactBase and returns zero or more Violations.
RuleRegistry = dict[str, Callable[[FactBase], list[Violation]]]


def resolve_value(
    candidates: list[tuple[RuleSource, str, str]],
) -> tuple[str, list[ResolutionStep]]:
    """Return the winning value and the full resolution chain.

    Most-specific-wins: MANIFEST > NET_CLASS > FAB_DFM > IPC_SEED.
    The chain contains every candidate sorted from least to most specific,
    so the caller can inspect why a particular source won.
    """
    if not candidates:
        raise ValueError("resolve_value requires at least one candidate")

    chain = [
        ResolutionStep(source=src, value=val, citation=cit)
        for src, val, cit in sorted(candidates, key=lambda c: c[0])
    ]
    return chain[-1].value, chain


def resolve_numeric_min(
    candidates: list[tuple[RuleSource, str, str]],
) -> tuple[str, list[ResolutionStep]]:
    """Return the winning numeric minimum and full resolution chain.

    Applies the same most-specific-wins order as resolve_value. Specificity
    beats magnitude: FAB_DFM=6 wins over IPC_SEED=15 because the fab's
    physical capability is more authoritative than the standard's general
    recommendation, even when the recommendation is more conservative.

    All candidate values must be parseable as floats; raises ValueError otherwise.
    """
    if not candidates:
        raise ValueError("resolve_numeric_min requires at least one candidate")

    for src, val, cit in candidates:
        try:
            float(val)
        except ValueError:
            raise ValueError(
                f"resolve_numeric_min: value {val!r} from {src.name} is not numeric"
            )

    chain = [
        ResolutionStep(source=src, value=val, citation=cit)
        for src, val, cit in sorted(candidates, key=lambda c: c[0])
    ]
    return chain[-1].value, chain


def evaluate(
    registry: RuleRegistry,
    fact_base: FactBase,
) -> list[Violation]:
    """Run every predicate in the registry and return all violations.

    No short-circuit: every predicate runs regardless of earlier failures.
    Results are sorted ERROR-first, then by rule_id lexicographically.
    """
    violations: list[Violation] = []
    for predicate in registry.values():
        violations.extend(predicate(fact_base))

    violations.sort(key=lambda v: (v.severity, v.rule_id))
    return violations

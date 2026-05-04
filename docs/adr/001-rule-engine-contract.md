# ADR 001 — Rule Engine Contract

**Status:** accepted  
**Spec:** `rule-engine-contract`  
**Date:** 2026-05-04

---

## Context

`pcb-spec` evaluates a board manifest against physical constraints and produces
violations. Without a shared contract, each downstream module (conformance
checker, rule emitter, CLI) would invent its own violation shape, rule lookup
logic, and override semantics. The experiment cannot produce reproducible numbers
if each phase outputs violations in a different structure.

Three design decisions required explicit resolution before implementation could
begin.

---

## Decision 1 — Predicates in code, not declarative YAML

**Rejected alternative:** define rules as YAML expressions, e.g.
`predicate: "width >= ipc_2152_min(current, copper_oz)"`.

**Reason for rejection:** a declarative rule language requires a parser, an
expression evaluator, and a variable binding model — a language runtime. For
v0.1, a Python function is simpler, directly testable, and produces no ambiguity
about evaluation semantics. YAML entries in `data/` are lookup tables, not
executable logic. If a check needs to be exposed to an LLM, the LLM receives the
docstring and the violation message, not the source.

**What this means in practice:** `RuleEntry.params` holds data (thresholds,
configuration). The callable lives in `RuleRegistry`, keyed by `rule_id`. The
two are related by convention, not by a field on `RuleEntry`.

---

## Decision 2 — Four-source resolution order

The resolution order is: `IPC_SEED < FAB_DFM < NET_CLASS < MANIFEST`
(most-specific-wins).

**IPC_SEED:** general standard recommendation. Applies when nothing more specific
has been configured. A conservative baseline, not a hard constraint.

**FAB_DFM:** physical capability of the chosen fab house. Not a soft minimum. A
net class or manifest value that goes below the fab DFM floor is a manifest
authoring error, not a legal override. `resolve_numeric_min` enforces this by
treating specificity as the authority, not magnitude — FAB_DFM=6 mil beats
IPC_SEED=15 mil because the fab's actual capability is more authoritative than
the standard's general recommendation.

**NET_CLASS:** routing intent for a group of nets (e.g. a power net that needs
wider traces than the DFM floor). More specific than FAB_DFM for design-intent
values; the fab floor remains a hard lower bound via `resolve_numeric_min`.

**MANIFEST:** explicit per-project override. Highest specificity. Use sparingly
— most values should be derivable from the lower layers.

**Why not take the maximum of all minimums?** Taking MAX would produce a
conservative result but would hide the actual authority structure. If IPC_SEED
says 15 mil and the fab supports 6 mil, taking MAX would silently apply the IPC
recommendation without telling the user that the fab can do better. The
resolution chain makes the winning source visible and auditable.

---

## Decision 3 — No constraint solving in v0.1

**Rejected alternative:** integrate a constraint solver (Z3, OR-Tools) to find
the minimum set of layout changes that satisfies all rules simultaneously.

**Reason for rejection:** out of scope for v0.1. The engine is a reporter: it
finds and describes violations; it does not solve them. Getting the violation set
correct and reproducible is the prerequisite for measuring anything. Once
baseline numbers exist, a solver can be layered on top without changing the
contract — `Violation` and `FactBase` are stable inputs to any future solver.

---

## Decision 4 — Stable violation hash

`Violation.stable_hash` is SHA-256 over `(rule_id, gate_id, net_name,
component_id)`, not over `message`.

**Why:** running `pcb-spec check` twice on the same board must produce the same
violation IDs, so diffs are meaningful ("2 new violations since last run").
Hashing over message text would create spurious diffs whenever violation
descriptions are improved. The identity tuple is the minimal set of fields that
uniquely identifies where a rule fired.

---

## Consequences

- Every downstream spec imports its types from `pcb_spec.engine`. No module
  defines its own violation or resolution types.
- Gate implementations (in `conformance-checker`) are plain Python functions
  with signature `(FactBase) -> list[Violation]`. They are registered in a
  `RuleRegistry` dict and driven by `evaluate()`.
- `FactBase.netlist` is typed `Any` until `kicad-netlist-parser` is
  implemented. The conformance-checker spec will tighten that type.
- Adding a new resolution source in the future requires adding a `RuleSource`
  member and updating the resolution order — a one-line change to each function.

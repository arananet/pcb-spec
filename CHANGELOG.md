# Changelog

All notable changes to `pcb-spec` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Guidelines:
- Add a new entry under `## [Unreleased]` as you work — no batching up for release day.
- Group entries under: Added, Changed, Deprecated, Removed, Fixed, Security.
- Reference the spec slug and PR number:  "Added dark mode (spec: dark-mode, #42)".
- On release, rename `[Unreleased]` to the new version with the release date,
  and open a fresh `[Unreleased]` section at the top.
- The release-drafter workflow auto-populates draft release notes from PRs —
  keep PR titles tidy so they flow straight into here.
-->

## [Unreleased]

### Added
- Manifest schema v0.1: JSON Schema + Pydantic models for all five sections (stackup, rules, net_classes, placement, gates) (spec: manifest-schema)
- `load_manifest` / `dump_manifest` helpers in `src/pcb_spec/schema/__init__.py`
- Auto-generated schema reference at `docs/manifest-schema.md`
- Three validated example manifests: `minimal-2layer`, `4layer-mixed-signal`, `controlled-impedance`
- Full test suite in `tests/test_schema.py` (17 tests, all passing)
- Board repo templates in `templates/board-repo/`: `AGENTS.md` agent contract, `pcb-spec.yml` three-gate CI pipeline (validate → KiCad export → schematic/layout/DFM gates → PR comment → release fab bundle), `KICAD_EXPORT.md` manual and headless export procedure
- `CLAUDE-implementation.md` architectural decision document: CLI + Skill (no MCP), final repo layout, CLI surface, skill structure, build order
- `rule-engine-contract` spec drafted: Rule/Violation/FactBase types, four-source resolution order, evaluation model
- `pcb-spec-skill` spec drafted: single spec replacing retired `llm-system-prompt`, `llm-authoring-assistant`, `llm-review-assistant`, `llm-drc-explainer`
- Rule engine contract implementation in `src/pcb_spec/engine.py`: `RuleSource`, `Severity`, `ResolutionStep`, `RuleEntry`, `Violation` (with `stable_hash`), `FactBase`, `RuleRegistry`, `resolve_value`, `resolve_numeric_min`, `evaluate` (spec: rule-engine-contract)
- `tests/test_engine.py` — 17 tests covering all unit and integration items in the spec's test_plan, all passing
- `docs/adr/001-rule-engine-contract.md` — four architectural decisions: predicates-in-code, four-source resolution order, no constraint solving, stable violation hash
- Standards rule library (spec: standards-rule-library): `data/ipc/ipc-2221.yaml` (IPC-2221B Table 6-1 voltage clearance, B1–B9), `data/ipc/ipc-2152.yaml` (IPC-2152 model parameters, IPC-2221 fallback polynomial), `data/fab/jlcpcb.yaml` + `pcbway.yaml` + `oshpark.yaml` (capability matrix structure; JLCPCB values require manual verification at https://jlcpcb.com/capabilities/pcb-capabilities and https://jlcpcb.com/blog/pcb-design-rules-best-practices)
- BOM component library (spec: bom-library-format): `data/bom/library.yaml` — 19 seed entries (linear regulators, LDO, NPN transistor, Schottky diode, USB connectors, MCUs, crystals, ferrite beads, passive package families) all with manufacturer datasheet citations
- `tests/test_standards.py` (19 tests) and `tests/test_bom_library.py` (9 tests), all passing
- KiCad rule emitter (spec: kicad-rule-emitter): `src/pcb_spec/emit/kicad.py` — `emit_dru()` generates `.kicad_dru` with one `track-width` rule per net class; impedance profile comment for controlled-impedance classes; CLI `pcb-spec emit kicad <manifest> [-o <path>]`
- `tests/test_kicad_emitter.py` (10 tests), all passing
- KiCad netlist parser (spec: kicad-netlist-parser): `src/pcb_spec/conformance/netlist_parser.py` — minimal sexp tokenizer + parser; `Netlist`/`Component`/`Net`/`NetNode` dataclasses; `component_refs()` and `net_names()` helpers
- Conformance checker (spec: conformance-checker): `src/pcb_spec/conformance/gates.py` — `run_schematic_gates()` with NET_CLASS_MEMBER_NOT_IN_NETLIST and PLACEMENT_COMPONENT_NOT_IN_NETLIST predicates; CLI `pcb-spec check <manifest> <netlist> [--report]`
- `tests/test_netlist_parser.py` (10 tests) and `tests/test_conformance.py` (10 tests), all passing
- Impedance calculator (spec: impedance-calculator): `src/pcb_spec/calc/impedance.py` — `microstrip_impedance()` and `stripline_impedance()` (IPC-2141A/Wadell closed-form); CLI `pcb-spec calc impedance --geometry microstrip|stripline`
- Current capacity calculator (spec: current-capacity-calculator): `src/pcb_spec/calc/current_capacity.py` — `min_trace_width_mm()` reading IPC-2221B coefficients from `data/ipc/ipc-2152.yaml`; CLI `pcb-spec calc current-capacity`
- `tests/test_impedance.py` (14 tests) and `tests/test_current_capacity.py` (12 tests), all passing
- Schema validator `pcb-spec validate` (spec: schema-validator): `src/pcb_spec/validator/__init__.py` (`validate()` → `ValidationResult`/`ValidationError` dataclasses), `src/pcb_spec/validator/rules.py` (placeholder), `src/pcb_spec/cli.py` (argparse: `validate` subcommand + `--report`), `src/pcb_spec/__main__.py` (`python3 -m pcb_spec` entry point)
- `tests/test_validator.py` — 15 tests (7 unit + 4 integration subprocess) covering all spec acceptance criteria, all passing
- `docs/report-schema.md` — public JSON report API reference (schema_version, status, manifest_path, errors)

### Changed
-

### Deprecated
-

### Removed
-

### Fixed
-

### Security
-

---

## [0.1.0] — YYYY-MM-DD

### Added
- Initial release.

[Unreleased]: https://github.com/arananet/pcb-spec/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/arananet/pcb-spec/releases/tag/v0.1.0

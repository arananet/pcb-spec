# pcb-spec specs roadmap

This is the development plan. Each entry will become an OpenSpec spec under
`.openspec/specs/`. Specs are listed in dependency order. The first one
(`manifest-schema`) is already drafted; the rest will be drafted next.

---

## Phase 0: Foundation

### 1. `manifest-schema`

**Status:** drafted (`.openspec/specs/manifest-schema.spec.yaml`)
**Dependencies:** none

Define the canonical YAML schema for the constraint manifest. JSON Schema +
Pydantic model. Examples for minimal, 4-layer mixed-signal, and controlled
impedance boards.

### 2. `standards-rule-library`

**Dependencies:** `manifest-schema`

Bundle public standards data as versioned YAML files: IPC-2152 current
capacity tables, IPC-2221 voltage spacing, common fab DFM minimums for
JLCPCB, PCBWay, OSH Park. Data, not code. User-replaceable. Each entry has
a citation pointing back to the standard clause or fab capability sheet.

### 3. `bom-library-format`

**Dependencies:** `manifest-schema`

Define a per-component YAML format describing pins, required externals,
package, ratings. The conformance checker cross-references the netlist
against this library. Seed with ~20 common parts (basic regulators, MCUs,
USB connectors, decoupling caps).

---

## Phase 1: Validator

### 4. `schema-validator`

**Dependencies:** `manifest-schema`

CLI: `pcb-spec validate <manifest.yaml>`. Validates against schema, checks
internal consistency (every net class member exists, every impedance
profile referenced is defined, every gate references real fields). Pure
Python, no external deps beyond YAML and JSON Schema. Returns structured
pass/fail with specific error codes. One afternoon of work.

---

## Phase 2: Calculators

### 5. `impedance-calculator`

**Dependencies:** `manifest-schema`

Wadell equations: microstrip, stripline, edge-coupled differential pairs.
Pure Python, takes geometry plus stackup, returns impedance. Wired up as an
LLM tool so the authoring workflow can compute target widths from impedance
targets rather than hardcoding them. Validated against published reference
values from Polar Instruments calculator.

### 6. `current-capacity-calculator`

**Dependencies:** `manifest-schema`, `standards-rule-library`

IPC-2152 polynomial implementation. Inputs: copper weight, layer location,
current, allowed temperature rise. Output: required width. The
deterministic backstop for any "trace width for X amps" question. Includes
via current capacity for sizing power delivery via stitching.

---

## Phase 3: Conformance checker

### 7. `kicad-netlist-parser`

**Dependencies:** `manifest-schema`

Read KiCad `.net` files (S-expression format) into an internal graph
representation: components, nets, pins, connections. KiCad first because
it's open and the format is documented. Parser is isolated from the gate
runner so future spec can add Altium/Eagle netlist parsers without
touching gate logic.

### 8. `conformance-checker`

**Dependencies:** `manifest-schema`, `bom-library-format`, `kicad-netlist-parser`

CLI: `pcb-spec check <manifest.yaml> <netlist.net>`. Walks the netlist
plus manifest, runs each schematic-phase gate, reports violations.
Human-readable terminal output plus structured JSON for CI integration.
Each violation cites the gate ID from the manifest so it's traceable.

---

## Phase 4: EDA rule translator

### 9. `kicad-rule-emitter`

**Dependencies:** `manifest-schema`, `impedance-calculator`

CLI: `pcb-spec emit kicad <manifest.yaml> -o rules.kicad_dru`. Generates
KiCad's native design rule syntax. Handles net classes, clearances,
impedance constraints (where KiCad supports them), differential pair
rules. KiCad's `.kicad_dru` format is documented and parseable.

Includes round-trip test: given a KiCad project with rules already loaded,
verify the manifest can regenerate equivalent rules. Catches schema gaps
where the manifest can't express something KiCad can.

### 10. `altium-rule-emitter` *(deferred)*

**Dependencies:** `kicad-rule-emitter`

Same pattern as KiCad but emits Altium's `.RUL` export format. Not
blocking the experiment; on the roadmap for later.

---

## Phase 5: LLM integration

### 11. `llm-system-prompt`

**Dependencies:** all of phases 0-2

Structured system prompt template that loads the manifest, the standards
rule library, the BOM library, and the calculator tool definitions.
Establishes the model's role as authoring/review/translation, never numeric
generation. Includes refusal patterns for "what trace width" questions
that aren't backed by a tool call.

Has an `eval_plan` block — this is the first AI-backed spec, so it links
to harness scenarios.

### 12. `llm-authoring-assistant`

**Dependencies:** `llm-system-prompt`, `schema-validator`

Conversational interface: user describes a board in prose, model produces
draft manifest YAML, schema validator runs automatically, model reports
gaps for the user to resolve. The model never commits a manifest that
fails validation.

`eval_plan` includes scenarios for: hallucinated trace width refusal,
missing-citation rejection, multi-turn manifest refinement.

### 13. `llm-review-assistant`

**Dependencies:** `llm-system-prompt`, `conformance-checker`

Reads a netlist plus manifest, summarizes the design in plain language,
flags risks the gates don't catch but a senior engineer would notice
(asymmetric decoupling, missing TVS on USB, sketchy thermal relief
patterns). Judgment-flavored review, explicitly distinguished from
deterministic validation.

### 14. `llm-drc-explainer`

**Dependencies:** `llm-system-prompt`, `kicad-rule-emitter`

Reads KiCad DRC output, maps each violation back to the manifest gate
that should have prevented it, suggests whether the manifest needs
tightening or the layout needs fixing.

---

## Phase 6: Experiment harness

### 15. `reference-projects`

**Dependencies:** `manifest-schema`, `conformance-checker`, `kicad-rule-emitter`

Add reference manifests for two existing boards from the author's bench
(Unamiga or Tapuino Reloaded variant + a deliberately small new project).
Used as test fixtures for the whole pipeline. Calibration data for the
standards rule library.

### 16. `experiment-metrics`

**Dependencies:** `reference-projects`

Simple CSV log of: number of validation failures over time, DRC violations
per route attempt, manifest changes per project iteration. Drives the
article followup with real numbers.

---

## Suggested build order

1. `manifest-schema` (foundation, blocks everything)
2. `standards-rule-library` + `bom-library-format` (data, can run in parallel)
3. `schema-validator` (one afternoon, unblocks LLM authoring path)
4. `impedance-calculator` + `current-capacity-calculator` (parallel)
5. `kicad-netlist-parser` → `conformance-checker`
6. `kicad-rule-emitter`
7. `llm-*` specs (lighter than they look once the engine underneath works)
8. `reference-projects` + `experiment-metrics` in parallel from phase 4 onward

The whole MVP is a few weekends of focused work. The experiment can start
running as soon as phases 0-3 are in place.

---

## Notes

- Specs in phases 5-6 will have `eval_plan` blocks pointing to
  `.harness/scenarios/`. Earlier phases are pure software with `test_plan`
  only.
- Every spec has `dependencies: []` filled in explicitly so the build
  order is mechanically derivable. Don't merge a spec whose dependencies
  aren't approved yet.
- The `out_of_scope_for_this_spec` field in `test_plan` is doing real work
  here — it's how the schema spec stays small while pointing forward to
  what the conformance checker will do.

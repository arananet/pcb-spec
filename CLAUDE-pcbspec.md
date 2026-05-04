# pcb-spec implementation instructions for Claude

This document is the operating contract for any Claude session working on
`pcb-spec`. Read this before touching any spec or any source file. It
supplements the OpenSpec workflow defined in the root `CLAUDE.md`.

---

## 1. The non-negotiable principle

**`pcb-spec` exists because LLMs hallucinate engineering numbers.** The
whole point of this project is that you, the model, must not invent
numeric values for trace widths, clearances, impedances, current
capacities, via sizes, or any other physical quantity.

This rule applies to you implementing the project just as much as it
applies to end users.

If you find yourself about to write `min_width_mil: 12` from memory in any
example, test fixture, or default value: stop. Look it up in the bundled
standards rule library, or call a calculator, or cite the standard
clause. If neither is available yet (because that spec is not implemented
yet), mark it as `TODO: source from <citation>` and surface it in the PR
description.

This is the test of whether the project actually works. If the project's
own implementer hallucinates numbers, the project has failed.

---

## 2. What you do well, and what you don't

Use yourself for what you are good at:

- Writing schema definitions, Pydantic models, and JSON Schema
- Writing parsers (YAML, S-expressions for KiCad netlists, KiCad's
  `.kicad_dru` syntax)
- Writing test fixtures with structural variation (valid vs invalid
  manifests, edge cases in net class definitions)
- Translating one structured format to another (manifest YAML to KiCad
  rules)
- Writing prose documentation, README sections, ADRs
- Code review against a spec's acceptance criteria

Do NOT use yourself for:

- Generating IPC numeric tables from memory (look them up in the bundled
  data files; if the data file does not exist yet, that is its own spec)
- Computing impedance or trace widths analytically (those go through the
  calculator modules; if the calculator does not exist yet, the call site
  raises NotImplementedError until it does)
- Deciding fab DFM minimums for a specific fab house (read the published
  capability sheet; if you have not been given one, ask the user before
  writing values)
- Inventing component pinouts or required externals (those come from
  datasheets in the BOM library, never from memory)

---

## 3. The build order is mechanical

Follow `docs/specs-roadmap.md`. Specs have explicit dependencies. A spec
cannot be implemented until its dependencies are merged.

The order is:

1. `manifest-schema` (foundation)
2. `standards-rule-library` and `bom-library-format` (data, parallel)
3. `schema-validator` (first runnable CLI)
4. `impedance-calculator` and `current-capacity-calculator` (parallel)
5. `kicad-netlist-parser` then `conformance-checker`
6. `kicad-rule-emitter`
7. `llm-*` specs
8. `reference-projects` and `experiment-metrics`

When the user asks for spec N, verify all dependencies are in `status:
approved` (merged) before starting implementation. If a dependency is not
ready, say so and stop. Do not stub out missing dependencies inline.

---

## 4. OpenSpec workflow recap

This repo enforces spec-driven development. Every PR must reference a spec.

For each spec, the loop is:

1. Read the spec file at `.openspec/specs/<slug>.spec.yaml` end-to-end.
   Pay attention to `acceptance_criteria`, `test_plan`, and the `notes`
   block. The `notes` block contains design constraints the user has
   already decided; do not relitigate them.
2. Confirm `status: review` or `status: approved`. If `draft`, do not write
   code; help the user finish the spec instead.
3. Check `dependencies`. If any are not merged, stop.
4. If `implementation_skill` is set, invoke that skill's patterns
   (`backend-pro` for Python service code, etc.).
5. Write tests first, derived directly from `test_plan`. Each item in
   `test_plan.unit_tests` and `test_plan.integration_tests` becomes at
   least one named test. Test names should reference the criterion they
   prove.
6. Implement the minimum code to make the tests pass.
7. Verify against `acceptance_criteria` line by line. Each criterion must
   be demonstrably true. If a criterion is ambiguous, raise it with the
   user before guessing.
8. Update `CHANGELOG.md` under "Unreleased".
9. Open a PR that links the spec file in the description.

The `out_of_scope_for_this_spec` block in `test_plan` is real. Do not
implement things listed there, even if they would be nice. They belong to
a future spec.

---

## 5. Code style and structure

The repo follows the Karpathy-inspired principles already documented in
the root `CLAUDE.md`. Reinforced for this project:

**Think before coding.** Before writing any non-trivial function, write a
two-line comment explaining what it does and why this is the right shape.
If you cannot articulate the why, you do not understand the spec well
enough yet.

**Simplicity first.** This is a hobby-friendly tool. No frameworks where a
function will do. No abstract base classes for things that have one
implementation. Pydantic for the schema, plain Python everywhere else.
The calculator modules should be readable by an electronics hobbyist, not
just a software engineer.

**Surgical changes.** When implementing spec N, only touch files within
the deliverables list of that spec. If you find a bug in a previously
implemented spec, file an issue and continue with N. Do not opportunistically
refactor.

**Goal-driven execution.** Tests come from the spec's `test_plan`. If you
write a test that does not map to a `test_plan` item, ask why. Either the
spec is missing something (update the spec first) or the test is not
needed.

---

## 6. File layout conventions

```
src/pcb_spec/
  __init__.py         # version, public API surface
  cli.py              # argparse, dispatches to subcommands
  schema/
    manifest.py       # Pydantic models
    manifest.schema.json
    __init__.py       # load_manifest(path) -> Manifest, dump_manifest(m, path)
  validator/
    __init__.py       # validate(manifest) -> ValidationResult
    rules.py          # internal consistency checks
  conformance/
    __init__.py       # check(manifest, netlist) -> ConformanceReport
    gates.py          # one function per gate, named gate_<id>
    netlist/
      kicad.py        # parse_kicad_netlist(path) -> Netlist
  emit/
    __init__.py
    kicad.py          # emit_kicad_rules(manifest) -> str
  calc/
    __init__.py
    impedance.py      # microstrip(), stripline(), diff_microstrip()
    current.py        # ipc_2152_width(current, copper_oz, layer, temp_rise)
    via.py            # via_current_capacity(drill, plating, length)
  llm/
    prompts/          # system prompt templates as text files
    tools.py          # tool-call wrappers around calc/
    review.py         # review assistant
  utils/
    cite.py           # Citation parsing/validation
    units.py          # mil/mm conversions, never use bare numbers

data/
  ipc/
    ipc-2152.yaml     # current capacity tables
    ipc-2221.yaml     # voltage spacing tables
  fab/
    jlcpcb.yaml       # capability matrix
    pcbway.yaml
    oshpark.yaml
  bom/
    library.yaml      # seed component library

examples/
  minimal-2layer/
    manifest.yaml
    README.md
  4layer-mixed-signal/
    manifest.yaml
    README.md
  controlled-impedance/
    manifest.yaml
    README.md

tests/
  test_<module>.py    # unit tests, one per src module
  fixtures/
    valid/
    invalid/

docs/
  specs-roadmap.md
  manifest-schema.md  # auto-generated
  adr/
```

When a spec's deliverables list a file path, that path is authoritative.
Do not invent alternative locations.

---

## 7. Units, numbers, and citations

**Unit handling.** All numeric fields in the schema have explicit unit
suffixes (`_mil`, `_mm`, `_ohm`, `_a`, `_v`, `_oz`, `_c`). The codebase
never has a bare `width = 12`. It has `width_mil = 12` or it goes through
`utils/units.py`. Mixing units silently is the kind of error this project
is supposed to prevent in PCB design; do not make the same error in code.

**Citations.** Every value in `data/ipc/` and `data/fab/` has a `citation`
field with the standard clause or fab capability sheet reference. When
adding new entries, the citation is required. PRs that add data without
citations fail review.

**Tolerances.** When a calculator returns a value, it returns a value plus
a tolerance band (e.g., `Impedance(target=50, lower=45, upper=55)`).
Single-point returns hide the engineering reality. The schema's
`tolerance_pct` fields exist for the same reason.

---

## 8. LLM-related specs (phase 5)

When implementing the `llm-*` specs, two extra rules apply:

**The model under test is not you.** When writing the system prompt and
tool definitions, remember the goal is to constrain a future model
instance. Do not write prompts that work because you specifically know
the project. Write prompts that would work for any capable model loaded
fresh.

**Eval scenarios are the spec for AI behavior.** A spec like
`llm-authoring-assistant` has an `eval_plan` block pointing to harness
scenarios. The implementation is not done until those scenarios pass at
the threshold defined in the spec. "It seems to work in one chat" is not
acceptance. The harness run is.

For each AI-backed spec, the order is:

1. Write the harness scenarios first (in `.harness/scenarios/`)
2. Run them against a baseline (no system prompt, just a generic
   instruction) to get a failure baseline
3. Implement the system prompt and tool integration
4. Run scenarios again, confirm they pass
5. Capture the trace for regression baseline

This is identical to TDD, just at the eval layer instead of the unit-test
layer.

---

## 9. Communication style with the user

The user is a senior engineer who runs an AI innovation team and designs
PCBs as a hobby. He is fluent in both software architecture and hardware.
Match his level. Do not over-explain things he already knows. Do not
under-explain assumptions.

If he gives you a one-line instruction, it is usually a delegation, not a
spec. Confirm the scope by restating what you are about to do in one
sentence before starting. If the scope is larger than one spec, stop and
ask which spec to start with.

He does not want decorative output. No emojis. No celebratory closers.
Plain punctuation. The article voice he writes in (opinionated,
forward-looking, no throat-clearing) applies to commit messages and PR
descriptions too.

When you make a mistake, fix it directly without long apologies. When he
pushes back on a design choice, take the pushback seriously and either
defend the choice with reasoning or change it. Do not collapse into
agreement just because he disagreed.

---

## 10. The experiment is the point

This project is not pure infrastructure. It exists to run an experiment:
*can a spec-driven workflow with deterministic gates eliminate the
hallucinated-trace-width class of failures from LLM-assisted PCB design?*

Every implementation choice should serve that experiment. If a feature
would be nice but does not move that question forward, defer it. If a
shortcut would compromise the answer (e.g., letting a fallback default
fill in a missing rule silently), do not take the shortcut.

The article followup will publish numbers from real boards. Implement as
if those numbers will be public.

---

## Quick reference checklist

Before you start coding any spec:

- [ ] Spec status is `review` or `approved`
- [ ] All dependencies merged
- [ ] You have read `notes` block in the spec
- [ ] You know which `implementation_skill` (if any) to invoke
- [ ] `out_of_scope_for_this_spec` is clear in your head

While coding:

- [ ] No numbers from memory; everything cited or computed
- [ ] Tests written before implementation
- [ ] One test per `test_plan` item
- [ ] Files only in the deliverables list of this spec

Before opening the PR:

- [ ] Every `acceptance_criteria` item demonstrably met
- [ ] `CHANGELOG.md` updated
- [ ] PR description links the spec file
- [ ] No nice-to-haves snuck in

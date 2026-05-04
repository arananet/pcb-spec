# Claude Code implementation instructions for pcb-spec

This document tells Claude Code how to implement `pcb-spec` as a CLI tool
plus a Claude Skill, replacing any earlier MCP-based plans. It supplements
`CLAUDE.md` and the OpenSpec workflow already in the repo.

Read this end-to-end before touching any code.

---

## 1. Architectural decision: CLI + Skill, not MCP

`pcb-spec` is a deterministic auditor. It reads stable file formats from
KiCad, validates them against a manifest, and emits stable file formats
back to KiCad. It does not need to interact with a running KiCad instance.
It does not need a long-running server. It does not need a JSON-RPC
protocol layer.

The architecture is:

- **`pcb-spec` Python CLI** — pip-installable, exposes `validate`,
  `check schematic|layout|dfm`, and `emit kicad`. Reads YAML manifests
  and KiCad export files. Writes structured reports and `.kicad_dru`
  rules. Pure Python, no daemons, no servers.
- **`kicad-cli`** — first-party KiCad binary, used to generate the export
  files the auditor reads (netlists, Gerbers, drills, BOMs).
- **Claude Skill at `.claude/skills/pcb-spec/`** — teaches Claude how to
  orchestrate the two CLIs above, how to author manifests, how to read
  gate reports, and how to explain DRC failures.

All LLM interactions go through the Skill. The CLI is the deterministic
engine. There is no MCP server in this design.

This decision is informed by:

- KiCad 9.0+ uses file formats with explicit stability guarantees that
  outlast any API surface
- The SWIG bindings are deprecated and slated for removal in KiCad 11.0
- The IPC API is still stabilizing, with incomplete schematic-side
  coverage
- `kicad-cli` is first-party, stable, and covers every export the auditor
  needs
- Skills compose with the rest of Claude Code without extra setup

Do not introduce MCP for any part of `pcb-spec`. If a future feature seems
to need it (e.g., live feedback during routing), that feature is out of
scope for the auditor.

---

## 2. Repo layout

The earlier roadmap document specified Python package structure. Update it
to drop the `llm/` subpackage in favor of the Skill. Final layout:

```
src/pcb_spec/
  __init__.py
  cli.py
  engine.py
  schema/
    manifest.py
    manifest.schema.json
    __init__.py
  validator/
    __init__.py
    rules.py
  conformance/
    __init__.py
    gates.py
    netlist/
      kicad.py
  emit/
    __init__.py
    kicad.py
  calc/
    __init__.py
    impedance.py
    current.py
    via.py
  utils/
    cite.py
    units.py

data/
  ipc/
    ipc-2152.yaml
    ipc-2221.yaml
  fab/
    jlcpcb.yaml
    pcbway.yaml
    oshpark.yaml
  bom/
    library.yaml

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
  test_<module>.py
  fixtures/

.claude/
  skills/
    pcb-spec/
      SKILL.md
      manifest-authoring.md
      gate-failure-explainer.md
      kicad-export.md
      dru-translation.md
      examples/
      cheatsheets/

templates/
  board-repo/
    AGENTS.md
    .github/workflows/pcb-spec.yml
    docs/KICAD_EXPORT.md

docs/
  specs-roadmap.md
  manifest-schema.md
  report-schema.md
  adr/
```

---

## 3. The CLI surface

`pcb-spec` is invoked as:

```
pcb-spec validate <manifest>
pcb-spec check schematic <manifest> <netlist.net>
pcb-spec check layout    <manifest> <board.kicad_pcb>
pcb-spec check dfm       <manifest> <fab-dir>
pcb-spec emit kicad      <manifest> [-o rules.kicad_dru]
```

Every subcommand returns:

- Exit code 0 on success, non-zero on any gate failure
- Human-readable Markdown to stdout
- Structured JSON to a file specified with `--report <path>` if requested

The Markdown and JSON outputs share a stable schema. The Skill reads the
JSON form. CI consumes both. The schema is documented in
`docs/report-schema.md` and treated as a public API: non-additive changes
require a version bump.

Implementation principle: every subcommand is a thin entry point that
calls into `src/pcb_spec/<module>/__init__.py`. The CLI layer does not
contain logic. It parses arguments, calls the library, formats output.
This keeps the library independently testable and embeddable.

---

## 4. Skill structure

The skill at `.claude/skills/pcb-spec/SKILL.md` follows Anthropic's skill
conventions. Its job is to teach Claude how to operate the toolchain.

### SKILL.md (entry point)

The entry point is short. It describes:

- What the project is (one paragraph)
- The four-step typical workflow: author manifest, validate, generate
  KiCad exports, run gates
- When to load each supporting markdown file
- Hard rules: no numeric values from memory, every value cited, refuse
  questions whose answer is a number unless a calculator is wired up

### Supporting files

Each supporting file is a focused playbook for one concern:

- `manifest-authoring.md` — how to draft a manifest from prose intent
  plus a stack of datasheets. Includes the schema reference, citation
  requirements, common mistakes, and the validation loop. Loaded when
  the user asks Claude to create or modify a manifest.

- `gate-failure-explainer.md` — how to read the JSON report from
  `pcb-spec check`, identify which gate fired, distinguish manifest
  errors from design errors, and propose fixes the human can apply in
  KiCad. Loaded when CI fails or the user pastes a report.

- `kicad-export.md` — the exact `kicad-cli` commands to run for each
  artifact, with troubleshooting for common errors. Loaded when Claude
  needs to regenerate exports.

- `dru-translation.md` — how to read a manifest and emit `.kicad_dru`
  syntax. Reference for the `pcb-spec emit kicad` implementation but
  also for explaining what rules KiCad will enforce. Loaded when the
  user asks about layout-time enforcement.

### Cheatsheets

Standards data the model is allowed to reference (because it is data,
not memory):

- `cheatsheets/ipc-2152-quick-ref.md` — current capacity tables, with
  citations
- `cheatsheets/jlcpcb-dfm.md` — JLCPCB capability sheet excerpts

These are flat data files, not prose. The model looks values up; it does
not paraphrase or interpret them.

### What the skill does NOT do

The skill does not contain code. It does not implement gates. It does
not parse files. All of that lives in the Python package. The skill
teaches Claude how to use the package.

The skill also does not duplicate the spec roadmap. The roadmap is for
humans planning what to build next. The skill is for Claude operating
the finished tooling.

---

## 5. Build order

The order is now:

1. `manifest-schema` (implemented)
2. `rule-engine-contract` (spec drafted)
3. `standards-rule-library`
4. `bom-library-format`
5. `schema-validator`
6. `impedance-calculator` and `current-capacity-calculator` (parallel)
7. `kicad-netlist-parser` then `conformance-checker`
8. `kicad-rule-emitter`
9. `pcb-spec-skill` — single spec replacing the four earlier `llm-*`
   specs. Covers the skill folder, supporting docs, and cheatsheets. Has
   an `eval_plan` block pointing to harness scenarios.
10. `reference-projects` and `experiment-metrics` (parallel)

The previous specs `llm-system-prompt`, `llm-authoring-assistant`,
`llm-review-assistant`, and `llm-drc-explainer` are retired. The skill
folder structure handles the separation of concerns at the file level.

---

## 6. Behavioral rules during implementation

These reinforce the existing `CLAUDE-pcbspec.md` rules.

**No numbers from memory, ever.** When writing tests, examples,
cheatsheets, or anything else: every numeric value cites its source
inline. If you do not have a citation for a value, write
`# TODO: source from <citation>` and surface it in the PR description.

**The skill teaches; it does not contain logic.** When implementing the
skill spec, resist the urge to embed Python code, decision trees, or
heuristics in the markdown. The skill is instructions for Claude on how
to use the CLI. The CLI does the work.

**One spec at a time.** Verify that all dependencies of the current spec
are merged before starting. Do not stub missing dependencies. Do not
implement nice-to-haves listed in `out_of_scope_for_this_spec`.

**Output schema stability.** The JSON report format from `pcb-spec
check` is consumed by CI and by the skill. Treat it as a public API.
Document it in `docs/report-schema.md`. Do not change it in a non-additive
way without bumping a schema version.

**The CLI is testable as a black box.** Tests should invoke the CLI as
a subprocess against fixtures, not just import library functions.
End-to-end CLI tests are the contract that protects the skill from
implementation drift.

**No MCP anywhere.** If you find yourself reaching for MCP to solve a
problem, stop. The answer is either a CLI flag, a report format addition,
or a skill instruction. If it seems impossible without MCP, raise it
before implementing anything.

---

## 7. CI implications

The GitHub Actions workflow at `templates/board-repo/.github/workflows/pcb-spec.yml`
uses `kicad-cli` and the `pcb-spec` CLI directly. It does not need to
change for this architecture; it was always CLI-first. Confirm during
implementation that no MCP-related steps have crept in.

The workflow is the canonical reference for "how does this run end to end
without a human." The skill should never instruct Claude to do anything
the CI cannot do headlessly.

---

## 8. Quick reference for new sessions

Before starting any work:

- [ ] Confirm the architecture is CLI + Skill (no MCP)
- [ ] Identify the spec slug for the work
- [ ] Verify all dependencies are in `status: approved`
- [ ] Read the spec's `notes` block

While implementing:

- [ ] Every numeric value cited or computed
- [ ] No nice-to-haves outside `acceptance_criteria`
- [ ] CLI tests run as subprocesses against fixtures
- [ ] Skill files contain no executable logic

Before opening the PR:

- [ ] All `acceptance_criteria` demonstrably met
- [ ] CHANGELOG.md updated
- [ ] README.md updated
- [ ] PR description links the spec
- [ ] No MCP code anywhere

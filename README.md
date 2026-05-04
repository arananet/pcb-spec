# pcb-spec

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec-driven](https://img.shields.io/badge/spec--driven-OpenSpec-blue)](#what-is-openspec)
[![Status: experimental](https://img.shields.io/badge/status-experimental-orange)]()
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![OpenSpec](https://img.shields.io/badge/OpenSpec-enforced-blueviolet)

Spec-driven PCB design. The constraint manifest is the source of truth. Schematic and board are derivative artifacts that must conform.

`pcb-spec` is an experiment in applying spec-driven development to PCB design. A YAML manifest captures stackup, rule tables, net classes, placement intent, and conformance gates. A schema validator and conformance checker enforce the spec deterministically. A rule translator emits native EDA syntax (KiCad first). LLMs can author and review the manifest, but every numeric value comes from a tool call or a cited standard, never from a model's prior. The goal is reproducible, auditable PCB design where AI assistance is constrained to what it actually does well: text-to-text translation, classification, and review.

## Why this exists

Ask a general-purpose LLM for a 2A trace width on 1oz copper and you might get 12 mil, 30 mil, or a confident paragraph that violates IPC-2152 by a factor of two. The model is generating plausible text. Plausible text is not an engineering deliverable.

Retrieval augmented generation does not fix this. RAG retrieves similar content. PCB design needs exact rule satisfaction. Those are different problems.

The fix is structural, not a better prompt:

1. A structured manifest the model can read but cannot author from memory
2. Tool calls (impedance, current capacity, via thermal models) for anything computed
3. A conformance gate that compares artifacts to the manifest and does not negotiate

The model becomes the authoring and review interface. The trust comes from the engine underneath.

## The schematic-vs-board split

A PCB project is two artifacts pretending to be one.

**Schematic** is a logical and topological problem. Wrong pin assignment, missing decoupling, wrong feedback divider. Failures are about correctness of intent.

**Board** is a geometric and physical problem. Trace too narrow for current, impedance miss, return path discontinuity, via stub resonance. Failures are about geometry and physics.

`pcb-spec` treats them as separate phases with separate gates, joined by the manifest as a contract.

## What's in the box

| Component | Role | Status |
| --- | --- | --- |
| **Manifest schema** | Canonical YAML schema (stackup, rules, net classes, placement, gates) | implemented |
| **Rule engine contract** | Rule/Violation/FactBase types, four-source resolution order, evaluation model | spec drafted |
| **Standards rule library** | IPC-2152, IPC-2221, common fab DFM minimums as bundled data | planned |
| **Schema validator** | `pcb-spec validate` — schema + internal consistency checks | planned |
| **Conformance checker** | Walks netlist + manifest, runs schematic-phase gates | planned |
| **EDA rule translator** | Emits native syntax (KiCad `.kicad_dru` first) | planned |
| **Calculator tools** | Wadell impedance, IPC-2152 current capacity, via thermal | planned |
| **Claude Skill** | `.claude/skills/pcb-spec/` — teaches Claude to operate the toolchain; replaces llm-* specs | planned |
| **Reference projects** | Real boards from the author's bench, used as test fixtures | planned |

## Using pcb-spec in a board repo

`pcb-spec` is a CI auditor for KiCad projects. Copy the files in
[`templates/board-repo/`](templates/board-repo/) into your hardware repo
to wire up the three-gate pipeline:

```
your-board-repo/
  AGENTS.md                          # agent contract for this repo
  manifest.yaml                      # your board's constraint manifest
  .github/workflows/pcb-spec.yml     # CI pipeline
  docs/KICAD_EXPORT.md               # manual export procedure
```

The pipeline runs on every PR: validates the manifest, exports KiCad
artifacts via `kicad-cli`, then runs three gates in sequence —
schematic, layout, DFM. Gate failures block the merge. The gate report
posts as a sticky PR comment. On a version tag, the Gerber bundle attaches
to the GitHub release.

See [`templates/board-repo/`](templates/board-repo/) for the full files
with inline documentation.

## Getting started (developing pcb-spec itself)

```bash
git clone https://github.com/arananet/pcb-spec.git
cd pcb-spec
pip install -e ".[dev]"
bash setup.sh          # install OpenSpec git hooks

# validate one of the example manifests
python3 -m pcb_spec.schema examples/minimal-2layer/manifest.yaml

# run the test suite
python3 -m pytest
```

## What is OpenSpec?

This repo uses OpenSpec for spec-driven development. Every feature starts with a spec file in `.openspec/specs/`. No spec, no code. Specs define acceptance criteria, test plans, and the implementation skill to use.

See `.openspec/specs/` for active specs. The roadmap of planned specs lives in [`docs/specs-roadmap.md`](docs/specs-roadmap.md).

## Project structure

```
.openspec/specs/        # Active spec files (one per feature)
src/pcb_spec/           # Python package
  engine.py             # Rule engine contract: types, resolution, evaluation loop
  schema/               # Manifest schema (JSON Schema + Pydantic)
  validator/            # Schema validator CLI
  conformance/          # Netlist parser + gate runner
  emit/                 # EDA rule translators (kicad/ first)
  calc/                 # Impedance, current capacity, via thermal calculators
data/                   # Bundled rule libraries (IPC, fab DFM)
examples/               # Reference manifests (minimal-2layer, 4layer-mixed-signal,
                        #   controlled-impedance)
.claude/
  skills/
    pcb-spec/           # Claude Skill: teaches Claude to operate the toolchain
      SKILL.md          # Entry point
      manifest-authoring.md
      gate-failure-explainer.md
      kicad-export.md
      dru-translation.md
      cheatsheets/      # IPC-2152 and fab DFM lookup tables with citations
templates/
  board-repo/           # Drop-in files for a KiCad board repo using pcb-spec
    AGENTS.md           # Agent contract for the board repo
    .github/workflows/
      pcb-spec.yml      # Three-gate CI pipeline
    docs/
      KICAD_EXPORT.md   # Manual and headless export procedure
docs/
  adr/                  # Architecture decisions
  specs-roadmap.md      # Full spec dependency graph and build order
  manifest-schema.md    # Auto-generated schema reference
  report-schema.md      # CLI JSON output schema (public API)
```

## Status

Experimental. `manifest-schema` is implemented and tested. `rule-engine-contract` and `pcb-spec-skill` are drafted. Everything else is planned — see [`docs/specs-roadmap.md`](docs/specs-roadmap.md) for the build order and dependencies. Architecture: CLI + Claude Skill, no MCP.

## Coding guidelines

Karpathy-inspired principles enforced through OpenSpec: think before coding, simplicity first, surgical changes, goal-driven execution. See `CLAUDE.md` and `CLAUDE-pcbspec.md`.

## License

MIT. See [LICENSE](LICENSE).

---

**Developer:** Eduardo Arana

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/H2H51MPWG)

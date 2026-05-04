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

| Component | Role |
| --- | --- |
| **Manifest schema** | Canonical YAML schema (stackup, rules, net classes, placement, gates) |
| **Standards rule library** | IPC-2152, IPC-2221, common fab DFM minimums as bundled data |
| **Schema validator** | `pcb-spec validate` — schema + internal consistency checks |
| **Conformance checker** | Walks netlist + manifest, runs schematic-phase gates |
| **EDA rule translator** | Emits native syntax (KiCad `.kicad_dru` first) |
| **Calculator tools** | Wadell impedance, IPC-2152 current capacity, via thermal — wired up as LLM tools |
| **LLM integration** | Authoring assistant, review assistant, DRC explainer |
| **Reference projects** | Real boards from the author's bench, used as test fixtures |

## What is OpenSpec?

This repo uses OpenSpec for spec-driven development. Every feature starts with a spec file in `.openspec/specs/`. No spec, no code. Specs define acceptance criteria, test plans, and the implementation skill to use.

See `.openspec/specs/` for active specs. The roadmap of planned specs lives in [`docs/specs-roadmap.md`](docs/specs-roadmap.md).

## Project structure

```
.openspec/specs/        # Active spec files (one per feature)
src/pcb_spec/           # Python package
  schema/               # Manifest schema definition
  validator/            # Schema validator
  conformance/          # Netlist parser + gate runner
  emit/                 # EDA rule translators (kicad/, altium/, allegro/)
  calc/                 # Impedance, current capacity, via thermal calculators
  llm/                  # Authoring/review/explain assistants
data/                   # Bundled rule libraries (IPC, fab DFM)
examples/               # Reference projects with manifests
docs/
  adr/                  # Architecture decisions
  specs-roadmap.md      # Planned specs and dependencies
```

## Status

Experimental. The schema is at v0.1. The first reference project is in progress. Article and experiment writeup pending real fab results.

## Coding guidelines

Karpathy-inspired principles enforced through OpenSpec: think before coding, simplicity first, surgical changes, goal-driven execution. See `CLAUDE.md`.

## License

MIT. See [LICENSE](LICENSE).

---

**Developer:** Eduardo Arana

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/H2H51MPWG)

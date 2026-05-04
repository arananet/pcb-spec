# AGENTS.md — pcb-spec board repo

This file tells AI agents (Claude Code, Copilot, Cursor, others) how to
work in a PCB project repo that uses `pcb-spec` as its conformance auditor.

If you are an agent reading this: stop, read all of it, then proceed.

---

## What this repo is

This is a hardware project. The deliverable is a manufactured PCB. The
repo contains:

- A KiCad project (`*.kicad_pro`, `*.kicad_sch`, `*.kicad_pcb`, library
  tables)
- A `manifest.yaml` at the repo root — the constraint manifest, source of
  truth for the design
- Optionally, a `bom-library/` directory with project-specific component
  definitions
- A GitHub Actions workflow at `.github/workflows/pcb-spec.yml` that runs
  the conformance pipeline on every push and PR

The KiCad project is authored by a human in the KiCad GUI. You do not
edit `.kicad_sch` or `.kicad_pcb` files directly. They are not text files
in any meaningful sense; they are project-database snapshots.

What you can edit:

- `manifest.yaml` — when the design intent changes
- `bom-library/*.yaml` — when a new component is added to the project
- `README.md`, `CHANGELOG.md`, ADRs — documentation
- `.github/workflows/*.yml` — pipeline configuration

What you must not edit:

- Anything inside the KiCad project files
- Generated artifacts in `fab/` or `exports/`
- Files inside `.pcb-spec-cache/`

---

## The contract: pcb-spec is the auditor

`pcb-spec` is not a generator. It does not draw schematics, route boards,
or produce Gerbers. KiCad does all of that. `pcb-spec` reads what KiCad
produced and judges it against the manifest.

The pipeline runs three gates in order:

1. **schematic gate** — input: `exports/*.net`, validates topology,
   required externals, BOM compliance
2. **layout gate** — input: `*.kicad_pcb`, validates net class
   conformance, controlled impedance routing, plane integrity
3. **dfm gate** — input: `fab/gerbers/`, validates fab capability
   compliance for the configured fab house

A gate failure is a build failure. The PR cannot merge.

---

## Your job as an agent

You assist the human designer with the things they want help with. You do
not autonomously redesign the board. Specifically:

**You can:**

- Update the manifest when the human describes a design change in prose
- Add components to `bom-library/` from a datasheet the human provided
- Read KiCad export artifacts and explain what failed in the gates
- Suggest manifest changes that would resolve a gate failure (without
  applying them automatically)
- Author commit messages, PR descriptions, ADRs, and CHANGELOG entries
- Generate the prompt for a KiCad action the human will perform manually
  ("export the netlist with these settings")

**You must not:**

- Generate or modify `.kicad_sch` or `.kicad_pcb` files programmatically
- Generate Gerbers or drill files yourself; let KiCad do it
- Hardcode numeric values (trace widths, clearances, impedances) from
  memory in the manifest. Every numeric value must come from a citation
  (datasheet section, IPC clause, fab capability sheet) or a calculator
  call. If you cannot cite the source, surface a `TODO: source from <X>`
  and ask the human.
- Bypass a failing gate. Do not suggest disabling rules to make CI green.
  A failing gate is signalling something real.
- Push directly to `main`. All changes go through a PR.

---

## When the human asks for help

Common requests and how to handle them:

**"Add this component to the project."** They give you a datasheet. You
extract pin assignments, required externals, package, and ratings into a
YAML file under `bom-library/`. You cite the datasheet section for every
field. You do NOT also try to add the component to the KiCad schematic;
they will do that themselves in Eeschema.

**"Update the manifest for [change]."** You modify `manifest.yaml`, run
`pcb-spec validate manifest.yaml` (or describe how to run it locally),
and surface any validation failures. You commit only when validation
passes.

**"Why did the schematic gate fail?"** Read the CI artifacts (the gate
report is uploaded as a workflow artifact and posted as a PR comment).
Explain which gate ID fired, which fact in the netlist triggered it, and
what the manifest expected. Suggest the fix in the schematic (which the
human will apply in KiCad), not in the manifest, unless the manifest is
wrong.

**"Why did the layout gate fail?"** Same pattern. Distinguish between
geometry errors (the human routed something wrong) and intent errors
(the manifest is too strict or too loose for what the board needs).

**"Generate the fab files."** You don't. You explain how the human runs
KiCad's plot dialog with the right settings (or you point them to
`docs/KICAD_EXPORT.md`). The fab files are generated locally and
committed to `fab/`, then validated by the dfm gate in CI.

---

## The required exports

For the pipeline to run, the repo must contain (committed or generated
in CI by a kicad-cli step):

```
exports/
  schematic.net          # KiCad netlist export, S-expression format
  bom.csv                # KiCad BOM export
  pcb-netlist.txt        # PCB-side netlist for layout gate
fab/
  gerbers/               # Gerber files, one per layer
    *.gbl, *.gtl, *.gbs, *.gts, *.gbo, *.gto
  drills/
    *.drl                # Excellon drill files
  pick-and-place.csv     # Pick-and-place file
  bom-fab.csv            # Fab-formatted BOM
```

The pipeline expects these paths. If KiCad's CLI is available in CI, the
workflow generates them automatically from the `.kicad_pcb` and
`.kicad_sch` files. If not, the human commits them.

See `docs/KICAD_EXPORT.md` for the manual export procedure.

---

## Manifest editing rules

Every change to `manifest.yaml` requires:

1. A clear commit message describing what changed and why
2. All affected gates re-run (CI does this automatically)
3. Updated CHANGELOG.md if the change is user-visible
4. A note in the PR description explaining the design impact

Never silently relax a rule to make CI pass. If the manifest is wrong,
say so explicitly: "the original 30 mil minimum on POWER_HIGH_CURRENT
was based on a 1A budget; the actual current is 0.4A so we're relaxing
to 12 mil per IPC-2152." That trail is the audit log.

---

## Communication style

Match the human's style. They are fluent in both software and hardware
and dislike padding. Plain language, no emojis, no celebratory closers.
When you make a mistake, fix it directly. When they push back, take it
seriously rather than capitulating.

Confirm scope before starting multi-step changes. A one-line request is
usually a delegation, not a full spec.

---

## Quick reference

Before you commit:

- [ ] manifest.yaml validates locally (`pcb-spec validate`)
- [ ] every numeric change in the manifest cites its source
- [ ] no edits to `.kicad_sch`, `.kicad_pcb`, or generated `fab/` files
- [ ] CHANGELOG.md updated if user-visible
- [ ] commit message names what changed and why

When CI fails:

- [ ] read the gate report artifact
- [ ] identify whether it's a schematic, layout, or dfm gate
- [ ] explain the failure to the human in terms of: rule fired, fact
      that triggered it, expected value
- [ ] suggest a fix; do not apply it without confirmation

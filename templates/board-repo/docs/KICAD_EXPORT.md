# KiCad export procedure

The `pcb-spec` pipeline reads files exported from KiCad. If your CI
environment has `kicad-cli` available (KiCad 8.0+), the workflow does
this automatically and you can ignore this document. If you generate
exports manually — or you want to run gates locally before pushing —
follow this procedure.

The pipeline expects this layout at the repo root:

```
exports/
  schematic.net          # for schematic gate
  bom.csv                # cross-reference for BOM library
fab/
  gerbers/               # for dfm gate
  drills/
  pick-and-place.csv
```

---

## 1. Schematic netlist

In Eeschema:

- **Tools → Generate Netlist File**
- Format: **KiCad** (S-expression)
- Output path: `exports/schematic.net`
- Click **Generate Netlist**

This is the input to the schematic gate. The S-expression format is the
one `pcb-spec` parses; the older Pcbnew format is not supported.

---

## 2. BOM export

In Eeschema:

- **Tools → Generate BOM**
- Use the default plugin (`bom_csv_grouped_by_value`) or any CSV plugin
- Output path: `exports/bom.csv`

The BOM is used to cross-reference against `bom-library/` and confirm
every component is sourced from the approved list.

---

## 3. Gerbers

In Pcbnew:

- **File → Plot**
- Output directory: `fab/gerbers/`
- Plot format: **Gerber**
- Layers to plot:
  - F.Cu, B.Cu (and inner layers if present)
  - F.Mask, B.Mask
  - F.SilkS, B.SilkS
  - F.Paste, B.Paste (only if assembly is required)
  - Edge.Cuts
- Options to enable:
  - **Plot footprint values**: off
  - **Plot footprint references**: on
  - **Use Protel filename extensions**: optional, but consistent with most
    fab houses
  - **Subtract soldermask from silkscreen**: on
- Click **Plot**

---

## 4. Drill files

In Pcbnew, still in the Plot dialog:

- Click **Generate Drill Files**
- Output directory: `fab/drills/`
- Drill file format: **Excellon**
- Map file format: **Gerber X2** (or PDF if your fab needs it)
- Drill origin: **Absolute**
- Units: **Millimeters**
- Zeros format: **Decimal format**

Click **Generate Drill File**.

---

## 5. Pick-and-place file

In Pcbnew:

- **File → Fabrication Outputs → Component Placement (.pos) File**
- Format: **CSV**
- Units: **Millimeters**
- Files: **Single file for all layers** (or split if your assembler
  requires it)
- Output: `fab/pick-and-place.csv`

---

## 6. Local validation

Before pushing, run the gates locally:

```bash
pcb-spec validate manifest.yaml
pcb-spec check schematic manifest.yaml exports/schematic.net
pcb-spec check layout    manifest.yaml *.kicad_pcb
pcb-spec check dfm       manifest.yaml fab/
```

If any gate fails, fix it before opening the PR. CI will run the same
checks.

---

## Headless export with kicad-cli

If you have KiCad 8.0+ installed, skip the GUI procedure and run:

```bash
# Schematic exports
kicad-cli sch export netlist --format kicadsexpr -o exports/schematic.net *.kicad_sch
kicad-cli sch export bom -o exports/bom.csv *.kicad_sch

# Layout exports
kicad-cli pcb export gerbers -o fab/gerbers/ *.kicad_pcb
kicad-cli pcb export drill   -o fab/drills/  *.kicad_pcb
kicad-cli pcb export pos --format csv -o fab/pick-and-place.csv *.kicad_pcb
```

This is what the GitHub Actions workflow runs. Keeping the same commands
locally and in CI prevents export-format drift.

### KiCad 7.0 differences

The `kicad-cli` flag names changed between 7.0 and 8.0. On 7.0:

- `sch export netlist` → same, but `--format` accepts `kicad` (no `sexpr` suffix)
- `pcb export gerbers` → `pcb export gerber` (singular)
- `pcb export pos` → `pcb export footprint-positions`

Run `kicad-cli <subcommand> --help` to confirm flag names for your
installed version before running headless exports.

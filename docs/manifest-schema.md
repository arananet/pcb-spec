# PCB-Spec Manifest

Constraint manifest for a PCB project. The single source of truth for stackup, rules, net classes, placement intent, and conformance gates.

> Auto-generated from `src/pcb_spec/schema/manifest.schema.json`. Do not edit by hand.

---

## `manifest_version` *(required)*

Schema version. Only '0.1' is supported in this release.

**Allowed values:** `0.1`

---

## `project` *(required)*

Project identity: name and revision string.

**Type:** `object`

**Fields:**

- `name` — Short project name, URL-safe.
- `revision` — Revision identifier, e.g. 'r1' or 'v2.1'.

---

## `stackup` *(required)*

Physical layer stackup. Dielectric parameters are referenced by fab stackup ID, not inlined.

**Type:** `object`

**Fields:**

- `fab_house_id` — Opaque fab house identifier, e.g. 'jlcpcb'. The validator does not check this against a known-fab library; that belongs to a separate spec.
- `stackup_id` — Fab-specific stackup ID that encodes dielectric, prepreg, and core thicknesses. References the fab's capability sheet.
- `layers` — Ordered list of copper layers. No duplicate layer numbers allowed.

---

## `rules` *(required)*

Rule tables for current capacity, spacing, fab DFM, and impedance. Each subsection requires a citation. Numeric values are populated by the standards-rule-library spec.

**Type:** `object`

**Fields:**

- `current_capacity` — Current-carrying capacity rules. Values sourced from IPC-2152.
- `spacing` — Clearance and creepage spacing rules. Values sourced from IPC-2221.
- `fab_dfm` — Fab-specific DFM minimums: trace width, annular ring, drill size, etc.
- `impedance` — Impedance constraint rules and named profiles for controlled-impedance nets.

---

## `net_classes` *(required)*

Named groups of nets sharing routing constraints. Keys use UPPER_SNAKE_CASE.

**Type:** `object`

---

## `placement` *(optional)*

Component placement intents. Optional. Each entry records where or how a component should be placed relative to nets or other components.

**Type:** `array`

---

## `gates` *(required)*

Conformance gates grouped by phase. Each gate has a stable ID used in violation reports.

**Type:** `object`

**Fields:**

- `schematic` — Schematic-phase gates: logical correctness, pin assignment, decoupling.
- `layout` — Layout-phase gates: trace geometry, impedance, return paths.
- `dfm` — DFM-phase gates: fab capability minimums, courtyard clearances.

---

# controlled-impedance

Manifest exercising impedance profiles. Used as a test fixture for the
cross-reference check between `net_classes.*.rules.impedance_profile` and
`rules.impedance.profiles`.

Two impedance profiles are defined:

| ID | Target | Source |
|---|---|---|
| `USB_90_DIFF` | 90-ohm differential | USB 2.0 Specification §7.1.1 |
| `SE_50_OHM` | 50-ohm single-ended | IPC-2141A, general RF convention |

Three net classes: DEFAULT (no profile), USB_DIFF (references USB_90_DIFF),
RF_50 (references SE_50_OHM).

**Known TODOs** (blocked on later specs):

- `min_width_mil` for USB_DIFF and RF_50 are set to the DFM floor (6 mil).
  The geometrically correct widths for the target impedances on the
  JLC04161H-3313 stackup must be computed by the `impedance-calculator`
  spec once it is merged.

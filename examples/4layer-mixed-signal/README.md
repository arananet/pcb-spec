# 4layer-mixed-signal

Realistic 4-layer hobby board manifest. Inner layers are dedicated GND and
PWR planes. Three net classes: DEFAULT, POWER, HIGH_SPEED.

This example exercises:

- Four-layer stackup with inner plane layers (JLCPCB JLC04161H-3313)
- Placement constraints referencing defined net classes
- Schematic, layout, and DFM gates with stable IDs

**Known TODOs** (blocked on later specs):

- `POWER.rules.min_width_mil` is set to the DFM floor (6 mil). The
  current-capacity-derived minimum per IPC-2152 must be computed once the
  `current-capacity-calculator` spec is merged.
- `HIGH_SPEED.rules.impedance_profile` is absent. The target trace width
  for 50-ohm single-ended SPI must be computed once the
  `impedance-calculator` spec is merged and an impedance profile is added
  to `rules.impedance.profiles`.

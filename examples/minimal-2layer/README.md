# minimal-2layer

Smallest possible valid pcb-spec manifest. Used as a test fixture.

Two copper layers. Single DEFAULT net class. No placement constraints.
No conformance gates. All rule entries empty — populated by the
`standards-rule-library` spec once that data is bundled.

The `min_width_mil: 6` value is JLCPCB's published DFM minimum trace
width (Standard PCB Capability sheet), not a current-capacity-derived
value. It is the absolute floor; actual trace widths for current-carrying
nets must be computed via the `current-capacity-calculator` spec.

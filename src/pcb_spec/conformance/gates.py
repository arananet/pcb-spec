"""Schematic-phase gate predicates for the conformance checker.

Each predicate takes a loaded Manifest and Netlist and returns a list of
Violations using the rule engine contract types.
"""
from __future__ import annotations

from pcb_spec.conformance.netlist_parser import Netlist
from pcb_spec.engine import RuleSource, Severity, Violation
from pcb_spec.schema.manifest import Manifest

__all__ = ["run_schematic_gates"]

_CITATION = "pcb-spec conformance-checker v0.1"


def _net_class_member_checks(manifest: Manifest, netlist: Netlist) -> list[Violation]:
    """Every net_class member must exist as a net in the netlist."""
    net_names = netlist.net_names()
    violations: list[Violation] = []
    for nc_name, nc in manifest.net_classes.items():
        for member in nc.members:
            if member not in net_names:
                violations.append(Violation(
                    rule_id="NET_CLASS_MEMBER_NOT_IN_NETLIST",
                    gate_id="SCH-NET-CLASS",
                    severity=Severity.ERROR,
                    message=(
                        f"Net '{member}' is assigned to net class '{nc_name}' "
                        f"in the manifest but does not exist in the netlist."
                    ),
                    net_name=member,
                    component_id=None,
                    expected=f"net '{member}' present in netlist",
                    actual="net not found",
                    citation=_CITATION,
                    remediation=(
                        f"Add net '{member}' to the schematic or remove it "
                        f"from net_classes.{nc_name}.members in the manifest."
                    ),
                ))
    return violations


def _placement_component_checks(manifest: Manifest, netlist: Netlist) -> list[Violation]:
    """Every placement component_id must exist as a component ref in the netlist."""
    comp_refs = netlist.component_refs()
    violations: list[Violation] = []
    for constraint in manifest.placement:
        if constraint.component_id not in comp_refs:
            violations.append(Violation(
                rule_id="PLACEMENT_COMPONENT_NOT_IN_NETLIST",
                gate_id="SCH-PLACEMENT",
                severity=Severity.ERROR,
                message=(
                    f"Component '{constraint.component_id}' is listed in "
                    f"manifest.placement but does not exist in the netlist."
                ),
                net_name=None,
                component_id=constraint.component_id,
                expected=f"component '{constraint.component_id}' present in netlist",
                actual="component not found",
                citation=_CITATION,
                remediation=(
                    f"Add component '{constraint.component_id}' to the schematic "
                    f"or remove it from manifest.placement."
                ),
            ))
    return violations


def run_schematic_gates(manifest: Manifest, netlist: Netlist) -> list[Violation]:
    """Run all v0.1 schematic-phase gate predicates. Returns sorted Violations."""
    violations: list[Violation] = []
    violations.extend(_net_class_member_checks(manifest, netlist))
    violations.extend(_placement_component_checks(manifest, netlist))
    violations.sort(key=lambda v: (v.severity, v.rule_id, v.net_name or "", v.component_id or ""))
    return violations

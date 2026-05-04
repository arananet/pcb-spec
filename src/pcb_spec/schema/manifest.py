"""
Pydantic models for the pcb-spec constraint manifest.

Five top-level sections: stackup, rules, net_classes, placement, gates.
Cross-references (impedance profile IDs, net class names) are validated
in model_validators that run after field-level parsing.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

SUPPORTED_VERSIONS = ["0.1"]


class Layer(BaseModel):
    number: int
    name: str
    type: Literal["signal", "plane", "mixed"]
    copper_oz: float


class Stackup(BaseModel):
    fab_house_id: str
    stackup_id: str
    layers: list[Layer]

    @model_validator(mode="after")
    def _no_duplicate_layer_numbers(self) -> Stackup:
        nums = [layer.number for layer in self.layers]
        if len(nums) != len(set(nums)):
            raise ValueError("layers list contains duplicate layer numbers")
        return self


class RuleSection(BaseModel):
    """One subsection of rules (current_capacity, spacing, fab_dfm).

    entries shape is deliberately open; the standards-rule-library spec
    will constrain it when that data exists.
    """

    citation: str
    entries: list[dict] = []

    @field_validator("citation")
    @classmethod
    def _citation_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("citation must be non-empty")
        return v


class ImpedanceProfile(BaseModel):
    id: str
    target_ohm: float
    tolerance_pct: float


class ImpedanceRules(BaseModel):
    citation: str
    profiles: list[ImpedanceProfile] = []

    @field_validator("citation")
    @classmethod
    def _citation_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("citation must be non-empty")
        return v


class Rules(BaseModel):
    current_capacity: RuleSection
    spacing: RuleSection
    fab_dfm: RuleSection
    impedance: ImpedanceRules


class NetClassRules(BaseModel):
    min_width_mil: float
    route_layers: list[str]
    impedance_profile: Optional[str] = None


class NetClass(BaseModel):
    description: str
    members: list[str]
    rules: NetClassRules


class PlacementConstraint(BaseModel):
    component_id: str
    net_class: Optional[str] = None
    notes: Optional[str] = None


class Gate(BaseModel):
    id: str
    rule: str


class GatePhases(BaseModel):
    schematic: list[Gate] = []
    layout: list[Gate] = []
    dfm: list[Gate] = []


class Project(BaseModel):
    name: str
    revision: str


class Manifest(BaseModel):
    manifest_version: str
    project: Project
    stackup: Stackup
    rules: Rules
    net_classes: dict[str, NetClass]
    placement: list[PlacementConstraint] = []
    gates: GatePhases

    @field_validator("manifest_version")
    @classmethod
    def _version_supported(cls, v: str) -> str:
        if v not in SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported manifest_version {v!r}; supported: {SUPPORTED_VERSIONS}"
            )
        return v

    @model_validator(mode="after")
    def _validate_cross_references(self) -> Manifest:
        defined_net_classes = set(self.net_classes.keys())

        # placement.net_class must resolve to a defined net class
        for constraint in self.placement:
            if constraint.net_class and constraint.net_class not in defined_net_classes:
                raise ValueError(
                    f"Placement references undefined net class {constraint.net_class!r}"
                )

        # net_classes.*.rules.impedance_profile must resolve to a defined profile
        defined_profiles = {p.id for p in self.rules.impedance.profiles}
        for nc_name, nc in self.net_classes.items():
            if nc.rules.impedance_profile and nc.rules.impedance_profile not in defined_profiles:
                raise ValueError(
                    f"Net class {nc_name!r} references undefined impedance_profile "
                    f"{nc.rules.impedance_profile!r}"
                )

        return self

"""Semantic consistency rules that run after Pydantic validation.

Currently empty: all cross-reference checks (impedance_profile refs,
net_class refs, gate id uniqueness) are enforced by Pydantic model_validators
in schema/manifest.py. Additional semantic rules go here as they are defined.
"""

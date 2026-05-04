# Changelog

All notable changes to `pcb-spec` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Guidelines:
- Add a new entry under `## [Unreleased]` as you work — no batching up for release day.
- Group entries under: Added, Changed, Deprecated, Removed, Fixed, Security.
- Reference the spec slug and PR number:  "Added dark mode (spec: dark-mode, #42)".
- On release, rename `[Unreleased]` to the new version with the release date,
  and open a fresh `[Unreleased]` section at the top.
- The release-drafter workflow auto-populates draft release notes from PRs —
  keep PR titles tidy so they flow straight into here.
-->

## [Unreleased]

### Added
- Manifest schema v0.1: JSON Schema + Pydantic models for all five sections (stackup, rules, net_classes, placement, gates) (spec: manifest-schema)
- `load_manifest` / `dump_manifest` helpers in `src/pcb_spec/schema/__init__.py`
- Auto-generated schema reference at `docs/manifest-schema.md`
- Three validated example manifests: `minimal-2layer`, `4layer-mixed-signal`, `controlled-impedance`
- Full test suite in `tests/test_schema.py` (17 tests, all passing)

### Changed
-

### Deprecated
-

### Removed
-

### Fixed
-

### Security
-

---

## [0.1.0] — YYYY-MM-DD

### Added
- Initial release.

[Unreleased]: https://github.com/arananet/pcb-spec/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/arananet/pcb-spec/releases/tag/v0.1.0

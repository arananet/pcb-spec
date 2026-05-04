# JSON Report Schema — Public API Reference

`pcb-spec validate --report <path>` writes a JSON file at `<path>`. This
document defines every field. The schema is a **public API**: non-additive
changes (field removal, type change, semantic change) require a `schema_version`
bump.

Current version: **0.1**

---

## Top-level object

| Field | Type | Description |
|---|---|---|
| `schema_version` | `string` | Always `"0.1"`. Bump on breaking changes. |
| `status` | `"pass"` \| `"fail"` | `"pass"` if the manifest is valid; `"fail"` if one or more errors were found. |
| `manifest_path` | `string` | The path passed to `pcb-spec validate`, as a string. |
| `errors` | `array[Error]` | List of errors. Empty (`[]`) on `"pass"`. |

## Error object

Each element of `errors` has:

| Field | Type | Description |
|---|---|---|
| `code` | `string` | Machine-readable error code (see table below). |
| `message` | `string` | Human-readable description of the error. |
| `location` | `string` | Dot-separated path to the field that caused the error (e.g. `net_classes.HIGH_SPEED.rules.impedance_profile`). May be `"manifest"` for root-level semantic errors or the file path for file-level errors. |

## Error codes

| Code | Meaning |
|---|---|
| `SCHEMA_ERROR` | The manifest does not conform to the JSON Schema / Pydantic model. Includes missing required fields and unsupported `manifest_version`. |
| `UNDEFINED_REF` | A field references an identifier that is not defined elsewhere in the manifest (e.g. an `impedance_profile` id that has no matching entry in `rules.impedance.profiles`, or a `net_class` key not present in `net_classes`). |
| `FILE_NOT_FOUND` | The manifest path does not exist on disk. |

## Example: passing manifest

```json
{
  "schema_version": "0.1",
  "status": "pass",
  "manifest_path": "examples/minimal-2layer/manifest.yaml",
  "errors": []
}
```

## Example: failing manifest

```json
{
  "schema_version": "0.1",
  "status": "fail",
  "manifest_path": "my-board/manifest.yaml",
  "errors": [
    {
      "code": "UNDEFINED_REF",
      "message": "Net class 'HIGH_SPEED' references undefined impedance_profile 'USB_90_DIFF'",
      "location": "net_classes.HIGH_SPEED.rules.impedance_profile"
    }
  ]
}
```

## Stability guarantee

Fields listed in this document will not be removed or have their type changed
without a `schema_version` bump. New **optional** fields may be added without
a version bump. CI and the pcb-spec-skill consume this schema; treat it as a
contract.

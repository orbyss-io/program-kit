---
description: Validate a JSON file against a supplied JSON Schema or describe a selected schema section using the installed deterministic tool. Use for structural JSON checks, not architectural or cross-artifact semantic approval.
---

Use the installed executable; do not construct a validation script or decide schema validity by
reading the documents yourself. Read `references/json-schema-tools.md` for supported dialects,
reference boundaries, setup, and exit codes. Resolve relative input paths against the consumer root.

`python .specify/extensions/program-kit-governance/scripts/json_schema.py validate --schema SCHEMA --input JSON`

For unfamiliar authoring fields, request a focused JSON Pointer instead of printing the whole schema:

`python .specify/extensions/program-kit-governance/scripts/json_schema.py describe --schema SCHEMA --section '/$defs/RECORD'`

Report the compact diagnostics. Invalid input does not authorize edits; repair only when requested.
After an authorized correction, rerun validation. Structural validity is not semantic approval.
If the runtime is missing, report the exact setup command; validation never installs dependencies.
Do not fetch external references automatically, overwrite a consumer's tool modifications, or
substitute the contributor checkout for the consumer's installed version.

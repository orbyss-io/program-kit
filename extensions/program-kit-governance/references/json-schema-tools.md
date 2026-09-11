# JSON Schema tools

The extension ships `scripts/json_schema.py`, `scripts/schema_runtime.py`, and exact dependency
pins. These are executable scripts, not an MCP server. The JSON Schema skill is optional guidance;
other skills and humans can invoke the executable directly without an additional agent session.

## Setup and installed copies

Normal Program Kit initialization provisions dependencies and records the installed tool hashes.
For a direct Spec Kit extension installation, run from the consumer root:

```sh
python .specify/extensions/program-kit-governance/scripts/schema_runtime.py setup
python .specify/extensions/program-kit-governance/scripts/schema_runtime.py record-copy
```

Setup uses pip (or uv when that interpreter has no pip) and network access to install pinned wheels into `.program-kit/cache/json-schema/`,
keyed by dependency content, Python ABI, and platform. It does not alter global Python or PATH.
Use the Python interpreter that will run the tool; separate Python versions need separate caches.
Do not commit that cache. `setup --offline` reuses an already prepared runtime; on a fresh machine
use `--wheelhouse PATH --offline` with the matching pinned wheels. No code is built from source.
Validation and description never install or download anything. On Windows, setup enables verified
system certificate trust for older pip versions that support it, and for uv. Never disable
certificate verification to work around a trust error.

In the Program Kit source checkout, use `extensions/program-kit-governance/scripts/` instead of
the installed `.specify` path. Set up that source runtime once before running development checks.
An installed copy here remains independent of the source, just like any consumer's installed copy.
There are no symlinks or automatic synchronization. Upgrade through the Program Kit updater:
it checks recorded hashes before replacing tools. Local modifications stop the upgrade; preserve
them and restore the installed version before retrying. `record-copy` is an installer operation,
not a way to approve or conceal local edits. Raw `specify extension add --force` bypasses this
Program Kit safeguard and can replace edits.

Before an offline upgrade to a new runtime, explicitly provision its target cache from the extracted
release: `python RELEASE/extensions/program-kit-governance/scripts/schema_runtime.py setup --project-root CONSUMER`.
The updater itself never downloads dependencies. Add `--wheelhouse PATH --offline` for offline provisioning.

## Interface and limits

`validate --schema PATH --input PATH [--resource PATH ...] [--max-errors 100]`

`describe --schema PATH [--section '/$defs/record'] [--depth 4] [--resource PATH ...]`

Paths are filesystem paths, not shell fragments. JSON is read as UTF-8 (an input BOM is accepted).
Duplicate object keys, NaN, and Infinity are input errors. Output is UTF-8 JSON. Both commands are
read-only. Use trusted local schemas within the normal sandbox: pathological regular expressions
or recursive schemas can consume resources; the tool is not an untrusted-code isolation boundary.

Supported `$schema` values are Draft 7 (`http://json-schema.org/draft-07/schema#`), 2019-09, and
2020-12 (their canonical `https://json-schema.org/draft/.../schema` URIs). Missing/unsupported
dialects are errors; a standalone boolean schema uses 2020-12. The engine validates the schema
before the instance. `format` remains annotation-only, stated in every validation report.

Internal references are resolved by the standards engine. Relative file references may load only
within the root schema's directory after resolving symlinks. No HTTP retrieval occurs. For schemas
with logical HTTP `$id` values, supply their referenced schemas explicitly with repeated
`--resource`; their declared IDs are registered locally. Missing references are execution errors,
never valid results. Unknown annotation/extension keywords are not custom validation rules.

Validation returns `valid`, total `errorCount`, bounded `errors`, and `truncated`. Errors contain
RFC 6901 `instancePath` and `schemaPath`, the failed keyword, and a bounded message. The empty
pointer means the root. Exit codes: **0** valid/description succeeded, **1** invalid instance,
**2** malformed input/schema, unresolved reference, missing runtime, or execution failure.
Descriptions expose only the selected fragment, expanding references to a bounded depth;
remaining references are explicit. Do not treat a description as validation.

The intake adapter calls this same engine. Architecture meaning, evidence, cross-file agreement,
hashes, and human confirmation remain the responsibility of the existing semantic validators.

# Mixed Python bootstrap completion repair

Trial `09c3543d`, candidate `6a47b3c`, reached final approval and INITIALIZED with
no bootstrap blockers, then failed at `complete-bootstrap`. The preserved consumer
is `program-kit-intake-bz8rcsh0`; it was not modified during this repair.

Native shell validators used Python 3.12, with a provisioned project schema cache.
The lifecycle completion entry point needed Specify's engine and re-entered its
isolated Python 3.13. That interpreter's schema cache did not exist. Earlier
terminal regression tests replaced shell commands with the test interpreter,
concealing this environment difference.

The run/resume/reopen CLI now provisions the existing pinned schema runtime for
both interpreters, then validates a schema in isolated child processes before
dispatch. Runtime dependencies remain version-specific. Normal validators and
completion steps do not install packages. Installer/import errors fail before
agent work, with the responsible interpreter in the diagnostic. No authority,
phase eligibility or approval requirement is weakened.

Real reproduction also found that uv inherited an inaccessible machine cache.
Its schema installation now uses the consumer's `.program-kit/cache/uv` instead;
no machine permissions or global configuration are changed.

## Verification

- `tests/validate_workflow_runtimes.py` exercises both interpreters, deduplication,
  installer/import failure, timeout, missing Python and CLI early exit.
- Its explicit `--mixed-python C:/Python312/python.exe` regression uses real Python
  3.13 and 3.12, installed scripts and unmodified native terminal shell steps. It
  first reproduces SCHEMA_RUNTIME_MISSING, then exercises fixed run and resume.
  Coding-agent dispatch is forbidden. A bounded test PATH avoids this development
  host's accumulated historical fixture paths exceeding CMD's variable limit.
- `tests/validate_json_schema.py` covers uv's project-local cache selection.

Evidence logs: `artifacts/mixed-python-runtime-regression.log` and
`artifacts/workflow-runtime-development.log`. This is deterministic runtime and
workflow evidence, not a new human or automated-agent intake trial.

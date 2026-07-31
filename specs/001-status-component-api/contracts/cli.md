# CLI Contract: Status Component and API Vertical Slice

## Public executable

The public executable is `program-kit`. It is a thin application layer over
versioned kernel contracts. It does not expose provider implementation types or
Spec Kit concepts.

V1 command names and options are ordinal, case-sensitive, invariant, and
non-interactive. Unknown, duplicate, conflicting, missing, or extra arguments
are refused through the same structured result contract as other recoverable
failures.

## Factory commands

```text
program-kit explain   --workspace <path> --request <path> [--format text|json]
program-kit construct --workspace <path> --request <path> [--format text|json]
program-kit evaluate  --workspace <path> --request <path> [--format text|json]
```

### `explain`

- Maximum live effect: `none`.
- Loads restricted YAML or JSON intake, validates and binds the typed model,
  resolves one exact closure, and returns an Integration Resolution
  Explanation.
- Must not create or modify live consumer artifacts.
- A missing or ambiguous selection returns `needs-input` or `blocked`, never an
  implicit choice.

### `construct`

- Requested effect comes from the canonical request and is bounded by the
  separately supplied exact authority grant.
- `constructionMode` is `new` or `repair`; repair remains the construction role,
  not a fourth provider role.
- Maps, validates, resolves, explains, constructs an isolated candidate,
  evaluates it, performs publication preflight, publishes recoverably, verifies
  live bytes, and admits only the complete set.
- A candidate-only request stops before live publication and reports
  `candidate-only`.
- After any uncertain live effect, the command returns `indeterminate` and does
  not blind-retry.

### `evaluate`

- Maximum live effect: `none`.
- Re-resolves the exact applicable closure and compares authoritative records,
  receipts, evidence, ownership, and live artifact bytes.
- Reports exact, missing, modified, stale, colliding, interrupted, unsupported,
  and unavailable state.
- Never repairs, recovers, adopts, or otherwise mutates the workspace.

## Utility commands

```text
program-kit help [--format text|json]
program-kit version [--format text|json]
```

These are CLI utility contracts, not provider operation roles. They still
return a safe versioned operation-result envelope in JSON mode and use the same
rendering/disclosure floor. `help` identifies the locally available exact
public commands and offline contract resources. `version` identifies the CLI,
kernel protocol, distribution, diagnostic catalog, and canonicalization
revisions without contacting a network.

Invoking `program-kit` without a command returns a structured request diagnostic
and non-success exit code; it does not enter an interactive prompt.

## Option contract

| Option | Meaning | Rules |
|---|---|---|
| `--workspace <path>` | Physical workspace locator | Required for factory commands; must resolve to one directory; excluded from canonical semantic output |
| `--request <path>` | Request/intake locator | Required for factory commands; must resolve inside the workspace to an allowed regular file |
| `--format text|json` | Output projection | Optional; stable default is `text`; value is exact and case-sensitive |
| `--` | End of options | Supported only where the next required token is a value; extra positional values remain invalid |

No abbreviated options, aliases, response files, environment-variable options,
implicit current-directory request lookup, global configuration search, or
shell-evaluated command strings exist in v1.

The physical workspace and request locators may be absolute at the invocation
boundary. Before admission, the kernel resolves them, rejects escapes,
symlinks/junctions outside the workspace, and uses only canonical logical paths
for semantic identity, diagnostics, and output bytes.

## Input contract

- `.yaml` and `.yml` use `program-kit.restricted-yaml/v1`.
- `.json` uses strict JSON with duplicate property rejection.
- Both project into the same neutral data tree, validate against the same exact
  JSON Schema Draft 2020-12 registry, bind to the same typed model, and produce
  the same canonical JSON identity.
- The request's `operation` must agree with the command.
- A `construct` request with `constructionMode: repair` requires exact observed
  state and authority bindings.
- No command reads semantic selections, provider choices, policy, credentials,
  or authority from environment variables.

## Output contract

### JSON mode

- `stdout` contains exactly one buffered UTF-8 JSON document conforming to
  `operation-result.schema.json`.
- No banner, help prose, progress, log line, or terminal escape sequence may
  appear on `stdout`.
- Canonical result data excludes random identifiers, timestamps, durations,
  physical paths, process IDs, machine names, and locale-dependent values.
- Recoverable result-pipeline failure uses the independent minimal fallback
  envelope.

### Text mode

- `stdout` is a faithful English projection of the authoritative result.
- Every rendered diagnostic includes its stable ID.
- Rendering may summarize but cannot change outcome, effect, disposition, or
  diagnostic meaning.
- Progress may use `stderr`; it must not contain secrets, raw exceptions,
  protected paths, or semantic data absent from the result.

No envelope is promised before process startup, after forced or unrecoverable
termination/resource failure, or when the selected output channel cannot be
written.

## Exit codes

Exit code is determined only by top-level outcome:

| Outcome | Exit code |
|---|---:|
| `succeeded` | `0` |
| `faulted` | `1` |
| `needs-input` | `2` |
| `blocked` | `3` |
| `cancelled` | `130` |

Diagnostic severity, wording, warnings, waiver presence, and change indicators
do not independently choose an exit code.

## Reference flow

```text
explain valid request
  -> succeeded / none / complete
  -> Integration Resolution Explanation available
  -> no live consumer writes

construct accepted request
  -> succeeded / committed / complete
  -> exact lock, complete artifact set, receipts, workspace snapshot

evaluate current workspace
  -> succeeded / none / complete

evaluate drifted workspace
  -> blocked / none / repair
  -> stable drift diagnostic and bounded repair request

construct approved repair request
  -> succeeded / committed / complete
  -> new evidence and receipts
```

## Provider boundary

CLI commands do not equal provider roles:

- `explain` invokes intake mapping plus kernel validation and resolution.
- `construct` may invoke intake-mapping, construction, and evaluation providers
  while the kernel retains resolution, publication, and admission.
- `evaluate` invokes intake-mapping and evaluation providers under kernel
  control.

The CLI composes an exact fixed first-party provider registry from the selected
distribution. Installed assemblies are never scanned or selected ambiently.

# CLI Contract: Session Integration Lifecycle

This contract extends the existing `program-kit` executable without changing
the meaning of the top-level factory commands.

## Public grammar

```text
program-kit session explain --workspace <path> --request <path> [--format text|json]
program-kit session install --workspace <path> --request <path> [--format text|json]
program-kit session verify  --workspace <path> --request <path> [--format text|json]
program-kit session remove  --workspace <path> --request <path> [--format text|json]
```

Command words, option names, and values are ordinal, case-sensitive, invariant,
and non-interactive. Unknown, missing, duplicate, conflicting, abbreviated, or
extra tokens return a structured request diagnostic. There are no aliases,
response files, provider-specific command names, environment-variable
selections, interactive menus, dry-run flags, force flags, or implicit current
workspace requests.

The second command word is part of the public command identity:

| Grammar | Operation contract | Maximum effect |
|---|---|---|
| `session explain` | `orbyss.program-kit:operation-contract:session-explain@1.0.0` | `none` |
| `session install` | `orbyss.program-kit:operation-contract:session-install@1.0.0` | `committed` |
| `session verify` | `orbyss.program-kit:operation-contract:session-verify@1.0.0` | `none` |
| `session remove` | `orbyss.program-kit:operation-contract:session-remove@1.0.0` | `committed` |

These are CLI application operations. They do not add a kernel-invokable
factory provider role.

## Shared options

| Option | Meaning | Rules |
|---|---|---|
| `--workspace <path>` | Physical consumer workspace locator | Required; must resolve to one repository root; physical value is excluded from canonical semantic output |
| `--request <path>` | Session integration request | Required; must be a regular non-reparse file inside the workspace |
| `--format text|json` | Result projection | Optional; exact values only; stable default `text` |

The request conforms to
`session-integration-request.schema.json`. Its `operation` must match the CLI
subcommand. Provider, adapter, definition, CLI release, and workspace scope are
exact request selections; no installed state selects them ambiently.

## `session explain`

- Validates the request, exact CLI identity, provider and adapter selection,
  canonical definition, target workspace, provider compatibility, and planned
  projection paths.
- Creates and seals no live provider artifact.
- Returns the complete proposed projection set, collision findings, applicable
  gates, expected installation-state digest, authority requirements, and
  whether a fresh provider session would be required.
- Returns `effectState: none` on every outcome.
- Rejects an authority grant because read-only explanation must not imply or
  consume effect authority.

## `session install`

- Requires the exact request-core identity and expected installation-state
  digest returned by a current explanation.
- Requires a separately supplied authority grant bound to that request core,
  workspace, provider, operation, and `committed` effect.
- Revalidates CLI bytes, definition, adapter, provider compatibility, live
  state, paths, ownership, and authority immediately before publication.
- Publishes a complete sealed provider projection set through the kernel's
  namespaced artifact-set publisher.
- Writes the admission receipt last and reports `succeeded/committed/complete`
  only when all live bytes and mandatory gates are proven.
- Reports partial or uncertain effects as `indeterminate` and never blind
  retries.

## `session verify`

- Requires no effect authority and returns `effectState: none` on every path.
- Compares the exact installation record, CLI observations, definition,
  adapter, provider surface, projection bytes, ownership, journal, and receipts
  with current state.
- Distinguishes `absent`, `exact`, `stale`, `drifted`, `incompatible`, `partial`,
  and `removed`.
- Separately reports provider-session availability as `not-evaluated`,
  `reload-required`, `available`, or `unavailable`.
- Never reloads the provider, repairs, removes, adopts, or rewrites artifacts.

## `session remove`

- Requires an exact admitted installation record, current live-state digest,
  and separately supplied request-bound authority grant.
- Deletes only unchanged projection artifacts whose logical paths and digests
  are recorded as integration-owned.
- Preserves the independently installed CLI, authority records, other skills,
  `AGENTS.md`, provider configuration, and every unproven or drifted path.
- Records a durable removal journal and final removal receipt; lifecycle
  evidence remains under the Program Kit state namespace.
- Has no force or recursive-name-discovery behavior.

## Source-authoring refusal

When the workspace contains the exact Program Kit source-authoring marker, all
four `session` lifecycle commands return `blocked`, `effectState: none`,
`primaryDisposition: stop`, and diagnostic
`program-kit.session/PKSES0006`. There is no force flag, waiver, or hidden
exception. Normal source build, test, pack, and Spec Kit workflows do not invoke
these commands.

## Structured output

JSON mode preserves the existing `program-kit.operation-result/v1` envelope.
The `command` enum and operation-contract identity gain:

- `session-explain`;
- `session-install`;
- `session-verify`; and
- `session-remove`.

The session payload records:

- exact definition, provider, adapter, conformance profile, scope, and CLI
  release;
- proposed or observed projection artifacts and ownership;
- request-core, installation, candidate-set, and live-state identities;
- installation state and separate session availability;
- actual changes, effects, journals, receipts, and evidence; and
- neutral and provider-specific diagnostics.

`stdout` contains one clean buffered UTF-8 JSON document. Logs, progress, raw
external output, absolute protected paths, exceptions, stack traces, prompts,
and transcripts never enter it. Text output is a faithful projection and every
rendered diagnostic includes its stable ID.

## Exit codes

The existing outcome mapping remains unchanged:

| Outcome | Exit code |
|---|---:|
| `succeeded` | `0` |
| `faulted` | `1` |
| `needs-input` | `2` |
| `blocked` | `3` |
| `cancelled` | `130` |

Warnings, reload-required state, diagnostic wording, and observed changes do
not independently select an exit code.

## Help and version

`program-kit help` lists the nested session command grammar, contract resource
identities, exact installed first-party session adapters, and which operations
may write. `program-kit version` adds the session integration protocol and
provider catalog revisions while remaining offline and side-effect free.

## Reference lifecycle

```text
session explain current request
  -> succeeded / none / complete
  -> exact candidate and expected-state digest
  -> authority required for install

session install without authority
  -> blocked / none / request-approval

session install exact authorized request
  -> succeeded / committed / complete
  -> complete provider projection + admission receipt

session verify before a fresh provider session
  -> succeeded / none / retry
  -> installation exact; session availability reload-required

session verify drifted skill
  -> blocked / none / repair
  -> no mutation

session remove drifted skill
  -> blocked / none / repair
  -> no deletion

session remove exact authorized installation
  -> succeeded / committed / complete
  -> provider projections absent; CLI preserved
```

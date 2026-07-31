# ProgramKit Development Tools — Architecture 2.0 review

Canonical source:
`pkid:design:program-kit:development-tools@2.0.0`

Canonical SHA-256:
`918db6923687e0098d2b5c59936714c4f804235dfa18299bd6d6830535c7d5cb`

This Markdown is a reviewer projection. The canonical JSON governs.

## What we are building

ProgramKit will let a ProgramKit-built application expose its own
consumer-owned development operations to a fresh AI session. ProgramKit
provides the reusable mechanics:

1. exact versioned Development Tool contracts and schemas;
2. complete deterministic projection from the application's Open Console
   operations;
3. one provider-neutral MCP stdio bridge;
4. explicit project-scoped registration lifecycle in the `program-kit` CLI;
5. thin Codex and Claude Code configuration writers; and
6. deterministic and genuine cold-session acceptance evidence.

The first proof is a tiny test-only generated Console application. It accepts a
challenge and returns a deterministic structured result. The fixture proves
the complete path; it is not a product operation.

## Why this exists

Without this layer, an AI session needs inherited shell instructions,
executable paths, and provider-specific setup. That is not genuine discovery,
is hard to audit, and couples every application to one provider.

The design instead makes the application's exact registered operations
discoverable in a new Codex or Claude Code session while keeping:

- application semantics with the consumer;
- executable behavior provider-neutral;
- project registration explicit and human-started;
- provider trust and permissions provider/human owned; and
- every package, schema, executable, configuration entry, and update
  digest-verifiable.

## Ownership

### Open Console projection

Open Console is the source of truth for command semantics. ProgramKit maps and
reports every operation in the exact document. Selection defaults to all.
Owners explicitly exclude only exact operation revisions.

Each operation is reported as selected, explicitly excluded, or selected but
blocked. Aliases never become duplicate tool identities. An ambiguous,
interactive, non-JSON, unbounded, or otherwise incompatible operation is never
silently omitted.

Structured inputs derive mechanically from Open Console arguments and options.
Successful output is exactly one canonical JSON document bound to an exact
schema. The application additionally declares the policy Open Console does not
own: side effects, filesystem/network/secret access, timeout, cancellation,
concurrency, and idempotency.

### Development Tools

`Orbyss.ProgramKit.Development@0.1.0-alpha.1` gains the provider-neutral
contracts, schemas, canonical serialization, validation, compatibility, and
evidence models.

The new
`Orbyss.ProgramKit.DevelopmentTools.Mcp@0.1.0-alpha.1` package owns the single
`program-kit-development-tools-mcp` executable. It implements pinned MCP
revision `2025-11-25` over stdio and contains no Codex- or Claude-specific
runtime code.

Before advertising operations, the bridge verifies all locked bytes. A
permitted call validates structured input, creates canonical Console tokens and
explicit stdin, starts one fresh consumer process, validates the result, and
ends the process. It does not retry, retain consumers, call a provider, invoke a
capability, or form a loop.

The persisted provider command is exactly:

```text
program-kit-development-tools-mcp serve
  --protocol 2025-11-25
  --registration-lock <absolute-normalized-lock-path>
  --registration-lock-digest sha256:<64-lowercase-hex>
```

There are no aliases, PATH/environment/current-directory discovery, feed
lookup, or alternate startup modes. Bridge exit `0` is orderly client
EOF/shutdown, `2` is syntax/contract/lock/path/byte refusal, and `3` is an
unexpected bridge failure. Consumer failures are structured MCP tool errors,
not bridge exits. The bridge starts the exact consumer executable directly,
without a shell or generic `invoke` verb; the Open Console exit contract and
schema-valid canonical stdout determine operation success.

### Provider registration

The existing CLI owns:

```text
program-kit development-tools register --provider <provider>
program-kit development-tools status --provider <provider>
program-kit development-tools update --provider <provider>
program-kit development-tools remove --provider <provider>
```

It first emits a deterministic proposal. Mutation requires explicit acceptance
of that exact proposal digest.

Codex writes only one owned `mcp_servers.<registration-id>` entry in project
`.codex/config.toml`. Claude Code writes only one owned `mcpServers` entry in
project `.mcp.json`. Neither writer changes user/global configuration, starts a
process, grants trust or permission, or modifies unrelated project bytes.
Claude registration never writes `.claude/settings.json`.

Provider ownership locks live under:

```text
.program-kit/development-tools/registrations/
  codex/<registration-id>.lock.json
  claude-code/<registration-id>.lock.json
```

`status` is read-only. `update` shows every added, removed, and changed
operation. `remove` deletes only exact owned state. Collision, tamper,
incompatibility, drift, or uncontained paths fail without partial mutation.
Register/update/remove first emit a canonical proposal. Supplying no acceptance
digest is preview-only; mutation requires
`--accept-proposal-digest sha256:<64-lowercase-hex>` and an exact recomputation
match. The existing ProgramKit CLI exit profile remains `0` success, `1`
conformance/owned-state refusal, `2` usage/input/I/O refusal, and `3`
unexpected internal failure.

## Safe execution policy

- Side effects: `none`, `read-only`, `additive`, `mutating`, or `destructive`;
  missing classification blocks.
- Filesystem, network, and secrets: denied unless positively declared.
- Secret values: never stored in declarations, manifests, locks, commands,
  output, diagnostics, or evidence.
- Timeout: positive and bounded.
- Cancellation: advertised only when explicitly supported; never implies
  rollback.
- Concurrency: explicit; default and proof are one.
- Retry: none.
- Idempotency: never inferred; mutating idempotency needs a caller key and
  declared replay scope.

Selection, registration, provider trust/permission, and invocation are
separate authority transitions.

## Provider choice

Direct execution is the provider-neutral conformance baseline but does not
provide persisted AI discovery. MCP stdio is selected because both reviewed
providers support project-scoped local servers and stable MCP supplies the
shared discovery/call contract.

Provider-native binding, remote MCP, Claude plugins, and instructional skills
as transport are deferred. Material Codex, Claude Code, or MCP documentation
drift stops implementation or update.

## Console and package boundaries

Development Tools binds the exact Open Console document and consumer
package/executable bytes. It does not bind dispatcher or Spectre internals. The
separately approved typed Console review is source context, not a dependency,
and each affected work unit rechecks the accepted/current Console baseline.

Consumer applications and proof fixtures use ProgramKit only from exact
locally prepared NuGet packages with controlled source mapping. Project
references, source/file includes, hint paths, and build-output coupling are
conformance failures.

## Acceptance

The acceptance catalog has 32 required fixtures across five layers:

1. neutral mapping, policy, package-only, process, and raw MCP conformance;
2. Codex and Claude project-configuration lifecycle fixtures;
3. genuine Codex sessions A/B/C;
4. genuine Claude Code sessions A/B/C on the human's other machine; and
5. cross-provider closure and governance.

Session A constructs/packages/registers and then ends completely. Session B is
new and receives semantic intent only—no conversation, path, command syntax,
process, environment hint, or manual shell instruction. After explicit removal,
session C cannot discover the tool.

Codex and Claude evidence bind identical neutral artifacts and canonical
fixture-result digests. Provider versions, trust, approvals, permissions, and
configuration observations remain provider-labelled. Cross-provider closure
waits for genuine returned Claude evidence. Identical deterministic output does
not imply equivalent prompts, reasoning, models, providers, or general
application behavior.

## Static conformance

The human selected `reuse-existing`. ProgramKit-owned implementation C# reuses:

- gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`;
- activation:
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`;
- verification:
  `pkid:profile:program-kit:private-csharp-gate-exhaustive@1.0.0`.

No new or extended analyzer/gate and no consumer attachment is authorized.
Package-only, runtime, provider, and cold-session behavior remains executable
conformance.

## Explicit exclusions

Corrective Reconstruction remains backlogged. V1 also excludes remote MCP,
native provider bindings, plugins/skills as transport, other providers,
publication, release, deployment, production data, infrastructure, secret
values, operational history, autonomous behavior, and website technical
authority.

This artifact is a design candidate. It authorizes no implementation,
registration, provider mutation, permission, or invocation.

# ProgramKit Development Tools design intent

## Human-started outcome

Design reusable ProgramKit infrastructure through which a ProgramKit-built
application can expose consumer-owned development operations to an AI session.
A fresh Codex or Claude Code session must be able to discover and invoke those
operations solely from an explicit, persisted, project-scoped registration.

The first proof is a deliberately minimal, test-only generated Console
application. It accepts a challenge and returns one deterministic structured
result. The fixture proves construction, package-only consumption, mapping,
registration, cold-session discovery, invocation, byte verification, update,
and removal. It is not a ProgramKit product operation.

This review set defines the design and implementation plan only. It does not
implement or register a tool, MCP bridge, provider integration, capability,
permission, or autonomous behavior.

## Product boundary

ProgramKit owns three reusable pieces:

1. A provider-neutral, versioned Development Tool contract derived from an
   exact Open Console document plus an explicit access-policy declaration.
2. One provider-neutral MCP standard-input/output bridge used unchanged by
   Codex and Claude Code.
3. Thin `program-kit` CLI configuration writers for the reviewed project
   registration contracts of Codex and Claude Code.

The consumer application owns operation meaning and execution. ProgramKit does
not invent application operations, rename the consumer executable, call a
provider, grant permission, or create a model/tool loop.

## Exact identities

- contract:
  `pkid:contract:program-kit:development-tool@1.0.0`;
- declaration schema:
  `pkid:schema:program-kit:development-tool-declaration@1.0.0`;
- manifest schema:
  `pkid:schema:program-kit:development-tool-manifest@1.0.0`;
- mapping-report schema:
  `pkid:schema:program-kit:development-tool-mapping-report@1.0.0`;
- registration-lock schema:
  `pkid:schema:program-kit:development-tool-registration-lock@1.0.0`;
- existing contract package:
  `Orbyss.ProgramKit.Development@0.1.0-alpha.1`;
- new neutral bridge package:
  `Orbyss.ProgramKit.DevelopmentTools.Mcp@0.1.0-alpha.1`;
- neutral bridge executable:
  `program-kit-development-tools-mcp`;
- MCP revision: `2025-11-25`.

Each consumer retains its own exact package and executable identity. The
manifest binds the exact consumer package, executable, Open Console document,
declaration, schemas, selected operations, and digests.

## Exact process and command semantics

The persisted provider entry starts only:

```text
program-kit-development-tools-mcp serve
  --protocol 2025-11-25
  --registration-lock <absolute-normalized-lock-path>
  --registration-lock-digest sha256:<64-lowercase-hex>
```

The provider entry stores the exact absolute bridge executable path and this
exact argument array. Each option occurs once. There are no aliases,
environment-variable fallbacks, current-directory scanning, PATH discovery,
package-feed lookup, or alternate startup modes.

Bridge process exit `0` means orderly client EOF/shutdown after valid
initialization; `2` means invalid syntax, protocol selection, lock, contract,
compatibility, identity, path, or byte verification; `3` means an unexpected
bridge failure. A consumer operation failure is an MCP tool result with
`isError: true`, not a bridge process exit. A client kill after timeout has no
bridge or consumer exit-code claim and is recorded as a client-observed
timeout.

The bridge invokes the exact consumer executable directly without a shell. It
uses the manifest-declared working directory, sanitized exact environment,
canonical token array derived from the Open Console operation, and only
explicitly declared standard input. It never adds a generic consumer `invoke`
verb. The operation's Open Console exit-code contract determines success versus
declared failure. Success also requires exactly one schema-valid canonical JSON
stdout document. Declared non-success, invalid stdout, unexpected exit, failed
start, cancellation, timeout, and internal bridge failure remain distinct
structured tool-result classifications.

The explicit CLI grammar is:

```text
program-kit development-tools register
  --provider <codex|claude-code>
  --project-root <absolute-path>
  --registration <declaration-file>
  --proposal-output <file>
  [--accept-proposal-digest sha256:<64-lowercase-hex>]

program-kit development-tools status
  --provider <codex|claude-code>
  --project-root <absolute-path>
  --registration-id <id>
  --output <file|->

program-kit development-tools update
  --provider <codex|claude-code>
  --project-root <absolute-path>
  --registration <declaration-file>
  --proposal-output <file>
  [--accept-proposal-digest sha256:<64-lowercase-hex>]

program-kit development-tools remove
  --provider <codex|claude-code>
  --project-root <absolute-path>
  --registration-id <id>
  --proposal-output <file>
  [--accept-proposal-digest sha256:<64-lowercase-hex>]
```

Without `--accept-proposal-digest`, register/update/remove only emit the
canonical proposal and do not mutate. With it, the command recomputes the
proposal from current exact bytes and mutates only when the digest matches.
ProgramKit's existing CLI exit profile remains `0` success, `1` conformance or
owned-state refusal, `2` usage/input/I/O refusal, and `3` unexpected internal
failure. Canonical JSON output contains no invocation or secret values;
diagnostics use the selected existing CLI diagnostics profile.

## Operation projection and selection

Open Console remains authoritative for command and operation semantics.
ProgramKit maps and reports every operation in the exact bound document.
Selection defaults to every current operation. The application owner only
declares exact-revision exclusions.

Arguments and options mechanically project to one structured input schema per
selected operation. Aliases remain Console syntax and never become duplicate
tool identities. A projectable successful operation emits exactly one
canonical UTF-8 JSON document on standard output, bound to an exact schema.
Diagnostics use standard error and never expose inputs, outputs, environment
values, credentials, or secrets.

An operation that is ambiguous, interactive, unbounded, non-JSON, missing an
exact side-effect classification, or otherwise incompatible remains visible
and blocked in the mapping report. It is never silently omitted or weakened.
The owner must correct it or explicitly exclude its exact revision.

Selection is not registration, permission, or invocation. A changed Open
Console document or selected set requires a human-started update proposal
before persisted provider configuration can change.

## Provider-neutral execution policy

The side-effect classification is one of `none`, `read-only`, `additive`,
`mutating`, or `destructive`. Filesystem, network, and secret access are denied
unless positively declared. Secret declarations identify provider-owned
references only; secret values never enter a manifest, lock, command line,
output, or evidence.

Each operation declares a positive bounded timeout, cancellation support, and
maximum concurrency. The default is concurrency one. The bridge starts one
fresh consumer process for a permitted call, never retries automatically, and
does not keep the process for later calls. Idempotency is never inferred; an
idempotent mutating operation requires a caller-supplied key and declared
replay scope.

The bridge validates exact locked bytes before discovery, validates input and
output schemas, maps the structured call to canonical Console tokens and
explicit standard input, translates MCP cancellation when the operation
declares support, and enforces the lower applicable timeout. MCP annotations
are informational projections, not permission grants.

## Explicit registration lifecycle

The existing `program-kit` CLI owns:

- `program-kit development-tools register --provider <provider>`;
- `program-kit development-tools status --provider <provider>`;
- `program-kit development-tools update --provider <provider>`;
- `program-kit development-tools remove --provider <provider>`.

The CLI first produces a deterministic proposal binding exact provider,
project, registration, configuration change, contract, schema, package,
executable, manifest, selected-operation, and provider-evidence bytes. Mutation
requires a human-started command accepting the exact proposal digest.

Codex writes only its owned project entry in `.codex/config.toml`. Claude Code
writes only its owned project entry in `.mcp.json`. Neither writer changes
user/global configuration, starts a process, approves trust, grants permission,
or touches unrelated project configuration. Claude registration never writes
`.claude/settings.json`.

Ownership is recorded under:

```text
.program-kit/development-tools/registrations/
  codex/<registration-id>.lock.json
  claude-code/<registration-id>.lock.json
```

Registration verifies exact bytes, refuses collisions, writes configuration
and the lock atomically, and starts nothing. `status` is read-only. `update`
requires a new proposal and reports every operation delta. `remove` verifies
the exact owned state and removes only that entry and lock. Missing, tampered,
changed, incompatible, colliding, or uncontained state fails without partial
mutation.

## Provider contracts

Codex uses a trusted project-scoped `.codex/config.toml`
`mcp_servers.<registration-id>` entry with the exact command and arguments,
`required = true`, an exact `enabled_tools` set, bounded startup/tool timeouts,
and prompt-or-stricter tool approval.

Claude Code uses a project-scoped `.mcp.json` `mcpServers` entry with the exact
command and arguments. The human separately trusts the workspace and approves
the server. Provider permissions remain Claude-owned `mcp__<server>__<tool>`
rules. The writer never adds an `allow` rule.

Direct executable invocation is the provider-neutral conformance baseline but
not persisted discovery. Provider-native bindings, remote MCP, Claude plugins,
and instructional skills as transport are deferred.

Authoritative sources must be rechecked at every implementation or update
boundary; material drift is a stop condition:

- <https://learn.chatgpt.com/docs/extend/mcp>
- <https://learn.chatgpt.com/docs/config-file/config-reference>
- <https://code.claude.com/docs/en/mcp>
- <https://code.claude.com/docs/en/permissions>
- <https://code.claude.com/docs/en/settings>
- <https://modelcontextprotocol.io/specification/2025-11-25/server/tools>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/transports>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation>

## Package-only consumer boundary

Consumer applications and proof fixtures consume ProgramKit only from exact
locally prepared NuGet packages through controlled package-source mapping.
ProgramKit project references, source/file includes, assembly hint paths, and
build-output coupling are conformance failures.

The Development Tool contract is host-profile-neutral. It binds the exact Open
Console operation document and consumer executable/package bytes, not a
dispatcher or Spectre implementation detail. The separate typed Console review
is source context, not authority for this review. Every implementation work
unit rechecks the accepted/current Console baseline and stops on material
incompatibility.

## Acceptance

Provider-neutral conformance and provider configuration fixtures run locally.
Genuine Codex proof uses isolated sessions A for package/construct/register, B
for cold discovery and invocation, and C for removal/non-discovery. No
conversation, executable path, command syntax, process state, environment hint,
or manual shell instruction crosses sessions.

The human runs the equivalent genuine Claude Code proof on another machine
from the same exact ProgramKit commit and artifacts, then returns provider
evidence for ProgramKit validation. Cross-provider closure remains open until
that evidence is genuine and valid. Deterministic fixture results may be
identical; no equivalence of prompts, model reasoning, provider behavior, or
general application behavior is claimed.

Negative acceptance covers missing/tampered bytes, incompatible versions,
collisions, permission denial, policy-blocked and excluded operations, new
operations before update, filesystem/network/secret denial, timeout,
cancellation, concurrency, retry/idempotency prohibition, update, removal,
package-only construction, surviving processes, and prohibited autonomous
behavior.

## Documentation and exclusions

Canonical technical documentation belongs to
`Orbyss.ProgramKit.Development`,
`Orbyss.ProgramKit.DevelopmentTools.Mcp`, the `program-kit` CLI, and
ProgramKit-owned schemas and evidence. A website may project it but cannot
become technical authority.

V1 excludes Corrective Reconstruction; providers beyond Codex and Claude Code;
remote MCP; provider-native bindings; plugins and skills as transport; feed
publication; release, deployment, production data, infrastructure, secret
values, operational history; self-registration; self-permission; automatic
start; provider or development-capability invocation; and autonomous behavior.

# ProgramKit Development Tools convergence notes

## Status and human rulings

These notes record decisions made after the validated `1.0.0` review set was
published. They do not amend the canonical design or authorize implementation.

- Development Tools is the sole active design concern.
- Corrective Reconstruction is held on the backlog until it has a concrete
  goal, first consumer, triggering scenario, and observable success condition.
- The replacement Development Tools review set must cover both Codex and Claude
  Code from the outset.
- ProgramKit will implement the provider-neutral setup and both provider
  integrations in this repository after exact human approval. Claude Code
  runtime acceptance may be executed by the human on another machine and
  returned as external evidence.
- Convergence will proceed section by section. The old canonical design and
  plan digests are baseline evidence, not current approval candidates.

## Product shape under convergence

The research supports three separately owned pieces:

1. A versioned, provider-neutral Development Tool executable contract owned by
   ProgramKit.
2. One provider-neutral MCP stdio bridge that exposes that contract without
   owning provider registration, trust, or permissions.
3. Thin provider registration integrations that translate the same reviewed
   registration into Codex project configuration or Claude Code project MCP
   configuration.

This avoids implementing a different tool protocol for every AI provider.
Provider-specific code owns only discovery/configuration, collision checks,
human trust boundaries, status, update, removal, and provider evidence.

No executable, bridge, registration integration, provider binding, capability,
permission, or runtime behavior exists yet.

## Claude Code authoritative findings

Research was limited to Anthropic's official Claude Code documentation and the
stable MCP specification:

- Claude Code supports local MCP servers over stdio and manages them explicitly
  with `claude mcp add`, `list`, `get`, and `remove`:
  <https://code.claude.com/docs/en/mcp>.
- Project-scoped servers live in `.mcp.json`. They are shareable but remain
  pending until the human trusts the workspace and approves the server. A
  cloned repository cannot approve itself:
  <https://code.claude.com/docs/en/mcp>.
- Claude Code MCP permissions use `mcp__<server>__<tool>` rules with `deny`,
  `ask`, and `allow`; restrictive policy takes precedence:
  <https://code.claude.com/docs/en/permissions>.
- Claude settings expose project-server enable/disable controls, but the
  registration integration must not grant trust or enable every project
  server:
  <https://code.claude.com/docs/en/settings>.
- Claude plugins can bundle MCP servers that start when the plugin is enabled.
  That lifecycle conflicts with the current explicit-registration and
  no-automatic-start boundary, so plugin transport is not the proposed first
  integration:
  <https://code.claude.com/docs/en/plugins-reference>.
- Stable MCP defines tool discovery/call and stdio transport independently of
  either provider:
  <https://modelcontextprotocol.io/specification/2025-11-25/server/tools> and
  <https://modelcontextprotocol.io/specification/2025-11-25/basic/transports>.

## Proposed Claude boundary for review

The current recommendation is project-scoped `.mcp.json`, because it is
reviewable, portable, provider-supported, and visible to a genuinely cold
Claude Code session. Registration would write only an owned server entry
pointing at exact locally materialized package/contract/bridge bytes. It would
not approve the server, alter Claude permission policy, start Claude Code, or
invoke a tool.

The human would explicitly trust and approve the project server in Claude Code.
Mutating Development Tool calls would remain subject to Claude's provider
permission flow. Update and removal would verify recorded ownership and exact
bytes before changing the owned entry.

The external acceptance record must include the Claude Code version, clean
machine/session preconditions, registration receipt, project trust/server
approval, cold-session discovery and semantic invocation, tool-call result,
and negative cases for collision, tampering, incompatible package versions,
permission denial, update, and removal.

## Converged section 1: product outcome and proof boundary

The human accepted this section during convergence.

The product is generic infrastructure through which a ProgramKit-built
application can expose its own consumer-owned development operations to an AI
session. ProgramKit owns the exact executable/tool contract, projection,
registration mechanics, provider bridge, validation, and evidence. It does not
invent or own the application's operation semantics.

The first acceptance proof uses a deliberately minimal, test-only generated
Console application. Its operation accepts a challenge value and returns a
deterministic structured response binding the challenge digest and exact tool
contract identity. The fixture exists only to prove construction, packaging,
registration, cold-session discovery, structured invocation, result validation,
and removal. It is not a ProgramKit product capability and is not installed or
advertised outside the bounded acceptance workspace.

An earlier proposal for a product-like `verify-artifact` proof operation was
rejected as unnecessary semantics. Discovery alone is insufficient evidence,
so the minimal fixture remains necessary to prove an actual invocation through
the exact registered bytes.

Converged outcome:

> A fresh Codex or Claude Code session can discover and invoke a
> consumer-owned operation from an explicitly registered ProgramKit-built
> Console application without inherited executable paths or command syntax. A
> minimal test-only Console fixture proves that path; ProgramKit does not
> prescribe application operation semantics.

## Converged section 2: Open Console mapping and selection

The human accepted the source-of-truth and policy recommendations with one
correction: selection defaults to all current Open Console operations, and the
application owner explicitly unselects only the operations that must not be
Development Tools.

ProgramKit maps and reports every operation from the exact bound Open Console
document. It derives operation revision, command path, aliases, description,
arguments, options, referenced schemas, standard-input/output/error contracts,
exit-code meanings, examples, and authority reference from that document.
Aliases remain alternate Console syntax and do not become duplicate Development
Tool identities.

The selection contract has these invariants:

- `defaultSelection` is `all`.
- Exclusions bind exact operation revisions, never display names, aliases, or
  positions.
- The mapping report lists every operation and classifies it as selected,
  explicitly excluded, or blocked from projection with an exact diagnostic.
- An operation that cannot satisfy the Development Tool contract is never
  silently omitted or weakened. Construction fails until the owner corrects
  the operation or explicitly excludes its exact revision.
- Selection does not register a provider tool, approve a server, grant a
  permission, or invoke an operation.
- The selected set and exact Open Console document digest are frozen into the
  generated Development Tool manifest and registration lock.
- A later Open Console revision may default-select a newly added operation when
  constructing a new manifest, but it cannot silently alter an existing Codex
  or Claude Code registration. The changed document/manifest digest requires an
  explicit human-started update that reports the added, removed, and changed
  operations before provider configuration changes.

Open Console remains the source of truth for operation semantics. The separate
Development Tool declaration owns only the AI execution and access policy that
Open Console does not currently express. Exact policy fields and their safe
defaults remain the next convergence decision.

## Converged section 3: structured invocation and fail-closed policy

The human accepted this section without changes.

ProgramKit mechanically derives one structured AI input schema for each
selected operation from the exact Open Console command:

- canonical positional-argument and option names become properties;
- requiredness, scalar/array shape, value type, occurrence, default, and
  dependency/conflict rules come from the existing argument and option
  descriptors;
- flags become booleans;
- aliases remain Console-only alternate syntax and never become additional AI
  properties;
- the bridge maps a validated structured call to one canonical token array and
  any explicitly declared standard input for the generated Console executable;
- the operation is projectable only when its successful standard output is one
  canonical JSON document bound to an exact schema.

The generated schema is a digest-bound projection, not a separately authored
input contract. Open Console remains authoritative, and projection drift is a
construction failure.

The provider-neutral safe defaults are:

- filesystem access denied;
- network access denied;
- secret access denied;
- maximum concurrency one;
- no automatic retry;
- no idempotency claim or replay;
- a positive bounded timeout owned by the Development Tool contract version;
- cancellation is advertised only when the application explicitly declares
  support;
- non-JSON, unbounded, interactive, or schema-ambiguous operations are blocked
  from projection until corrected or explicitly excluded.

Access beyond a denied default requires an exact positive declaration. Secret
declarations may identify provider-owned secret references but never contain
secret values. Registration and evidence contain no input, output, environment,
credential, or secret values.

Side effects cannot be inferred honestly from the current Open Console
document. Every selected operation therefore requires one explicit
classification from the closed set `none`, `read-only`, `additive`, `mutating`,
or `destructive`. A missing classification keeps the operation selected in the
mapping report but marks it blocked; it cannot enter a generated manifest or
provider registration. The owner must classify or explicitly exclude it.

Provider selection, provider registration, provider permission, and actual
invocation remain separate human-authority transitions. The policy is not a
permission grant, and derived MCP annotations are informational projections
only.

## Next convergence question

Converge the exact provider-neutral package, executable, manifest, operation,
and registration identities, including how one provider-neutral MCP bridge is
shared by the Codex and Claude Code registration integrations.

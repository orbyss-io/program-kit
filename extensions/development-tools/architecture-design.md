# ProgramKit Development Tools

Human-readable projection of
`pkid:design:program-kit:development-tools@1.0.0`.

Canonical design SHA-256:
`6ec7ac36df528e838ec2423d6f2bf3838e27b31edd93f5c09a66c3730b1f44b2`.
If this projection differs from `architecture-design.json`, the JSON is
authoritative.

## Decision

Select a provider-neutral executable contract with a direct-process conformance
baseline and one first reviewed provider projection: a thin Codex MCP stdio
adapter pinned to stable MCP `2025-11-25`. Direct executable invocation is not a
Codex discovery mechanism; an instructional skill is not a tool transport or
permission boundary; no authoritative provider-native arbitrary-executable
contract was found. Plugin packaging, remote MCP, and additional providers are
deferred.

This review is independent from Corrective Reconstruction. Approval of either
review set grants no authority over the other.

## Exact identities

| Role | Identity |
|---|---|
| Tool contract | `pkid:contract:program-kit:development-tool@1.0.0` |
| Tool manifest schema | `pkid:schema:program-kit:development-tool-manifest@1.0.0` |
| Registration lock schema | `pkid:schema:program-kit:development-tool-registration-lock@1.0.0` |
| Proof package | `Orbyss.ProgramKit.DevelopmentTool.ConsoleProof@0.1.0-alpha.1` |
| Proof executable | `program-kit-development-tool-console-proof` |
| Adapter package | `Orbyss.ProgramKit.DevelopmentTool.Adapter.Codex.Mcp@0.1.0-alpha.1` |
| Adapter executable | `program-kit-development-tool-codex-mcp` |
| Codex server id | `program_kit_console_proof` |
| MCP tool name | `program-kit.console-proof.invoke` |

## Provider-neutral invocation

The exact command form is:

```text
program-kit-development-tool-console-proof invoke --contract-digest <sha256> --operation <operation-id>
```

One canonical UTF-8 JSON input is read from stdin; exactly one canonical UTF-8
JSON result is written to stdout. Redacted diagnostics may use stderr. Exit `0`
is success, `1` is declared failure or cooperative cancellation, `2` is
input/identity/contract/permission rejection, and `3` is unexpected internal
failure. A provider-enforced process kill is recorded as timeout and receives no
fabricated tool exit code.

The manifest digest-binds package, nupkg, executable, schemas, operations,
compatibility, and documentation. Each operation declares a closed side-effect
class (`none`, `read-only`, `additive`, `mutating`, or `destructive`), positive
timeout, cancellation support, maximum concurrency, idempotency/replay rule,
filesystem roots, network allowlist, and named secret references. Access is
denied unless positively declared and approved. The adapter does not retry.

## Codex adapter and registration

At implementation start, official Codex and MCP sources are fetched again.
Material drift stops PKDT-W030. The adapter exposes exactly one MCP server/tool,
validates schemas and bytes before advertisement, maps structured results and
errors, translates cancellation, enforces the lower contract/provider timeout,
and derives annotations only as review hints.

A human explicitly starts register, status, update, or remove. Registration
targets only `mcp_servers.program_kit_console_proof` in trusted project-scoped
`.codex/config.toml`, uses `required = true`, an exact enabled-tool allowlist,
bounded timeouts, and prompt-or-stricter approval. It verifies package,
contract, executable, and adapter bytes; refuses server/tool collisions; and
records the normalized owned-table digest and exact byte identities in
`.program-kit/development-tools/codex.lock.json`.

Update and removal verify both lock and current table, preserve unrelated TOML,
and refuse drift. Removal deletes only the exact owned table and lock.

## Authority and security boundary

The tool and adapter never register themselves, grant permissions, auto-start,
invoke ProgramKit development capabilities, call an AI provider, or form an
autonomous loop. Tool discovery is not invocation authority. Secret values never
enter manifests, locks, command lines, output, diagnostics, or evidence.

The proof tool and adapter consume ProgramKit only through exact locally
prepared NuGet packages with controlled package-source mapping. Project
references, source/file includes, assembly hint paths, build-output coupling,
and uncontrolled first-party sources fail conformance.

## Cold-session proof

Session A prepares packages, constructs the exact proof and adapter, registers,
verifies, records evidence, and ends completely. Session B starts fresh with no
conversation, executable path, command syntax, process, environment hint, or
manual shell instruction. The human provides semantic intent only. Codex must
discover and invoke solely from persisted registration.

Negative cases cover missing/tampered adapter, incompatible package, collisions,
filesystem/network/secret denial, timeout, cancellation, concurrency,
idempotency, explicit update, and explicit removal followed by cold
non-discovery.

## Open decision and deferrals

The only implementation-time decision is whether authoritative provider
contracts have materially drifted before PKDT-W030. Drift blocks and returns to
design. Plugin packaging, remote transport, extra providers, repository split,
feed publication, release, deployment, and website projection are deferred
review units. Canonical technical documentation remains in ProgramKit or the
future owning Development Tool repository.

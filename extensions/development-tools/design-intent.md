# ProgramKit Development Tools design intent

## Human-started outcome

Design a provider-neutral, versioned executable Development Tool contract for
ProgramKit-built applications and prove it first with an exact generated Console
tool. The first reviewed provider integration is Codex through an explicitly
installed, thin MCP standard-input/output adapter. No tool, adapter, binding, or
provider capability is implemented or registered by this design review.

## Required identity and transport decisions

- Contract identity:
  `pkid:contract:program-kit:development-tool@1.0.0`.
- Tool-manifest schema identity:
  `pkid:schema:program-kit:development-tool-manifest@1.0.0`.
- Registration-lock schema identity:
  `pkid:schema:program-kit:development-tool-registration-lock@1.0.0`.
- First proof package:
  `Orbyss.ProgramKit.DevelopmentTool.ConsoleProof@0.1.0-alpha.1`.
- First proof executable:
  `program-kit-development-tool-console-proof` with platform suffixes treated as
  package content, not as a change of tool identity.
- First adapter package:
  `Orbyss.ProgramKit.DevelopmentTool.Adapter.Codex.Mcp@0.1.0-alpha.1`.
- First adapter executable:
  `program-kit-development-tool-codex-mcp`.
- First persisted Codex server identifier:
  `program_kit_console_proof`.
- First MCP tool name:
  `program-kit.console-proof.invoke`.
- Provider-neutral invocation is a fresh process for one operation. It accepts
  one canonical UTF-8 JSON input document on standard input and emits exactly
  one canonical UTF-8 JSON result document on standard output. Diagnostics may
  use standard error and may never contain inputs, outputs, environment values,
  secret values, or credentials.
- The provider-neutral executable syntax is
  `program-kit-development-tool-console-proof invoke --contract-digest <sha256> --operation <operation-id>`.
  Ambient command discovery, alternate aliases, and executable-path inference
  are rejected.
- Exit code `0` means schema-valid success; `1` means a declared operation
  failure or cooperative cancellation; `2` means input, contract, identity, or
  permission rejection; `3` means an unexpected internal failure. A host kill
  after timeout has no tool exit-code claim and is reported by the adapter as a
  timed-out invocation.

## Contract semantics

The manifest binds exact package id/version/nupkg digest, executable relative
path and digest, runtime target, contract revision/digest, operation names,
input/output JSON Schemas and digests, exit-code profile, timeout, cancellation,
maximum concurrency, idempotency, side-effect classification, filesystem roots,
network allowlist, and named secret references. Side effects use the closed set
`none`, `read-only`, `additive`, `mutating`, and `destructive`. Filesystem,
network, and secret access are denied unless positively declared and approved.
Secret references name a provider-owned secret source; secret values never enter
the manifest, lock, registration, command line, stdout, or evidence.

Each operation declares a positive timeout, whether cancellation is supported,
and maximum concurrency. The default and first proof are cancellation supported,
maximum concurrency one, network denied, secrets denied, and a fixture-scoped
read/write root. An idempotent mutating operation requires a caller-supplied
idempotency key and a declared replay scope; other operations must not claim
idempotency. The adapter never retries a call automatically.

The adapter validates inputs and outputs against exact schemas, verifies all
locked bytes before advertising a tool, translates MCP cancellation to process
cancellation, enforces the lower of the contract timeout and Codex
`tool_timeout_sec`, and refuses concurrency above the declaration. MCP
annotations are derived projections for user review, never permission
enforcement or authority.

## Explicit Codex registration

Registration is a human-started ProgramKit command over an exact prepared local
package root, tool manifest, and adapter manifest. It edits only the reviewed
`mcp_servers.program_kit_console_proof` table in trusted project-scoped
`.codex/config.toml`. The table uses the exact adapter executable and arguments,
`required = true`, an exact `enabled_tools` allowlist, bounded startup/tool
timeouts, and prompt-or-stricter approval. Registration verifies exact package,
contract, executable, and adapter bytes; refuses an existing server-id or tool
name; records ownership and the normalized owned-table digest in
`.program-kit/development-tools/codex.lock.json`; and never claims ownership of
unrelated configuration.

Update and removal are separate explicit human-started commands. Both verify the
registration lock and current owned table before mutation, preserve unrelated
TOML, and refuse missing, changed, or colliding ownership. Removal deletes only
the exactly owned server table and registration lock. The tool and adapter never
register themselves, grant permissions, start automatically, invoke development
capabilities, call an AI provider, or create a tool-to-model loop.

## Transport decision

- Direct executable is the provider-neutral conformance baseline but has no
  persisted Codex discovery mechanism.
- An undocumented provider-native executable binding is rejected because no
  authoritative Codex contract was found.
- MCP standard input/output revision `2025-11-25` is selected because current
  Codex documentation defines project-scoped MCP configuration and the stable
  protocol defines tool discovery, structured schemas/results, cancellation,
  progress, and standard-input/output framing.
- An instructional skill may teach a workflow that invokes a separately
  registered tool, but it is not the tool transport, identity, permission
  boundary, or cold-session discovery proof.
- Plugin packaging and any later provider adapter are deferred review units.

Authoritative provider sources to re-check at implementation start:

- <https://learn.chatgpt.com/docs/extend/mcp>
- <https://learn.chatgpt.com/docs/config-file/config-reference#configtoml>
- <https://modelcontextprotocol.io/specification/2025-11-25/server/tools>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/transports>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress>

Material provider-contract drift is a stop condition, not an invitation to infer
a new binding.

## Package-only proof boundary

The Console proof is constructed with the current generated Console dispatcher
and lifecycle source truth. It consumes ProgramKit only from exact locally
prepared NuGet packages through a generated `NuGet.Config` with controlled
package-source mapping. Consumer project references to ProgramKit, source/file
includes, assembly hint paths, and ProgramKit build-output coupling are
conformance failures.

## Cold-session acceptance

Session A prepares exact packages, constructs the proof tool and adapter,
registers the exact reviewed Codex table, verifies the lock and bytes, records
evidence, and ends completely. All processes from session A must be absent.

Session B is a new Codex session with no inherited conversation, executable
path, command syntax, process state, environment hint, or manual shell
instruction. The human states only the semantic intent to use the registered
Console proof. Codex must discover the tool solely through persisted provider
registration and invoke it successfully. Evidence records provider version,
project trust scope, discovered server/tool identity, input/output schema
digests, invocation/result digests, exit classification, approval observation,
process boundaries, and exact package/adapter/registration-lock digests.

Negative fixtures cover missing and tampered adapters, changed or incompatible
packages, server and tool-name collisions, denied filesystem/network/secret
permissions, timeout, cancellation, concurrency, idempotency, explicit update,
and explicit removal followed by non-discovery in a third cold session.

## Documentation ownership and exclusions

Canonical technical documentation remains in ProgramKit or a future owning
Development Tool repository. A website may project reviewed documentation but
may not become technical authority. This review excludes implementation,
registration, an MCP server, a provider wrapper, a capability, autonomous
behavior, package-feed publication, release, deployment, and changes outside
the ProgramKit repository.

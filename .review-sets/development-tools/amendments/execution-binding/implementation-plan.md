# Development Tools alpha.5 execution-binding implementation plan amendment

> Non-authoritative human-readable projection. The canonical source is
> `implementation-plan.json`. If this projection and the canonical JSON differ,
> the canonical JSON governs. This document grants no implementation authority.

Canonical SHA-256: `sha256:7acb5f6cc110e0c4967119e6ae49c84545f92a20e18b2b9245c2510f3c833417`.
Source commit: `01a9a820d422d92da7f2df977db66c4d4f888924`.
Frozen approved plan SHA-256: `sha256:0ee9304510bbfaa6de508bf4fd5f0726625cb33e77aced26cbfe5a15db72c5a3`.
State: `ready-for-human-decision`; implementation remains `not-started`.
Static conformance remains the approved `reuse-existing` decision.

## Exact amendment

- Every requirement, dependency, required outcome, input, output, allowed edit, compatibility obligation, stop condition, verification command, trace, gate selection, selection lock, and activation-evidence reference is preserved from the approved plan.
- Every activation matrix is `approval-fixed` to `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`, digest `sha256:9603f5e67d256b381df4e69dce99fd9aafeaded20c947cfe699adb9dec7ecd8b`.
- Every verification profile is `execution-resolved` for `pkid:profile:program-kit:private-csharp-gate-exhaustive` within `[1.0.0,1.1.0)` under the exact compatibility policy.
- The current compatible selection is `1.0.1`, digest `sha256:2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f`; execution must record an exact binding receipt.
- Scope, authority, product semantics, package selection, required outcomes, allowed edits, and stop conditions cannot be execution-resolved.

## Work units

### PKDT-W010

**Depends on:** none

**Required outcome**

Generalize the implemented operation contracts into one host-neutral OperationContractCatalog plus explicit exposure bindings, preserving exact operation identity/revision and the approved reuse-existing Program Kit static-gate binding.

**Allowed edits**

- schemas/operations and bounded operation-contract source, registry, serialization, compatibility, fixtures, tests, documentation, solution, package, and lock files. Do not edit or reinterpret the completed Program Kit health-patching extension.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Catalogs and bindings validate and canonicalize deterministically; one semantic operation revision can bind Console and OpenAPI exposures without duplicating semantics; all current operation contracts remain compatible; current private gate, build, and tests pass.

**Stop conditions**

- Stop if current operation/Open Console source contradicts host-neutral identity, an exposure must become semantic authority, the health-patching task would be widened, or implementation would create or extend a static gate.

### PKDT-W020

**Depends on:** PKDT-W010

**Required outcome**

Project exact generated Console and generated API hosts from exposure bindings, including reserved host-owned structured Console introspection over the complete catalog or one selected operation with deterministic syntax and collision refusal.

**Allowed edits**

- Bounded generated Console/OpenAPI projection, host metadata, reserved introspection grammar, serializers, collision validation, fixtures, tests, documentation, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Help/completion remain human-facing; structured introspection exposes only catalog facts, composes no application service, invents no domain meaning, contains no secrets, selects exact aliases/paths, and refuses every reserved-token collision deterministically.

**Stop conditions**

- Stop if introspection requires a domain command, invokes application services, weakens host-neutral identity, exposes secrets, invents semantics, or Open Console/OpenAPI compatibility cannot be preserved.

### PKDT-W030

**Depends on:** PKDT-W020

**Required outcome**

Implement one provider-neutral stdio MCP bridge that mechanically projects the same operation catalog into exact tool names, descriptions, input/output schemas, results, failures, and direct operation invocation across the current modern and legacy MCP eras.

**Allowed edits**

- Bounded MCP bridge project/executable, discovery negotiation, tools list/call projection, process adapter, fixtures, tests, canonical documentation, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Modern server/discover and legacy initialize negotiate independently; tools/list is primary; direct one-operation MCP works without any capability; results remain application-owned; timeout, cancellation, concurrency, stdout/stderr, byte integrity, and failure behavior pass.

**Stop conditions**

- Stop on material MCP contract drift, provider-specific bridge code, stdout contamination, invented result semantics, shared mutable consumer execution, missing exact byte verification, automatic retry, nested model/tool loops, or capability-as-transport behavior.

### PKDT-W040

**Depends on:** PKDT-W030

**Required outcome**

Implement deterministic project-scoped tool-registration proposal, exact human acceptance, provider ownership locks, status, update, and removal while keeping registration, trust/permission, and invocation as separate transitions.

**Allowed edits**

- Bounded Development Tools registration core and CLI grammar; Codex and Claude Code project MCP entry renderers; proposal/lock schemas; atomic mutation, collision, drift, fixtures, tests, docs, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Proposal bytes are deterministic; no provider/workspace mutation occurs before exact acceptance; status is read-only; update and removal preserve unrelated bytes; trust/permission remains provider-owned; no command starts a provider or tool.

**Stop conditions**

- Stop if mutation can precede acceptance, ownership is ambiguous, user/global provider state is required, status mutates, writes are uncontained/non-atomic, removal adopts unrelated state, or registration implies trust, permission, or invocation.

### PKDT-W050

**Depends on:** PKDT-W010

**Required outcome**

Define the optional application-authored outcome-capability bundle, deterministic descriptor/procedure/knowledge-closure structure, exact operation/schema bindings, composition/handoff rules, publisher attestation boundary, readiness checks, and authoring safeguard.

**Allowed edits**

- Generic capability bundle/descriptor/procedure/knowledge-closure schemas and verifier; compatibility, authoring diagnostics/materializers, fixtures, tests, documentation, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: One or many operations may support a meaningful outcome; one-operation capabilities require real intake, interpretation, remediation, or safety value; required bindings and transitive closure preflight exactly; Program Kit validates conformance without authoring or approving domain semantics.

**Stop conditions**

- Stop if the contract creates one capability per command, universal workflow/result state, inferred domain semantics, prose-only closure, implicit authority, required source checkout, or a new capability/provider wrapper under implementation rather than an application-authored test fixture.

### PKDT-W060

**Depends on:** PKDT-W050

**Required outcome**

Generalize the existing capability bundle engine to acquire exact public local-directory, zip, NuGet, HTTPS, and GitHub-release sources, normalize carriers, verify publisher/package/tool/catalog/capability/adapter/closure identities and digests, and store immutable content by digest.

**Allowed edits**

- Bounded existing capability bundle verifier/acquisition/storage source and CLI source-kind parsing; carrier adapters; schemas, fixtures, tests, documentation, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Every source kind converges on one verified normalized bundle; format and location are explicit; mutable references resolve to locked immutable bytes; traversal, collision, ambiguity, partial acquisition, and digest mismatch fail closed; private/authenticated acquisition remains unsupported.

**Stop conditions**

- Stop if separate lifecycle engines emerge, a remote source activates content, credentials are required, runtime packages reference session capability content, carrier semantics leak into canonical bundles, or immutable bytes cannot be reproduced.

### PKDT-W070

**Depends on:** PKDT-W040, PKDT-W060

**Required outcome**

Implement the shared explicit capability lifecycle: deterministic initialize proposal, acceptance, provider/bundle ownership locks, refresh, update, status, removal, preflight, canonical reads, pruning, provider projections, and one atomic flat workspace catalog.

**Allowed edits**

- Bounded existing capabilities CLI engine and provider renderers; workspace content store, locks, flat catalog, discover-capabilities projection, transactional filesystem support, schemas, fixtures, tests, documentation, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Installation activates nothing; initialize and tool registration remain distinct accepted transitions; provider-native selection sees thin individual capabilities; discover-capabilities reads one flat grouped catalog; refresh repairs derived bytes only from unchanged locked sources; update alone accepts changed authoritative bytes; tampered locks fail closed.

**Stop conditions**

- Stop if refresh adopts new source or lock bytes, catalogs become authoritative/editable inputs, indexes nest, Program Kit adds confidence routing, provider trust/permission is mutated, initialization implies registration, or runtime/application executables edit AI workspace state.

### PKDT-W080

**Depends on:** PKDT-W070

**Required outcome**

Repackage Program Kit consumer capabilities as the reference generic application-capability payload with the same closure, digest, initialization, refresh, update, provider projection, catalog, and cold-session rules, preserving only a narrowly documented embedded-delivery bootstrap distinction.

**Allowed edits**

- Program Kit capability bundle payload/catalog/knowledge closure, package manifest, materializers, provider projections, package-only consumer fixtures, tests, documentation, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Every supported Program Kit consumer operation has package-only outcome guidance parity; cold sessions need no source checkout or internal memory; contributor architecture/debugging remains source-attached and separately initialized; the generic verifier treats Program Kit like any other publisher.

**Stop conditions**

- Stop if Program Kit dogfood receives semantic/conformance exceptions, consumer journeys require source/assembly/test-fixture archaeology, runtime references provider capability content, or contributor-only knowledge leaks into package-only consumer closure.

### PKDT-W090

**Depends on:** PKDT-W080

**Required outcome**

Close deterministic and package-only acceptance for host parity, direct MCP, capability closure and triggering fixtures, lifecycle authority, catalog drift/refresh/update, Program Kit dogfood, and every no-autonomy negative.

**Allowed edits**

- Isolated package-only applications/workspaces; JTest-shaped publisher fixture; Console/API/MCP fixtures; deterministic provider configuration fixtures; lifecycle/closure/tamper/collision tests; evidence schemas, records, docs, solution, package, and lock files.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: All 42 reviewed fixtures pass, including cold semantic JTest-shaped outcome, direct MCP without capability, Console introspection parity, incomplete-closure refusal, changed-byte explicit update, refresh repair, no self-registration/permission/loop, and Program Kit package-only reference proof.

**Stop conditions**

- Stop if any fixture inherits syntax or source knowledge, application semantics are supplied by Program Kit, provider-native behavior is claimed from deterministic fixtures, changed bytes are silently accepted, or the active health-patching task is altered.

### PKDT-W100

**Depends on:** PKDT-W090

**Required outcome**

Prove genuine isolated Codex cold-session discovery, direct tool use, outcome-capability activation, guided registered-operation use, changed-byte refusal/update, refresh repair, removal, and non-discovery after removal from exact reviewed package bytes.

**Allowed edits**

- Isolated Codex acceptance workspaces; provider-labelled evidence schemas/records/validators; bounded acceptance scripts and canonical documentation. No user-global provider mutation.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Fresh Codex sessions use native tool and skill selection without inherited syntax, distinguish direct operation from outcome guidance, respect project trust/approval, reproduce exact evidence, and cease discovery after exact removal.

**Stop conditions**

- Stop on material Codex drift, non-cold or unisolated sessions, user/global writes, inherited command knowledge, fabricated/non-genuine selection, missing trust/approval observation, secret-bearing evidence, or different package/lock bytes.

### PKDT-W110

**Depends on:** PKDT-W090, PKDT-W100

**Required outcome**

Validate genuine returned Claude Code evidence, close cross-provider and governance acceptance, finalize canonical documentation, and record completion without overstating Program Kit conformance as application semantic approval.

**Allowed edits**

- Exact returned Claude Code evidence; cross-provider closure records; publisher-attestation/conformance documentation; final acceptance records and validators; review validation and implementation evidence.

**Verification**

- `dotnet test ProgramKit.sln --no-restore --maxcpucount:1 --property:UseSharedCompilation=false` from `.`.
  Expected: Locked restore, current private gate, build, full suites, package-only proofs, deterministic evidence, genuine provider-labelled Codex and Claude Code evidence, all negatives, documentation ownership, changed-file scope, and publisher/conformance distinction pass.

**Stop conditions**

- Stop and leave closure open if Claude evidence is unavailable, changed, fabricated, non-cold, incomplete, secret-bearing, or from different bytes; also stop on any suite, package-only, gate, no-autonomy, documentation-authority, or scope failure.

## Requirement trace

- `PKDT-R001`: PKDT-W010, PKDT-W020, PKDT-W030, PKDT-W090, PKDT-W110. One exact host-neutral operation identity/revision owns semantics across Console, OpenAPI, and MCP exposure bindings.
- `PKDT-R002`: PKDT-W020, PKDT-W090, PKDT-W110. Generated Console structured introspection is reserved, host-owned, deterministic, collision-safe, non-executing, secret-free, and parity-complete.
- `PKDT-R003`: PKDT-W030, PKDT-W090, PKDT-W100, PKDT-W110. The neutral MCP bridge supports current modern and legacy discovery/tool contracts and direct one-operation use without a capability.
- `PKDT-R004`: PKDT-W040, PKDT-W070, PKDT-W090, PKDT-W100, PKDT-W110. Tool registration is deterministic and explicit; registration, provider trust/permission, and invocation remain separate.
- `PKDT-R005`: PKDT-W050, PKDT-W080, PKDT-W090, PKDT-W110. Application capability bundles are optional, outcome-oriented, publisher-authored, and never mechanically one capability per command.
- `PKDT-R006`: PKDT-W050, PKDT-W060, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Capability procedures bind exact operation/schema identities and carry finite transitive knowledge closure, interpretation, remediation, authority, stop, and completion guidance.
- `PKDT-R007`: PKDT-W050, PKDT-W060, PKDT-W080, PKDT-W090, PKDT-W110. Program Kit verifies integrity, compatibility, completeness, and package binding without authoring or approving application domain semantics.
- `PKDT-R008`: PKDT-W060, PKDT-W070, PKDT-W090, PKDT-W110. Public local, NuGet, HTTPS, and GitHub-release carriers normalize through one verified acquisition and content-addressed storage engine.
- `PKDT-R009`: PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Capability initialize, refresh, update, status, removal, preflight, reads, and pruning remain Program Kit CLI-owned and human-authorized.
- `PKDT-R010`: PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Refresh repairs derived bytes only from unchanged trusted locks and bundles; update alone accepts changed authoritative bytes; lock tampering fails closed.
- `PKDT-R011`: PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. One derived flat workspace catalog supports on-demand discover-capabilities while provider-native selection owns normal activation.
- `PKDT-R012`: PKDT-W050, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Tool-ready and agent-guided readiness remain independent, exact, diagnostic, and non-authorizing.
- `PKDT-R013`: PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Program Kit dogfoods the same generic application capability contract and proves every supported consumer operation from packages without source checkout.
- `PKDT-R014`: PKDT-W050, PKDT-W060, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Runtime packages and application executables remain isolated from provider-session content and never mutate AI workspace configuration or locks.
- `PKDT-R015`: PKDT-W030, PKDT-W040, PKDT-W050, PKDT-W070, PKDT-W090, PKDT-W100, PKDT-W110. No universal result/workflow envelope, Program Kit confidence router, automatic registration/initialization, self-permission, retry, nested index, or autonomous model/tool loop exists.
- `PKDT-R016`: PKDT-W090, PKDT-W100, PKDT-W110. Cold provider evidence proves semantic capability activation, direct MCP use, introspection parity, closure refusal, explicit changed-byte update, refresh repair, removal, and package-only Program Kit parity.
- `PKDT-R017`: PKDT-W050, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Official application content and publisher attestation remain distinct from Program Kit conformance and provider-labelled observations.
- `PKDT-R018`: PKDT-W010, PKDT-W020, PKDT-W030, PKDT-W040, PKDT-W050, PKDT-W060, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110. Program Kit-owned implementation reuses the exact current private gate and does not alter or widen the completed health-patching task.

## Exact approval boundary

Approval must identify architecture design `sha256:bdf4e01cc95425342cc8720d11a4b0672bc16b809afc802ad4af4035777e62d8`, static-conformance disposition `sha256:bb7f82782ce173494a3f32b3e7e23b5f792028bed41989ddb7b83020aac677d2`, compatibility policy `sha256:7e25932cedcb88476c6cfeedc3ef6102f146cfd7842b72ea48ec5bf4e8e74b59`, and canonical plan `sha256:7acb5f6cc110e0c4967119e6ae49c84545f92a20e18b2b9245c2510f3c833417`.
Approval authorizes only execution of the preserved PKDT-W010 through PKDT-W110 plan with successful compatible binding resolution. It does not authorize provider trust or permission, user-global writes, application semantic approval, publication, release, deployment, external-repository mutation, or autonomous behavior.
Any unresolved, incompatible, missing, stale, or materially changed selection stops before implementation and requires renewed human review.

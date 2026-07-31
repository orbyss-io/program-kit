# Program Kit operation exposure and application capabilities — implementation plan

> Non-authoritative human-readable projection. The canonical source is
> `implementation-plan.json`. If this projection and the canonical JSON differ,
> the canonical JSON governs. This document grants no implementation authority.

Canonical SHA-256: `sha256:0ee9304510bbfaa6de508bf4fd5f0726625cb33e77aced26cbfe5a15db72c5a3`
State: `ready-for-human-decision`; implementation remains `not-started`.
Static conformance: `reuse-existing`.

## Dependency order

- `PKDT-W010` depends on: none
- `PKDT-W020` depends on: PKDT-W010
- `PKDT-W030` depends on: PKDT-W020
- `PKDT-W040` depends on: PKDT-W030
- `PKDT-W050` depends on: PKDT-W010
- `PKDT-W060` depends on: PKDT-W050
- `PKDT-W070` depends on: PKDT-W040, PKDT-W060
- `PKDT-W080` depends on: PKDT-W070
- `PKDT-W090` depends on: PKDT-W080
- `PKDT-W100` depends on: PKDT-W090
- `PKDT-W110` depends on: PKDT-W090, PKDT-W100

## Work units

### PKDT-W010

**Depends on:** none

**Required outcome**

Generalize the implemented operation contracts into one host-neutral OperationContractCatalog plus explicit exposure bindings, preserving exact operation identity/revision and the approved reuse-existing Program Kit static-gate binding.

**Allowed edits**

- schemas/operations and bounded operation-contract source, registry, serialization, compatibility, fixtures, tests, documentation, solution, package, and lock files. Do not edit or reinterpret the completed Program Kit health-patching extension.

**Expected verification**

- Catalogs and bindings validate and canonicalize deterministically; one semantic operation revision can bind Console and OpenAPI exposures without duplicating semantics; all current operation contracts remain compatible; current private gate, build, and tests pass.

**Stop conditions**

- Stop if current operation/Open Console source contradicts host-neutral identity, an exposure must become semantic authority, the health-patching task would be widened, or implementation would create or extend a static gate.

### PKDT-W020

**Depends on:** PKDT-W010

**Required outcome**

Project exact generated Console and generated API hosts from exposure bindings, including reserved host-owned structured Console introspection over the complete catalog or one selected operation with deterministic syntax and collision refusal.

**Allowed edits**

- Bounded generated Console/OpenAPI projection, host metadata, reserved introspection grammar, serializers, collision validation, fixtures, tests, documentation, solution, package, and lock files.

**Expected verification**

- Help/completion remain human-facing; structured introspection exposes only catalog facts, composes no application service, invents no domain meaning, contains no secrets, selects exact aliases/paths, and refuses every reserved-token collision deterministically.

**Stop conditions**

- Stop if introspection requires a domain command, invokes application services, weakens host-neutral identity, exposes secrets, invents semantics, or Open Console/OpenAPI compatibility cannot be preserved.

### PKDT-W030

**Depends on:** PKDT-W020

**Required outcome**

Implement one provider-neutral stdio MCP bridge that mechanically projects the same operation catalog into exact tool names, descriptions, input/output schemas, results, failures, and direct operation invocation across the current modern and legacy MCP eras.

**Allowed edits**

- Bounded MCP bridge project/executable, discovery negotiation, tools list/call projection, process adapter, fixtures, tests, canonical documentation, solution, package, and lock files.

**Expected verification**

- Modern server/discover and legacy initialize negotiate independently; tools/list is primary; direct one-operation MCP works without any capability; results remain application-owned; timeout, cancellation, concurrency, stdout/stderr, byte integrity, and failure behavior pass.

**Stop conditions**

- Stop on material MCP contract drift, provider-specific bridge code, stdout contamination, invented result semantics, shared mutable consumer execution, missing exact byte verification, automatic retry, nested model/tool loops, or capability-as-transport behavior.

### PKDT-W040

**Depends on:** PKDT-W030

**Required outcome**

Implement deterministic project-scoped tool-registration proposal, exact human acceptance, provider ownership locks, status, update, and removal while keeping registration, trust/permission, and invocation as separate transitions.

**Allowed edits**

- Bounded Development Tools registration core and CLI grammar; Codex and Claude Code project MCP entry renderers; proposal/lock schemas; atomic mutation, collision, drift, fixtures, tests, docs, solution, package, and lock files.

**Expected verification**

- Proposal bytes are deterministic; no provider/workspace mutation occurs before exact acceptance; status is read-only; update and removal preserve unrelated bytes; trust/permission remains provider-owned; no command starts a provider or tool.

**Stop conditions**

- Stop if mutation can precede acceptance, ownership is ambiguous, user/global provider state is required, status mutates, writes are uncontained/non-atomic, removal adopts unrelated state, or registration implies trust, permission, or invocation.

### PKDT-W050

**Depends on:** PKDT-W010

**Required outcome**

Define the optional application-authored outcome-capability bundle, deterministic descriptor/procedure/knowledge-closure structure, exact operation/schema bindings, composition/handoff rules, publisher attestation boundary, readiness checks, and authoring safeguard.

**Allowed edits**

- Generic capability bundle/descriptor/procedure/knowledge-closure schemas and verifier; compatibility, authoring diagnostics/materializers, fixtures, tests, documentation, solution, package, and lock files.

**Expected verification**

- One or many operations may support a meaningful outcome; one-operation capabilities require real intake, interpretation, remediation, or safety value; required bindings and transitive closure preflight exactly; Program Kit validates conformance without authoring or approving domain semantics.

**Stop conditions**

- Stop if the contract creates one capability per command, universal workflow/result state, inferred domain semantics, prose-only closure, implicit authority, required source checkout, or a new capability/provider wrapper under implementation rather than an application-authored test fixture.

### PKDT-W060

**Depends on:** PKDT-W050

**Required outcome**

Generalize the existing capability bundle engine to acquire exact public local-directory, zip, NuGet, HTTPS, and GitHub-release sources, normalize carriers, verify publisher/package/tool/catalog/capability/adapter/closure identities and digests, and store immutable content by digest.

**Allowed edits**

- Bounded existing capability bundle verifier/acquisition/storage source and CLI source-kind parsing; carrier adapters; schemas, fixtures, tests, documentation, solution, package, and lock files.

**Expected verification**

- Every source kind converges on one verified normalized bundle; format and location are explicit; mutable references resolve to locked immutable bytes; traversal, collision, ambiguity, partial acquisition, and digest mismatch fail closed; private/authenticated acquisition remains unsupported.

**Stop conditions**

- Stop if separate lifecycle engines emerge, a remote source activates content, credentials are required, runtime packages reference session capability content, carrier semantics leak into canonical bundles, or immutable bytes cannot be reproduced.

### PKDT-W070

**Depends on:** PKDT-W040, PKDT-W060

**Required outcome**

Implement the shared explicit capability lifecycle: deterministic initialize proposal, acceptance, provider/bundle ownership locks, refresh, update, status, removal, preflight, canonical reads, pruning, provider projections, and one atomic flat workspace catalog.

**Allowed edits**

- Bounded existing capabilities CLI engine and provider renderers; workspace content store, locks, flat catalog, discover-capabilities projection, transactional filesystem support, schemas, fixtures, tests, documentation, solution, package, and lock files.

**Expected verification**

- Installation activates nothing; initialize and tool registration remain distinct accepted transitions; provider-native selection sees thin individual capabilities; discover-capabilities reads one flat grouped catalog; refresh repairs derived bytes only from unchanged locked sources; update alone accepts changed authoritative bytes; tampered locks fail closed.

**Stop conditions**

- Stop if refresh adopts new source or lock bytes, catalogs become authoritative/editable inputs, indexes nest, Program Kit adds confidence routing, provider trust/permission is mutated, initialization implies registration, or runtime/application executables edit AI workspace state.

### PKDT-W080

**Depends on:** PKDT-W070

**Required outcome**

Repackage Program Kit consumer capabilities as the reference generic application-capability payload with the same closure, digest, initialization, refresh, update, provider projection, catalog, and cold-session rules, preserving only a narrowly documented embedded-delivery bootstrap distinction.

**Allowed edits**

- Program Kit capability bundle payload/catalog/knowledge closure, package manifest, materializers, provider projections, package-only consumer fixtures, tests, documentation, solution, package, and lock files.

**Expected verification**

- Every supported Program Kit consumer operation has package-only outcome guidance parity; cold sessions need no source checkout or internal memory; contributor architecture/debugging remains source-attached and separately initialized; the generic verifier treats Program Kit like any other publisher.

**Stop conditions**

- Stop if Program Kit dogfood receives semantic/conformance exceptions, consumer journeys require source/assembly/test-fixture archaeology, runtime references provider capability content, or contributor-only knowledge leaks into package-only consumer closure.

### PKDT-W090

**Depends on:** PKDT-W080

**Required outcome**

Close deterministic and package-only acceptance for host parity, direct MCP, capability closure and triggering fixtures, lifecycle authority, catalog drift/refresh/update, Program Kit dogfood, and every no-autonomy negative.

**Allowed edits**

- Isolated package-only applications/workspaces; JTest-shaped publisher fixture; Console/API/MCP fixtures; deterministic provider configuration fixtures; lifecycle/closure/tamper/collision tests; evidence schemas, records, docs, solution, package, and lock files.

**Expected verification**

- All 42 reviewed fixtures pass, including cold semantic JTest-shaped outcome, direct MCP without capability, Console introspection parity, incomplete-closure refusal, changed-byte explicit update, refresh repair, no self-registration/permission/loop, and Program Kit package-only reference proof.

**Stop conditions**

- Stop if any fixture inherits syntax or source knowledge, application semantics are supplied by Program Kit, provider-native behavior is claimed from deterministic fixtures, changed bytes are silently accepted, or the active health-patching task is altered.

### PKDT-W100

**Depends on:** PKDT-W090

**Required outcome**

Prove genuine isolated Codex cold-session discovery, direct tool use, outcome-capability activation, guided registered-operation use, changed-byte refusal/update, refresh repair, removal, and non-discovery after removal from exact reviewed package bytes.

**Allowed edits**

- Isolated Codex acceptance workspaces; provider-labelled evidence schemas/records/validators; bounded acceptance scripts and canonical documentation. No user-global provider mutation.

**Expected verification**

- Fresh Codex sessions use native tool and skill selection without inherited syntax, distinguish direct operation from outcome guidance, respect project trust/approval, reproduce exact evidence, and cease discovery after exact removal.

**Stop conditions**

- Stop on material Codex drift, non-cold or unisolated sessions, user/global writes, inherited command knowledge, fabricated/non-genuine selection, missing trust/approval observation, secret-bearing evidence, or different package/lock bytes.

### PKDT-W110

**Depends on:** PKDT-W090, PKDT-W100

**Required outcome**

Validate genuine returned Claude Code evidence, close cross-provider and governance acceptance, finalize canonical documentation, and record completion without overstating Program Kit conformance as application semantic approval.

**Allowed edits**

- Exact returned Claude Code evidence; cross-provider closure records; publisher-attestation/conformance documentation; final acceptance records and validators; review validation and implementation evidence.

**Expected verification**

- Locked restore, current private gate, build, full suites, package-only proofs, deterministic evidence, genuine provider-labelled Codex and Claude Code evidence, all negatives, documentation ownership, changed-file scope, and publisher/conformance distinction pass.

**Stop conditions**

- Stop and leave closure open if Claude evidence is unavailable, changed, fabricated, non-cold, incomplete, secret-bearing, or from different bytes; also stop on any suite, package-only, gate, no-autonomy, documentation-authority, or scope failure.

## Requirements

- **PKDT-R001:** One exact host-neutral operation identity/revision owns semantics across Console, OpenAPI, and MCP exposure bindings. Work units: PKDT-W010, PKDT-W020, PKDT-W030, PKDT-W090, PKDT-W110.
- **PKDT-R002:** Generated Console structured introspection is reserved, host-owned, deterministic, collision-safe, non-executing, secret-free, and parity-complete. Work units: PKDT-W020, PKDT-W090, PKDT-W110.
- **PKDT-R003:** The neutral MCP bridge supports current modern and legacy discovery/tool contracts and direct one-operation use without a capability. Work units: PKDT-W030, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R004:** Tool registration is deterministic and explicit; registration, provider trust/permission, and invocation remain separate. Work units: PKDT-W040, PKDT-W070, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R005:** Application capability bundles are optional, outcome-oriented, publisher-authored, and never mechanically one capability per command. Work units: PKDT-W050, PKDT-W080, PKDT-W090, PKDT-W110.
- **PKDT-R006:** Capability procedures bind exact operation/schema identities and carry finite transitive knowledge closure, interpretation, remediation, authority, stop, and completion guidance. Work units: PKDT-W050, PKDT-W060, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R007:** Program Kit verifies integrity, compatibility, completeness, and package binding without authoring or approving application domain semantics. Work units: PKDT-W050, PKDT-W060, PKDT-W080, PKDT-W090, PKDT-W110.
- **PKDT-R008:** Public local, NuGet, HTTPS, and GitHub-release carriers normalize through one verified acquisition and content-addressed storage engine. Work units: PKDT-W060, PKDT-W070, PKDT-W090, PKDT-W110.
- **PKDT-R009:** Capability initialize, refresh, update, status, removal, preflight, reads, and pruning remain Program Kit CLI-owned and human-authorized. Work units: PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R010:** Refresh repairs derived bytes only from unchanged trusted locks and bundles; update alone accepts changed authoritative bytes; lock tampering fails closed. Work units: PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R011:** One derived flat workspace catalog supports on-demand discover-capabilities while provider-native selection owns normal activation. Work units: PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R012:** Tool-ready and agent-guided readiness remain independent, exact, diagnostic, and non-authorizing. Work units: PKDT-W050, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R013:** Program Kit dogfoods the same generic application capability contract and proves every supported consumer operation from packages without source checkout. Work units: PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R014:** Runtime packages and application executables remain isolated from provider-session content and never mutate AI workspace configuration or locks. Work units: PKDT-W050, PKDT-W060, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R015:** No universal result/workflow envelope, Program Kit confidence router, automatic registration/initialization, self-permission, retry, nested index, or autonomous model/tool loop exists. Work units: PKDT-W030, PKDT-W040, PKDT-W050, PKDT-W070, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R016:** Cold provider evidence proves semantic capability activation, direct MCP use, introspection parity, closure refusal, explicit changed-byte update, refresh repair, removal, and package-only Program Kit parity. Work units: PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R017:** Official application content and publisher attestation remain distinct from Program Kit conformance and provider-labelled observations. Work units: PKDT-W050, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.
- **PKDT-R018:** Program Kit-owned implementation reuses the exact current private gate and does not alter or widen the completed health-patching task. Work units: PKDT-W010, PKDT-W020, PKDT-W030, PKDT-W040, PKDT-W050, PKDT-W060, PKDT-W070, PKDT-W080, PKDT-W090, PKDT-W100, PKDT-W110.

## Approval boundary

Approval must identify the exact canonical design and plan digests.
Approval would not authorize provider trust or permission, user-global writes,
application semantic approval, publication, release, deployment, external
repository mutation, or autonomous behavior. Material deviation stops for
renewed human design review.

_Generated deterministically beside the canonical plan by_
_`materialize-implementation-plan.ps1`._

# Program Kit operation exposure and application capabilities convergence

## Status

The human completed section-by-section convergence and explicitly approved all
recommendations, including the exact `reuse-existing` static-conformance
disposition. This record is design input, not approval of the canonical design
or implementation plan produced from it.

The review remained inside the Program Kit repository. The active
`[HEALTH-PATCHING] Program Kit` task was not read from uncommitted bytes,
altered, or widened. Convergence used committed main through
`13ed51549b50ab08590054695db7ace5731d8e3d`. Before materialization, committed
main first advanced to `928c529b07a5a33d941a2ab5e8bf3384caa40cf6`,
strengthening Git-normalized C# gate manifest-digest verification. During final
validation it advanced again to
`f555745e77ebce234f7e54665869a32cc555ba45`, adding the completed alpha-3
package-only consumer proof/handoff and merged-branch cleanup policy. Those
commits were reconciled. The cold consumer proof is preserved as the existing
package-only foundation that the application-capability dogfood must
generalize; the branch policy affects repository workflow only. Neither commit
alters the converged product design or widens the completed health task.

## Preserved foundations

- Exact project-scoped registration remains explicit and digest-accepted.
- One provider-neutral MCP stdio bridge remains shared by Codex and Claude
  Code.
- Provider trust, permission, and invocation remain separate.
- Package-only consumers cannot use Program Kit project/source/build coupling.
- Exact byte verification, collision refusal, explicit update/removal,
  provider-labelled genuine evidence, and no-autonomy remain.
- Skills remain rejected as executable transport.
- Existing embedded Program Kit capability delivery, closure verification,
  locks, provider wrappers, and cold-session checks are generalized rather than
  discarded.
- The private Program Kit source gate remains the selected static gate.

## Compatible amendments

- Open Console becomes the Console exposure contract rather than the root
  operation-semantics catalog.
- Console and OpenAPI exposures bind one host-neutral operation catalog.
- The MCP bridge supports modern `2026-07-28` and legacy `2025-11-25` through
  wire negotiation.
- Generated Console hosts gain one reserved structured introspection surface.
- Registration uses exact operation identities and one selected invocation
  binding per operation.
- Current embedded capability mechanics become one generic engine for embedded
  and external bundles.

## Materially new design

- Optional publisher-authored outcome capability bundles.
- Exact operation bindings independent of Console, HTTP, and MCP syntax.
- Finite consumer knowledge closure with transitive schemas, examples,
  diagnostics, migrations, interpretation, and materializers.
- Separate acquisition and workspace/provider lifecycle CLI planes.
- Content-addressed bundle storage and separately locked derived workspace
  projections.
- One flat workspace capability catalog and an on-demand
  `discover-capabilities` meta capability.
- Human-started application-capability authoring/scaffolding safeguards.
- Independent `tool-ready` and `agent-guided` readiness claims.
- Program Kit package-only dogfood as the reference application payload.
- Explicit separation between publisher-official content and Program Kit
  conformance.

## Section 1 — Product and ownership

The human aligned with these decisions:

1. `OperationContractCatalog` is the host-neutral semantic source.
2. Open Console owns Console syntax; OpenAPI owns HTTP syntax.
3. A shared operation identity requires application-owner semantic equivalence,
   not merely a shared handler.
4. Outcome capability bundles are optional and inert.
5. Application ownership is semantic; Program Kit ownership is conformance.
6. Capabilities represent outcomes, not commands. One-operation capabilities
   remain valid when they add intake, interpretation, remediation, or safety.
7. Guidance activation grants no execution authority.
8. Canonical procedures are provider-neutral; provider wrappers are thin
   deterministic projections.
9. No universal workflow/result/next-action envelope is introduced.
10. Capability handoffs are exact, acyclic, and separately preflighted.
11. Provider-native selection is reused without a Program Kit scoring system.
12. One on-demand `discover-capabilities` capability reads one flat catalog.
13. Source kind, carrier, bundle kind, logical identity, and content identity
    remain distinct.
14. Acquisition is separate from verification and initialization; later reads
    never re-resolve the source.
15. Embedded Program Kit and external application bundles share one engine.

## Section 2 — Generated Console introspection

The human aligned with:

- `--program-kit-introspect` for the full catalog;
- `--program-kit-introspect=<exact-operation-revision>` for one operation;
- no short alias and no ordinary application command reservation;
- exact argument shapes and precedence above completion/help/application
  dispatch;
- one versioned JSON shape with transitive schema closure;
- generated bytes embedded in the host;
- no application service composition, secrets, reflection, network, or
  configuration reads; and
- MCP `tools/list` as primary registered-agent discovery, with Console
  introspection providing direct/offline parity.

No API introspection endpoint was inferred.

## Section 3 — MCP projection

The human aligned with:

- modern MCP `2026-07-28` plus legacy `2025-11-25`;
- `server/discover`/per-request metadata for modern and `initialize` for legacy;
- no startup `--protocol` argument;
- core stdio tools only for the first implementation;
- a Console-process adapter first and an explicit future HTTP adapter boundary;
- one active binding per operation per registration;
- `<scope>__<name>` tool names with the agreed 128-character hash truncation;
- portable object-root inputs and results for dual-era support;
- exact application results without a Program Kit application-result envelope;
- no retry, inferred idempotency, or conflation of protocol and execution
  failures;
- bounded application-owned server instructions plus Program Kit authority
  suffix;
- separate provider permission; and
- working `tool-ready` and `agent-guided` labels.

## Section 4 — CLI acquisition and lifecycle

The human aligned with two CLI planes.

`capability-bundles` owns explicit `local`, `nuget`, `https`, and
`github-release` acquisition, verification, inspection, and pruning.

`capabilities` owns initialize, refresh, update, status, remove, preflight,
read, and resource retrieval.

Additional rulings:

- sources are exact and V1 is public/anonymous;
- acquired bytes enter a content-addressed workspace store;
- verification reports integrity, compatibility, completeness, and publisher
  authority without semantic endorsement;
- every mutation previews and requires the exact accepted proposal digest;
- embedded Program Kit capabilities retain a no-bundle-reference shorthand;
- one command mutates one exact bundle/provider and may select exact capability
  subsets;
- required tool bindings resolve during lifecycle proposals;
- missing bindings produce setup-required; ambiguity blocks;
- tool registration and capability locks remain separate;
- removal does not prune source bytes;
- refresh reconstructs derived bytes from the same bundle, while update accepts
  new authoritative bundle bytes; and
- a tampered ownership lock cannot be adopted through refresh.

## Section 5 — Capability structure and closure

The human aligned with:

- one machine descriptor plus one canonical deterministic procedure;
- stable local operation-binding names resolving to exact operation and schema
  revisions;
- no Console path, API route, or MCP tool name embedded in the capability;
- deterministic procedure sections for identity, trigger, outcome, non-goals,
  inputs, authority, procedure, interpretation, human decisions, stop
  conditions, completion, diagnostics, and migration;
- a typed finite digest-bound knowledge graph;
- shared resources without byte duplication;
- missing closure refusal before guided execution;
- required dependencies versus optional handoffs;
- no authority transfer or automatic target invocation on handoff;
- a human-started product capability-design safeguard;
- tool-only as a valid explicit product outcome;
- scaffolding and coverage without inferred domain semantics;
- one flat derived workspace catalog;
- provider-native selection, no nested indexes or confidence router;
- `discover-capabilities` for on-demand catalog explanation;
- Program Kit built-ins as the reference external-style payload; and
- contributor-only capabilities remaining source-attached.

The human additionally confirmed the catalog integrity model:

- publisher operation/capability catalogs are immutable digest-bound inputs;
- Program Kit derives the workspace catalog only from accepted locks;
- derived catalog/provider bytes are atomically replaced;
- manual edits are drift and unusable;
- accepted refresh repairs projections from unchanged verified source;
- accepted update is required for changed authoritative bundle bytes; and
- filesystem ownership cannot prevent all manual writes, so digest verification
  and fail-closed reads are the authority.

## Section 6 — Acceptance and static conformance

The human aligned with:

1. Five evidence layers: provider-neutral, package-only, provider
   configuration, genuine provider sessions, and closure/governance.
2. Host-neutral identity proof across Console, API, and MCP.
3. Independent direct-tool and agent-guided proof.
4. Genuine cold JTest semantic intent with no inherited syntax or source.
5. Independent negative removal/tamper cases for every closure class.
6. Separate registration, capability initialization, permission, and invocation
   transitions.
7. Correct refresh versus update classification for changed bytes.
8. Release-blocking Program Kit package-only dogfood.
9. Separate publisher-official and Program Kit-conformant claims.
10. Exact `reuse-existing` static-conformance disposition.

The reused gate is:

- `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`;
- activation matrix
  `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`;
- Program Kit-owned source scope only.

No new analyzer, gate extension, consumer attachment, or gate-establishment
work is authorized. Protocol, package-only, provider, lifecycle, and
cold-session claims remain executable evidence.

## Current official-provider reconciliation

The materialization check used current official sources:

- Codex supports trusted project `.codex/config.toml` and exact stdio MCP
  command/args, allow lists, timeouts, and separate approval modes.
- Codex defines a skill as a reusable workflow and supports explicit or implicit
  skill activation.
- Claude Code uses project `.mcp.json`; a cloned repository cannot approve its
  own server.
- Claude Code uses `.claude/skills/<name>/SKILL.md`; description text drives
  model selection, while full content loads when invoked.
- Claude Code tool search defers MCP tool definitions and uses server
  instructions for category-level discovery.
- MCP `2026-07-28` is stateless and uses `server/discover` plus per-request
  protocol metadata; its stdio compatibility rules preserve fallback to legacy
  initialized servers.
- MCP `2025-11-25` remains the legacy initialized contract.

These findings support companion guidance plus executable MCP. They do not
justify skills as transport, Program Kit ranking, or provider permission
mutation.

## Convergence result

All material architecture and static-conformance decisions are explicit.
Formal Architecture Design and Implementation Plan artifacts may now be
materialized and presented for a separate exact-digest human approval.

Convergence approval is not design/plan approval and grants no implementation,
registration, provider, permission, package publication, or runtime authority.

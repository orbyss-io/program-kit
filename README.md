# Program Kit CLI

> **AI builds it. Human intent governs it.**

Program Kit is being redesigned as a human-governed, AI-provider-neutral .NET
software factory. Its CLI turns approved intent into contract-bounded,
ordinary software through explicit construction and evaluation operations.

## Project status: v1 redesign and first executable proof

The previous implementation has not been deleted. It is preserved on the
[`archive/pre-rebuild-2026-07-31`](https://github.com/orbyss-io/program-kit/tree/archive/pre-rebuild-2026-07-31)
branch so its code, tests, documentation, and hard-won lessons remain available
as prior art.

The repository now contains both the converged v1 design records and the first
executable vertical slice. That slice proves the public `explain`, `construct`,
and `evaluate` operation model for one deliberately narrow .NET 10 + CShells
0.0.28 Status component/API fixture. It generates an ordinary component NuGet
package and ASP.NET Core application, admits published artifacts with a receipt,
detects drift without mutating the workspace, and proves the generated API can
restore, build, start, and serve `/status` without Program Kit at runtime.

This is not yet a released or general-purpose Program Kit CLI. It is the first
testable product proof after one more necessary redesign. The archived
implementation remains historical prior art, not authority for v1 behavior;
its commands and package surfaces are not promises. The current implementation
is intentionally small so developers and architects can review the product
boundaries before more providers, capability mappings, or authoring experiences
are added.

Feature 001 was **accepted as the bounded first product foundation**. A bounded
closure audit on
2026-08-01 rejected the earlier prototype for material authority, provider,
admission/recovery, diagnostic, snapshot, and product-proof gaps. The current
candidate addresses those gaps, and the repository-owned gate passes 91 tests
plus deterministic evidence, formatting, and whitespace verification. The
exact accepted review candidate is commit
`16c6c627dfc9cd2211993580019f43d084dc718d`; its implementation/evidence
ancestor is `2f7151b25022d7e380d3b09e662f6debe9d787f3`, and its
distribution-manifest digest is
`sha256:60b63f41a220c95df0fb87abcb7bbca94f17f97da8c361350d1115539110e557`.
The human-authorized evidence ledger now records 80 satisfied, 5 explicitly
superseded, and 0 missing outcomes. On 2026-08-01, product owner and requirements
author `joey-orbyss` separately accepted that exact bounded candidate under
T095 after a final independent readiness audit returned READY. This accepts the
`explain`, `construct`, and `evaluate` foundation demonstrated by Feature 001;
it does not declare Program Kit generally released, multi-provider,
migration-ready, or complete.

Merge verification subsequently found that the accepted manifest had hashed
three NuGet lock files from a CRLF-projected authoring worktree even though the
repository requires canonical UTF-8/LF source bytes. Correction commit
`4d1c519fd5e788c36252437de03cb8c1ccb13c33` makes source provenance fail closed
on BOM, invalid UTF-8, or CR bytes and records the canonical source closure.
Commit `bed501be2db48cbf0c8f6ea9880fac9367820c73` removes a Windows-only SDK
restore-source assumption while preserving the exact governed-feed allowlist.
Candidate commit `c84335ee9eea4666fc69af5c2e49cbce821b8fbb` pins this clone to
LF-safe Git behavior and makes canonical index/worktree text a fail-fast local
and CI gate. Protected pull-request run `30720316337` passed the complete
vertical-slice workflow on Ubuntu and Windows. The corrected exact candidate's
distribution-manifest digest is
`sha256:25fd0146dcca3fe8b8d359a9a208e51504718eb978b95fde60570a33cd8ecebd`.
The prior T095 acceptance remains valid only for its exact historical binding.
On 2026-08-01, `joey-orbyss` explicitly accepted corrected candidate
`c84335ee9eea4666fc69af5c2e49cbce821b8fbb`, bound to the corrected manifest
digest above, under refreshed T095. This decision accepts the documented
bounded scope and limitations; it does not declare Program Kit generally
released, multi-provider, migration-ready, or complete.
The exact per-task audit is available in
[`specs/001-status-component-api/reviews/task-closure-audit.md`](specs/001-status-component-api/reviews/task-closure-audit.md).

## What is the Program Kit CLI?

Program Kit is a development-time semantic toolchain and software factory. It
accepts human-approved software definitions, resolves them against exact
contracts and supported capabilities, and constructs the plumbing,
projections, relationships, and integrations it can honestly guarantee.
Custom business behavior remains clearly bounded, human- or AI-authored, and
evaluated against its declared contract.

The CLI is the public, independently callable entrance to that factory. A human,
an automation system, Spec Kit, or another orchestrator should be able to submit
the same explicit operation request and receive the same kind of structured
resolution, evidence, diagnostics, and result.

Program Kit is not a new programming language, an autonomous product owner, a
universal source-code translator, or a runtime required by the software it
creates. Generated applications are ordinary software: developers can inspect,
build, test, run, and own them with the normal tools of their ecosystem.

## The problem we want to solve

AI-assisted software projects often carry their own disconnected instructions,
terminology, generation rules, and assumptions. That makes contribution
inconsistent, obscures architectural intent, and makes features difficult to
reuse or integrate safely across products.

Program Kit aims to provide a shared, model-neutral development protocol:
versioned software definitions, canonical contracts, explicit capability
selection, deterministic mechanics where determinism is supportable, and
evidence-backed explanations everywhere else. The goal is not merely to
generate code. The goal is to keep software legible to people and composable
through governed contracts as it grows.

## What it should offer

For architects, Program Kit should provide:

- a precise way to express software identity, capabilities, relationships,
  dependencies, policies, ownership, and constraints;
- an integration-resolution explanation before live artifacts are written;
- traceability from approved intent to contracts, selected implementations,
  generated artifacts, and evidence;
- clear outcomes when components integrate directly, require an explicit
  adapter or migration, or are provably incompatible; and
- stable semantic views for reviewing a system without pretending that source
  inspection, security review, debugging, or performance analysis is obsolete.

For developers, Program Kit should provide:

- one consistent CLI contract for mapping approved input, constructing a
  bounded result, and evaluating that result;
- reproducible generation of supported project plumbing and integrations;
- exact dependency, provider, tool, and contract selection instead of ambient
  discovery or hidden best guesses;
- actionable, machine-readable diagnostics that explain what failed, why it
  matters, and what kind of next action is valid; and
- consumer-owned output that continues to build, test, and run without Program
  Kit, Spec Kit, or an AI provider at runtime.

The first implementation is intentionally .NET-first. It proves the first
bounded model with a pinned .NET 10 construction profile while keeping contracts
free of unnecessary .NET-specific meaning.

## How we envision it being used

The intended workflow is collaborative and evidence-led:

1. People describe a software goal and the meaning that must be preserved.
2. Architects, developers, domain experts, and AI assistants refine that intent
   into reviewable definitions and contracts.
3. A human explicitly approves the identity-forming choices.
4. Program Kit resolves exact capabilities and explains the proposed
   construction or integration before it changes live consumer artifacts.
5. The CLI constructs only what falls inside its declared support envelope and
   preserves custom implementation as separately owned work.
6. Evaluation produces structured evidence and diagnostics, including honest
   unknown, unsupported, drifted, or incompatible outcomes.
7. The resulting application is built, tested, reviewed, and operated as
   ordinary software.

For teams that want a guided discovery, specification, planning, and task
workflow, Spec Kit is the recommended orchestrator. Program Kit v1 remains an
independent factory: it does not embed a second planning system and does not
depend on Spec Kit at runtime. A future thin adapter may hand an approved Spec
Kit plan to Program Kit through the same public CLI contracts available to any
other caller.

## Provider-neutral AI-session integration proof

The second executable proof adds a provider-neutral development-session
integration boundary without moving AI-session behavior into generated
applications or the factory kernel. `Orbyss.ProgramKit.Cli` is packed and
installed into each consumer workspace as an exact local .NET tool. The public
session lifecycle then supports `session explain`, `session install`, `session
verify`, and `session remove` through versioned structured requests and results.

Canonical session meaning, authority requirements, diagnostics, disclosure,
installation records, and conformance rules live outside provider adapters.
The first adapter projects that meaning into one Codex repository skill at
`.agents/skills/program-kit/SKILL.md`. The adapter does not launch Codex, edit
global provider configuration, add an MCP server, copy Program Kit source, or
make Codex part of the generated application's runtime. An opt-in review script
is the only repository harness allowed to launch a live Codex process, and its
ten-session evidence remains a separate human-owned acceptance gate.

Session effects require exact request-bound authority. Installation admits only
verified generated-owned projection bytes; verification is read-only; removal
uses the admitted record and refuses missing, drifted, or unproven targets.
Program Kit source workspaces are marked and deliberately reject consumer
session initialization, catalog, preflight, read, and removal operations. This
repository continues to use Spec Kit—not Program Kit's consumer capability—to
develop Program Kit itself.

This proof is intentionally not a general provider plugin framework, native
planning system, runtime agent harness, global Codex installer, migration
engine, or promise that arbitrary agent behavior is deterministic. The
provider-neutral contract and deterministic mechanics are automated; the live
session experience and semantic product approval remain explicit review gates.
Current evidence and pending gates are recorded in
[`specs/002-session-integration-proof/verification.md`](specs/002-session-integration-proof/verification.md).

## What can be exercised now

The repository pins .NET SDK `10.0.302`, restores from exact package versions,
and keeps the downloaded CShells dependency mirror outside version control.
Use the smallest verification tier that proves the current change:

```powershell
# Normal edit loop: unit feedback without restore or evidence regeneration
./eng/Invoke-Verification.ps1 -Mode Fast

# Public-contract changes: unit plus contract feedback
./eng/Invoke-Verification.ps1 -Mode Contract

# Once before a PR: locked restore, isolated build, unit/contract, changed-file hygiene
./eng/Invoke-Verification.ps1 -Mode PrePr
```

Protected CI owns the complete acceptance, conformance, deterministic-evidence,
and Windows/Linux proof. The full local
`./eng/Invoke-VerticalSliceQuickstart.ps1` remains available for release work,
CI diagnosis, or a change whose declared invalidation set requires it. Spec Kit
customization and upgrade safeguards are documented in
[`eng/SPECKIT.md`](eng/SPECKIT.md).

The public executable supports `explain`, `construct`, `evaluate`, `help`, and
`version`, plus the provider-neutral `session explain`, `session install`,
`session verify`, and `session remove` lifecycle. Run the isolated ten-workspace
package and lifecycle proof with:

```powershell
./eng/Invoke-SessionIntegrationQuickstart.ps1
```

The accepted first factory request fixture lives under
`tests/Fixtures/Reference.Status/Valid/`; it is evidence for the operation
model, not a declaration that Status is kernel meaning.

Known boundaries are explicit: only one first-party .NET profile is supported;
the validated first slice does not promise future provider or consumer-domain
coverage; recovery is intentionally limited; and external NuGet packages remain
correctly classified as verified-equivalent rather than canonical across
environments. Mirror integrity, package claims, canonical snapshots,
repeatability, deterministic provenance/SBOM, hostile-filesystem safety,
local-safety, and relocated-runtime evidence now pass. The evidence ledger is
reconciled. The corrected cross-platform merge candidate passed protected
Windows/Ubuntu verification and received refreshed T095 acceptance for its
exact binding. The
evidence and decision status are recorded in
[`specs/001-status-component-api/verification.md`](specs/001-status-component-api/verification.md)
and
[`specs/001-status-component-api/reviews/first-vertical-slice.md`](specs/001-status-component-api/reviews/first-vertical-slice.md).

## Why the implementation is starting again

The archived Program Kit implementation was developed using Program Kit's own
capabilities and governance model. That created a circular-authority defect: the
product being evaluated was also acting as the authority that defined how it
should be evaluated. Assumptions could reinforce themselves, and changing the
tool risked changing the rules used to justify the same change.

V1 removes that self-governing bootstrap loop. Program Kit itself is now
specified, planned, implemented, and reviewed with Spec Kit and the standard
.NET toolchain. Program Kit's own factory operations must never be a prerequisite
or source of authority for building Program Kit. Historical code may inform a
decision, but it cannot silently decide one.

This boundary is also important for users: Spec Kit governs how this repository
develops Program Kit, while Program Kit owns its eventual public factory
contracts. Neither tool is allowed to grant human authority or reinterpret
unknown intent on its own.

## V1 goals and objectives

Program Kit v1 is being designed to:

- keep human approval authoritative for product meaning and identity-forming
  decisions;
- make governed integration resolution the central product promise—never leave
  compatibility ambiguous or unsupported by actionable evidence;
- construct deterministic outputs only inside exact, pinned, declared support
  envelopes and make every weaker claim visible;
- provide portable, versioned software definitions that link intent, contracts,
  selections, dependencies, policies, artifacts, and evidence;
- establish clear ownership for consumer-authored, seeded, generated, and
  external artifacts;
- fail closed on ambiguous identities, providers, authority, ownership, or
  publication state;
- make diagnostics a stable public contract usable by both people and AI
  sessions; and
- prove the smallest complete vertical slice—including invalid paths,
  repeatability, drift, repair, integration explanation, and runtime
  independence—before broadening the product.

V1 deliberately does not promise autonomous invention or approval of semantics,
universal composability, arbitrary source-to-source conversion, hidden or
best-effort integration, multi-ecosystem implementation, a native roadmap or
task system, untrusted third-party execution, or self-hosting.

## Design with us

The design process is part of the product work, not a private step before it.
We want practitioners to challenge the vocabulary, authority boundaries,
developer experience, architectural usefulness, diagnostics, and first
vertical slice while those choices can still change.

Start with these current records:

- [Design convergence and decision ledger](DESIGN.md)
- [Product identity](DESIGN-PRODUCT-IDENTITY.md)
- [Program Kit Constitution](.specify/memory/constitution.md)
- [Spec Kit and Program Kit planning boundary](DESIGN-PLANNING.md)
- [First vertical slice](DESIGN-VERTICAL-SLICE.md)
- [First feature specification](specs/001-status-component-api/spec.md)

Questions, counterexamples, use cases, and pull requests are welcome. The most
useful contributions explain the real outcome a developer or architect needs,
the constraint Program Kit must preserve, and the evidence that would prove the
design works. You can begin through
[GitHub Issues](https://github.com/orbyss-io/program-kit/issues).

The destination is ambitious but concrete: software that AI can help build,
people can govern by intent, and teams can integrate without relying on hidden
assumptions.

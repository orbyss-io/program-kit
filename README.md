# Program Kit CLI

> **AI builds it. Human intent governs it.**

Program Kit is being redesigned as a human-governed, AI-provider-neutral .NET
software factory. Its CLI will turn approved intent into contract-bounded,
ordinary software through explicit construction and evaluation operations.

## Project status: v1 redesign in progress

The previous implementation has not been deleted. It is preserved on the
[`archive/pre-rebuild-2026-07-31`](https://github.com/orbyss-io/program-kit/tree/archive/pre-rebuild-2026-07-31)
branch so its code, tests, documentation, and hard-won lessons remain available
as prior art.

Active v1 design work is taking place on
[`codex/initialize-spec-kit`](https://github.com/orbyss-io/program-kit/tree/codex/initialize-spec-kit).
This branch deliberately contains design records and specifications before a
new implementation. The archived implementation is a historical reference,
not the authority for v1 behavior, and its commands and package surfaces should
not be read as promises for the redesigned product.

This pause is intentional. We want to design Program Kit v1 in the open, test
its foundations before they become code, and give developers, architects, and
other contributors a meaningful opportunity to shape the product.

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

The first implementation is intentionally .NET-first. It will prove the model
with a pinned .NET 10 construction profile while keeping the semantic contracts
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

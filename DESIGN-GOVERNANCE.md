---
artifact-kind: program-kit-design-category
category: governance-enforcement-and-self-hosting
status: active
last-updated: 2026-08-01
active-batch: GOV-B01
parent-ledger: DESIGN.md
---

# Program Kit Design — Governance, Enforcement, and Self-Hosting

## 1. Category objective

Define who may authorize identity-forming or effectful changes, how authority is
represented and verified, which invariants are executable, and how Program Kit
avoids recreating the circular self-dependency that caused this redesign.

The category preserves these accepted boundaries:

- the human product owner retains final authority over product intent
  (`DEC-003`, `DEC-005`);
- Program Kit is developed with Spec Kit and does not consume its own planning
  facilities (`DEC-002`, `DEC-029`);
- operation providers, session capabilities, installation, and diagnostic
  remedies never grant themselves authority (`DEC-031`, `DEC-033`, `DEC-038`);
- kernel integrity, admission, provenance, evidence freshness, and diagnostic
  truth are non-bypassable (`DEC-023`); and
- v1 executes only explicitly registered first-party operation providers
  (`DEC-033`).

## 2. Batch register

| Batch | Items | Status | Purpose |
|---|---|---|---|
| `GOV-B01` | `GOV-001`–`GOV-004` | `active` | Define the self-hosting boundary, human-required decisions, authority providers, and approval records. |
| `GOV-B02` | `GOV-005`–`GOV-009` | `queued` | Define gate suppression, executable versus review-only principles, and warning/error profiles. |
| `GOV-B03` | `GOV-010`–`GOV-012` | `queued` | Define initial security and supply-chain obligations, target framework, and justified foundational technologies. |

## 3. Active batch: Bootstrap independence and human authority

`GOV-B01` resolves:

- `GOV-001`: whether Program Kit may ever self-host again;
- `GOV-002`: what evidence is required before any future self-use;
- `GOV-003`: which decisions always require human authority; and
- `GOV-004`: what makes an approval authoritative to the kernel.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### GOV-001 — The kernel always retains an independent bootstrap path

**Recommendation:** Building, testing, repairing, and releasing the Program Kit
kernel and CLI must remain possible from repository source with the declared
standard .NET toolchain and Spec Kit development workflow, without executing
Program Kit against itself or trusting Program Kit-generated governance input.
The current redesign never self-hosts.

Program Kit may later exercise its published CLI against isolated examples,
fixtures, first-party extension packages, or other explicitly downstream
consumer surfaces. Such dogfooding is optional verification, runs after the
independent product is built, and cannot define the constitution, kernel
protocols, diagnostic catalog, gates, build graph, release authority, or source
needed to repair Program Kit.

No same-session rule change may generate or approve the evidence that declares
that rule valid. Program Kit source capability guidance is loaded before
capability authoring and is not refreshed by its own in-progress change.

### GOV-002 — Optional dogfooding requires evidence, not maturity claims

**Recommendation:** Optional downstream Program Kit dogfooding may begin only
after all of these are true:

- an independently built and published CLI exposes stable public operation and
  result contracts;
- a clean environment can build, test, and repair the product without the
  dogfood step or its generated outputs;
- the selected slice has reproducibility, drift, fail-closed publication,
  diagnostics, and conformance fixtures;
- failure or removal of the dogfood path cannot block product recovery or
  release;
- the dogfood subject cannot modify or approve the kernel rules evaluating it;
  and
- the human explicitly accepts the exact subject, purpose, version, and evidence
  boundary.

This threshold permits honest consumer-path testing but never promotes
foundational self-hosting. Reconsidering that stronger boundary would require a
new product decision, not gradual convenience-driven coupling.

### GOV-003 — Humans approve identity, authority, trust, and widened effects

**Recommendation:** A human decision is always required to establish or change:

- the constitution, product identity, kernel protocol, or non-bypassable
  invariant;
- canonical semantic identity or meaning, vocabulary authority, and intentional
  contract-breaking revisions;
- provider, profile, version, dependency, executable-trust, and resolution-lock
  selection unless an already approved exact policy makes the selection unique;
- governance policy, authority grants, exceptions, waivers, or gate suppression;
- artifact ownership reclassification or adoption of custom bytes as governed
  input;
- destructive, irreversible, external-publication, or materially widened
  effects; and
- product/package release or any future execution of third-party code.

An approved operation or policy may pre-authorize bounded deterministic
construction, evaluation, exact restoration, and publication within its scope.
Those actions do not need repetitive human confirmation when the kernel proves
that identity, authority, targets, and preconditions remain unchanged. AI may
prepare candidates and evidence but cannot make the identity-forming decision.

### GOV-004 — Authority is an exact scoped grant from a configured provider

**Recommendation:** The kernel consumes canonical authority-grant artifacts
issued through an explicitly configured authority provider. A grant declares at
least its immutable identity and revision, asserted issuer and role, exact
subjects, permitted operations and effect classes, request and lock bindings,
conditions, validity or expiry, revocation source, and provenance/evidence
references.

The requesting operation, provider, session capability, or AI cannot issue or
broaden the grant that authorizes itself. On every use, the kernel validates the
authority provider, grant digest, subject and operation scope, current
conditions, freshness, and revocation state. Prose in chat, instructions,
diagnostics, commit messages, or generated files is not kernel authority unless
an approved provider translates an explicit human action into the grant.

V1 may ship a repository-local human-approval provider whose records are
reviewable and version-controlled. It honestly proves the presence, exact
scope, and provenance assertion of a record, not the real-world identity of a
person cryptographically. Signed, pull-request-review, organizational-policy,
or hardware-backed providers may be added later through the same public
contract without changing kernel authority semantics.

### GOV-B01 delivery boundary

The first CLI needs one repository-local authority provider, one exact scoped
grant schema, positive and negative scope/freshness/revocation fixtures, and a
build test proving Program Kit remains independently buildable without invoking
itself.

V1 does not need cryptographic identity, an organization directory, remote
policy service, hardware keys, or self-hosted generation.

## 4. Revision record

- Created after Diagnostics and AI Guidance closed under `DEC-040`.
- Preserved the current Spec Kit development method and made independent
  bootstrap an architectural boundary rather than a temporary repository habit.
- Activated `GOV-B01` for self-hosting and human authority.

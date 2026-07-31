---
artifact-kind: program-kit-design-category
category: governance-enforcement-and-self-hosting
status: active
last-updated: 2026-08-01
active-batch: GOV-B02
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
| `GOV-B01` | `GOV-001`–`GOV-004` | `completed` | Define the self-hosting boundary, human-required decisions, authority providers, and approval records. |
| `GOV-B02` | `GOV-005`–`GOV-009` | `active` | Define gate suppression, executable versus review-only principles, and warning/error profiles. |
| `GOV-B03` | `GOV-010`–`GOV-012` | `queued` | Define initial security and supply-chain obligations, target framework, and justified foundational technologies. |

## 3. Accepted batch: Bootstrap independence and human authority

`GOV-B01` resolves:

- `GOV-001`: whether Program Kit may ever self-host again;
- `GOV-002`: what evidence is required before any future self-use;
- `GOV-003`: which decisions always require human authority; and
- `GOV-004`: what makes an approval authoritative to the kernel.

The human accepted all four recommendations. They are governed by
`DEC-041`.

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

## 4. Active batch: Gates, waivers, and enforcement modes

`GOV-B02` resolves:

- `GOV-005`: whether gates may ever be suppressed;
- `GOV-006`: the required shape and scope of any permitted exception;
- `GOV-007`: whether every constitutional principle must become executable;
- `GOV-008`: which obligations necessarily remain human review; and
- `GOV-009`: when warnings are allowed instead of blocking errors.

The following recommendations remain **unaccepted** until the human confirms or
revises them.

### GOV-005 — Kernel gates are never suppressible

**Recommendation:** Gate contracts declare applicability and one result status:
`passed`, `failed`, `not-applicable`, `waived`, or `not-evaluated`. Unknown or
unproven applicability fails closed. `not-evaluated` can never support
admission.

Kernel gates protecting schema and protocol integrity, identity uniqueness,
finite closure, exact resolution, authority, ownership and publication
preconditions, provenance, evidence applicability and freshness, diagnostic
truth, disclosure safety, and trusted-state atomicity are non-waivable. No CLI
flag, environment variable, profile, extension, provider, or administrative
role can turn their failure into admission.

Consumer or organization policy gates may be declared waivable by their owning
contract. A non-waivable gate cannot be changed by attaching a waiver; changing
its classification is a versioned authority-owned policy or protocol revision
subject to normal human approval.

### GOV-006 — A permitted exception is an exact waiver, never suppression

**Recommendation:** Program Kit has no global suppression, ignore list, or
`--force` bypass. A waivable policy violation may be admitted only through an
exact canonical waiver artifact declaring:

- waiver identity, revision, issuing authority grant, and provenance;
- exact gate and diagnostic IDs with their revisions;
- exact subjects, artifact revisions, operation/profile scope, and effect class;
- the accepted risk and rationale;
- required compensating controls and evidence;
- activation and finite expiry condition; and
- revocation source and replacement relation when applicable.

Wildcards, implicit inheritance, repository-wide scope by default, and
non-expiring waivers are invalid. The kernel revalidates scope, evidence,
freshness, expiry, and revocation on every use. A waiver is identity-forming and
belongs in the resolution lock and evaluation evidence.

A waived violation remains visible as `waived`; it is never rewritten as
`passed` or deleted from diagnostics. The operation may still have top-level
outcome `succeeded` under the selected policy, but admission and evidence state
must explicitly say that a waiver was used. Expiry affects future evaluation
and does not rewrite historical receipts.

### GOV-007 — Every principle declares an enforcement mode, not fake automation

**Recommendation:** Every constitutional or policy principle declares one
primary enforcement mode:

1. **executable invariant** — a mechanically decidable kernel or provider gate;
2. **evidence-backed obligation** — Program Kit validates required evidence,
   while an authorized party owns the underlying claim;
3. **human-review obligation** — judgment is recorded through an exact approval
   artifact; or
4. **explicit aspiration** — direction without a current admission claim,
   owner, or enforcement consequence.

Each principle also identifies its owner, subjects, applicability, required
evidence, failure disposition, and whether any policy waiver is permitted.
Mechanically decidable parts should be automated, but Program Kit never claims
that every constitutional concern can or must become code. Aspirations cannot
be cited as passed gates or conformance evidence.

### GOV-008 — Human review owns fitness and accepted risk

**Recommendation:** Human review remains necessary for product intent and
semantic adequacy, architecture and trade-off fitness, user-impact judgment,
threat and privacy risk acceptance, exception rationale and compensating
controls, and final release readiness where the selected release policy
requires it.

Program Kit validates that the exact review record exists, applies to the exact
subject and revision, came through an accepted authority provider, answers the
required review schema, and remains fresh. It does not present reviewer
competence, attentiveness, or the truth of a judgment as mechanically proven.
Human review cannot override a non-waivable kernel gate.

### GOV-009 — Severity is profile-owned; mandatory failure remains blocking

**Recommendation:** Severity, gate status, outcome, and admission are separate.
A warning is allowed only for a non-blocking observation or a visibly waived
policy violation under the exact selected governance profile. A mandatory
applicable gate that fails or is not evaluated produces `blocked` or
`needs-input`, never a warning selected by a convenience switch.

Governance profiles are exact, versioned, digested, selected, and locked. They
may promote an advisory warning to a blocker and may define policy-gate
applicability or waivability. They cannot downgrade kernel gates or diagnostic
disclosure. Profile change is identity-forming and requires the applicable
authority.

### GOV-B02 delivery boundary

The first CLI needs a gate-result schema, one non-waivable kernel gate, one
waivable policy gate, an exact waiver schema, one evidence-backed obligation,
one human-review record, and fixtures proving expiry, revocation, scope
mismatch, unknown applicability, and profile downgrade refusal.

V1 does not need a general policy language, remote policy engine, waiver
dashboard, or automatic risk scoring.

## 5. Revision record

- Created after Diagnostics and AI Guidance closed under `DEC-040`.
- Preserved the current Spec Kit development method and made independent
  bootstrap an architectural boundary rather than a temporary repository habit.
- Activated `GOV-B01` for self-hosting and human authority.
- The human accepted `GOV-B01` in full under `DEC-041`.
- Required permanent independent bootstrap, allowed only non-authoritative
  downstream dogfooding after explicit evidence, and kept identity, trust,
  policy, ownership, widened effects, and release under human authority.
- Defined exact scoped grants from configured providers while recording the
  honest non-cryptographic limit of the v1 repository-local provider.
- Completed `GOV-B01` and activated `GOV-B02` for gates, waivers, enforcement
  modes, human review, and warnings.

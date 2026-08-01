---
artifact-kind: program-kit-design-category
category: governance-enforcement-and-self-hosting
status: closed
last-updated: 2026-08-01
active-batch: none
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
| `GOV-B02` | `GOV-005`–`GOV-009` | `completed` | Define gate suppression, executable versus review-only principles, and warning/error profiles. |
| `GOV-B03` | `GOV-010`–`GOV-012` | `completed` | Define initial security and supply-chain obligations, target framework, and justified foundational technologies. |

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

## 4. Accepted batch: Gates, waivers, and enforcement modes

`GOV-B02` resolves:

- `GOV-005`: whether gates may ever be suppressed;
- `GOV-006`: the required shape and scope of any permitted exception;
- `GOV-007`: whether every constitutional principle must become executable;
- `GOV-008`: which obligations necessarily remain human review; and
- `GOV-009`: when warnings are allowed instead of blocking errors.

The human accepted all five recommendations. They are governed by
`DEC-042`.

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

## 5. Accepted batch: Security floor and technology foundations

`GOV-B03` resolves:

- `GOV-010`: which security, privacy, supply-chain, provenance, signing, and
  SBOM obligations belong in the initial constitution;
- `GOV-011`: whether .NET 10 remains the initial target; and
- `GOV-012`: which technologies are justified foundations and which remain
  target-provider or future-slice choices.

The human accepted all three recommendations. They are governed by
`DEC-043`.

### GOV-010 — V1 has a concrete local-first security and supply-chain floor

**Recommendation:** The initial constitution makes these obligations mandatory
for the Program Kit CLI and every shipped first-party executable operation
provider:

- no secret value enters source, canonical artifacts, locks, diagnostics,
  provenance, SBOMs, test fixtures, or ordinary logs;
- no telemetry, source upload, or network access occurs by default; every
  external process, network source, credential use, and filesystem effect is
  declared, bounded, authorized, and evidenced;
- direct and transitive dependencies, package sources, toolchain, templates,
  and build inputs are exact, locked, and attributable; locked restore fails on
  drift or an unapproved source;
- release evidence records the source revision, exact SDK and tools,
  construction identity, dependency locks, provider and catalog digests, test
  and gate results, and every released artifact digest;
- dependency vulnerability and license evaluation use identified scanner and
  database revisions; unavailable or stale analysis is reported as unavailable
  or stale, never as clean, and policy violations block unless the exact policy
  gate permits and receives an approved waiver; and
- every released Program Kit CLI and first-party executable-provider package
  includes a deterministic SBOM using one exact selected standard and revision.
  Consumer-product SBOM generation is a target-profile capability and is
  mandatory only when that selected profile requires it.

V1 makes no cryptographic-signing claim. Released artifacts, provenance, and
SBOMs carry exact digests and explicitly state their unsigned or externally
attested posture. Package signing, key custody, organizational identity, and
transparency-log policy require a later authority design; Program Kit must not
invent a local signing scheme that implies trust it cannot prove.

Security evidence is identity- and freshness-bound. Updating a vulnerability
database, dependency, SDK patch, or policy produces new evidence rather than
rewriting an earlier receipt. The security floor does not create a runtime
monitoring or telemetry product.

### GOV-011 — Target .NET 10 LTS, with an exact deliberately updated SDK

**Recommendation:** The Program Kit kernel, CLI, first-party .NET providers, and
initial generated .NET profile target `net10.0` and the stable C# language
version shipped with the selected SDK. Preview language and runtime features
are prohibited in the release profile.

The repository pins one exact supported .NET 10 SDK patch in `global.json`
without ambient roll-forward. Patch updates are explicit reviewed dependency
changes that regenerate build and security evidence. The design pins the .NET
10 product line rather than hard-coding today's patch forever.

As verified on 2026-08-01, Microsoft's
[official support policy](https://dotnet.microsoft.com/en-us/platform/support/policy)
lists .NET 10 as active LTS through 2028-11-14. Approaching support end, a
platform withdrawal, or an incompatible required capability triggers a new
human-approved target decision. Program Kit never silently retargets generated
consumer products.

### GOV-012 — Technologies have bounded roles; the kernel stays small

**Recommendation:** V1 accepts these technology roles:

- the .NET 10 SDK, BCL, and stable C# are the kernel and CLI implementation
  platform;
- `System.Text.Json` is the in-process JSON parser and serializer, with Program
  Kit-owned canonicalization rules rather than reliance on serializer defaults;
- JSON Schema is the public structural schema format for JSON operation and
  artifact boundaries, but it does not replace the typed semantic model,
  kernel invariants, or executable conformance;
- NuGet is the exact delivery mechanism for Program Kit, CShells, and
  first-party .NET provider code, using central version management and locked
  restore from declared sources; and
- standard SDK-style MSBuild and `dotnet` commands build, test, pack, and expose
  declared external-tool evidence. Custom tasks or targets are not kernel
  extension mechanisms.

Roslyn is accepted only inside exact first-party .NET construction or
evaluation providers that require syntax, symbol, analyzer, or code-fix
evidence. It does not define portable semantics and need not be a kernel
dependency. Its package and compiler versions, inputs, diagnostics mapping, and
support profile are exact.

Source generators, custom MSBuild tasks/targets, runtime weaving, reflection
discovery, and compile-time hidden generation are not required by the first
CLI. Prefer explicit materialized construction artifacts with manifests and
drift evidence. A later vertical slice may justify one of these technologies
through an exact operation contract without making it a universal foundation.
Program Kit may eventually generate a source-generator project as consumer
output without relying on source generators to implement its own kernel.

No CLI framework, dependency-injection container, test framework, schema
library, analyzer framework, or SBOM library becomes constitutional merely by
being convenient. The implementation plan selects the smallest exact package
that satisfies an accepted contract and records provenance, determinism,
diagnostic adaptation, update policy, and an exit path.

### GOV-B03 delivery boundary

The first CLI needs an exact `global.json`, central and locked NuGet versions,
declared package sources, standard SDK-style build/test/pack, canonical JSON and
published schemas, provenance and SBOM output for released executable
artifacts, and security-evidence freshness diagnostics. Roslyn is added only if
the first vertical slice selects source-level C# evaluation.

V1 does not need package signing, telemetry, remote policy, custom MSBuild
tasks, source generators, or a blanket dependency framework.

## 6. Revision record

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
- The human accepted `GOV-B02` in full under `DEC-042`.
- Made integrity gates non-waivable, replaced suppression with exact finite
  policy waivers, and required every principle to declare executable,
  evidence-backed, human-review, or aspirational enforcement.
- Kept judgment and accepted risk under human review and made warnings
  subordinate to exact locked profiles that cannot downgrade kernel gates.
- Completed `GOV-B02` and activated final Governance batch `GOV-B03` for the
  security, supply-chain, framework, and technology floor.
- The human accepted `GOV-B03` under `DEC-043`.
- Established the local-first security and supply-chain floor, selected .NET 10
  LTS with explicit SDK patch updates, and gave JSON Schema, NuGet, MSBuild, and
  Roslyn bounded roles without adopting hidden generation or package signing.
- Closed Governance, Enforcement, and Self-Hosting with all twelve questions
  resolved.
- Activated the First Vertical Slice category.

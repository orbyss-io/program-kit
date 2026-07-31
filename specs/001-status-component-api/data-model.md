# Data Model: Status Component and API Vertical Slice

## Purpose

This model defines the governed records needed to explain, construct, evaluate,
publish, and inspect the first Program Kit vertical slice. It describes
contractual state, not implementation classes. All canonical records are
immutable values identified by schema version and SHA-256 digest.

## Model-wide rules

- Every canonical document declares one exact schema identity.
- Every governed identity is authority-qualified and resolves to one immutable
  revision plus content digest.
- References point to authoritative records; views do not duplicate or redefine
  their meaning.
- Canonical paths are slash-separated, repository-relative logical paths. Drive
  letters, roots, backtracking segments, and protected absolute paths are
  invalid.
- Canonical collections declare whether order is meaningful. Set-like
  collections are emitted in contract-defined identity order.
- Unknown values are absent or represented by an explicit closed state; they
  are never guessed.
- Secret values are never model fields. Secure external references may be
  modeled only when a selected contract requires them; this slice requires none.
- Human-readable prose is a projection from stable message or explanation
  keys. Automation consumes identities, enums, and typed values.

## Identity primitives

### GovernedIdentity

Uniquely identifies governed meaning or implementation.

| Field | Meaning | Rules |
|---|---|---|
| `authority` | Namespace owner | Non-empty canonical URI-like identifier |
| `kind` | Contract-owned identity kind | Closed per protocol revision |
| `name` | Authority-local name | Non-empty; no path inference |
| `revision` | Immutable semantic or implementation revision | Exact; never a range or `latest` |
| `digest` | Content identity | SHA-256 over canonical bytes |

Two records with the same authority, kind, name, and revision but different
digests are an integrity conflict, not alternative versions.

### ArtifactReference

Points to an exact available artifact.

| Field | Meaning | Rules |
|---|---|---|
| `identity` | Governed artifact identity | Exact `GovernedIdentity` |
| `mediaType` | Declared representation | Exact supported media type |
| `logicalPath` | Workspace-relative locator | Normalized slash path |
| `digest` | Referenced bytes | SHA-256 |
| `ownership` | Mutation boundary | `generated-owned`, `seeded-handoff`, or `consumer-owned` |

The digest proves identity only while the bytes remain resolvable. Missing bytes
make current reproduction or evaluation unavailable without rewriting history.

### TraceReference

Connects a derived claim to its authority.

| Field | Meaning |
|---|---|
| `source` | Exact `ArtifactReference` containing authoritative material |
| `pointer` | Stable document-relative pointer |
| `claimKind` | Contract-defined kind of claim |

Trace references do not grant authority and cannot turn a view into source truth.

## Authoring and semantic records

### SoftwareDefinitionBundle

The portable unit submitted to Program Kit.

| Field | Meaning | Validation |
|---|---|---|
| `schema` | Bundle schema identity | Exactly `program-kit.software-definition-bundle/v1` |
| `identity` | Bundle identity | Kind is `component-bundle` or `application-bundle` |
| `semanticRecords` | Linked consumer-owned meaning | At least one exact reference |
| `implementationRecords` | Linked source or implementation inputs | Explicit ownership and digest |
| `relationships` | Separately owned assertions | Exact endpoints and contract type |
| `profiles` | Requested contract/target/evaluation profiles | Exact identities |
| `selections` | Human-approved provider and capability choices | Exact; no ranges |
| `dispositions` | Explicit handling of optional/unsupported material | Closed values with trace |

The reference slice has two bundles:

- `Reference.Status`: a component bundle with a consumer-owned Status contract,
  consumer-owned custom behavior, and selected .NET host-participation profile.
- `Reference.Status.Api`: an application bundle that requires the exact Status
  contract/package and contributes one declared status endpoint to one selected
  host assembler.

### RelationshipAssertion

A separately owned immutable relationship between governed endpoints.

| Field | Meaning |
|---|---|
| `identity` | Assertion's own authority-qualified identity |
| `from` / `to` | Exact endpoint identities |
| `contract` | Exact relationship contract |
| `cardinality` | Contract-defined cardinality |
| `order` | Explicit only when semantic; otherwise absent |
| `mapping` | Exact mapping/adapter reference when applicable |
| `trace` | Source of the approved assertion |

An assertion cannot rewrite either endpoint. Content conflict fails integrity;
meaning conflict resolves only as direct, explicitly adapted, or incompatible.

### FactoryRequest

The public, stateless invocation contract.

| Field | Meaning | Rules |
|---|---|---|
| `schema` | Request schema | Exactly `program-kit.factory-request/v1` |
| `operation` | Requested public behavior | `explain`, `construct`, or `evaluate` |
| `constructionMode` | Construction intent | `new` or `repair`; present only for `construct` |
| `rootBundle` | Exact operation root | One `ArtifactReference` |
| `workspaceIdentity` | Logical workspace identity | Never the host absolute path |
| `requestedEffect` | Maximum effect | `none`, `candidate-only`, or `commit` |
| `selections` | Exact profiles/providers/capabilities | Complete, pinned, approved |
| `authorityGrant` | Exact grant reference | Required for candidate or commit effects |
| `expectedState` | Optimistic publication precondition | Closure/state digest when effects are possible |

The CLI receives the physical workspace path separately for location only. It is
normalized out of canonical semantics and cannot change output bytes.

### AuthorityGrant

An exact authorization claim from a configured provider.

| Field | Meaning |
|---|---|
| `identity` | Immutable grant identity |
| `issuerAssertion` | What the provider asserts about the issuer |
| `subjects` | Exact governed subjects |
| `operations` | Allowed operations |
| `effects` | Maximum allowed effects |
| `requestBinding` | Exact request digest when bound |
| `lockBinding` | Exact resolution-lock digest when known |
| `conditions` | Contract-owned finite conditions |
| `validity` | Explicit validity/freshness limits |
| `revocation` | Revalidation reference |
| `provenance` | Exact origin record |

V1's repository-local provider proves record presence and asserted provenance,
not cryptographic human identity.

## Resolution and explanation records

### ProviderManifest

The semantic authority for one first-party executable provider.

| Field | Meaning |
|---|---|
| `identity` | Provider semantic identity and revision |
| `distribution` | Exact package identity, version, digest, and source |
| `roles` | Subset of `intake-mapping`, `construction`, `evaluation` |
| `contracts` | Exact supported operation contracts |
| `profiles` | Exact contract, target, and reproducibility profiles |
| `inputs` / `outputs` | Typed accepted and produced records |
| `contributionSeams` | Exact seams used or owned |
| `diagnosticCatalog` | Exact catalog identity and digest |
| `conformanceEvidence` | Exact fixture/evidence references |
| `effects` | Declared process, filesystem, tool, and network effects |

Installation or discovery does not select or authorize the provider.

### ResolutionLock

The immutable complete operation closure.

| Field | Meaning |
|---|---|
| `schema` | Exactly `program-kit.resolution-lock/v1` |
| `identity` | Lock identity and digest |
| `requestDigest` | Canonical request digest |
| `rootBundle` | Exact resolved root |
| `resolvedItems` | Canonically ordered exact identities and digests |
| `relationships` | Resolved assertion identities and dispositions |
| `providers` | Exact role/provider selections |
| `profiles` | Exact protocol, target, evaluation, and reproducibility profiles |
| `toolchain` | Exact SDK/tools and declared environment inputs |
| `policies` | Exact governance profile and waivers |
| `closureDigest` | Digest over the complete canonical closure |
| `constructionIdentity` | Digest over every output-affecting input, when complete |

Zero or multiple valid selections prevent lock issuance. A lock never contains a
range, best match, implicit fallback, or ambiently discovered choice.

### IntegrationResolutionExplanation

The first architect-visible product value.

| Field | Meaning |
|---|---|
| `schema` | Exactly `program-kit.integration-resolution-explanation/v1` |
| `requestDigest` / `lockDigest` | Exact subject closure |
| `root` | Explained bundle |
| `semanticCoverage` | Declared, custom-bounded, unsupported, and unknown areas |
| `relationships` | Direct, adapted, or incompatible result with causes |
| `selections` | Exact providers/profiles and why they apply |
| `seams` | Contribution/assembler ownership and conflict rules |
| `artifactPlan` | Planned artifacts and ownership |
| `gates` | Applicable gate expectations and current status |
| `waivers` | Visible exact policy waivers |
| `evidence` | Existing and required proof |
| `blockers` | Precise unresolved conditions |
| `trace` | Source for every governed claim |

It is a reproducible explanation, not an impact graph, migration plan, source
analysis, runtime model, or global semantic truth.

## Construction and artifact records

### CandidateArtifactSet

A complete isolated proposal before live publication.

| Field | Meaning |
|---|---|
| `constructionIdentity` | Exact lock-derived identity |
| `rootBundle` | Operation root |
| `candidateRoot` | Non-semantic isolated location |
| `artifacts` | Canonically ordered manifest entries |
| `preconditions` | Expected live ownership/state/collision observations |
| `gateResults` | Complete mandatory applicable results |
| `setDigest` | Digest over canonical manifest and Program Kit-owned bytes |
| `state` | Candidate lifecycle state |

Each artifact entry records logical path, ownership, media type, content digest,
producer identity, canonical claim class, and authoritative source references.

### Artifact-set lifecycle

```text
draft
  -> sealed
  -> evaluated
  -> publication-prepared
  -> publishing
  -> published-unadmitted
  -> admitted

Any state before publishing -> rejected
publishing or published-unadmitted -> interrupted or recovery-required
```

- Only `admitted` has a valid admission/publication receipt.
- `interrupted` and `recovery-required` are explicit and untrusted even when physical
  writes succeeded.
- Recovery or repair starts a new authorized construction request; it does not
  resume through hidden process state.

### PublicationJournal

A durable, recoverable account of planned and observed live writes.

| Field | Meaning |
|---|---|
| `constructionIdentity` | Candidate being published |
| `expectedLiveState` | Precondition digest |
| `operations` | Canonically ordered create/replace actions and safe backups |
| `completedOperations` | Durable completed-step identities |
| `observedState` | Verified live state after interruption or completion |
| `state` | `prepared`, `publishing`, `committed`, or `incomplete` |

The journal supports honest recovery; it does not make multi-file filesystem
mutation physically atomic.

### AdmissionPublicationReceipt

Historical evidence for a complete set.

| Field | Meaning |
|---|---|
| `schema` | Exactly `program-kit.construction-receipt/v1` |
| `constructionIdentity` | Exact construction claim |
| `lockDigest` | Exact resolution lock |
| `artifactSetDigest` | Complete published manifest |
| `gateResults` | Exact mandatory applicable evidence |
| `publicationState` | Must be `admitted` |
| `observedLiveState` | Post-publication verification digest |
| `claimClasses` | Canonical-byte, verified-equivalent, or custom-bounded per artifact |
| `support` | Freshness and retention policy references |

The locally packed component package is an external-tool output. It has an exact
digest within a run and is evaluated under its named verifier; it is not called
byte-canonical unless the pinned toolchain fixture proves that stronger claim.

## Evaluation, diagnostics, and continuation

### GateResult

| Field | Meaning |
|---|---|
| `gate` | Exact gate identity/revision |
| `mode` | `executable-invariant`, `evidence-backed`, or `human-review` |
| `status` | `passed`, `failed`, `not-applicable`, `waived`, or `not-evaluated` |
| `subjects` | Exact evaluated subjects |
| `evidence` | Exact evidence references |
| `waiver` | Exact finite waiver when status is `waived` |
| `diagnostics` | Findings supporting the status |

Kernel gates cannot be waived. Unknown applicability becomes `not-evaluated`
and blocks admission.

### OperationResult

The authoritative result of every recoverable public command path.

| Field | Meaning | Closed values |
|---|---|---|
| `schema` | Result schema | `program-kit.operation-result/v1` |
| `operation` | Public operation | `explain`, `construct`, `evaluate` |
| `requestIdentity` | Available request digest | Exact or absent when unavailable |
| `constructionIdentity` | Available construction identity | Exact or absent |
| `outcome` | Top-level result | `succeeded`, `needs-input`, `blocked`, `cancelled`, `faulted` |
| `phase` | Furthest completed/attempted phase | Protocol-defined closed enum |
| `effect` | Proven live effect | `none`, `candidate-only`, `committed`, `indeterminate` |
| `disposition` | Primary caller guidance | `complete`, `retry`, `provide-input`, `request-approval`, `repair`, `revise`, `stop` |
| `artifacts` / `receipts` / `evidence` | Exact available outputs | Canonically ordered |
| `diagnostics` | Complete diagnostic collection or bounded view | Never hides outcome causes |
| `continuation` | Stateless needs-input continuation | Present only when applicable |

There is no partial-success or unknown outcome. `succeeded` requires complete
bytes and a `complete` disposition.

### Diagnostic

| Field | Meaning |
|---|---|
| `id` | Permanent authority-qualified diagnostic ID |
| `catalog` | Exact catalog identity, revision, and digest |
| `severity` | `info`, `warning`, `error`, or `fatal` |
| `category` | `request`, `semantic`, `resolution`, `policy`, `conformance`, `workspace`, `external`, or `internal` |
| `phase` | Furthest applicable operation phase |
| `occurrenceKey` | Stable duplicate-grouping key |
| `subjects` | Typed affected subjects/locations |
| `rule` | Violated contract/rule/profile |
| `messageKey` / `parameters` | Safe renderable content |
| `cause` / `consequence` | Bounded typed explanation |
| `expected` / `observed` | Safe classified values |
| `remediations` | Typed proposals |
| `evidence` / `documentation` | Offline-resolvable exact references |

Diagnostic trigger and violated-invariant meaning never change for an ID.

### Remediation

| Field | Meaning |
|---|---|
| `kind` | Closed remediation kind |
| `targets` | Exact bounded subjects |
| `preconditions` | State, freshness, and ownership requirements |
| `effectClass` | Maximum proposed effect |
| `authorityRequired` | Exact required grant characteristics |
| `request` | Structured command arguments, request artifact, or digested patch |
| `postconditions` | Verifiable expected result |
| `retryPhase` | Safe phase from which a new operation may begin |

A remediation proposes action; it never authorizes or executes itself.

### Continuation

| Field | Meaning |
|---|---|
| `schema` | Exactly `program-kit.continuation/v1` |
| `requestDigest` | Original canonical request |
| `completedWork` | Exact reusable work and evidence |
| `missingInputs` | All independently known typed needs |
| `choices` | Exact supported choices without ambient selection |
| `authority` | Required approval/grant |
| `lock` / `workspace` / `evidence` | Freshness bindings |
| `digest` | Complete continuation identity |

Resume is a new stateless operation that revalidates every binding.

## Workspace view

### WorkspaceSnapshot

A generated-owned canonical projection written to
`.program-kit/workspace.snapshot.json`.

| Field | Meaning |
|---|---|
| `schema` | Exactly `program-kit.workspace-snapshot/v1` |
| `rootBundle` | One exact root |
| `closureDigest` | Finite resolved operation closure |
| `evidenceDigest` | Applicable evidence set |
| `constructionIdentity` | Current construction when available |
| `identities` | Exact governed subjects |
| `semanticCoverage` | Declared/custom/unknown states with trace |
| `bindings` / `selections` | Exact contracts, providers, profiles, versions |
| `relationships` / `seams` | Resolved graph and composition ownership |
| `artifacts` | Logical path, ownership, producer, digest, claim class |
| `provenance` | Exact sources and providers |
| `gates` / `reviews` / `waivers` | Governance state |
| `evidence` / `receipts` | Exact proof and historical claims |
| `support` / `retention` | Availability and freshness |
| `diagnosticState` | Unresolved, drifted, unavailable, incomplete, or redacted state |
| `trace` | Authority for every governed claim |

The snapshot is current only when its closure and evidence digests match a fresh
evaluation. It guides new sessions to authoritative records and source; it does
not become a global graph or infer runtime behavior.

## Reference integration relationships

```text
Reference.Status.Api
  requires exact Status contract
  consumes exact local Reference.Status package
  selects exact first-party .NET host assembler

Reference.Status
  owns Status semantics and custom behavior
  realizes exact Status contract
  contributes exact host-participation feature

Status endpoint contribution
  is immutable
  targets one exact assembler
  declares route/cardinality/order identity
```

Direct integration succeeds only when every identity, contract, package digest,
profile, provider, seam rule, authority, and mandatory gate resolves exactly.

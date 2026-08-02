# Data Model: Program Kit Adapter for Spec Kit

**Feature**: `003-speckit-adapter`

**Canonical machine profile**: `program-kit.canonical-json/v1`

**Human authoring projection**: restricted YAML where explicitly stated

This model separates installation, compatibility, selection, activation, and
authority. Relationships never imply a later state.

## 1. DistributionBinding

Exact identity of the workspace-local Program Kit CLI selected by the consumer.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | Exact distribution-binding schema |
| `packageId` | string | Exactly `Orbyss.ProgramKit.Cli` in V1 |
| `packageVersion` | revision | Exactly `1.0.0-alpha.2` in V1 |
| `commandName` | string | Exactly `program-kit` |
| `invocationKind` | enum | `dotnet-tool-manifest`; test-only evidence may identify `tool-path` |
| `toolManifest` | logical path | `.config/dotnet-tools.json`; regular file inside workspace |
| `reportedVersion` | revision | Must equal package version |
| `packageDigest` | digest | Observed exact acquired package bytes |
| `executableDigest` | digest | Observed invoked executable bytes |
| `runtimeProfile` | governed identity | Exact net10 runtime profile |
| `distribution` | governed identity | Exact compiled distribution identity |

Validation rejects PATH fallback, version ranges, mismatched reported version,
missing package bytes, symlink/junction escape, or an executable outside the
declared workspace-local tool installation.

## 2. WorkspaceInitializationRequest

Explicit bounded request to seed absent neutral Program Kit workspace state.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.workspace-init-request/v1` |
| `canonicalProfile` | identity | Exact canonical JSON profile |
| `workspaceIdentity` | governed identity | Exact consumer workspace subject |
| `distributionBinding` | `DistributionBinding` | Must match invoked CLI |
| `requestedBy` | safe value | Human or authorized-agent declaration; never authority for later operations |
| `requestedEffect` | enum | Exactly `bootstrap-absent-files` |
| `manifestPath` | logical path | Exactly `program-kit.yaml` in V1 |
| `lockPath` | logical path | Exactly `program-kit.lock.json` in V1 |

The request contains no profile, provider activation, grant, package source,
factory operation, or network instruction.

## 3. WorkspaceManifest

Consumer-owned requested composition. It is created only when absent by
initialization as a seeded handoff and becomes consumer-owned immediately.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.workspace/v1` |
| `distribution` | exact package selection | Must equal invoked distribution |
| `factory.selections` | array of `NamedProfileSelection` | Zero or more; aliases and identities unique under ordinal comparison |
| `factory.defaultSelection` | optional alias | Must name exactly one declared selection |

### NamedProfileSelection

| Field | Type | Rules |
|---|---|---|
| `alias` | identifier | Lowercase stable repository identity; no wildcard |
| `provider` | governed identity | Exact installed first-party provider |
| `targetProfile` | governed identity | Exact target profile supported by provider |
| `selectionAuthority` | trace reference | Explicit human/repository policy source |

V1 accepts an empty selection set or exact
`dotnet10-cshells-0.0.28@1.0.0`. It rejects ranges, best matches, duplicate
aliases, unregistered providers, and a default without a selection.

## 4. DistributionCatalog

Read-only inventory generated from the exact invoked distribution descriptor.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.distribution-catalog/v1` |
| `distributionBinding` | reference | Exact observed binding |
| `providers` | array of `CatalogEntry` | Stable order by governed identity |
| `schemas` | identity/digest collection | Exact public schema catalog |
| `diagnosticCatalogs` | artifact references | Exact kernel/provider catalogs |
| `canonicalProfiles` | identity/digest collection | Exact supported profiles |
| `evidence` | evidence references | Packaged support/conformance evidence |
| `digest` | digest | Canonical bytes of complete inventory |

### CatalogEntry

Includes exact provider identity, profile identities, supported roles, input and
output kinds, effects, processes, contracts, support status, provenance, and
conformance evidence. It has no selected/activated/authorized flag because
catalog presence means only **available**.

## 5. WorkspaceRestoreRequest

Explicit request to validate a manifest and materialize its exact lock.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.workspace-restore-request/v1` |
| `workspaceIdentity` | governed identity | Exact workspace |
| `distributionBinding` | reference | Must match invoked CLI and manifest |
| `manifest` | artifact reference | Regular `program-kit.yaml` inside workspace |
| `lockPath` | logical path | Exactly `program-kit.lock.json` in V1 |
| `mode` | enum | `base` or `factory` |
| `allowedSources` | artifact references | Empty in V1 normal operation; any acquisition source must be explicit |

`base` permits zero selections. `factory` requires at least one exact supported
selection and resolves every referenced item.

## 6. WorkspaceResolutionLock

Program Kit-generated accepted exact resolution.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.workspace-lock/v1` |
| `workspaceIdentity` | governed identity | Exact workspace |
| `distributionBinding` | full binding | Exact package/executable release |
| `manifestDigest` | digest | Canonical admitted manifest |
| `mode` | enum | `base` or `factory` |
| `resolvedItems` | array | Package, provider, profile, contract, schema, catalog, dependency, evidence |
| `selections` | array | Exact resolved named selections; empty is valid only for base |
| `defaultSelection` | optional alias | Resolved manifest default |
| `unresolvedItems` | array | Unavailable, unsupported, ambiguous, or incomplete items |
| `closureDigest` | digest | Complete canonical closure |
| `evidence` | array | Current exact support/conformance evidence |
| `digest` | digest | Canonical lock bytes |

A lock is current only while distribution, manifest, selected identities,
contracts, dependencies, catalogs, and retained evidence named by the closure
remain exact. Unrelated repository bytes do not affect it.

## 7. AdapterCompatibilityManifest

Immutable release-owned compatibility boundary shipped in the extension.

| Field | Type | V1 value/rule |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-adapter-compatibility/v1` |
| `adapter` | release identity | `orbyss-program-kit-adapter@0.1.0` |
| `specKitVersions` | exact array | Only `0.15.1` |
| `programKitVersions` | exact array | Only `1.0.0-alpha.2` |
| `runtimeProfiles` | exact array | net10.0 runtime identity |
| `providerProfiles` | exact array | First-party .NET + `dotnet10-cshells-0.0.28@1.0.0` |
| `contractBindings` | identity/digest map | Every consumed Program Kit/adapter schema and canonical profile |
| `commandBindings` | exact map | Adapter command to supported Program Kit command/result version |
| `translationProfile` | exact closed binding | Definition family/schema/media types, bundle/request/result schemas, provider identity, and target-profile identity used by V1 translation |
| `platforms` | exact array | Windows and Linux |
| `releaseArtifacts` | artifact references | Executable, schemas, instructions, diagnostic catalog |
| `digest` | digest | Canonical manifest bytes |

No installed file probing may invent an identity absent from this manifest or a
public Program Kit preparation result.

## 8. AdapterProjectConfig

Repository-owned consumer configuration at exactly
`.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`.
The adjacent `.local.yml` layer and environment layers are non-semantic for
this adapter. The extension ships the adjacent
`orbyss-program-kit-adapter-config.template.yml`; that template remains
extension-owned while the instantiated project file is consumer-owned.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-adapter-config/v1` |
| `programKit.invocation` | enum | Exactly `dotnet-tool-manifest` |
| `programKit.manifest` | logical path | `program-kit.yaml` |
| `programKit.lock` | logical path | `program-kit.lock.json` |
| `activation.defaultMode` | enum | `off`, `assist`, `required`; recommended `assist` |
| `activation.features` | map | Exact feature key to `FeatureOverride` |
| `defaultRequestedEffect` | enum | `none`, `candidate-only`, `committed`; default `none` |

### FeatureOverride

| Field | Type | Rules |
|---|---|---|
| `mode` | enum | `off`, `assist`, `required` |
| `applicability` | enum | `applicable`, `disabled`, `not-applicable`, `unresolved` |
| `selection` | optional alias | Allowed only when applicable; exact lock entry |
| `decisionSource` | trace | Explicit repository/human decision |

Activation-mode resolution is exact feature override, project default mode,
then `off`. After applicability resolves true, profile resolution is exact
feature selection override, then `defaultSelection` from the current Program
Kit workspace lock. There is no adapter-owned profile default.

## 9. FeatureHandoff

Small reviewed projection from approved Spec Kit meaning into one supported
Program Kit definition family. Authored as restricted YAML; admitted as
canonical JSON. It is seeded-handoff on first creation and then consumer-owned.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-handoff/v1` |
| `feature` | identity/logical root | Exact feature key and `specs/<feature>` root |
| `intentOwner` | safe identity | Named human/accountable role |
| `sources` | artifact observations | spec, plan, tasks where applicable; whole bytes are provenance only |
| `applicability` | decision | Exact state and source |
| `effectiveSelection` | selection binding | Required only when applicable; explicit/inherited source |
| `definitionFamily` | governed identity | Exact provider-supported family |
| `definition` | object | Explicit provider-specific supported fields |
| `implementation` | artifact bindings | Consumer-owned custom implementation references |
| `requestedOperation` | enum | Initially construct/evaluate journey |
| `maximumEffect` | enum | `none`, `candidate-only`, `committed` |
| `ownership` | array | Generated versus consumer-owned choices |
| `trace` | array of `TraceBinding` | Exactly one source for every output-affecting field |
| `unresolved` | array | Must be empty for translation |
| `unsupported` | array | Must be empty for translation |
| `deferred` | array | Explicitly excluded from current generation |
| `excluded` | array | Explicit non-factory meaning |

The handoff cannot contain a grant, issuer, authority decision, secret, absolute
path, raw exception, or executable remediation.

## 10. TraceBinding

Deterministic link from one handoff/output field to its approved source.

| Field | Type | Rules |
|---|---|---|
| `targetPointer` | JSON Pointer | One identity/output-affecting handoff field |
| `sourceKind` | enum | `spec-block`, `plan-decision`, `task-row`, `human-decision`, `compatibility-fixed` |
| `sourceArtifact` | optional artifact reference | Required for file-backed source |
| `sourceAnchor` | identifier | Unique `FR-NNN`, `SC-NNN`, named decision, or `TNNN` |
| `observedValue` | canonical JSON value | Exact human-approved projected value |
| `sourceBlockDigest` | digest | Canonical normalized named block |
| `mappingAuthority` | reference | Handoff review or fixed compatibility authority |

Missing/duplicate anchor or changed block digest stales only the target pointer
and generated outputs whose declared inputs include it.

## 11. HandoffReview

Human evidence binding one exact handoff; never a Program Kit grant.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-handoff-review/v1` |
| `handoff` | artifact reference | Exact handoff digest |
| `reviewer` | safe identity | Named human |
| `decision` | enum | `approved` or `rejected` |
| `reviewedFields` | JSON Pointer array | Must cover every identity/output-affecting field for approval |
| `limitations` | safe values | Explicit unsupported/deferred/excluded meaning |
| `recordedAt` | declared instant | Provenance only; not determinism input |
| `digest` | digest | Canonical review record |

Any handoff byte edit makes the review stale. Source edits are evaluated through
the handoff's field-level trace.

## 12. AdapterRequest

Canonical input to the deterministic adapter executable.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-adapter-request/v1` |
| `operation` | enum | `doctor`, `activate`, `disable`, `handoff`, `validate`, `prepare`, `explain`, `construct`, `evaluate`, `cleanup` |
| `workspace` | governed identity/logical root | Exact consumer workspace |
| `feature` | optional feature identity | Required for feature operations |
| `config` | artifact reference | Exact project config |
| `handoff` | optional artifact reference | Required after proposal where applicable |
| `review` | optional artifact reference | Required for effect-bearing translation |
| `grant` | optional artifact reference | Required only for explicit construct; exactly supplied by caller |
| `requestedEffect` | enum | Cannot exceed handoff maximum |
| `outputRoot` | logical path | Exact feature-local adapter-owned root |

The request cannot contain credentials, environment substitutions, shell
commands, implicit defaults, or multiple candidate grants.

## 13. AdapterGeneratedManifest

Exact ownership and invalidation record for adapter-generated feature files.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-adapter-manifest/v1` |
| `adapterRelease` | release identity | Exact extension/executable |
| `compatibility` | artifact reference | Exact compatibility manifest |
| `feature` | identity | Exact feature |
| `inputs` | artifact/trace references | Declared semantic, implementation, profile, schema inputs |
| `outputs` | artifact references | Every generated definition/request/result |
| `ownership` | enum per output | Adapter-generated-owned only |
| `invalidationSets` | map | Claim/output to exact inputs |
| `digest` | digest | Canonical complete manifest |

Cleanup may remove only outputs whose current digest equals this manifest.

## 14. PreparationRequest and PreparationProposal

### PreparationRequest

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.preparation-request/v1` |
| `rootBundle` | artifact reference | Exact software-definition bundle |
| `workspaceIdentity` | governed identity | Exact workspace |
| `constructionMode` | enum | `new` or `repair` |
| `desiredEffect` | enum | `candidate-only` or `committed` |
| `selections` | exact selections | Must match current factory lock |
| `evaluationContext` | declared context | Same honesty rules as factory request |
| `expectedLock` | artifact reference | Current exact workspace lock |

### PreparationProposal

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.preparation-proposal/v1` |
| `requestBinding` | digest | Canonical preparation request plus relevant closure |
| `closureDigest` | digest | Resolved prospective construction closure |
| `liveStateDigest` | digest | Current observed live state |
| `subjects` | governed identity array | Exact construction subjects |
| `operation` | enum | `construct` |
| `constructionMode` | enum | Exact requested mode |
| `maximumEffect` | enum | Exact requested ceiling |
| `explanation` | public explanation | Complete resolution/gate/blocker data |
| `authorityRequirements` | typed requirements | Required issuer/scope/effect/conditions |
| `ungrantedProjection` | typed object | Complete prospective request excluding grant |
| `evidence` | references | Exact inputs/live-state observations |
| `digest` | digest | Canonical proposal artifact |

Preparation writes neither candidate nor live product state.

## 15. HumanAuthorityDecisionRecord

Consumer-owned explicit decision supplied to the repository authority provider.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.authority-decision-record/v1` |
| `proposal` | artifact reference | Exact current preparation proposal |
| `reviewer` | safe identity | Human-declared identity; no cryptographic claim |
| `decision` | enum | `approve` or `deny` |
| `subjects` | governed identities | Must exactly equal or narrow proposal subjects |
| `operations` | enum array | Only proposed operation |
| `effects` | enum array | Equal to or narrower than proposal ceiling |
| `conditions` | typed array | Exact bounded conditions |
| `validity` | finite interval | No unbounded grant |
| `provenance` | artifact reference | Exact reviewed record/source |
| `recordedAt` | declared instant | Provenance, not proof of identity |

## 16. AuthorityRecordRequest and result

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.authority-record-request/v1` |
| `proposal` | artifact reference | Current exact proposal |
| `decision` | artifact reference | Current exact human decision |
| `grantPath` | logical path | New repository authority record path |
| `revocationPath` | logical path | New/reviewable revocation path |

The result references either an exact seeded-handoff grant/revocation pair or a
structured refusal with no partial authority file.

## 17. AdapterResult

Versioned result from every adapter operation.

| Field | Type | Rules |
|---|---|---|
| `schema` | identity | `program-kit.spec-kit-adapter-result/v1` |
| `canonicalProfile` | identity | Exact canonical JSON profile |
| `operation` | enum | Exact adapter operation |
| `adapterRelease` | release identity | Exact executing extension/binary |
| `compatibility` | status/bindings | Compatible, incompatible, stale, not-evaluated |
| `outcome` | enum | `succeeded`, `not-applicable`, `needs-input`, `blocked`, `cancelled`, `faulted` |
| `furthestStage` | enum | `request`, `compatibility`, `applicability`, `handoff`, `translation`, `invocation`, `publication`, `completion` |
| `effectState` | enum | `none`, `adapter-files-only`, `program-kit-candidate`, `program-kit-committed`, `indeterminate` |
| `primaryDisposition` | enum | Complete/retry/provide-input/request-approval/repair/revise/stop |
| `artifacts` | references | Adapter-owned or referenced artifacts |
| `diagnostics` | typed view | Adapter catalog identities only |
| `disclosure` | typed entries | Exact withheld/visible decisions |
| `programKitResult` | optional JSON document | Exact unmodified schema-valid Program Kit result |

## 18. State transitions

### Workspace/distribution state

```text
absent
  -> installed       (exact local CLI bytes acquired)
  -> available       (catalog recognizes exact packaged support)
  -> selected        (consumer manifest + accepted current lock)
  -> activated       (one applicable request names selection)
  -> authorized      (one current exact external grant matches request)
```

No transition is automatic. Base initialization may stop at available with zero
selected profiles.

### Feature adapter state

```text
unresolved
  -> disabled | not-applicable | applicable
applicable
  -> handoff-proposed
  -> handoff-reviewed
  -> translated
  -> prepared
  -> authority-required
  -> grant-supplied
  -> constructed
  -> evaluated
```

Any changed traced semantic value stales `handoff-reviewed` and its downstream
closure. Changed custom implementation bytes stale translation/preparation and
downstream evidence, not unrelated semantic choices. Disablement stops future
participation but preserves all historical states/artifacts.

### Adapter publication state

```text
staged -> validated -> published
   |          |
   +------> refused/interrupted (untrusted, recoverable, never admitted)
```

Only complete adapter-owned sets become published. Program Kit product
publication remains governed by the existing kernel journal/admission model.

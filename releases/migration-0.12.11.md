# Program Kit 0.12.11

This patch adds reusable Foundation BFF/Keycloak and EF/PostgreSQL compositions,
corrects feature lifecycle ownership, and packages the selected runtime roots.
It installs scoped verification and operation-sized task guidance together,
while preserving application ownership, exact consumer locks and historical
evidence. Installing this patch does not migrate an existing application's data
or adopt different Foundation packages.

## Feature-owned lifecycle and selected-root packaging

Features own service registration and lifecycle contributions. Provider preparation
precedes dependent policy admission and managed workers through the selected
Foundation lifecycle. An aggregate Composition library needs a concrete selection
or reuse responsibility; it is not required for initialization ordering. Consumers
use the unchanged published Foundation host rather than adding a host executable.

Build and stage the current selected package roots and their exact runtime closure.
For a pure library, select its package identity explicitly with
`Build.ps1 -RootPackage <PackageId>`. Fresh pack inventory excludes stale or
unselected packages, test probes and engineering dependencies. Deselecting a
customized scaffold preserves its source/project group and physical architecture
classification while removing its selected roots and managed runtime activations.
Untouched scaffolds can retire; review application-owned solution references.
Managed/configuration conflicts remain failures requiring scoped repair.

## Reusable compositions and configuration

Select `foundation-bff-keycloak` or `foundation-bff-keycloak-postgresql` from the
installed .NET composition templates. Declare the actual runtime directory,
application feature projects, package roots and native test adapter in
`eng/foundation-composition.json`. Nested runtime layouts and independent features
remain supported. The explicit selection uses the existing sync mechanism.

Configure the application origin, identity realm, callback/logout routes, client
and audience together. Keep the public identity issuer separate from private
discovery, backchannel and administration addresses. Supply credentials through
the declared deployment providers. Typed operational settings have authoritative
defaults, relational checks, precedence and lifecycle semantics. Owner-defined
protocol routes and compatibility policies are not arbitrary configuration knobs.
In the selected BFF, `/api` paths use 401/403 authentication errors; other paths
use browser redirects. Assert the initial response in native tests.

Use the generated `docs/architecture/foundation-configuration.md` reference and
Mermaid ownership/flow diagram. `python eng/foundation_composition.py --repository
. --effective` displays redacted configured-source attribution. Read it alongside
the maintained runtime inspector's actual activated typed values, owner DLL hashes
and provider observations. A flattened native memory provider cannot reconstruct
the original host JSON/environment order; neither view supplies missing observed
owners. Do not include secrets in either view.

## Readiness, scoped verification and product acceptance

Materialization, platform readiness and product acceptance remain distinct.
Inspect maintained setup without starting services, or use
`python eng/foundation_setup.py --repository . --status` to inspect the latest
outcome and its input/evidence freshness. Explicit setup execution exercises the
maintained authentication/provider checks. Mutable services require fresh checks
beside the operation that depends on them. Default readiness does not deploy
application schemas or run a product operation. The disposable fixture envelope
uses Development loopback origins and an owned private Docker alias; production
TLS/proxy and existing identity provisioning need actual deployment checks.

Installed tasks and implementation instructions schedule enabling work beside
the first relevant product operation rather than restoring a blanket foundation
phase. Preserve application-specific ownership, transaction, conflict, replay and
recovery tests. Reuse maintained native xUnit/MTP reporting with `--native-report
xunit-trx`; empty, duplicate, skipped or failed cases cannot establish a pass.
Changed relevant inputs, a newer failure or interruption invalidate reusable
evidence. A toolkit check alone never establishes application acceptance.

Scoped verification retains original failures and only reuses evidence for
unchanged inputs. For replaced test projects, record the existing
`testOwnershipReplacements` mapping in `eng/verification.json` and run fresh,
unfiltered successor regressions. Browser durability checks establish the exact
server draft identity/version/content before restart and authenticated readiness
before inspecting recovery, while keeping diagnostics free of payloads.

## Migration, verification and recovery

Checkpoint the consumer's source and preserve failed attempts. Install this
release through the maintained resumable updater; review its plan before applying
affected changes. Retain accepted architecture, task IDs, completed work, captured
dependency profiles, native locks, custom configuration and data. Repair affected
lifecycle/packaging/verification responsibilities in place. Existing supported
dependency selections remain valid; adopt an exact qualified Foundation profile
only through the existing reviewed dependency transition and its native checks.

Provider connectivity and lifetimes remain provider-owned. Application schema,
transaction contents and outcome mapping remain application/deployment-owned.
Do not introduce uncontrolled startup migrations. Prove conflict handling,
retained synthetic data and restart in a disposable reproduction before a separate
live rollout. Reconcile production Keycloak client/scope/theme desired state through
the identity owner; initial synthetic realm import is not a production update path.
Git or toolkit recovery cannot roll back externally deployed services or databases.

Retry the same verified updater after fixing a reported failure; preserve its
sealed original inputs and failed evidence. Do not delete installations, historical
profiles or consumer artifacts to manufacture a pass. Local Windows qualification
uses Chromium/WebKit because of the documented Firefox host limitation; CI retains
Firefox. Publication still requires dependency maintenance, fresh local Release
evidence and the complete tagged Release workflow. Public composition/default
availability follows actual Foundation publication and exact qualification.

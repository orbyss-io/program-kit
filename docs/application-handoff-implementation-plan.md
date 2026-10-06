# Application handoff implementation plan

Date: 2026-10-06. W1, W2, W4 and W5 implemented and validated; W3 has a demonstrated
application-owned metadata path and remains incomplete for publisher-owned framework coverage.
See [execution journal](application-handoff-execution-journal.md) for source boundaries, recovery,
implementation details, validation evidence and the concrete upstream dependency.

Deliver the application-owned outputs needed by infrastructure, documentation and integration
receivers. Those receivers choose their own infrastructure and publishing workflows. Complete the
native producers, maintained human inputs and receiver assembly so the consumer remains usable
after removing AI tooling.

Read the [design](application-handoff-design.md),
[inventory](application-handoff-inventory.md) and
[illustrative example](application-handoff-example.md) with this plan. The example is fictional;
its paths and behavior are not proof of implemented outputs.

## Working directory and source boundary

Continue in the existing worktree:

`C:\Users\tech_\.codex\worktrees\human-infrastructure-handoff\program-kit`

Branch: `codex/human-infrastructure-handoff`.
Inventory baseline: `087290b7d3fc3f6abf5b2460e94b1d3af367ec31`.

Read `AGENTS.md`, inspect current status and preserve the saved planning files and any subsequent
changes. The original checkout at `C:\Users\tech_\Code\program-kit` contains separate uncommitted
Foundation-contract work; do not edit it, switch its branch or import its dirty files. Compare
committed upstream changes if coordination becomes necessary and record the chosen source state.

This plan scopes implementation to Program Kit and disposable fixtures. Foundation source may be
inspected for real descriptor/settings interfaces, but changes in Foundation or real consumers
require separate authorization. Do not migrate De Zaaglijst. Record concrete external dependencies
and complete unaffected work rather than inventing upstream APIs.

## Product boundary

Produce application identities, packages/bundles/assets, applicable Dockerfiles or image references,
existing feature descriptors, configuration/API contracts, runtime/data requirements and human
documentation inputs. Include only applicable, implemented outputs.

Infrastructure directories, Bicep/Terraform modules, cloud adapters, provisioning, production
orchestration and documentation publishing systems are outside scope. Local Compose can remain an
application run/example input. Keep it explicitly local and do not promote fixture credentials or
topology into production requirements.

Foundation consumers retain the existing application bundle and separately published host image
model. Do not introduce consumer Foundation host images, another feature registry, duplicated
configuration defaults or an approval ledger.

## Work packages

Implement in dependency order. Update this plan's progress and keep a separate concise execution
journal with decisions, changed inputs, check results and any unresolved external dependency.

### W1 Stable application identity and input contract

- [x] Identify existing application/component identity inputs and preserve package, feature, shell
      and OpenAPI identities. Distinguish product identity from authentication settings.
- [x] Add one consumer-owned declaration for the stable application ID and references needed for
      receiver assembly. Prefer a small native `eng/` input; finalize its name/schema against the
      fixture and document that choice. It references authorities and never copies setting values
      or feature definitions.
- [x] Feed the explicit application ID into the existing bundle descriptor instead of deriving it
      from the checkout directory. Preserve readable historical descriptors. For existing
      consumers, offer a clear migration/diagnostic and retain historical meaning; do not silently
      rename applications or rewrite old releases.
- [x] Define component-to-artifact/contract bindings without assuming each API, feature, shell or
      bounded context is a separate deployed process.

Completion: explicitly selected identity survives folder renaming; ambiguous/missing identity is
diagnosed according to the documented migration policy; old descriptors remain readable.

Primary targets: `eng/release_bundle.py`, `eng/application-bundle.schema.json`, native input/schema,
template ownership and `tests/validate_release_bundle.py`.

### W2 Human documentation and application requirements

- [x] Scaffold a small consumer-owned product guide, ordinary build/run instructions and review
      scenarios. Use existing documentation where appropriate; preserve consumer customization.
- [x] Provide conventions for purpose, terminology, roles, delivered capabilities, inputs, expected
      outcomes, failures and prerequisites. Link actual public contracts and meaningful tests.
- [x] Provide application-owned runtime/data requirements: dependency capabilities, protocols,
      read-only/writable paths, startup/shutdown, implemented health surfaces and applicable migration
      artifact/invocation/compatibility constraints.
- [x] Reuse `eng/README.md`, existing authored explanations and compiler XML documentation. Planned
      architecture/specifications do not establish delivered behavior. Avoid boilerplate that claims
      absent features or invented commands.
- [x] Route applicable planning/task/implementation/delivery guidance to maintain affected outputs
      with normal feature changes. No approval fingerprints or lifecycle history prerequisites.

Completion: fixture readers can explain and follow delivered behavior with ordinary tools and no
agent history. Authored guides/configuration remain consumer-owned through sync/upgrade.

Primary targets: .NET templates and `managed-files.json`, `dotnet_sync.py`, applicable governance
references/guidance, scaffold/upgrade regression fixtures.

### W3 Supported settings contracts

- [x] Inspect actual Foundation/profile configuration declarations and available metadata/export
      interfaces. Select supported mechanisms; do not guess APIs.
- [x] Define the export/assembly contract for setting paths, owner/scope, type, requiredness, supported
      defaults/constraints, secret classification, binding/precedence and restart/reload behavior.
      Include semantic explanations and cross-setting constraints when structural schemas cannot
      express them.
- [ ] Reuse the selected SPA-PKCE schema where applicable. Export framework-owned metadata from its
      owning producer and application-owned metadata from source-backed consumer declarations.
      Do not infer a complete contract from configuration sample values.
- [x] Ensure metadata export does not open storage, contact identity services or run application
      initialization. Exclude secret values from exports, examples and assembled outputs.
- [x] If an upstream exporter is missing, implement the native assembly seam and demonstrate the
      consumer-owned path. Record the exact missing upstream contract; do not claim complete
      framework settings coverage or mark this work package complete until coverage is real.

Completion: settings metadata matches actual fixture validation/defaults/scope and remains
independent of runtime initialization. Missing metadata is explicit, with no fabricated coverage.

Status: **partial, upstream dependency open**. `settings-metadata.schema.json` and the native
assembler implement source-bound application metadata with explicit owner/scope requirements,
secret exclusion and conflict/staleness checks. The real fixture exporter shares its typed defaults
and range declarations with actual validation, without application initialization. The selected
SPA-PKCE structural schema is reused when present. Required missing scopes still prevent ready output. The separately authorized Foundation
follow-on now implements source-candidate Build 0.2.0 settings companion schema 1. Program Kit
binds the actual selected nupkg ID/version/hash and its compiled assembly, without interpreting
publisher source paths as consumer paths. Real locally packed JsonProfileSettings metadata
matches compiled defaults and admission and is consumed outside the toolkit. This complete
named-type scope does not cover host, CShells/Nuplane, authentication, Json.AspNetCore binding
or other option owners; W3 therefore remains partial. No unpublished version enters selection.

### W4 Receiver index and assembly

- [x] Add an ordinary `eng/` producer for an index and reproducible receiver output under ignored
      `artifacts/handoff/`. Finalize its minimal schema after mapping existing authorities in W1.
- [x] Reference the existing application bundle descriptor/checksum, actual package feature
      descriptors, host image digest, registered API contracts, settings metadata, human guides and
      applicable runtime/migration/asset outputs.
- [x] Bind to actual application identity/version/source and artifact hashes. Keep release-specific
      integrity separate from authored requirements and defaults.
- [x] Support multiple components/APIs and multiple features in one package. Use explicit applicable
      categories and referenced inputs so omission cannot be mistaken for completeness.
- [x] Fail clearly for required missing/stale/conflicting outputs, identity mismatch and unresolved
      references. Do not label draft inventories ready for receivers.
- [x] Validate safe contained paths and archive entries. Select files deliberately; do not package
      arbitrary repository contents, agent state, credentials or development secret values.
- [x] Keep the existing runtime bundle format unchanged for the host. The receiver archive/index
      accompanies it; ordinary tools can consume the output.

Completion: an independent receiver can locate and verify every applicable output without toolkit
installation or source-side caches. The index is navigation/integrity metadata, not another registry.

### W5 Ordinary engineering and complete delivery

- [x] Integrate handoff generation into documented native engineering at the point real inputs
      exist. Stage and final release description remain distinct; exports cannot imply that staging
      alone is a completed release.
- [x] Remove the consumer release workflow's dependency on the installed extension's
      `public_availability.py` and catalog by making the required verification implementation and
      selected inputs ordinary retained engineering assets.
- [x] Reuse the existing `eng/building-blocks.lock.json` and actual source/version selections.
      Inspect dependent imports/profile selection before relocating code. Do not create divergent
      verifiers or a second selection authority.
- [x] Preserve public availability, exact host digest, component checks, package closure,
      compatibility, attestation and publication ordering. Do not delete or weaken a gate to make
      toolkit removal succeed.
- [x] Include applicable receiver outputs in existing CI/release artifact delivery and document
      which generated outputs are runtime bundles versus receiver handoffs.

Completion: native handoff production and the consumer release verification path remain viable
after toolkit removal, with all existing substantive checks retained. No publication is performed
during this implementation task.

## Acceptance fixture and checks

- [x] Use a small disposable application with real delivered behavior, two registered API contracts
      and explicit component/artifact bindings. Exercise multiple features per package; do not
      assume two APIs require two processes.
- [x] Include real typed settings validation/defaults, safe runtime requirements and human examples.
      Add migration inputs only when the fixture actually has persistence.
- [x] Verify identity under checkout rename and historical descriptor compatibility.
- [x] Reject missing/tampered/stale artifacts, mismatched identities, unresolved references and
      secret-bearing receiver inputs. Check deterministic output and supported path/archive handling.
- [x] Compare settings export to actual application validation. Exercise documentation run/review
      steps and reject claims for unimplemented behavior.
- [x] In a disposable copy, remove installed AI extensions/integration instructions, engine state and
      caches while retaining ordinary engineering/configuration/source. Build, test, generate
      contracts, package and assemble the handoff through retained commands.
- [x] Consume the receiver output outside the source/toolkit installation. Verify references/hashes
      and read the human inputs with ordinary tools.
- [x] Verify public-availability failure and wrong host-image selection still reject release after
      relocation. Do not contact registries with credentials in fixtures when mocks/local feeds
      establish the harness contract.
- [x] Add targeted validators and update `tests/validation-inventory.json` with meaningful input
      ownership/dependencies. Run affected bundle/schema, scaffold/upgrade, OpenAPI,
      standalone-engineering and normal-development checks as applicable.
- [x] Run bounded Development:
      `./scripts/Test-ProgramKit.ps1 -BrowserEngines 'chromium,webkit'`.
      Keep Firefox in CI; the local Windows Firefox launch limitation is known.

Baseline evidence from this session: 15 release-bundle tests passed and generated-contract schema
validation passed. Re-run relevant checks after implementation; these results do not validate new
handoff behavior. Preserve logs and report exact coverage/limitations.

## Implemented outputs and exact acceptance scope

- Consumer-owned `eng/application-handoff.json`: explicit stable application identity; component
  bindings to existing package IDs/API registry identities; category applicability and required
  setting owner/scopes. Historical descriptors remain readable; migration retains the released ID.
- Managed native `handoff_contract.py`, `application_handoff.py`, `verify_handoff.py`, format schemas
  and ordinary engineering instructions. Descriptor/package/closure/API hashes, source freshness,
  registered and publisher-required API coverage, contained archive paths and secrets are checked.
  Index/ZIP/checksum are ignored outputs under artifacts/handoff/, alongside the unchanged host bundle.
- Consumer-owned documentation/run/review/runtime scaffolds; normal feature guidance maintains
  affected inputs. Native contract-path OpenAPI registries survive the legacy inline migration.
- Retained exact selected catalog and canonical public-availability verifier under eng/, rendered
  from the existing dependency-profile authority. Existing lock, availability, exact host, closure,
  compatibility, repository verification, attestation and publication ordering remain enforced.
- Release assembles/attests/distributes the receiver outputs. CI uploads source/contract inputs;
  these inputs and staging alone are not labeled complete release handoffs.

Acceptance uses a real stateless Python HTTP application with two precise source-generated contracts
and shared typed settings, plus a separately compiled .NET library for native restore/build/test/
contract-mode/package/assembly after removing toolkit state. Offline package descriptors and pipeline
receipts in the HTTP assembly fixture are synthetic seam fixtures, not evidence of Foundation
publisher emission, exporter execution or host activation of that Python application. Existing
managed-source/OpenAPI initialization/normalization/negative and bundle/closure checks were exercised
separately. Metadata completeness and exhaustive interface registration still need owning-producer
and application review; no live Foundation/multi-API runtime or full framework settings acceptance
is claimed. The .NET removal fixture correctly generates an incomplete handoff for missing framework
metadata; the standalone application-owned fixture qualifies ready assembly and independent reading.

Initial completion checks: 9 handoff tests and 15 bundle tests pass; schema, scaffold, native build contract,
availability, exporter-upgrade, dependency-profile and targeted OpenAPI/feature-closure checks pass.
Final bounded Development passes all 70 checks with the requested chromium,webkit
configuration. Evidence: `artifacts/handoff-validation/` and
`artifacts/validation-runs/20261006T103312Z-d43c382c/journal.json`. This is Development evidence,
not a Release receipt, browser integration qualification or paid-worker authorization. Firefox stays
in CI under the known Windows host limitation. The initial targeted failures and corrections are
preserved and explained in the execution journal.

The user subsequently accepted the companion recommendation after requesting the initial
implementation push (4ed712f). Foundation follow-on uses an isolated source checkout at main
ab22740d9bc86f01d3220751182cdcfcef9104ef on codex/settings-metadata-companion, coordinated with
the concurrent contract owner by explicit user authorization. Its schemas/emitter preserve
FeatureDescriptor v1/v2 meanings. Settings type/defaults are read from a deliberately bounded
Roslyn syntax subset; owning semantics bind the exact reviewed source inventory. Compilation
binds the assembly hash, and no-build packing cannot refresh stale provenance. The first real
owner declaration covers JsonProfileSettings code construction only. Build candidate 0.2.0 is
independently versioned; neither it nor the changed runtime package has been published here.

Follow-on acceptance: 10 handoff tests and all 70 bounded Development checks pass with
chromium,webkit. Targeted schema/scaffold/native build contract and actual publisher schema/
package/assembly integration pass; independent receiver uses Python -I outside source/toolkit.
Evidence: artifacts/handoff-validation/settings-development-final.log and
artifacts/validation-runs/20261006T112456Z-4e2da65f/journal.json. The initial 69/70 run correctly
required the new managed schema to be staged; its failure and rerun remain preserved. Foundation
source candidate is pushed at 0cd7947f9c8b3624c72929b9feb67afddd8ae772. W3 remains partial.

Next required action: review/integrate this source candidate with the authoritative Foundation
owner, qualify metadata declarations for the remaining applicable configuration scopes, and
publish through that owner's existing gates before changing Program Kit dependency selections.
Dynamic defaults, nested/partial/inherited/constructed settings and nonprimitive option graphs
need an independently qualified owning producer; this task does not infer or hand-copy defaults.
Host/CShells/Nuplane ownership remains explicit and requires their supported contracts. Original
checkouts, real consumers and concurrent dirty runtime work remain untouched.

## Completion and execution boundaries

Implementation is complete when applicable receiver outputs are maintained, generated and
independently usable; existing descriptors/contracts and release checks remain authoritative;
upgrade preserves consumer work; and targeted plus bounded Development validation pass.

If a real upstream metadata dependency prevents full completion, record its exact API/source owner,
affected outputs and demonstrated partial coverage. Do not mark that work complete or quietly lower
the requirement.

Read and follow repository instructions for all actions. No paid workers, interactive intake,
bootstrap orchestration, package/site publication, stable tags or complete Release suite are
authorized by this plan. Release preparation remains a later explicit user decision with the
human-terminal rule in `AGENTS.md`.

At handoff back to the user, report implemented packages, validation, remaining external dependencies
and the next required action. Keep the plan and execution journal current on this feature branch.
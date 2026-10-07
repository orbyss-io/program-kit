# Application handoff design

Draft for the feature branch. Program Kit's delivery is an application that humans can maintain,
together with the application-owned outputs other people need to do their work. Infrastructure
teams receive artifacts and runtime contracts. Documentation teams receive product behavior,
interfaces and verified examples. These receivers choose their own tools and processes.

Program Kit owns the completeness and correctness of its application handoff. Infrastructure
design, provisioning, cloud modules, deployment orchestration and documentation-team publishing
workflows belong to the receivers. No infrastructure directory or cloud adapter is part of this
feature. Dockerfiles and local Compose inputs are application deliverables when applicable; they
do not require Program Kit to model a production environment.

This increment defines the output boundary and examples. Templates, exports and packaging changes
remain implementation work. Existing foundations are the
[consumer engineering boundary](consumer-engineering.md) and
[application bundle profile](../extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md).

## Outputs supplied by the application

| Output | Content | Receiver use |
| --- | --- | --- |
| Application identity | Stable application/component identities, release version and source revision | Identify what is being documented or deployed |
| Build and release artifacts | Application packages/bundles, static assets, applicable Dockerfiles or immutable image references, hashes and build entry points | Build, retrieve and run the delivered software |
| Feature descriptors | Existing feature identities, dependencies, routes and activation metadata | Understand and select the packaged capabilities |
| Configuration contracts | Setting names, types, defaults, validation, scope, secret requirements and supported binding mechanisms | Supply valid configuration and explain supported settings |
| Interface contracts | OpenAPI and other implemented public interface/event contracts | Integrate with the application and produce reference documentation |
| Runtime requirements | Required dependencies/capabilities, ports, files, writable state, startup/shutdown and implemented health behavior | Determine what the application needs from its execution environment |
| Data change artifacts | Applicable migrations, their entry points and compatibility constraints | Incorporate application-owned data changes into the receiver's process |
| Human documentation inputs | Purpose, capabilities, user journeys, roles, terminology, runnable examples and review scenarios | Maintain human guides, tutorials and product documentation |

Only emit applicable outputs. A library does not automatically need Docker or a database. An
unimplemented capability remains clearly identified as planned. Outputs describe delivered
software and its requirements; they do not select compute services, network topology, secret
stores, resource sizing policies or a production identity/database installation.

Application identity and authentication requirements are separate concerns. Give each application,
runtime component, package and feature its existing identity where relevant. Authentication outputs
describe the application's accepted issuer/client/role requirements without inventing production
realm values, credentials or provider administration procedures.

## Preserve existing authorities

Feature descriptors already come from `Orbyss.Foundation.Build` during packaging, at
`orbyss-foundation/feature.json`. The handoff exposes those descriptors rather than defining a
second feature registry. `shells.json` retains application activation selections.

The Foundation consumer profile already produces an `application-bundle.zip` with
`application-bundle.json` and runs against a separately published, digest-pinned host image. Supply
that bundle and the image identity. A consumer Dockerfile is applicable only when its selected
application profile actually builds an image. This feature does not introduce a derived Foundation
host image or change the existing host ownership contract.

Retain `hostsettings.json`, `shells.json` and `nuplane.settings.json` as consumer-owned inputs.
Export configuration metadata from typed declarations/validation wherever possible. Each setting
needs its scope, accepted values, supported default, requiredness, secret classification and
restart/reload behavior. Describe actual binding/precedence rules. Do not duplicate defaults across
code and prose, or export secret values. Exporting metadata must not initialize application storage
or contact external services.

Multiple APIs can have separate artifacts and configuration or share a runtime. A feature, shell,
bounded context or package is not automatically a separate deployed service. The handoff reports
the actual application structure without deciding how a receiver should deploy it.

## Human documentation inputs

Humans should be able to understand and operate the application after its AI files are removed.
Keep ordinary build/run instructions, product behavior and review scenarios with application
source. Documentation receivers can turn those inputs into their preferred manuals and tutorials.

Describe who a capability is for, its terminology, role requirements, inputs, observable outcomes,
failure cases and applicable examples. Link interface contracts and meaningful tests. Preserve
unique behavioral explanations in authored text; generated API/configuration references complement
them. A documentation handoff must not consist only of schemas or an AI task history.

Ordinary engineering commands remain under `eng/`; applicable application packaging/run inputs
can remain under `deploy/`. Existing locations need not move. Agent scripts, engine state and caches
are removable; application build scripts and configuration are part of the human-maintainable repo.

## Handoff assembly

Use a generated index under `artifacts/handoff/` to locate applicable outputs for a release. The
index references existing descriptors, contracts and artifacts and binds them to their application
identity, version, source revision and hashes. It may accompany an archive or immutable artifact
locations. Final index fields and format remain to be designed against a concrete fixture.

The index is a navigation and integrity aid. It does not become another application registry,
deployment model, approval ledger or source of configuration defaults. Retain source inputs in
their ordinary repository locations, and keep generated copies regenerable.

Receivers need no installed Program Kit, Spec Kit workflow, AI instructions or engine state to
read the handoff, build the source or use its artifacts. They can use it in infrastructure,
documentation, integration or another workflow without Program Kit knowing that workflow.

The [illustrative handoff](application-handoff-example.md) shows the intended output for a
fictional application with two APIs, PostgreSQL and Keycloak requirements.

## Acceptance and implementation sequence

1. Inventory the existing application outputs and identify concrete omissions for each receiver.
   Start with application identities, existing bundle/feature descriptors, configuration contracts
   and human behavior/run/review inputs. Avoid new schemas until existing authorities are mapped.
2. Add applicable output generation and guide conventions through normal engineering. Preserve
   consumer-owned files during installation and upgrade; update affected outputs with feature work.
3. Assemble the release index from actual artifacts. Reject missing references, mismatched
   identities/hashes, stale generated contracts and secret values. Do not label incomplete draft
   outputs a complete handoff.
4. Exercise a small multi-API fixture. Confirm packaged feature descriptors, settings contracts,
   public interfaces and documentation examples agree with the delivered application.
5. Remove toolkit installations, AI instructions, engine state and caches in a disposable copy.
   Build/run/review through ordinary application commands and consume the handoff independently.
6. Check receiver completeness: an infrastructure reader can identify artifacts and requirements;
   a documentation reader can explain and demonstrate delivered behavior. Neither needs agent
   history. Receiver implementation and production deployment are outside this acceptance scope.

Likely code touchpoints are native `eng/` packaging/configuration exports, the existing application
bundle packager, template ownership declarations and applicable feature guidance. Coordinate with
the separate Foundation configuration-contract work before adding export APIs. This branch starts
from committed source and excludes that work's uncommitted edits.

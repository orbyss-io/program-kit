# Application handoff output inventory

Program Kit already produces the core Foundation application artifacts. The missing delivery is a
complete, discoverable set of application facts: stable identity, configuration metadata, human
documentation inputs, runtime/data requirements and an index connecting them to delivered artifacts.
Reuse existing descriptors and contracts.

Scope: Program Kit producers, templates and guidance at commit
`087290b7d3fc3f6abf5b2460e94b1d3af367ec31`, inspected on 2026-10-06 on
`codex/human-infrastructure-handoff`. This is a source inventory, not deployed-consumer acceptance.
The branch's design/example are proposals. Uncommitted Foundation-contract work is outside this
baseline.

## Existing outputs and gaps

| Output | Current state | Missing work |
| --- | --- | --- |
| Application identity | Bundle records ID, version and source commit | ID comes from checkout directory name; provide an explicit stable identity |
| Application packages and bundle | Native build/pack, validated closure, ZIP, descriptor and checksum exist | Make actual outputs discoverable alongside other applicable assets |
| Image or Dockerfile | Foundation image identity/digest exists; consumer host Dockerfiles are retired | Reference the existing image; include Dockerfiles only where the selected profile owns an image build |
| Feature descriptors | Packaged identities, dependencies, routes and shell activation exist | Link these existing authorities to delivered artifacts |
| Configuration contract | Runtime values and a selected SPA-PKCE schema exist | Application-wide supported-setting metadata and export are missing |
| Public API contracts | OpenAPI producer/compatibility/client pipeline exists; registry starts empty | Collect actual registered contracts and connect them to application components |
| Runtime requirements | Some facts exist in profile guidance, configuration and local Compose inputs | Supply requirements independently of development fixtures and AI guidance |
| Data changes | Persistence guidance calls for migration artifacts | Reference actual artifacts, invocation and application compatibility |
| Human documentation | Engineering README, XML comments and architecture/specification inputs exist | Maintained delivered-product overview, terminology/roles, run instructions and review scenarios |
| Handoff index | No producer found in inspected templates/scripts | Assemble references and hashes without another feature/configuration registry |
| Receiver distribution | Release workflow publishes bundle files and public-availability evidence | Include applicable API/settings/documentation/runtime/migration outputs |
| Independence | Native build commands exist; consumer release still calls an installed extension | Keep complete handoff/release production available through ordinary engineering |

## Producers to reuse

### Application artifacts and identity

[Build.ps1](../extensions/program-kit-dotnet/templates/dotnet/files/eng/Build.ps1) builds, tests,
packs to `artifacts/packages/<version>`, stages `artifacts/release-bundle` and invokes the registered
OpenAPI pipeline. Final descriptor/ZIP production is a separate
[release_bundle.py](../extensions/program-kit-dotnet/templates/dotnet/files/eng/release_bundle.py)
`describe` step. Staged inputs are not yet a finished release.

The descriptor gets version from `VERSION`, binds source commit and host image digest, and currently
sets `application.id = repository.name`. Renaming a checkout therefore changes its application ID.
An explicit consumer-owned identity should feed the existing descriptor. Preserve compatibility
with historical descriptors rather than silently rewriting their identities.

The bundle allowlist contains validated configuration/packages plus its descriptor. It does not
automatically include API contracts, human guides, migrations or frontend assets. A receiver handoff
can accompany this runtime bundle without changing what the host consumes.

### Feature metadata and interfaces

The [runtime profile](../extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md)
assigns descriptor emission to `Orbyss.Foundation.Build` at `orbyss-foundation/feature.json`.
The bundle reader supports versions 1 and 2, including multiple features per package, and checks
activation/dependencies/routes.
[feature_metadata.py](../extensions/program-kit-dotnet/templates/dotnet/files/eng/feature_metadata.py)
updates activation, not descriptor emission. Reuse these package, feature and shell identities.

The [OpenAPI pipeline](../extensions/program-kit-dotnet/templates/dotnet/files/eng/openapi_pipeline.py)
exports, normalizes, checks compatibility, generates client types and compiles the consuming
application for registered contracts. The
[registry](../extensions/program-kit-dotnet/templates/dotnet/files/eng/openapi-contracts.json)
starts with `contracts: []`; it does not prove every implemented API is registered.
The [contract schema](../extensions/program-kit-dotnet/templates/dotnet/files/eng/openapi-contract.schema.json)
already records identity, shell, features and output paths. Reference these instead of another API
catalog. A feature, shell or API is not automatically a separate process.

### Configuration metadata

Runtime configuration files contain values. The
[bundle schema](../extensions/program-kit-dotnet/templates/dotnet/files/eng/application-bundle.schema.json)
defines the descriptor envelope, not every application's supported settings.
The [SPA-PKCE schema](../extensions/program-kit-dotnet/templates/dotnet/web-profiles/spa-pkce/eng/spa-pkce.schema.json)
covers one selected profile.

A receiver needs keys, types, requiredness, supported defaults/constraints, scope, secret
classification, binding/precedence and restart/reload behavior. Coordinate exports with Foundation
owners for framework settings and application owners for feature settings. Assemble actual metadata;
do not infer the complete contract from sample values or invent upstream export APIs. Export must
not initialize application storage or contact external services.

### Runtime requirements and data changes

[Application Compose](../extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/deploy/compose.application.yml)
reveals some image/mount/port/configuration requirements.
The [identity fixture](../extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/deploy/compose.identity.yml)
uses development startup behavior and credentials. Classify these as local examples, and do not
promote their values into a secret-free release handoff or production configuration contract.

Describe actual dependency capabilities, protocols, read-only/writable paths, startup/shutdown and
implemented health behavior. The runtime profile leaves application health with features; do not
invent a host health model to fill a field.

[Persistence guidance](../extensions/program-kit-dotnet/references/persistence-profiles.md) already
requires migration bundles or provider-supported idempotent artifacts. Reference the real artifact,
owner, invocation and application compatibility constraints. Receiver provisioning and deployment
orchestration are outside this feature.

### Human documentation inputs

[eng/README.md](../extensions/program-kit-dotnet/templates/dotnet/files/eng/README.md) documents native
commands. [Build props](../extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Build.props)
enable compiler XML documentation. Architecture/specification inputs carry intent and journeys,
but do not establish delivered behavior.

No application run/review/tutorial producer or template was found in the inspected extensions and
presets. Maintain a small consumer-owned application guide covering delivered purpose, terminology,
roles, verified run examples and observable review outcomes. Link real interfaces/tests and preserve
authored explanations independently of agent history.

## Release independence issue

The [consumer release workflow](../extensions/program-kit-dotnet/templates/dotnet/files/.github/workflows/application-release.yml)
invokes `.specify/extensions/program-kit-building-blocks/scripts/public_availability.py` and reads
the extension catalog. It uses the result to verify the host image and publish component evidence.
Removing installed tooling removes this release prerequisite.

Make the required executable/catalog/selected inputs available through ordinary engineering while
preserving public-availability and exact-image checks. Do not remove that validation, accept arbitrary
images or replace it with an unconditional success. This needs dedicated regression coverage.

## Implementation order and owners

| Order | Deliverable | Owner | Completion check |
| --- | --- | --- | --- |
| 1 | Stable application identity and receiver input locations | Consumer declaration; existing bundle producer | Folder rename preserves selected identity; historical compatibility retained |
| 2 | Human guide and runtime/data requirements | Consumer authorship; scaffold conventions; applicable feature guidance | Delivered examples can be followed without agent history |
| 3 | Supported-settings export | Foundation/profile and application owners; Program Kit assembly | Matches actual settings semantics; no secrets; no runtime initialization |
| 4 | Handoff index and assembly | Native engineering referencing existing artifacts | Multiple APIs/features discoverable; hashes agree; incomplete inputs fail |
| 5 | Complete ordinary-engineering delivery | Native packaging and preserved release checks | Full handoff generation works after toolkit removal |

Qualify against a small deterministic consumer fixture: missing/stale references, identity mismatch,
multi-feature packages, multiple API contracts, settings parity, secret exclusion and human examples.
Authored application files remain consumer-owned; exporter/index tools can be managed; generated
handoffs remain ignored. Infrastructure adapters and documentation publishing stay receiver-owned.

## Verification performed

- `python tests/validate_release_bundle.py`: 15 tests passed, covering real offline bundle
  production/admission, descriptor closure, hashes, deterministic archives, stale configuration,
  tamper rejection and the published-host boundary.
- `python tests/validate_generated_contract_schemas.py`: passed; actual descriptor and runtime
  closure producers conform to their shipped schemas.

These checks establish existing bundle behavior. They do not establish the proposed settings export,
handoff, multi-API runtime or production acceptance. This increment changes contributor documents only.
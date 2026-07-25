---
artifact-kind: implementation-plan
artifact-id: pkid:plan:program-kit:host-tooling
artifact-version: 1.0.0
intended-contract: pkid:schema:program-kit:implementation-plan
intended-contract-version: 1.0.0
design-ref-id: pkid:design:program-kit:host-tooling
design-ref-version: 1.0.0
design-digest: sha256:df33ffc00dd296957a606862eca8119f596f64af1f78429127717d90fc974632
review-state: awaiting-human-approval
implementation-status: not-started
---

# Program Kit host-tooling extension implementation plan

## 1. Authority and execution gate

This plan implements only the exact `architecture-design.json` bytes bound in
the frontmatter and `review-manifest.json`. Implementation may begin only after
the human explicitly approves the exact design and plan SHA-256 values.

Human approval authorizes repository implementation and bounded verification;
it does not authorize provider provisioning, credentials, network discovery,
cloud changes, container execution, Dev Container execution, deployment,
publication, release activity, or consumer-domain design.

The repository's current canonical implementation-plan schema requires exact
artifact references, including digests, for every planned output. Prospective
source and package artifacts do not yet exist and their digests must not be
invented. This Markdown plan is therefore the truthful review representation.
`PKHT-W010` must first extend planning to represent prospective outputs without
fake integrity claims, then materialize this plan as a canonical JSON instance
without changing its approved scope or sequencing.

Any change to ownership, dependency direction, protocol role, security
boundary, Options semantics, generated runtime closure, external execution
boundary, or deferred scope stops implementation for a revised design and
renewed human approval.

## 2. Requirements

| ID | Required outcome |
| --- | --- |
| `PKHT-R001` | One provider-neutral Operations contract owns operation identity and projections. |
| `PKHT-R002` | .NET configuration sources have explicit stable order, precedence, startup, reload, secret, failure, and compatibility declarations. |
| `PKHT-R003` | Typed and named Options bindings generate binding and validation, with required/security-critical bindings validated on startup. |
| `PKHT-R004` | Fixed, scoped snapshot, and monitored consumption are explicit and lifetime-safe; restart-required settings cannot claim live application. |
| `PKHT-R005` | Built-in providers and custom provider generation use a closed, versioned module ABI with no arbitrary code or ambient discovery. |
| `PKHT-R006` | Optional Azure Key Vault and Azure App Configuration adapters bind external credentials, refresh policy, and secret-safe evidence. |
| `PKHT-R007` | ASP.NET Core host profiles preserve the boundary between transport authentication/authorization mechanics and consumer-domain conclusions. |
| `PKHT-R008` | A confidential interactive OIDC profile uses authorization code flow with PKCE and exact validation/security requirements. |
| `PKHT-R009` | A JWT resource-server profile validates access tokens and never accepts an ID token as an API access token. |
| `PKHT-R010` | Endpoint security disposition and named ASP.NET Core policy attachment are explicit, deterministic, and projection-neutral. |
| `PKHT-R011` | Exact local foreign OpenAPI input generates a client through a pinned Kiota adapter with lock and provenance. |
| `PKHT-R012` | Explicit low-level application composition generates a pinned Aspire AppHost without inventing environment or deployment meaning. |
| `PKHT-R013` | Explicit development-container input generates and validates deterministic Dev Container artifacts without execution. |
| `PKHT-R014` | FastEndpoints optionally projects the same operation and security contracts without becoming a semantic owner. |
| `PKHT-R015` | An Aspire-backed Keycloak fixture proves provider substitution and deterministic realm import only for disposable local testing. |
| `PKHT-R016` | Every generator is deterministic, cancellation-aware, secret-safe, provenance-bound, and isolated by explicit output root. |
| `PKHT-R017` | Direct comprehensive Compose modeling, automatic execution, production provisioning, and consumer-domain semantics remain absent. |
| `PKHT-R018` | Version maps, migrations, generated consumers, package closure, fixtures, documentation, and independent review close the extension. |

## 3. Exact starting inputs

The implementation starts only from:

- the approved exact `architecture-design.json` and this plan;
- `design-intent.md`;
- Program Kit baseline design `0.3.0` at
  `sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9`;
- accepted Engine design intake at
  `sha256:ef94f62ecfa7c7afa092d82070c3652636d4b44b396e3e06dda1e279e816dd46`,
  used only for declared cross-boundaries and Operations convergence;
- the repository-pinned .NET target profile and Program Kit dependency policy;
- exact external standards and documentation enumerated in the design.

No ambient package, SDK, image, executable, current-user credential, provider
metadata, sibling repository, generated output, or machine cache is source
truth.

Before any external technology is selected, its work unit must record exact
version, source revision, license, distributable/package/image/tool digest,
resolved dependency closure, supported target profile, and acceptance result.
“Latest” is never a durable selection.

## 4. Work units

### `PKHT-W010` — governance and Operations convergence

**Requirements:** `R001`, enabling `R018`.

**Allowed edits:** Program Kit planning schemas/models/validators required to
represent truthful prospective outputs; new Operations schemas, package,
models, validators and tests; DotNet/Workbench operation references; solution,
central package/version maps, documentation, and migration artifacts.

**Required outcomes:**

1. Add a planning-contract revision that distinguishes a prospective output
   identity from integrity evidence for bytes that already exist. It must not
   weaken exact references where integrity is asserted.
2. Materialize this approved plan as canonical JSON and prove it is
   semantically equivalent to the approved Markdown work units.
3. Create `Orbyss.ProgramKit.Operations` over Artifacts only, owning the compact
   operation descriptor/catalog/invocation/progress/result surface accepted by
   the Engine intake.
4. Migrate `DotNetOperationBinding` through an explicit version map so DotNet,
   OpenAPI, ASP.NET Core, FastEndpoints, and later projections cannot become
   parallel operation owners.

**Verification:** schema/model drift, semantic validation, JSON round trip,
dependency scans, version impact and migration tests, isolated Operations
consumer, existing Program Kit unit/conformance suites.

**Stop conditions:** stop if Operations requires any host, transport, task,
Engine, identity, authorization, provider, or development-capability
dependency; stop if planning integrity semantics would be weakened.

### `PKHT-W020` — configuration composition and typed Options

**Requirements:** `R002`, `R003`, `R004`, part of `R016`.

**Depends on:** `W010`.

**Allowed edits:** DotNet configuration and shell schemas/models/validators,
generation modules, host renderers, locks/provenance, focused tests and
fixtures, documentation, version/migration artifacts.

**Required outcomes:**

1. Replace the unused minimal configuration-binding placeholder with explicit
   ordered source descriptors and typed/named Options bindings.
2. Model provider identity, precedence, optionality, startup behavior, reload
   capability, polling/refresh trigger where applicable, secret
   classification, failure disposition, and restart requirement.
3. Generate `AddOptions<T>`, binding, exact validators, and
   `ValidateOnStart` for required/security-sensitive settings. Prefer
   source-generated binding and validation when supported by the pinned .NET
   profile.
4. Generate lifetime-safe fixed, scoped-snapshot, and monitored consumption.
   Reject snapshot-to-singleton capture, monitor use without provider reload
   support, and live monitoring of restart-required topology.
5. Generate disposable bounded monitor subscription scaffolding and redacted
   diagnostics; non-trivial reactions are queued into consumer-owned bounded
   services.

**Verification:** deterministic API/Console/Worker hosts; precedence matrix;
missing/invalid startup values; named Options; valid reload; invalid reload
candidate; scoped consistency across scopes; singleton monitor notification;
subscription disposal; restart-required rejection; redaction; build/analyzer
proof; no unused intent fields.

**Stop conditions:** stop if .NET runtime behavior cannot support a declared
guarantee, if a provider does not produce a usable change token, or if safe
invalid-reload behavior requires a new runtime controller.

### `PKHT-W030` — provider-generation module ABI and built-in providers

**Requirements:** `R005`, part of `R002`, `R004`, `R016`.

**Depends on:** `W020`.

**Allowed edits:** configuration provider contracts/catalog, DotNet generation
module registration, selected built-in provider projections, conformance
fixtures, docs and package/version metadata.

**Required outcomes:**

1. Define a finite, versioned provider descriptor and generator registration
   ABI. Canonical input selects a known provider identity and exact revision,
   never an arbitrary .NET type or script.
2. Cover only reviewed built-ins useful to generated hosts, including JSON,
   environment variables, command line, in-memory, user secrets for
   development, key-per-file, and explicit chained configuration where the
   pinned host permits it.
3. Declare which providers support reload and the mechanism/limitations used
   to prove it. File watcher limitations in containers and network shares must
   remain visible.
4. Enforce provider ordering, duplicates/conflicts, package closure, secret
   rules, deterministic registration, and stable diagnostics.

**Verification:** provider matrix and negative catalog tests; repeated
generation; output-tree digest; isolated host build; controlled file changes;
unsupported reload rejection; no reflection or assembly scanning.

**Stop conditions:** stop for any provider requiring ambient discovery,
arbitrary code execution, unbounded polling, or an unreviewed dependency.

### `PKHT-W040` — Azure configuration provider adapters

**Requirements:** `R006`, part of `R004`, `R016`.

**Depends on:** `W030`.

**Allowed edits:** optional Azure provider packages/modules, exact selection
evidence, schemas/models, generation, fixtures with fake/emulated boundaries,
docs and version metadata.

**Required outcomes:**

1. Select exact Azure Key Vault configuration and Azure App Configuration
   packages and credential abstractions after source/license/closure review.
2. Generate endpoint and credential references, never credentials or secret
   values. Prefer externally supplied credentials/managed identity-compatible
   abstractions.
3. Model Key Vault reload intervals and App Configuration key/sentinel
   selection, refresh interval, request/manual trigger, Key Vault references,
   and outage behavior exactly as supported.
4. Keep provider-specific cached-value behavior explicit; do not generalize it
   into a universal Program Kit guarantee.

**Verification:** deterministic generation and build; fake provider startup,
rotation/refresh, sentinel consistency, invalid secret, credential failure,
outage, cancellation and redaction tests; dependency/license/lock proof.

**Stop conditions:** stop if verification requires live credentials or cloud
mutation, or if selected provider behavior contradicts the base reload model.

### `PKHT-W050` — ASP.NET Core OIDC, JWT, and authorization host profiles

**Requirements:** `R007`–`R010`, parts of `R003`, `R016`, `R017`.

**Depends on:** `W020`, `W030`.

**Allowed edits:** Operations/DotNet transport-security schemas and models,
ASP.NET Core generator modules, exact framework/package evidence, generated
host fixtures, OpenAPI security projection, docs and version metadata.

**Required outcomes:**

1. Define separate `oidc-confidential-interactive-code-pkce` and
   `oauth-jwt-resource-server` profiles. Do not define a generic “identity
   provider” switch.
2. Generate explicit authentication schemes/defaults, required packages,
   middleware order, cookie/OIDC or JWT bearer registration, named host policy
   references, anonymous disposition, endpoint attachment, and OpenAPI
   security metadata.
3. Interactive profile: exact authority/metadata, client identity and external
   secret/assertion reference, callbacks, code flow, PKCE, state/correlation,
   nonce, cookie, HTTPS, token validation, claim mapping, PAR disposition, and
   session rules.
4. Resource-server profile: access-token-only validation of issuer, audience,
   signature, allowed algorithms, lifetime, HTTPS metadata, and selected JWT
   access-token profile. Map inbound claims only by explicit selection.
5. Expose the transport `ClaimsPrincipal` and named policy outcome only through
   explicit consumer adapters. Generate no domain role/grant/policy meaning.

**Verification:** deterministic API/web fixtures; positive/negative OIDC and
JWT protocol vectors; wrong issuer/audience/algorithm/signature/token type;
expired/not-yet-valid token; ID-token-as-access-token rejection; nonce/state/
correlation failures; secure cookie/callback behavior; 401 versus 403;
anonymous versus protected endpoints; secret redaction; isolated build.

**Stop conditions:** stop if the initial framework handler cannot prove a
required protocol guarantee, if a product quirk enters the base profile, or if
consumer-domain policy meaning would be required.

### `PKHT-W060` — pinned Kiota foreign-client adapter

**Requirements:** `R011`, `R016`, `R017`.

**Depends on:** `W020`.

**Allowed edits:** foreign OpenAPI input descriptor, Kiota provider module,
exact tool/package evidence, bounded process invocation, locks/provenance,
fixtures, docs and version metadata.

**Required outcomes:** validate and digest one explicit local OpenAPI input;
select exact Kiota tool/language/options; generate only into an explicit
isolated output root; retain `kiota-lock.json`; normalize/digest the output
tree; emit runtime dependency requirements; distinguish foreign input from
Program Kit-owned OpenAPI projection.

**Verification:** same input/tool/options produce identical output; changed
input or option changes lock/provenance; invalid OpenAPI, tool failure,
cancellation and partial output fail closed; generated client builds and calls
a deterministic fixture server.

**Stop conditions:** stop if generation requires network retrieval, login,
ambient cache input, unpinned tool behavior, or Program Kit reimplementation of
Kiota.

### `PKHT-W070` — Aspire AppHost generation

**Requirements:** `R012`, `R016`, `R017`.

**Depends on:** `W020`, `W030`.

**Allowed edits:** low-level application-composition input, Aspire generator
module, exact SDK/integration evidence, generated project fixtures, docs and
version metadata.

**Required outcomes:** generate a pinned AppHost project from explicit project,
executable, container, parameter, endpoint, reference, wait, volume, and
selected integration inputs; pass only declared configuration/secret
references; keep run/deploy outside deterministic generation.

**Verification:** repeated generation and output digest; generated AppHost
build; model-shape assertions without starting resources; missing/cyclic/
conflicting references fail with stable diagnostics; generated consumers do
not reference Program Kit generation assemblies.

**Stop conditions:** stop if Aspire inputs would become canonical environment
or deployment semantics, or if proof requires starting infrastructure.

### `PKHT-W080` — Dev Container generation and validation

**Requirements:** `R013`, `R016`, `R017`.

**Depends on:** `W020`, `W030`.

**Allowed edits:** development-container schemas/models/validators, generator
module, vendored exact schema/spec evidence, fixtures, docs and version
metadata.

**Required outcomes:** generate explicit `.devcontainer/devcontainer.json`,
optional Dockerfile, Compose fragment only when required by the selected Dev
Container profile, features, mounts, ports, users, lifecycle commands and
scripts. Preserve command/script semantics exactly as human input; Program Kit
owns structure, escaping, references, validation and provenance, not the
meaning of arbitrary setup actions.

**Verification:** exact schema validation; path/escape/secret tests; repeated
generation; representative folder/image/Dockerfile/Compose-backed fixtures;
no execution; no claim that a Dev Container is the Engine's governed work
boundary.

**Stop conditions:** stop if arbitrary setup behavior would be invented, if
generation needs container execution, or if the required Compose model expands
beyond the bounded Dev Container projection.

### `PKHT-W090` — optional FastEndpoints projection

**Requirements:** `R014`, `R007`, `R010`, `R016`.

**Depends on:** `W050`.

**Allowed edits:** optional FastEndpoints adapter, exact source/package
evidence, generator modules, fixtures, docs and version metadata.

**Required outcomes:** project the same Operations and transport-security
profiles into FastEndpoints endpoint/configuration source; preserve route,
request, response, error, anonymous/protected and named-policy behavior; keep
ASP.NET Core middleware as the security owner and FastEndpoints as syntax/tool
specialization.

**Verification:** projection parity matrix against Minimal API output;
deterministic build/run fixture; OpenAPI and security equivalence; package
closure; no adapter-specific semantic owner.

**Stop conditions:** stop if FastEndpoints security convenience APIs alter the
base policy/profile semantics or require provider-specific identity meaning.

### `PKHT-W100` — optional Keycloak/Aspire local-test fixture

**Requirements:** `R015`, `R007`–`R009`, `R012`, `R016`, `R017`.

**Depends on:** `W050`, `W070`.

**Allowed edits:** test-fixture-only realm descriptor/generator, exact
Keycloak/Aspire/image evidence, generated Aspire fixture, protocol tests,
redacted evidence and documentation.

**Required outcomes:** generate a minimal realm import with explicit realm,
client, redirect URI, audience/scope mapping, test-only principals and
secret-reference placeholders; bind a pinned Keycloak container through the
pinned Aspire integration; prove the same generated OIDC client and JWT API
profiles work without adding Keycloak to base contracts.

Container execution remains a separately human-started test action. Fixture
state is disposable and import is neither backup nor production provisioning.

**Verification:** offline realm JSON/schema/semantic checks always run; when
explicitly authorized, the isolated integration profile starts the resource,
waits for readiness, exercises OIDC/JWT positive and adversarial paths,
captures redacted evidence, and tears down owned state.

**Stop conditions:** stop without explicit execution authority; stop on
unpinned images, durable credentials, production provisioning behavior,
provider claims entering domain meaning, or fixture state outside its isolated
root.

### `PKHT-W110` — migration and extension closure

**Requirements:** `R016`–`R018` and closure of all preceding requirements.

**Depends on:** `W040`, `W060`, `W080`, `W090`, `W100`.

**Allowed edits:** version maps/selections/migrations, package locks, generated
fixtures, docs, self-hosted design/plan projections, test-plan profiles,
independent review and bounded remediation.

**Required outcomes:** remove superseded operation/configuration placeholders;
prove one owner per semantic concept; update reverse impact and generated
consumer migrations; freeze exact external selections; run all deterministic,
security, redaction, dependency, compatibility and isolated-consumer proofs;
record truthful status and independent findings.

**Verification:** repository formatting/build/test plan; all unit,
conformance, workflow and isolated consumer tests; clean repeated generation;
package/source/license/lock scans; design/plan/schema/model consistency;
independent review with no unresolved material finding.

**Stop conditions:** stop on any unclosed migration, parallel owner, dirty
generated output, flaky/nondeterministic fixture, secret exposure, unreviewed
dependency, or material deviation.

## 5. Parallel execution

Parallel work is permitted only after the shared foundations land:

| Phase | Work units |
| --- | --- |
| Foundation | `W010` → `W020` → `W030` |
| Independent adapters | `W040`, `W050`, `W060`, `W070`, `W080` after their declared dependencies |
| Dependent projections | `W090` after `W050`; `W100` after `W050` and `W070` |
| Closure | `W110` after all selected units |

Each parallel unit owns disjoint provider/projection paths. Changes to shared
schemas, base contracts, central package versions, solution topology, or
generation infrastructure must be integrated serially through their owning
foundation unit.

## 6. Requirement trace

| Requirement | Owning work unit(s) |
| --- | --- |
| `R001` | `W010` |
| `R002`–`R004` | `W020`, proven across `W030`, `W040`, `W050`, `W110` |
| `R005` | `W030` |
| `R006` | `W040` |
| `R007`–`R010` | `W050`, parity in `W090`, substitution proof in `W100` |
| `R011` | `W060` |
| `R012` | `W070`, used by `W100` |
| `R013` | `W080` |
| `R014` | `W090` |
| `R015` | `W100` |
| `R016` | every work unit; closure in `W110` |
| `R017` | every work unit; boundary scan in `W110` |
| `R018` | `W010` migration start and `W110` final closure |

## 7. Deliberately unimplemented

The plan contains no work unit for comprehensive Docker Compose semantics,
automatic execution, production Keycloak administration, provider discovery,
dynamic client registration, opaque-token introspection, custom OpenAPI
generation, consumer-domain identity/authorization, deployment, or release.
Adding any of these requires a new human-started design.

## 8. Completion rule

The extension is complete only when `W110` closes every requirement with exact
evidence and no material finding. Passing a build, generating example code, or
running a Keycloak fixture alone is not completion. Status must remain truthful
if any optional adapter approved by this plan is not implemented.

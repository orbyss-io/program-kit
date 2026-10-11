# Adopting reusable consumer foundations

This implements the [accepted foundation plan](../reusable-consumer-foundations-plan-2026-10-10.md).
The implementation checklist records current development qualification. Publication and an
existing application's adoption remain separate actions. Notes and De Sportomgeving have
not been migrated by this work.

For a new consumer, retain its accepted dependency profile and choose the BFF/Keycloak
composition or its EF/PostgreSQL variant from the installed .NET composition templates.
Copy the selected template to `eng/foundation-composition.json`; set the actual application
feature projects, selected package roots, runtime directory and native test adapter. A
composition selects feature-owned behavior on the unchanged Foundation host. It needs
neither an aggregate Composition library nor a consumer host executable.

Configure the public application origin, callback/logout paths, realm, client and audience
together. Declare the public identity origin separately from private discovery/backchannel
and administration addresses. The public issuer identifies resource owners; never derive
it from a private administration endpoint. Supply client/database credentials through the
declared deployment configuration providers. Do not commit them into templates or views.

Use the existing repository setup preview/apply flow to materialize the explicit selection.
Review reported conflicts before applying; managed outputs remain owned by sync, while
application feature source remains consumer-owned after scaffolding. Do not replace
custom configuration, native locks, accepted ADRs or architectural history. Link the
generated `docs/architecture/foundation-configuration.md` reference and Mermaid diagram.
When deselecting a feature, sync retains its customized source project as a consumer-owned
group and releases its governed contribution. Its physical architecture role remains
classified, while selected roots and runtime activations exclude it. Untouched scaffolds
can retire; reconcile the application-owned solution if it still references such a project.
`python eng/foundation_composition.py --repository . --effective` gives the redacted source
projection; its label distinguishes configured inputs from observed activated options.
The maintained runtime inspector observes the actual activated options and provider sources.
Its native shell provider is a flattened memory projection on the selected host; it cannot
recover the original host JSON/environment provider ordering. Read the paired configured-source
view for declared input attribution and the runtime view for actual typed values, owner DLL
hashes and native provider observations. Neither view substitutes for an unobserved owner.

Run explicitly authorized maintained setup checks using `eng/foundation_setup.py`; an
inspection without `--execute` starts no service. Materialization is not readiness. Readiness
in this maintained adapter covers fresh disposable services, loopback HTTP Development
origins and an owned private Docker alias on port 8080. Validated production TLS/proxy
inputs require targeted setup checks of the actual deployment and its existing identity
and provider provisioning, using the maintained tests rather than another harness.
Platform readiness
requires actual restore/build, selected feature activation, applicable service checks and
nonempty maintained authentication/provider cases. A failure names the repair and retains
its streams in normal `artifacts/tests/` output. Product acceptance additionally requires
the application's ownership/security, transaction, conflict, replay and recovery cases.
Put remaining enabling work beside the first operation that needs it. Keep due security,
provider and authority gates; do not reintroduce an all-story foundation phase.
The selected BFF's `FoundationBffCookieFeature.ApiRedirectAsErrorAsync` treats `/api`
paths as API authentication errors (401/403); other paths use the browser login/access-denied
redirect contract. Place HTTP API adapters under `/api` when that error contract is intended.
This prefix and the maintained BFF routes are owner-defined protocol behavior, not timeout
settings. An anonymous test must inspect the initial response and assert the intended exact
contract; automatic redirects can hide it behind an identity-page response.
Use `python eng/foundation_setup.py --repository . --status` to inspect the latest outcome
and input/evidence freshness without running a test or service. Mutable services still need
fresh checks beside the dependent operation. The selected xUnit/MTP adapter can use the
maintained Focused runner with `--native-report xunit-trx`; named native results reject empty,
duplicate, skipped or failed execution without requiring a runner migration.

For an existing consumer, first checkpoint its source and retain failed evidence. Install
the published toolkit through its supported upgrade mechanism when available. Review the
accepted project responsibilities and map the composition input to the actual feature
registrations and package roots. Apply the existing
[lifecycle ownership repair](application-lifecycle-repair.md) where an unnecessary aggregate
owns provider initialization or application workers. Preserve legitimate selection presets.
Retired test projects use the existing successor-ownership mapping and fresh unfiltered
successor tests; renaming a runner does not erase a failure.

The provider owns connectivity/lifetimes and the deployment-controlled migration seam.
Keep application schema, transaction contents and outcome mapping in their existing owners.
Do not run uncontrolled migrations during application startup. Prove upgrade conflict
handling, retained synthetic data and restart first in a disposable reproduction. Then
review an explicit live consumer adoption separately, including its backup/restore and
forward migration policy. Toolkit synchronization never migrates live data.

The local Keycloak realm contains synthetic test identities. Import is initial fixture
setup, not an update protocol for an existing production realm. Reconcile existing client,
scope, redirect/logout and theme desired state through the identity owner. Configure TLS,
trusted proxy forwarding, public hostname/backchannel routing and least-purpose secret
references before deployment. Maintained theme selection and admitted branding retain only
their qualified envelope; custom templates, flows or behavior require targeted qualification.

Changed package/template bytes, captured profiles, relevant configuration, service/setup
inputs, environment or tested theme invalidate the corresponding evidence. A newer failure,
interruption or empty test selection cannot reuse an older pass. Development candidates
are explicit local selections, with distinct versions and exact retained bytes; they do
not establish immutable public availability. Public adoption waits for approved Foundation
publication and fresh exact-composition qualification, then profile and knowledge regeneration
together. Dependency maintenance and the full Release publication gates remain mandatory.

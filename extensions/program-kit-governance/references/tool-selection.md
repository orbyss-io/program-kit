# Tool and integration selection

## Retained ordinary-development selections

<!-- program-kit:knowledge-rule principle.retained-engineering-selections -->
Reuse the accepted exact dependency profile and existing engineering tools during feature work.
Task generation carries their applicable compatibility, security and behavior checks into owned
tasks with explicit dependencies. It does not reopen bootstrap research, install alternatives,
change pins or execute compatibility/admission work before saving tasks. Research only a concrete
new capability gap or substantive override; retain accepted authority and actual verification.
<!-- /program-kit:knowledge-rule -->

## Bootstrap candidate research

Select capabilities before products. Research current options at bootstrap time because ecosystems, compatibility, maintenance, and security change.

Apply `default-adoption.md`: respect explicit intake selections and use the versioned Program Kit
profile for ordinary choices when intake is silent. Research verifies compatibility and records
exceptions; it does not reopen every explicit or default choice. Ask the human only about a genuine
exception, material acknowledgement, or consequential decision without a safe default.

For each candidate record:

- capability and risk addressed;
- fit with detected technologies and architecture;
- active maintenance, release recency, license, adoption, and exit cost;
- Spec Kit compatibility and integration mechanism;
- permissions, scripts, network behavior, and supply-chain trust;
- enforcement strength and false-positive/false-negative profile;
- lifecycle trigger, version pin, upgrade test, and removal path;
- alternatives and reasons for selection or rejection.

Community Spec Kit catalogs are discovery inputs, not endorsements. Inspect extension commands, hooks, scripts, and transitive tools. Mandatory quality controls belong in deterministic CI even when Spec Kit hooks give earlier feedback.

Evaluate rather than automatically install:

- Architecture Governance for ADR/architecture artifact gates.
- ADR tooling or a local adapter when the current ADR kit adapter is incompatible.
- API evolution uses the existing OpenAPI/compatibility pipeline and `modularity-and-contracts.md`.
  API Evolve v1.0.0 was evaluated and is not admitted; do not repeat its baseline/task/release hooks.
- Reqnroll BDD for valuable multistep executable examples in .NET contexts.
- ArchUnitNET for compiled .NET dependency and layering rules.
- Structurizr DSL/C4 and arc42 when architecture-as-code and navigable documentation fit.

Program Kit's generated C4 review projection uses the optional, managed Structurizr Local profile in
`c4-viewer-tool.json`. The profile records authoritative sources, retrieval date, exact version,
license and supply-chain boundaries, update triggers, and removal path. Viewing is not a project
technology decision and does not add a bootstrap runtime dependency. Invoke
`speckit-program-kit-governance-view-c4`; never substitute Structurizr Lite or an unpinned `latest`
image.

<!-- program-kit:knowledge-rule principle.dotnet-host-default -->
Selecting .NET selects `Orbyss.Foundation.Host` with CShells and Nuplane as
Program Kit's default, unless the human explicitly opts out. Dynamic activation, tenancy,
isolation or reload requirements are not prerequisites for this default. Use the published,
digest-pinned `ghcr.io/orbyss-io/foundation-host` image and the managed OpenAPI exporter from
the effective dependency profile; consumers produce feature packages and application bundles.
Minimal APIs describe endpoint style within that host, not a consumer-owned host.

Before reporting architecture review clear, compare the proposed host/exporter with the actual
human decisions in the conversation, intent, plan and cited ADRs. A proposed custom host or custom exporter without
an explicit human opt-out is an unresolved choice: explain the contradiction and obtain the
human's decision before treating it as the architecture. An assistant-authored Proposed ADR,
absence of dynamic requirements, silence or a passing helper supplies no opt-out. An Accepted
label alone cannot establish human consent either. Preserve a real human opt-out, its rationale
and the hosting, composition, deployment and exporter responsibilities it changes; support that
choice without a qualification ceremony. Review the exporter separately against its actual
supported contracts; a host proposal does not establish incompatibility.

Resolve profile knowledge before evaluating packages: run installed
`program-kit-building-blocks/scripts/publisher_knowledge.py --target .` without `--profile`
first. It follows captured consumer inputs, or the installed index default for a fresh consumer.
The latter is candidate metadata, not an adopted/restored profile or runtime proof. Read exact
package facts from that result; use an explicit historical profile only for deliberate comparison,
never as the current default. Missing/corrupt captured inputs need repair, not a fallback to new pins.
<!-- /program-kit:knowledge-rule -->

Use ASP.NET Core Minimal APIs as the default built-in HTTP endpoint style when HTTP is required.
Evaluate schema generation/compatibility, route identity, authorization, validation, error contracts,
cancellation and OpenAPI behavior within the selected host. A third-party endpoint framework needs
its own capability gap and decision; vertical slicing does not imply one.

For the Program Kit .NET-to-TypeScript chain, use the effective profile's managed exporter,
`.oasdiff-version` and isolated `openapi-typescript` defaults. `eng/openapi_init.py` initializes
that contract. A custom export utility requires an explicit justified choice and examination of
the real unsupported capability; do not invent one from an unaccepted host proposal.

For modular dependency enforcement, evaluate a deterministic MSBuild/project-graph check and an
assembly architecture test such as ArchUnitNET. Prefer the smallest combination that can fail CI on
forbidden module and feature references, cycles, and unauthorized exceptions.

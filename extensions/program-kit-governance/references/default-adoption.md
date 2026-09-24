# Default adoption

## Executable selection and first use

The bootstrap workflow resolves defaults before validating assessment/research outputs and before
approval. `bootstrap_defaults.py` writes missing structured selections to the existing decision
register and records their source. It never changes confirmed intake or an approved register.
The stage registry and `bootstrap_handoff.py` enforce when the resulting choices must be usable.

When no application language or platform is selected, the managed application default is
.NET with the published Foundation host. Managed BFF/SPA authentication also implies that
dependency. A browser-only explicit anonymous profile does not require an invented backend.
An explicit alternate language or host is preserved: a conflict with managed authentication or
an unavailable engineering adapter must be resolved before adopting that combination.

For managed sign-in without a provider selection, use the shipped Keycloak local adapter for
development and bounded evaluation. Its version/configuration remains owned by the existing web
profile, not by a second bootstrap pin. Production identity hosting is a separate decision due
before production deployment; it does not prevent a local first slice. Preserve an explicitly
selected consumer identity service. Applying this default does not authorize paid infrastructure.

Declare persistence needs structurally per data owner in the existing `persistence` collection.
The shared persistence resolver turns `server-relational` plus an absent/`auto` profile into
`ef-postgresql` for .NET. It preserves explicit profiles and does not infer a durable store from
free text. Assessment must translate confirmed durability needs into this declaration. Provider
selection is distinct from later admission and real-provider behavior evidence.

The register's `first_slice` names source journey IDs, a useful outcome and why that boundary is
small enough. Each unresolved question declares an owner, kind and due stage. Apply a known
default immediately; only consequential questions without a safe default need human answers.
Unattended workers must not treat an asynchronous question as answered. Required answers are
recorded against the exact question at the native handoff, then the user resumes the workflow.

"No additional constraints supplied" is sufficient to adopt an applicable local default. It is
not a claim that no constraints exist. A generic unanswered constraints question must not shadow
resolved defaults with a new architecture blocker. Preserve known conflicts; require facts needed
for an actual present action, and defer production hosting, paid services and operational choices
until those actions become necessary. Default adoption never supplies spending authorization.

## Bootstrap promise

Program Kit produces a complete, opinionated, usable baseline. Human attention is reserved for
deviations, material acknowledgements, and consequential decisions that cannot be answered safely
from the confirmed bootstrap intake or the selected Program Kit profile.

The absence of an explicit project choice is not a reason to leave an ordinary engineering choice
open when an applicable Program Kit default exists. Defaults are authoritative for the baseline but
remain easy to supersede through an explicit intake override or a later Accepted ADR.

## Decision precedence

Browser projects also adopt `ui-experience-v1`: independent brand/layout/CSS/page intent, optional
SVG logo and default Lucide icons, WCAG 2.2 AA target, initial-render public metadata, private export
exclusion, and no default analytics. These are reviewed baseline defaults, not new host middleware
or a forced frontend framework. Override through the normal decision register.

Classify every bootstrap choice by the first applicable source:

1. **Explicit intake**: direct project intent such as "use PostgreSQL" or "Keycloak is the initial
   identity provider". Adopt it; do not reopen it merely because implementation details remain.
2. **Explicit override**: intake or project configuration deliberately replaces a Program Kit
   default. Record the default, override, reason, and affected evidence.
3. **Program Kit default**: apply the selected versioned profile when intake is silent.
4. **Derived default**: apply a low-risk consequence of accepted project shape and guardrails,
   recording the rationale and override path.
5. **Genuinely unresolved**: require human input only when business, legal, regulatory, security,
   financial, tenancy, production, or recovery context makes a safe default inappropriate.
6. **Deferred until triggered**: record decisions that are not yet material. They do not block
   unrelated specifications or implementation.

Words expressing commitment in confirmed intake evidence (`must`, `uses`, `is`, `will`, `initial shape`)
are explicit intent. Examples, alternatives, future directions, and phrases such as `evaluate`,
`such as`, or `for example` remain candidates.

## Adoption evidence

For .NET persistence, apply `program-kit-dotnet/references/persistence-profiles.md` while resolving
data-owner intent: no store means none; server-relational storage inherits EF/Npgsql/PostgreSQL unless
an explicit alternative or existing provider takes precedence. Record the proposal per owner in
`bootstrap-decisions.json.persistence` immediately. Admission, materialized packages and tested
compatibility are separate later evidence; do not ask the user to redesign a selected database merely
because a test harness lacks its service. Research unresolved consumer-owned packages against the
managed pins and record compatibility or a concrete override.

Write `docs/architecture/bootstrap-decisions.json` using schema version `1.0`. It records the
versioned default profile, selected profiles, adopted choices and their sources, overrides,
material acknowledgements, genuinely unresolved decisions, and deferred decisions. Every adopted
choice includes a stable ID, decision, rationale, and easy override path.

The assessment human gate approves the exact hash of the assessment, tooling evaluation, decision
backlog, decision register, and concise review packet. Architecture may then treat explicit intake,
Program Kit defaults, and derived defaults as accepted bootstrap authority under the ratified
constitution. Consolidate them in `docs/architecture/decisions/bootstrap-baseline.md`; do not create
one approval chore per ordinary default.

Project-specific choices outside that reviewed baseline still require the normal ADR process.

## Managed toolchain precedence

Selected Program Kit technology profiles supply exact toolchain and package pins through their
managed manifests. Those pins are baseline authority before current-version research and before
probing the local environment. Research verifies compatibility and maintenance; it does not replace
a managed pin with a current candidate. A missing or older local installation is a remediation
requirement: clearly urge the user to install or upgrade to the exact managed version, side-by-side
where the ecosystem supports it.

Only an explicit user decision may retain a different locally installed .NET SDK as project truth.
Record that exception in `bootstrap-decisions.json.toolchain` with source `override`, a non-empty
reason, and an override entry whose ID is `managed-toolchain-version`. Ordinary managed pins use
source `program-kit-default`, exactly match the selected profile manifests, and need no separate ADR.

When Node remediation is approved but no supported manager is present, stop with an actionable
manager-install instruction rather than choosing or installing one implicitly. On Windows, prefer
the official per-user `fnm` routes (WinGet, Scoop, or the release binary); do not send a
non-administrator shell into an elevation-bound Chocolatey install. After `fnm install`, verify the
pin in the same process with `fnm exec --using=<version> node --version`; parent-shell PATH or profile
activation is not valid immediate verification evidence.

## .NET default

When .NET is selected, the external application-neutral `Orbyss.Foundation.Host` and application release-bundle model are the
automatic runtime default. Consumer repositories create packable feature projects and activation,
configuration, package-closure, and release evidence—not a custom `.Host` project or application
`Program.cs`. Adopt this model unless the confirmed bootstrap intake explicitly opts out. An opt-out records the alternate
host, reason, consequences, and affected managed baseline.

The standard runtime introduces independently pinned Orbyss Foundation, Forms, and Localization packages plus pinned
CShells/Nuplane dependencies and configured package sources. The assessment review packet must
disclose that material supply-chain fact. Approving the assessment records the human acknowledgement;
it does not download packages or run restore. Repository synchronization and networked restore remain
separate actions.

## Secure browser default

When a browser UI and authenticated HTTP boundary are detected, adopt the Program Kit
`bff-cookie-v1` secure web profile unless explicit intake or an Accepted ADR selects another
deployment shape. “SPA” describes the client UI and does not by itself select browser-held bearer
tokens. The same-origin BFF remains the default for React and other SPA frontends.

Select `spa-pkce-v1` only for an independently hosted static client that must call APIs directly, or
when an explicit decision accepts browser token exposure and the profile's renewal, storage, CORS,
and logout consequences. Record the profile and version in the bootstrap decision register. Feature
specifications inherit the chosen profile and must not reopen its ordinary implementation details.

Every authenticated browser adoption also inherits threat model
`program-kit-web-threat-model-v1` and evidence profile
`program-kit-web-security-evidence-v1`. These own the attacker model, source authority/status,
control traceability, configurable-default rationale, residual risks, assurance levels, and review
triggers. A consumer records only its additions and overrides; an override is incomplete without an
owner, affected control/default, evidence, review condition, and regression test.

## Proportional decisions

Do not turn every valid question into an ADR or bootstrap blocker. Close ordinary details through
the applicable default, feature specification, acceptance criteria, or deterministic test. Defer
production topology, workload objectives, legal retention, and recovery objectives until their
lifecycle gates when they do not block the first vertical slice.

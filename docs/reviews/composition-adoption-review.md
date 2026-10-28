# Maintained composition adoption and intake review

Maintenance checkout: `artifacts/worktrees/bootstrap-intake-analysis`, branch
`codex/bootstrap-intake-analysis`, implementation baseline
`d83156f4e7ac0e1235c923c25e2c5ae9afa67faa`. This review extends the separate
[private EF metadata repair](private-ef-design-metadata-review.md). It does not
authorize a consumer migration, replace human story review, or certify agent obedience.
Only synthetic fixtures are retained here. The scoped private consumer was inspected
read-only; its source, credentials, authored architecture and locks were not imported.

## Causes and owning repairs

| Observation | Disposition and owner |
| --- | --- |
| Accepted Foundation selection without an active v2 resource graph | Guidance/discovery gap plus use of a legacy entrypoint. Native phase context now identifies the missing graph without starting the app; the optional scaffold also explains its compatibility scope. [Composition guidance](../../extensions/program-kit-dotnet/references/foundation-compositions.md) puts the maintained route first. Existing guidance was available; file availability cannot prove the agent read it. |
| Missing Json.AspNetCore in the legacy BFF shell | Confirmed template omission, repaired separately in the EF maintenance diff. The typed renderer already included the descriptor dependency closure. This was not evidence of a defective OIDC protocol implementation. |
| Feature-relative constitution link rejected as traversal | Confirmed path-contract defect in [sync readiness](../../extensions/program-kit-governance/scripts/sync_readiness.py). Markdown links resolve against their source document; repository setup targets keep their own confinement rules. Real escape, encoded escape and aliases remain rejected. |
| Exact selected optional Tasks capabilities rejected | Confirmed selection gap in [composition rendering](../../extensions/program-kit-dotnet/scripts/composition_render.py). Feature-owned selected package IDs participate in admission; exact profile/catalog/publisher checks remain authoritative. No prefix-based admission was added. |
| Authored ShellFeature declarations under different filenames | Confirmed reconciliation gap. Inspect declarations and ownership rather than treating a missing generated filename as a missing feature. Ambiguous source requests bounded reconciliation; this is conservative discovery, not a complete C# compiler. |
| Full baseline conflicts with architecture, shell overlays and repaired files | Conflicts remain real. [dotnet_sync](../../extensions/program-kit-dotnet/scripts/dotnet_sync.py) offers explicit `--composition-only` preview/apply through the existing native transaction for configuration adoption. It preserves authored sources, realm/frontend inputs, local repairs and old ownership evidence instead of authenticating them with fabricated hashes. |
| External product secret absent from the generic topology | Supported `configurationEnvironment` binding in [model](../../extensions/program-kit-dotnet/scripts/composition_model.py) and [runner](../../extensions/program-kit-dotnet/templates/dotnet/files/eng/composition_run.py). Missing input rejects before native processes. Product values remain external and separate from generated infrastructure credentials; configuration contains references, not values or value hashes. |
| Read-only provider requires deployed schema and grants | Explicit existing prepare/deployment/run ownership. Prepare provisions owned infrastructure; native EF deployment remains an explicit operation under a deployment identity. Runtime read-only Prepare admits the deployed schema and least-privilege grants. No automatic migrations were added. |
| External React/theme changes absent from source closure | Explicit confined `inputs` and complete tree snapshots in [runtime closure](../../extensions/program-kit-dotnet/templates/dotnet/files/eng/runtime_closure.py) and [HostedPages preparation](../../extensions/program-kit-dotnet/templates/dotnet/files/eng/prepare_hosted_pages.py). Added, changed and removed inputs affect freshness; existing React, SDK assets, branding and lockfiles are preserved. |
| Duplicated public auth presentation and asset serving | Missed native capability in the reported earlier implementation, plus stale guidance favoring a custom writer. [Secure web guidance](../../extensions/program-kit-dotnet/references/secure-web-profiles.md) now leads with selected HostedPages/Web.Presentation and scopes historical fallback examples. Current inspected source delegates to native features; historical removal chronology is not independently established by an unborn Git history. |
| Unsupported PNG ancillary metadata rejected | Correct native admission, not a parser defect. Guidance explains the earlier contract and reviewed deployment-derivative route. No admission rule was weakened; the manifest producer itself is not a PNG decoder. |
| oasdiff 1.34.0 reports ERR but exits zero by default | Confirmed producer invocation defect: [openapi_contracts.py](../../extensions/program-kit-dotnet/templates/dotnet/files/eng/openapi_contracts.py) now supplies `--fail-on ERR`. Independent real-binary controls and the original wrapper reproduce the issue; [regression](../../tests/validate_openapi_breaking_gate.py) preserves exact-review semantics. |

Metadata qualification hashes and retained Forms browser evidence do not establish
a real Keycloak/OIDC journey. Reuse unchanged supplier middleware/client/realm
evidence and run only the affected consumer configuration/login/product checks.
The generic native coding hook stays read-only and starts no Host or browser.

## Coding and constitution assessment

The scoped code review found coherent capability/provider boundaries and
owner-filtered queries. A `Func<IServiceProvider, ...>` at a documented composition
or cold-export seam is not by itself a factory-pattern violation. Review scope,
disposal, context ownership and delayed resolution. Typed admitted configuration
already exists in the inspected source; a repeated string at a composition boundary
is a focused maintainability opportunity, not proof that domain code reads raw
configuration. The [coding context](../coding-context.md) and installed
implementation-check now prompt that semantic review before a pattern is replicated.

A remaining consumer finding is the broad treatment of caller cancellation and
deterministic database failures as storage/commit uncertainty, including read-only
queries. It is source-confirmed, not runtime-reproduced here. Distinguish caller
cancellation, dependency deadlines, deterministic SQLSTATE and potentially committed
post-dispatch effects; preserve reconciliation for the last case. No private source
or test body is copied here, and no consumer correction was performed.

The inspected constitution contains useful ownership, provider separation and
proportional-evidence rules. It also mixes durable constraints with identity,
roadmap and unsettled feature details. A useful constitution should change design,
implementation or review decisions: state a durable rule, its reason, applicability
and a practical way to assess it. Cover significant boundaries/native reuse,
quality scenarios, effects/failure semantics, configuration/lifetimes, evolution
and exception/amendment review where relevant. Keep exact pins in their maintained
selection and changing product details in specifications/ADRs.

[Product founding](../../extensions/program-kit-governance/references/product-founding.md),
the product-intake command and read-only review output now teach that distinction
and present six authoring review questions. Existing C4 export and explicit
constitution/ADR ratification remain separate actual human review points. No fixed
principle count, universal factory/Options/TDD rule, semantic score or approval
receipt was introduced. An already ratified consumer constitution requires its
ordinary amendment review; it was not silently rewritten.

There is no universal industry constitution format. The guidance draws on
[Spec Kit's principles and governance](https://github.github.com/spec-kit/reference/agentic-sdd.html),
[its illustrative template](https://github.com/github/spec-kit/blob/main/templates/constitution-template.md),
[SEI quality-attribute reasoning](https://www.sei.cmu.edu/library/reasoning-about-software-quality-attributes/)
and [ISO/IEC/IEEE 42010 architecture description](https://www.iso.org/standard/74393.html).
These support decision-guiding principles, stakeholder concerns and concrete
quality scenarios; they do not certify this project or mandate every template example.

## Review walkthrough and evidence limits

For a fresh synthetic service, accept the selected Foundation decision, create the
v2 graph with exact qualified pins and native BFF/Keycloak/PostgreSQL resources,
then preview the native configuration. Supply the declared external product secret;
prepare packages/infrastructure; explicitly deploy native EF SQL with the deployment
identity and grant the runtime role only its needed access. Start the generated
Host and test one real login and owner-bound product operation. Reuse that setup on
resume rather than copying protocol code or rebuilding the supplier test suite.

For a retained legacy consumer, inspect the migration proposal and
`dotnet_sync.py --composition-only --check --json` first. Review authored feature
identity seams, shell overrides, realm identities, frontend/SDK/locks and existing
managed-file repairs. Apply only the reviewed native transaction. Whole-baseline
conflicts and product runtime readiness remain separate claims. An exception used
to adopt one consumer is not evidence that every baseline conflict has been repaired.

Focused fixtures exercise feature-relative links, exact capability admission,
authored filenames/ambiguous identities, configuration-only preservation and
rollback, external input add/change/remove, environment projection and secret-name
collision. Actual archive installation checks the shipped output rather than source
text alone. The local
[final evidence index](../../artifacts/composition-adoption-review/final-evidence.json)
records exact execution journals, costs, final native outcome and archive hashes
after source is frozen. It is a local diagnostic, not a release attestation.
Source review, deterministic behavior, observed agent
behavior and actual human acceptance remain distinct.

Final integration checks also exposed premature retirement of customized but
still-selected scaffolds. The renderer now keeps their existing canonical desired
entries so the native reconciliation owner preserves the original hashes and
authored bytes; actual removal of the feature still uses ordinary retirement.
The original retirement assertions were retained. A nested-route unit fixture
also needed the now-explicit empty bindings list, and the knowledge index needed
the new guidance heading. Those fixture/index repairs do not weaken production
validation. Original failed runs remain
`artifacts/validation-runs/20261026T233035Z-e69fef27` and
`artifacts/validation-runs/20261026T233035Z-9f599b49`.

The first final native owner operation passed in 272.281 seconds with independent
external-key HMAC verification and actual disposal. Its enclosing journal
`artifacts/validation-runs/20261026T233028Z-dfee7e73` correctly remains
needs-attention because the guidance index changed concurrently. The retained
`artifacts/t/co-d3670d7d/source-movement.json` identifies that sole change; native
runtime, fixture and emitted-helper inputs were unchanged. The final evidence
index distinguishes this scoped result from the subsequent frozen-source checks.

Earlier bounded evidence is retained independently:

- Original oasdiff wrapper counterexample:
  `artifacts/openapi-breaking-gate/6cc7015e46974e9f93740c834ec59dfd/results.json`.
  Native default returned zero with an ERR; the unchanged wrapper accepted it.
- Corrected real-binary review/threshold scenario:
  `artifacts/validation-runs/20261026T230802Z-bf981d4d/results.json`
  (1.015 seconds for the check; 1.87 seconds including runner overhead).
- Installed native phase review:
  `artifacts/tests/native-phase-review/d9015711c8394610a51ae566441826e4/index.md`.
  This verifies installed instructions and read-only behavior, not agent choices.
- Installed source intake scenario:
  `artifacts/tests/product-intake/6733f46a1d24`; fictional authoring and decisions,
  with C4 export and separately scoped constitution/ADR confirmation.

The optional profile parameter in the existing shared fixture preserves its
default behavior. The focused owner operation exercises the affected native
Host/login/deployment seam. It does not rerun every golden/nested-shell, typed
operation, emitted-CI or paid story scenario merely because those scenarios import
the fixture. External input freshness, authored-source reconciliation and rollback
receive focused regressions; these do not claim whole-baseline consumer repair.

## Release and upgrade boundary

Foundation.Build 0.3.3 is publicly available and qualified as a new Program Kit
default; existing consumer profiles and locks remain unchanged. The exact retained
0.3.7/Build 0.3.2 profile is also exercised for composition compatibility, with EF
Design in a separate nonpackable tooling startup. That does not requalify private
Design inside a packed Build 0.3.2 provider; the separate 0.3.3 native proof owns it.
Follow [workaround retirement](../maintenance/private-ef-design-metadata.md) only
after the original consumer is requalified with its temporary hook absent.

Program Kit changes remain uncommitted and unpublished. Local preview archives are
for the explicitly requested local installation, not public release acceptance.
Exact-source Windows/Linux package CI and disposition of the separate recoverable
Nuplane analyzer-discovery finding remain public release work. Local Firefox cannot
launch on this Windows host; affected Chromium/WebKit checks do not replace CI Firefox.

---
description: Research current architecture, delivery, and quality tooling for the detected context.
---

## Input

`$ARGUMENTS` identifies the confirmed intake and the workflow-generated bootstrap context path.

Read the compact bootstrap stage brief first. Its confirmed intake routing, required full read of
the decision register, managed profile pins, and `stage_plan.observed_toolchain` define the research
scope. Do not run local `--version`, runtime-list, repository-status, or source-tree probes; those
observations and the normalized repository shape are already supplied. Follow `stage_plan.mode` and research only the enumerated
`stage_plan.research_questions`. In `baseline-verification` mode, do not survey competing products:
verify only a material compatibility, support, license, maintenance, or supply-chain risk for the
already selected baseline. Do not print or read the linked evidence index in full. Query one
indexed artifact and heading range only when the brief lacks a fact required for a current research
claim. Do not bulk-read every unchanged bootstrap artifact or enumerate installed files. The source
artifacts remain authoritative when the stage brief identifies missing detail or a hash mismatch.
Use the brief's `governance.paths` and `output_contract` directly. Do not search `.specify`, dump
catalogs, or inspect `governance_state.py` to rediscover paths or contracts already supplied there.
Use `output_contract.artifact_target_bytes` as the initial generation target and
`output_contract.artifact_byte_budgets` as the hard boundary after all writes. Report final byte
counts; do not trade away required evidence merely to reach a target.

For a single-journey baseline verification, compose the first complete
`tooling-evaluation.md` draft in at most 700 words and aim below 5,500 UTF-8 bytes. Do not write a
long draft and trim it toward the target, and do not measure it repeatedly. When updating multiple
files in one patch, use exactly one patch operation per path; never target the same file twice in a
single patch call. Run the supplied terminal validation batch after the write and repair only a
named diagnostic.

## Rules

Use `stage_plan.building_blocks.composition_contracts` when supplied to check managed capability
options before proposing a stack. Distinguish supported managed options from unverified adapter
ideas. If Forms lists Angular, React and Vue renderers, a Blazor proposal remains an explicit
architecture compatibility question; it cannot silently become a selected managed renderer.
Preserve explicit user preferences and assign incompatible proposals to architecture for a
supported choice or a reviewed custom adapter/override, without asking users for placement files.

For selected `ui-experience-v1`, read its profile and `ui-evidence-v1.json`. Preserve the distinction
between standards, provider contracts, bounded empirical findings and experimental conventions.
Use the versioned layout/token/icon/metadata defaults and the isolated pinned acceptance graph;
research compatibility and deviations, not another universal frontend stack. Treat npm download
counts as a dated adoption signal, not market share or proof of design quality.

Use current research rather than memory for version-sensitive claims that are material to the
bounded research plan. Prefer official documentation, specifications, project release notes, and
original research. Record source URL, publication or release date when available, access date,
relevant version, maintenance signals, license, adoption cost, and trust/supply-chain
considerations. Do not repeat general product descriptions or re-research an accepted choice that
has no listed uncertainty.

Read and preserve `docs/architecture/bootstrap-decisions.json`. Research validates explicit intake
choices and Program Kit defaults, supplies current version evidence, and records an override only
when a demonstrated incompatibility exists. It must not demote an explicit choice or default to
Proposed merely because alternatives exist.

Treat `managed_profile_pins` in the stage brief as version-selection authority. Copy its exact
`pins` into `bootstrap-decisions.json.toolchain` with source `program-kit-default` and an empty
`override_reason`. Use current research and the locally installed environment only to establish
compatibility, support status, upgrade guidance, and remediation—not to substitute a newer or older
candidate for a managed pin. If a required managed .NET SDK is not installed locally, urge the user
to install or upgrade to that exact SDK (side-by-side where supported); do not rewrite the pin to
match `dotnet --version`. Retaining a different local .NET SDK requires an explicit user decision,
source `override`, a non-empty reason, and an override record with ID
`managed-toolchain-version`. Never create a separate ADR merely to re-approve a managed pin.

Revalidate generic advice against the detected languages, frameworks, architecture style, team constraints, deployment environment, and risk. A popular tool is not automatically a suitable tool.

Research whether the proposed module and slice boundaries can be enforced with the detected build
system and language toolchain. Distinguish compile-time project or package edges, runtime activation
dependencies, public contracts, and data access. Do not treat framework-supported feature
dependencies or inheritance as evidence that a cross-feature reference is architecturally valid.

## Output

Create or update `docs/architecture/tooling-evaluation.md` with:

- problem/capability first, candidates second;
- mandatory capability versus optional accelerator;
- compatibility with the installed Spec Kit version;
- lifecycle trigger for adopting the tool;
- alternatives and rejection reasons;
- executable enforcement location (local, CI, architecture test, contract test, runtime, or manual gate);
- version pin and upgrade-validation policy;
- explicit review of workflow/extension scripts and permissions before installation.

Evaluate only capability families selected by the normalized brief or required by an accepted
boundary. Do not survey API/schema, web security, secrets, SBOM/provenance, observability,
deployment, or ecosystem-specific tools when their surfaces are explicitly excluded. Record a
single not-applicable statement for excluded families instead of researching individual products.

After research, update the decision register with verified defaults, overrides, material
acknowledgements, genuinely unresolved decisions, and deferred triggers. Validate it against the
standalone bootstrap-decisions schema named by `output_contract`. Preserve its exact item
shapes: an acknowledgement contains only `id` and `summary`; put research evidence, risk detail,
and triggers in `tooling-evaluation.md`, not extra acknowledgement fields. Preserve the exact fields
defined by intake for every other collection. Keep the human-facing decision set small. Move
implementation details into later specifications and adoption triggers rather than creating a
separate blocking ADR for every tool.

Evaluate API Evolve when the project introduces a versioned external API, event, RPC, or schema contract. Evaluate Reqnroll BDD when multistep externally observable behavior benefits from executable examples. Evaluate ArchUnitNET when .NET assembly dependency rules are present. These are evaluation triggers, not automatic acceptance.

When .NET modularity or multi-tenancy is present, evaluate CShells and CShells.AspNetCore against the
triggers and risks in the .NET technology profile. When ASP.NET Core HTTP endpoints are present,
evaluate built-in Minimal APIs and OpenAPI support before adding an endpoint framework.
For the accepted Program Kit .NET OpenAPI chain, treat the managed exporter, `.oasdiff-version`, and
isolated generator defaults as adopted; do not describe oasdiff as an unresolved candidate or create
a tooling ADR unless the project proposes an override.

For a selected .NET profile, `Orbyss.Foundation.Host` is already the Program Kit default unless intake
explicitly opted out. Evaluate compatibility and disclose the preview dependency/source risk; do
not replace that default with a conventional host merely because runtime multitenancy is absent.

Keep research proportional. For a single-language, single-interface, dependency-free local
application, use the target supplied by `output_contract` and research only the runtime plus the
accepted verification mechanism. Report sources and counts after writing; do not print the complete
artifact or a repository-wide diff.

Before reporting completion, run the single command in `output_contract.validation_commands` using
the run ID from the stage brief. It performs output, managed-pin, and assessment-governance checks in
one bounded process. If it passes, stop immediately: do not inspect a diff, remeasure files, read
another source, or run another command. Repair only its named diagnostic, rerun that same batch once,
and stop when it passes.

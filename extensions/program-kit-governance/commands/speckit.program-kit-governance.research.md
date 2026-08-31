---
description: Research current architecture, delivery, and quality tooling for the detected context.
---

## Input

`$ARGUMENTS` identifies the initial design and may include the bootstrap assessment path.

## Rules

Use current research rather than memory for version-sensitive claims. Prefer official documentation, specifications, project release notes, and original research. Record source URL, publication or release date when available, access date, relevant version, maintenance signals, license, adoption cost, and trust/supply-chain considerations.

Read and preserve `docs/architecture/bootstrap-decisions.json`. Research validates explicit intake
choices and Program Kit defaults, supplies current version evidence, and records an override only
when a demonstrated incompatibility exists. It must not demote an explicit choice or default to
Proposed merely because alternatives exist.

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

Always evaluate architecture documentation, ADR management, dependency/architecture tests, linters/analyzers, unit/integration/contract/acceptance testing, API/schema compatibility, security scanning, dependency and secret scanning, SBOM/provenance, observability validation, documentation drift, and repository hygiene when relevant.

After research, update the decision register with verified defaults, overrides, material
acknowledgements, genuinely unresolved decisions, and deferred triggers. Keep the human-facing
decision set small. Move implementation details into later specifications and adoption triggers
rather than creating a separate blocking ADR for every tool.

Evaluate API Evolve when the project introduces a versioned external API, event, RPC, or schema contract. Evaluate Reqnroll BDD when multistep externally observable behavior benefits from executable examples. Evaluate ArchUnitNET when .NET assembly dependency rules are present. These are evaluation triggers, not automatic acceptance.

When .NET modularity or multi-tenancy is present, evaluate CShells and CShells.AspNetCore against the
triggers and risks in the .NET technology profile. When ASP.NET Core HTTP endpoints are present,
evaluate built-in Minimal APIs and OpenAPI support before adding an endpoint framework.

For a selected .NET profile, `ProgramKit.Host` is already the Program Kit default unless intake
explicitly opted out. Evaluate compatibility and disclose the preview dependency/source risk; do
not replace that default with a conventional host merely because runtime multitenancy is absent.

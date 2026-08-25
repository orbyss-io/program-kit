---
description: Research current architecture, delivery, and quality tooling for the detected context.
---

## Input

`$ARGUMENTS` identifies the initial design and may include the bootstrap assessment path.

## Rules

Use current research rather than memory for version-sensitive claims. Prefer official documentation, specifications, project release notes, and original research. Record source URL, publication or release date when available, access date, relevant version, maintenance signals, license, adoption cost, and trust/supply-chain considerations.

Revalidate generic advice against the detected languages, frameworks, architecture style, team constraints, deployment environment, and risk. A popular tool is not automatically a suitable tool.

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

Evaluate API Evolve when the project introduces a versioned external API, event, RPC, or schema contract. Evaluate Reqnroll BDD when multistep externally observable behavior benefits from executable examples. Evaluate ArchUnitNET when .NET assembly dependency rules are present. These are evaluation triggers, not automatic acceptance.


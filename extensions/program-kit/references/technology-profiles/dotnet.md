# .NET profile

When .NET is detected, evaluate and normally enforce:

- current supported SDK/runtime policy pinned in `global.json` where appropriate;
- nullable reference types enabled;
- compiler warnings and selected Roslyn/.NET analyzers treated as errors in CI;
- explicit cancellation propagation for cancellable I/O and long-running work;
- async APIs that do not block or hide background work;
- immutable or deliberately mutable public contracts with compatibility tests;
- central package/version management and locked/repeatable restore as appropriate;
- deterministic builds, Source Link, analyzers, formatting, dependency audit, SBOM, and provenance for distributed artifacts;
- unit, integration, architecture, contract, and acceptance tests selected by risk;
- ArchUnitNET when assembly dependency rules need executable enforcement;
- Reqnroll when business-critical multistep behavior benefits from executable examples.

Framework choices, ORM use, source generators, serializers, test frameworks, and analyzer packages remain project-specific Proposed technologies until accepted by ADR.


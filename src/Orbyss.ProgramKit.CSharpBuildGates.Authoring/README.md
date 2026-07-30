# C# build-gate authoring

This development-only package provides deterministic Roslyn syntax helpers,
optional versioned rule recipes, and transactional scaffolding for
consumer-owned analyzers.

It contains no `DiagnosticAnalyzer`, source-generator, or incremental-generator
registration. Recipe assets are inert until a consumer explicitly supplies its
own semantic owner, rule and diagnostic identities, parameters, applicability
profiles, fixtures, compatibility claim, and suppression policy.

Program Kit public contract analyzers remain Program Kit-owned selections.
Scaffolding records those selections separately and never copies a `PKCC`
diagnostic into consumer-owned source. Scaffolded participation generators
validate the fresh invocation nonce but emit a constant receipt marker and
constant hint name, so freshness evidence does not perturb consumer binaries.

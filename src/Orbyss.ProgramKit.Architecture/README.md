# Orbyss.ProgramKit.Architecture

This package owns domain-neutral architecture contracts and pure semantic
validation. It has no Roslyn, MSBuild, runtime-host, or consumer-application
dependency.

Architecture Design `1.0.0` remains registered and readable. Architecture
Design `2.0.0` retains the v1 contract and requires exactly one exact
`StaticConformanceDisposition@1.0.0` reference.

`StaticConformanceDisposition` records:

- statically decidable invariants and their narrowest reliable enforcement
  layers;
- one explicit `reuse-existing`, `extend-existing`, `create-new`,
  `not-justified`, or `blocked-unavailable` decision;
- selected gates and activation matrices or linked gate designs;
- residual risks and claims outside static proof; and
- the exact human decision source.

An empty gate selection is valid only for `not-justified` with exact human
acceptance. `blocked-unavailable` is a blocking state, never an empty
selection. The v1-to-v2 migration requires the caller to supply the exact
human-selected disposition and never invents one.

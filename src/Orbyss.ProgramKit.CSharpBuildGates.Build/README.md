# Orbyss.ProgramKit.CSharpBuildGates.Build

This development-only package supplies the direct, opt-in mechanics for an
exact consumer-controlled C# build gate. It does not contain policy analyzers
and never discovers one. A validated binding must provide every selected
public Program Kit contract analyzer and consumer-owned analyzer as an exact
`ProgramKitCSharpGateAnalyzer` item, together with finite activation cells and
the complete expected compiler-input inventory.

The package:

- attaches only matrix-applicable analyzer assemblies as compiler analyzers;
- rejects the private `Orbyss.ProgramKit.CSharpGate` on consumer source;
- rejects analyzer substitution, duplication, disablement, warning demotion,
  inventory drift, and post-validation mutation;
- evaluates only the four versioned temporary-exception kinds;
- creates a unique compilation nonce and isolated receipt root while mapping
  compiler document paths to a stable logical root;
- requires a distinct, byte-stable same-assembly receipt from every applicable
  analyzer beneath that isolated root;
- emits a participation receipt or a typed exception-use receipt; and
- runs from normal compiler invocation, including build, test-project, pack,
  publish, and explicitly bound generated-project verification profiles.

The package has no `lib/`, `ref/`, `runtime/`, or `buildTransitive/` assets.
Its task assembly is loaded from `tools/net10.0` only by the direct `build/`
import.

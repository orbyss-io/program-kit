# Orbyss.ProgramKit.CSharpBuildGates.Contracts

This package owns provider-neutral, runtime-inert C# build-gate contract
models and deterministic validators. It contains no Roslyn analyzer,
source-generator, MSBuild activation, environment discovery, assembly loading,
network lookup, mutable registry, or runtime-host dependency.

The `1.0.0` definition makes every policy boundary explicit:

- semantic ownership is `compiler-baseline`,
  `program-kit-public-contract`, or `consumer-owned`;
- Program Kit-private `PKCS` diagnostics cannot appear in a consumer gate;
- `PKCC` diagnostics retain exact Program Kit public-contract ownership;
- consumer diagnostics use a collision-free consumer-owned prefix;
- project, source, generated-source, additional-file, configuration, and lock
  inventories contain exact stable-ordered paths and SHA-256 values, never
  globs;
- activation is a finite conjunctive matrix of project, source, command,
  implementation boundary, verification profile, and analyzer components;
- temporary non-execution uses one finite condition kind with human authority,
  bounded lifetime/use, compensation, and evidence;
- suppressions remain source-local, keep the analyzer executing, and require
  exact reconciliation; and
- selection locks, same-assembly participation receipts, and verification
  evidence preserve distinct typed failure layers.

The package validates declared bytes only. Binding files, running compilers,
evaluating temporary-condition inputs, and executing verification belong to
later explicitly invoked Program Kit operations.

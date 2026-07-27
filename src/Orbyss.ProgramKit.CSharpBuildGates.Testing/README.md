# Orbyss.ProgramKit.CSharpBuildGates.Testing

This development-only package owns the compiler-backed verification harness for
consumer-controlled C# build gates. The public request selects only a finite
gate command, implementation boundary, and verification profile. It exposes no
executable field and no argument list.

The harness:

- requires the exact pinned `dotnet` SDK before executing;
- maps the five gate commands to fixed build/test/pack/publish/MSBuild
  templates;
- validates only explicitly supplied receipt and package paths;
- verifies package/runtime isolation;
- caps and redacts captured process output;
- kills the complete process tree on cancellation;
- promotes evidence atomically only after successful verification; and
- emits stable typed evidence with no local path, timestamp, or duration.

Validation, rendering, scaffolding, and binding do not use this process
boundary and do not load analyzer assemblies.

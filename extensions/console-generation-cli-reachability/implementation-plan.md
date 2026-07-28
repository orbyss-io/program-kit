# Console generation CLI reachability implementation plan

Artifact identity:
`pkid:plan:program-kit:console-generation-cli-reachability@0.1.0-alpha.1`.

Design:
`pkid:design:program-kit:console-generation-cli-reachability@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

This is a transitional, digest-bound implementation plan review artifact. It
does not instantiate the legacy Implementation Plan `3.0.0` contract or
preempt the `0.1.0-alpha.3` contract owned by `PKAV-W020`.

## `PKCG-W010` Bind exact Console generation inputs and close CLI/refresh reachability

Required outcome: `dotnet generate-host console` and `dotnet refresh-host`
construct the already-supported `DotNetConsoleGenerationInput` exclusively
from exact manifest-bound files and complete with integrity-verified generated
output.

Depends on: none.

Allowed edits:

- `schemas/dotnet/` for the new immutable alpha artifact-input manifest schema;
- `src/Orbyss.ProgramKit.DotNet/Inputs/` for the host-keyed Console input
  binding and resolved-input path support;
- `src/Orbyss.ProgramKit.DotNet/Schemas/`,
  `src/Orbyss.ProgramKit.DotNet/Composition/`, and exact schema evidence for
  registration and serialization;
- `src/Orbyss.ProgramKit.CommandLine/Operations/DotNet/` for manifest-bound
  Console input construction shared by generation and refresh;
- `src/Orbyss.ProgramKit.CommandLine/README.md` for the exact manifest journey;
- focused unit/conformance tests and fixtures required to prove the design.

Implementation obligations:

1. Preserve the legacy manifest schema bytes and register the new
   `0.1.0-alpha.1` schema beside it.
2. Add a host-keyed Console manifest binding containing exact binding,
   consumer-assembly, and compilation-reference revisions.
3. Resolve every revision through the existing manifest allow-list resolver.
   Expose or derive a contained physical path only after exact byte
   verification.
4. For a selected Console host, require exactly one matching entry and
   cross-check the Open Console revision, consumer path/digest, reference
   membership, uniqueness, and deterministic ordering.
5. Construct and pass a non-null `DotNetConsoleGenerationInput` to the existing
   coordinator. Keep API and Worker construction unchanged.
6. Add a real composed CLI Console test and a real refresh create/unchanged
   Console journey.
7. Add negative schema/model/service tests for absent, duplicate, default,
   stale, mismatched, unordered, and escaping inputs and prove no generated
   output is left behind.
8. Update exact schema resource digests, schema-model conformance, diagnostics
   documentation where needed, and the CLI README.

Compatibility:

- Legacy API and Worker manifests remain accepted without byte changes.
- Legacy Console CLI invocations become an early explicit input failure rather
  than reaching the coordinator with null.
- The new Console manifest contract is `0.1.0-alpha.1`; later global contract
  progression remains owned by the approved alpha transition.
- No CLI command or option is renamed.

Verification:

- locked restore when dependency state requires it;
- mandatory private Program Kit C# gate through a no-restore solution build;
- focused .NET schema, input resolver, Console command, and refresh tests;
- repository routine and exhaustive conformance profiles;
- changed-file and staged-scope review proving no unrelated dirty work entered
  the commit.

Stop conditions:

- any implementation requires ambient discovery or an unverified file path;
- a Console input can be selected without exact host/document/digest binding;
- API or Worker compatibility changes;
- generated output mutates before complete input validation;
- local publication topology, JTest mutation, package publication, capability
  contracts, or the alpha-transition plan must change;
- the existing private gate or tests fail for this patch;
- any material design deviation is discovered.

Completion:

Commit and push this one bounded work unit. Report its commit immediately so
the waiting consumer agent can retry the backed Console generation flow.

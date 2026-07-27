# Program Kit generated Console command dispatch intent

Status: review input only
Owner: `pkid:domain:program-kit:toolkit`

## Human request

A Program Kit consumer rebuilding JTest 2.0 reported that generated Console
hosts parse their typed Open Console grammar but do not expose the successful
parse to consumer code. The current generated `Program.Main` handles parser
failure and information output, then enters generic host execution and
eventually returns `0` without executing the parsed command.

The reporting consumer is built from Program Kit commit
`74c1abc4379ea3dfc39f624ade22a3a4191787bb`. The same gap remains on Program
Kit `main` at `fe52a2f7bb04dbafe42c65fcec412ae0c1cbc5ae`.

JTest's approved CLI design uses the backed `dotnet generate-host console`
operation and a typed Open Console document. Its process result is derived from
run evidence:

- `0`: every suite passed;
- `1`: any case failed, errored, timed out, or was cancelled;
- `2`: usage, input, or validation failure; and
- `3`: unexpected internal failure.

JTest work unit `JT2-W070` is blocked by explicit human decision because its
approved plan forbids a divergent hand-written host. `JT2-W080` through
`JT2-W100` are downstream. JTest is consumer evidence only; its repository and
domain behavior are not Program Kit design inputs or edit targets.

## Required outcome

A consumer must be able to:

1. author an Open Console document;
2. invoke the backed deterministic Console host generator;
3. implement one consumer-owned command dispatcher in the generated host
   assembly;
4. register that dispatcher and its ordinary consumer services at the
   composition root;
5. receive the successful canonical `Command`, `Options`, and `Arguments`;
6. return an integer process exit code chosen from the consumer's declared
   command contract; and
7. regenerate from unchanged source bytes with byte-identical outputs.

Parser failures and information output retain their current behavior and exit
codes. A successful command parse with no dispatcher registration fails closed
before hosted behavior starts. Program Kit does not silently replace the
missing dispatch with exit code `0`.

## Accepted design constraints

- Keep the generated `GeneratedConsoleParser.cs` and
  `GeneratedConsoleParseResult.cs` bytes unchanged for the same Open Console
  input.
- Keep generated applications free of a runtime reference to the
  `Orbyss.ProgramKit.DotNet` generator package.
- Keep the dispatcher port generated into the host assembly, like the existing
  FastEndpoints dispatcher port, so consumer-owned host source can implement it
  without a new Program Kit runtime package.
- Use explicit composition-root registration. Consumer service and dispatcher
  implementations remain constructor-injected; no static behavioral
  collaborator or ambient dispatcher is introduced.
- Resolve the dispatcher only for a successful command parse. Parse failures,
  help, and completion do not require application composition.
- Resolve required registration before starting configured hosted behavior.
- Start the configured host, dispatch exactly once, stop it in a bounded
  `finally` path, and return the dispatcher's integer unchanged.
- Pass the host application-stopping token to the dispatcher. The consumer owns
  its semantic mapping of cancellation and unexpected failure to declared exit
  codes.
- Record the exact dispatcher contract revision and exact Open Console document
  revision in deterministic generation lock/evidence.
- Preserve the existing Open Console document as the authority for command and
  exit-code declarations. Program Kit does not invent JTest semantics or clamp
  a returned integer to a Program Kit-owned status model.

## Shell compatibility constraint

The current `dotnet-shell` v11 contract requires every host to select at least
one shell identity and requires the base `CShells` package at version `0.0.28`.
This bounded change does not revise that ABI or the shell schema.

A Console command dispatcher may use ordinary consumer services with an empty
feature-activation selection. It therefore requires no CShells feature package
merely to execute one command, while still retaining the existing base shell
composition and package constraint.

Making the base CShells runtime itself optional would require a separate
versioned shell-contract migration and is deliberately outside this request.

## Rejected alternatives

- Do not make consumers edit generated parser or parse-result files.
- Do not require a Program Kit generator package at generated-host runtime.
- Do not use reflection, assembly scanning, static registries, ambient service
  location, hooks, watchers, or provider bindings to discover a dispatcher.
- Do not silently return `0` when a parsed command has no registered
  dispatcher.
- Do not map every consumer exception to a Program Kit-owned exit code; the
  consumer's declared CLI contract owns that distinction.
- Do not import JTest types, evidence models, test semantics, or repository
  conventions into Program Kit.
- Do not broaden this work into a base-CShells-optional shell contract.

## Approval boundary

This intent authorizes design work only. Runtime implementation remains blocked
until a human explicitly approves the exact canonical architecture design and
implementation-plan digests produced from this review set.

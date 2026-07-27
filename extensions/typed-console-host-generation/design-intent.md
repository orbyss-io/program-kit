# Typed Console host generation design intent

## Human-started outcome

Program Kit must generate a complete executable .NET Console host from a
language-neutral Open Console document and an explicit .NET binding document.
The generated project owns its entry point, pinned Spectre.Console.Cli
integration, command tree, typed settings, request construction, deterministic
document validation, consumer-validation orchestration, CShells composition,
help, completion, exit-code handling, and generated-output evidence.

The consumer owns a separate referenced project containing request models,
handler and optional validator contracts and implementations, one Console
`IShellFeature`, and ordinary application services. Consumer code has no
knowledge of generated host types, dependency-injection mechanics, or Spectre.

## Required caller-visible behavior

- Every Open Console command generates typed settings and one generated Spectre
  command.
- Every command maps explicitly to one consumer request constructor and one
  handler contract.
- Generated document validation always runs before optional consumer
  validation.
- Consumer validation returns one or more plain-text messages; failure prints
  them uniformly, exits with the document's invalid-invocation code, and never
  invokes the handler.
- Commands without a consumer validator invoke their handlers directly after
  document validation.
- Handler integers pass through unchanged at the managed entry point.
- Parse, document-validation, and consumer-validation failures use the
  document's invalid-invocation exit code.
- Help and completion describe the declared grammar without composing consumer
  services.
- Exactly one Console shell feature is allowed. Missing or duplicate features,
  handlers, or validators fail closed.
- Regeneration from identical inputs is byte-identical.

## Binding authority

Open Console remains language and framework neutral. It owns command grammar,
logical value types, cardinality, canonical defaults, conflicts,
prerequisites, parsing conventions, help, completion, streams, and host
exit-code roles.

The separate .NET binding document owns CLR metadata names, nullability,
generic arguments, explicit generated symbols, constructor positions and
parameter names, logical-source mappings, mandatory explicit default
dispositions, handler and validator contracts, the single feature type,
consumer project path, and exact reference-assembly identity and digest.

Program Kit verifies the binding against the exact compiled consumer reference
assembly through metadata inspection without loading or executing consumer
code. Candidate generated source is compiled against those exact reference
bytes before publication.

## Generated-output integrity

Every generated host root is entirely Program Kit-owned. Generation emits an
in-tree manifest covering every generated payload file and a sibling external
anchor sealing the manifest. Build and publication verify these bytes.

Ordinary generated drift blocks build, refresh, and publication. A human may
authorize `refresh-host --repair-generated-output`, which quarantines the
drifted tree and regenerates only from authoritative consumer inputs.

No runtime source-tree verification is generated. Normal builds and debugger
launches enforce integrity through a private build target and required
compile-time attestation. Publication independently verifies current source and
build evidence.

## Maintenance flow

Program Kit distributes an installable `maintain-software` capability for
small, explicit, architecture-compatible application changes. It shares the
same backed completion profiles as `implement-software-plan`: refresh affected
derived artifacts, verify integrity, build, test, review, record, commit, and
push.

Each coherent maintenance unit is committed as one reversible historical
event. Program Kit upgrades require explicit approval of an exact version and
occur before the affected refresh. Material architectural changes route to
`design-software`.

Program Kit canonical capabilities are packaged as inert payloads and become
discoverable only after explicit initialization into a selected consumer
workspace. Authoring, building, packing, and fixture verification must not
activate them in this workspace or write user-global provider configuration.

## Accepted dependency and framework decisions

- Spectre.Console `0.55.0`, exact.
- Spectre.Console.Cli `0.55.0`, exact.
- CShells `0.0.28`, exact.
- Spectre parsing is used only where the versioned .NET projection profile
  proves fidelity to Open Console.
- The generated host uses `CommandApp`, an existing-container type registrar,
  `AsyncCommand<TSettings>`, command attributes, branches, and `IAnsiConsole`.
- No second executable parser, generated untyped option dictionary, runtime
  generator dependency, reflection scanning, service locator, interceptor,
  arbitrary converter, hook, watcher, or autonomous loop is introduced.

## Explicit deferrals

- A language-neutral catalog of reusable semantic validation kinds remains
  deferred until real consumer validators provide evidence for generalization.
- Dynamic shell completion is unsupported in this revision.
- External signing and hostile coordinated rewriting of source, verifier,
  anchor, build integration, and repository history are outside the workspace
  integrity threat model.
- Program Kit package publication, release qualification, promotion, and JTest
  implementation remain separately authorized work.

## Approval boundary

Only explicit human approval of the exact canonical
`architecture-design.json` and `implementation-plan.json` digests authorizes
implementation. Approval authorizes the bounded PKTCH-W010 through PKTCH-W110
work units, their required tests, commits, pushes, and final integration into
Program Kit `main`. It does not authorize package publication, release state,
deployment, external consumer modification, or a material deviation from the
reviewed design.


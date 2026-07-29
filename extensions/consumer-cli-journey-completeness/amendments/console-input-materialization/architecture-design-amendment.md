# Program Kit Console input materialization architecture amendment

Artifact identity:
`pkid:design-amendment:program-kit:consumer-cli-console-input-materialization@0.1.0-alpha.1`.

Amends, without changing, the exact approved design
`pkid:design:program-kit:consumer-cli-journey-completeness@0.1.0-alpha.1`
with SHA-256
`9d336e3015daa8a8ec771d8e8aacc29020175a10174df7964d23088656468648`.

State: `ready-for-human-decision`.

## Reason for the amendment

The approved base design proves that the packaged CLI can consume an exact
Console generation input set. New JTest evidence shows that this is not a
complete consumer journey. A clean consumer must first author
`shell.json`, `open-console.json`, `console-binding.json`, and the alpha
artifact-input manifest, including the exact consumer reference assembly and
the complete compilation reference-assembly closure. The removed
consumer-specific `JTest.HostInputs` helper performed that work; it is not part
of Program Kit and must not be recreated.

A cold proof that starts from pre-canned Console manifests would prove only
input consumption and would mask this missing product behavior. The incomplete
local package candidate built during `PKCJ-W010` is therefore not a deliverable.

This amendment adds one product-owned mechanical materialization boundary. It
does not change the base capability-delivery architecture, infer consumer
semantics, or authorize implementation before exact digest approval.

## Required consumer outcome

A clean consumer with only the exact `0.1.0-alpha.2` local package closure can:

1. retrieve the complete capability, command, schema, and troubleshooting
   knowledge for Console input materialization through the installed CLI;
2. supply one typed request containing all consumer-owned semantic selections
   and one explicit consumer project;
3. explicitly authorize a no-restore build of that project;
4. have Program Kit resolve the exact consumer reference assembly and complete
   compiler reference closure from that one evaluated build;
5. receive a canonical, digest-bound, refreshable Console input directory; and
6. pass that directory directly to the existing packaged
   `dotnet generate-host console` command.

No Program Kit checkout, custom helper, project/assembly string inspection,
solution scan, package-feed scan, ambient cache scan, or hand-authored framework
reference list is part of the supported journey.

## Public command

The finite descriptor catalog gains exactly this command:

```text
program-kit dotnet materialize-console-inputs <request> \
  --workspace-root <dir> \
  --output <dir> \
  --build-consumer
```

`--build-consumer` is a required valueless flag. It is the caller's explicit
authority for the command to execute the selected consumer project build. The
command never restores, updates, publishes, runs tests, builds a solution, or
selects another project. Absence of the flag is an invocation error, not a
request to discover prebuilt state.

The command writes only normal build outputs selected by the explicit project
build and Program Kit-owned files under the explicit materialization output. It
does not mutate the project, source, package configuration, global tool state,
canonical Program Kit knowledge, or an existing unowned output.

## Request contract

Add
`pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.1`
and an equivalent strict typed model. The request carries every semantic value
that Program Kit is not allowed to invent:

- request identity, contract version, owner identity, and output-set identity;
- one safe workspace-relative consumer project path;
- consumer project identity and display name;
- exact target framework `net10.0`, configuration, and platform;
- one complete shell intent, including its host identities and exact input
  version-map and version-selection references;
- one complete Open Console intent for exactly one Console host;
- exact feature, validation-result, request, handler, optional validator,
  constructor, generated-symbol, and operation-revision selections required by
  the existing Console binding contract; and
- the safe workspace-relative paths and exact expected digests of any
  consumer-owned version-map, version-selection, or other supplied artifact
  bytes that are copied into the output closure.

The intent shapes are strict, finite, and schema-addressable. They omit only
values that are mechanical results of the selected build or of canonical
serialization: output-relative paths, assembly names, content digests, shell
and document revision digests, manifest entries, ordering, and the compilation
reference closure.

Unknown properties, duplicate properties, duplicate identities, case drift,
defaulted identities, absolute paths, `.`/`..` traversal, symlink/reparse
escapes, unsupported frameworks/configurations, and missing exact digests fail
before build or output mutation.

## Consumer Console integration project seam

The selected project is one consumer-owned **Console integration project**,
separate from the Program Kit-generated host. It is not a contracts-only
assembly and it is not the generated executable. Its exact `TargetRefPath`
assembly owns the complete binding-visible seam:

- one public concrete request type per Open Console command;
- one public nongeneric handler interface per command;
- the optional public nongeneric validator interface per command;
- the one public validation-result type;
- exactly one public, sealed, concrete, nongeneric, parameterless Console
  `IShellFeature`;
- one public, sealed, concrete, nongeneric handler implementation per handler
  contract and, when selected, one equivalent validator implementation; and
- the ordinary application services composed by that feature.

The canonical consumer-facing naming convention for a command named
`Run` is `IRunHandler`; the exact metadata name remains an explicit request
selection rather than a name Program Kit guesses. Regardless of its selected
name, every handler contract has exactly this structural shape:

```csharp
public interface IRunHandler
{
    ValueTask<int> HandleAsync(
        RunRequest request,
        CancellationToken cancellationToken);
}
```

The generated host creates no handler contract and contains no consumer
implementation. It has one one-way `ProjectReference` to the selected Console
integration project, constructor-injects the exact selected interface, and
calls `HandleAsync`. The selected `IShellFeature` registers exactly one
unkeyed scoped concrete implementation for each selected handler interface and
zero or one unkeyed scoped implementation for each optional validator.

The materializer validates this seam against the exact selected reference
assembly before it promotes any input. It refuses an internal, class, generic,
missing, duplicated, wrong-request, wrong-return, wrong-method, or
wrong-cancellation-token handler contract. It also refuses a binding-visible
request, handler, validator, validation result, feature, or implementation that
is absent from the selected integration assembly, and refuses missing,
duplicate, keyed, factory, instance, open-generic, or wrong-lifetime
registrations through the existing generated-host composition proof.

A dedicated contracts-only project plus a separate implementation/composition
project is not supported by this revision. Supporting that split would require
an explicit two-project binding, two independently digest-bound assembly
closures, generated project-reference changes, and expanded metadata and
constructor verification. Program Kit must stop and route that request back to
design rather than silently treating either project as the current single
integration project.

The embedded materialization guide includes this topology, the minimal exact
request/handler/optional-validator/validation-result/feature skeletons, and the
registration rules. The request schema alone is not presented as sufficient
authoring guidance.

The guide is registered under the exact supporting-resource identity
`dotnet-console-input-materialization-guide`. It gives a consumer AI session a
complete, ordered authoring recipe:

1. create one ordinary consumer-owned `net10.0` class library outside every
   Program Kit-owned/generated root;
2. add the exact current `CShells.Abstractions` and
   `Microsoft.Extensions.DependencyInjection.Abstractions` package references
   required by the selected feature and registration seam, with the reviewed
   exact versions and restore/source-policy warning;
3. add one public concrete request, one public
   `I<Command>Handler`-convention interface, and one public sealed concrete
   implementation per Open Console command;
4. optionally add the exact validator interface and implementation;
5. add the shared public validation-result type;
6. add exactly one public sealed parameterless `IShellFeature` and register
   each handler and optional validator as one unkeyed scoped
   implementation-type registration;
7. express every CLR metadata name, request constructor mapping, and project
   path in the semantic materialization request;
8. call `dotnet materialize-console-inputs` with that request and explicit
   build authority; and
9. call the existing `dotnet generate-host console` with the emitted
   `shell.json` and `artifact-manifest.json`.

The guide contains a complete minimal class-library project file and compiling
C# source example, not pseudocode fragments. Its package versions and source
must be conformance-tested against an isolated consumer project built only from
the release candidate feed and reviewed external sources. The example must
exercise one handler and one optional validator and must map one-to-one to the
materialization-request example.

Program Kit never writes or edits this consumer-owned source project. The
capability and guide give the AI the rules; the human-started consumer
development flow owns source authoring. Program Kit writes only the explicit
owned materialization output and generated-host output, and both remain
lock/digest protected.

## Exact project-build and reference-closure boundary

After request, path, ownership, and output preflight, Program Kit invokes the
installed `dotnet` executable without a shell against only the selected project:

```text
dotnet build <project> --configuration <configuration> \
  --framework net10.0 --no-restore
```

The command uses the repository's existing contained process runner and
cancellation behavior. Missing restore assets are a setup blocker with an
actionable diagnostic; the materializer never weakens source mapping or adds a
feed.

After a successful build, Program Kit invokes a finite `dotnet msbuild`
evaluation against the same project and identical global properties to obtain
`TargetRefPath` and `ReferencePathWithRefAssemblies`. This is an evaluated item
query, not a filesystem, solution, feed, or cache scan. Program Kit accepts only
one managed consumer reference assembly and a finite non-empty compilation
reference set. The generation compiler closure is the exact union of that
consumer `TargetRefPath` and the evaluated
`ReferencePathWithRefAssemblies`; the consumer reference must occur exactly
once in the union.

Every selected file is opened read-only, contained to the exact path returned by
the evaluated project, hashed, copied into a content-addressed staging path, and
hashed again. References are ordinally ordered by managed assembly identity and
digest. Identical duplicate results are collapsed; duplicate assembly
identities with different bytes, missing files, non-managed files, changing
bytes, path aliases, and the consumer reference assembly occurring zero or more
than once fail closed.

The complete compilation reference set comes only from the exact evaluated
build. Program Kit does not inspect arbitrary assemblies, search SDK packs,
walk NuGet caches, infer missing references, or contact a feed.

## Canonical output set

The materializer emits one owned directory containing:

- canonical `shell.json`;
- canonical `open-console.json`;
- canonical `console-binding.json`;
- canonical copies of the exact supplied version-map, version-selection, and
  other declared consumer artifacts;
- content-addressed read-only copies of the consumer reference assembly and
  every compilation reference assembly;
- canonical `artifact-manifest.json` using the existing
  `pkid:schema:program-kit:dotnet-artifact-input-manifest@0.1.0-alpha.1`
  contract and exactly one `consoleGenerations` row for the selected host; and
- `.program-kit-console-inputs.lock.json` using new schema
  `pkid:schema:program-kit:dotnet-console-input-materialization-lock@0.1.0-alpha.1`.

The lock binds the materializer contract, exact Program Kit CLI version, request
digest, project path, framework/configuration/platform, build command contract,
consumer reference digest, ordered reference closure, output-relative paths,
and every output digest. It is ownership and freshness evidence, not approval.

The existing `dotnet generate-host console` command consumes the emitted
`shell.json` and `artifact-manifest.json` unchanged. It continues to validate
all exact input bytes and never invokes the materializer implicitly.

## Transactionality, refresh, and determinism

All Program Kit output is rendered and verified in a bounded staging directory
under the selected output parent before promotion. The final directory is
promoted atomically only after every schema, semantic, metadata, digest, and
cross-reference check passes.

For an absent output, the result is `created`. For an output carrying an exact
Program Kit materialization lock whose owned bytes still match, the command
rebuilds and reevaluates the selected project, then reports `unchanged` for
byte-identical current results or atomically reports `updated` for a changed
current closure. A modified owned file, missing owned file, unowned collision,
unexpected file, unsupported prior lock, or concurrent transaction is
`refused`; it is never repaired silently.

Two clean materializations from identical request and build bytes must produce
identical content bytes and lock evidence after excluding only the caller-chosen
absolute output root. Output paths inside artifacts are always normalized
forward-slash relative paths. JSON is strict canonical UTF-8 without a BOM.

Cancellation or failure may leave the explicitly authorized ordinary consumer
build outputs, but it leaves no promoted partial Program Kit input directory
and no lock claiming ownership of incomplete bytes.

## Validation and failure behavior

The materializer aggregates request/schema diagnostics before the build.
Post-build diagnostics bind a stable Program Kit ID, exact request path or
evaluated item, expected contract, bounded remediation, and stop condition.

At minimum it fails closed for:

- missing or stale supplied artifact digest;
- project or output path escape, symlink/reparse escape, or path alias;
- unsupported target framework/configuration/platform;
- missing restore state or failed consumer compilation;
- zero, multiple, stale, or changing consumer reference assemblies;
- empty, missing, escaping, non-managed, or changing compilation references;
- duplicate reference paths or divergent duplicate assembly identities;
- semantic binding values absent from the request;
- Open Console operations not reconciling one-to-one with binding intent;
- metadata mismatch in feature, validation, request, handler, validator, or
  constructor contracts;
- a contracts-only project, a binding-visible type or implementation outside
  the selected Console integration assembly, or a handler interface whose
  exact `HandleAsync` seam is not satisfied;
- existing modified/unowned materialization files;
- output transaction interruption; and
- any attempt to run in Program Kit's authoring workspace.

The command never fills a semantic field with a guess and never treats build
success as authority or approval.

## Capability knowledge closure

The embedded payload gains the
`dotnet-console-input-materialization-guide` supporting resource. The exact
command descriptor, request schema, lock schema, existing shell/Open Console/
binding/artifact-manifest schemas, diagnostic entries, and guide are registered
in the knowledge closures of `design-software`, `maintain-software`,
`implement-software-plan`, and `publish-dotnet-application-locally`.

Canonical procedures tell the agent to retrieve and describe the materializer
and retrieve this exact guide before designing, creating, or refreshing the
Console integration project or its generation inputs. The general
troubleshooting resource covers build, reference evaluation, stale input,
ownership, and transaction diagnostics. Schemas alone are not claimed to be
the full instructions, and an agent is not expected to reverse-engineer an
assembly, fixture, package, or error sequence to learn the seam.

This writes consumer-owned operational inputs, not Program Kit canonical
knowledge. The base read-only knowledge-plane boundary remains unchanged.

## Cold-consumer acceptance change

The final `PKCJ-W010` cold proof must start from:

- the packed alpha.2 flat feed;
- an isolated tool path, package cache, NuGet configuration, and empty consumer
  workspace;
- consumer project source and explicit semantic request fixtures; and
- no pre-canned shell, Open Console document, binding, artifact manifest,
  reference assembly, or framework reference closure.

The installed CLI must materialize the complete input set, generate a real
Console host from it, and verify the generated host. The proof must show that
all materialized reference paths are output-relative copies selected by the
explicit evaluated project and that no source checkout/project reference/custom
helper supplied product behavior.

## Compatibility and versioning

This is additive product behavior inside the not-yet-delivered coordinated
`0.1.0-alpha.2` candidate. It does not select or increment the product version.
Existing generation contracts and `dotnet generate-host` syntax remain stable.
The request and materialization-lock contracts begin independently at
`0.1.0-alpha.1`. Any future incompatible contract change advances its own alpha
revision and requires explicit migration behavior.

No existing immutable schema bytes or approved base design/plan bytes change.

## Static conformance disposition

Disposition: `reuse-existing`.

This amendment reuses the Program Kit repository-scoped gate
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0` with digest
`sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`
and activation matrix
`pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`
with digest
`sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`.

The gate remains a repository requirement, not a newly designed gate per
review set. The new materializer's containment, deterministic ordering,
explicit-process, no-DOM, and dependency-boundary invariants are compatible
with that active gate.

## Explicit non-goals

- Recreating `JTest.HostInputs` or any consumer-specific helper.
- Inferring shell, Open Console, CLR binding, identity, approval, or authority
  semantics from source or assemblies.
- Restoring packages, selecting feeds, changing NuGet configuration, scanning a
  solution/cache/SDK directory, or contacting a network source.
- Running tests, publishing packages, creating a GitHub Release, or mutating
  JTest.
- Combining input materialization and host generation into an implicit command.
- Supporting frameworks other than the current exact `net10.0` contract.

## Acceptance

Implementation is acceptable only when:

1. help and `commands describe` expose every input, side effect, authority
   boundary, output, diagnostic class, and example;
2. all new and referenced schemas are retrievable from the installed package
   and the relevant capability closures are mechanically complete;
3. `dotnet-console-input-materialization-guide` contains a complete compiling
   class-library project, source, registration, semantic-request, materialize,
   and generate sequence whose exact package versions are validated in the
   cold consumer;
4. the retrieved guide makes the single Console integration project, public
   per-command `I<Command>Handler` interface, exact `HandleAsync` signature,
   implementation ownership, feature composition, and unsupported
   contracts-only split explicit;
5. one request plus one explicit project is sufficient to materialize every
   Console generation input;
6. the evaluated build, not a scan or hand-authored list, supplies the complete
   compiler reference closure;
7. semantic values are copied only from the request and all mechanical values
   are exact deterministic projections;
8. create, unchanged, update, refuse, cancellation, and interrupted-transaction
   behavior is proven without partial promoted output;
9. missing/stale/escaping/duplicate/changing reference and malformed or
   split-project handler-seam negatives fail closed;
10. two isolated clean materializations are byte-identical;
11. the package-only cold proof materializes, generates, and verifies a real
   Console host without pre-canned generated inputs;
12. package inspection proves no custom JTest helper, source checkout pointer,
    authoring marker, or unlisted capability knowledge is shipped; and
13. the full build, 584-or-higher unit suite, routine conformance, exhaustive
    repository gate, payload verification, package inspection, and cold proof
    all pass before the one atomic `PKCJ-W010` commit and push.

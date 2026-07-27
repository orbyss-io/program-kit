# ProgramKit Development Tools validation report

## Result

The review set is ready for an explicit human decision. Design artifacts only
were created. No executable-tool contract, Console proof, adapter, MCP server,
registration, provider binding/wrapper, capability, permission, or runtime
behavior was implemented.

Canonical design:
`6ec7ac36df528e838ec2423d6f2bf3838e27b31edd93f5c09a66c3730b1f44b2`.

Canonical plan:
`3b44ee514087fc6934a094766453434f9e9d0f6f04f84d909438fe2eb4752e85`.

## Repository source truth

- ProgramKit start commit:
  `b4b14cd88a1e931531cbcdeddc2c2273ad96f4f4` on `main`.
- The ProgramKit worktree was clean at intake. The parent repository already
  reported its `program-kit` gitlink as modified and that state was preserved.
- Current Console source generates a host-local dispatcher contract, resolves
  exactly one implementation, starts the host, dispatches once with the
  application-stopping token, returns the consumer integer, and stops in a
  finally path. The design uses these current bytes rather than older Console
  assumptions.
- Current CommandLine composition backs validation, normalization, digest,
  .NET generation, local package preparation/publish, and capability operations.
  General render/graph/check operations are not registered.
- Existing local package preparation and NuGet source mapping already provide
  the required package-only foundation.
- Existing provider adapters initialize development-capability skills; they do
  not define a generic executable-tool contract or provider registration flow.

## Review split

Development Tools owns executable identity, invocation/access semantics,
provider transport, explicit registration lifecycle, and cold discovery.
Corrective Reconstruction owns source ownership, migration decisions,
reconstruction, and conformance evidence. Neither needs the other to meet its
acceptance proof. Combining them would couple unrelated approval and ownership,
so they are separate review sets with no cross-dependency.

## Validation performed

- JSON syntax passed for canonical design, canonical plan, provider evidence,
  and 12 acceptance fixtures.
- `JsonSchemaWorkbenchValidator` passed the canonical architecture schema
  `pkid:schema:program-kit:architecture-design@1.0.0`
  (`19606f994af588d3d48284391af3880e1ade0315980189ad681026d7e43976e2`).
- `ArchitectureDesignValidator` passed.
- `JsonSchemaWorkbenchValidator` passed the canonical plan schema
  `pkid:schema:program-kit:implementation-plan@2.0.0`
  (`119bc1a17ed4f1c2eef193e5c0c75df0c7c4ea9b33b55d206b871bca4614c32d`).
- `ImplementationPlanDocumentValidator` passed.
- The two schema/semantic checks ran as two focused tests in a temporary
  review-only harness. Both passed; the harness and its converters were removed.
- Plan/design digest binding, requirement/trace equality, uniqueness, serial
  dependency ordering, fixture-id uniqueness, and Markdown digest projection
  binding passed.
- `dotnet restore ProgramKit.sln --locked-mode` passed.
- The unit-test project rebuilt with the mandatory C# gate: zero warnings and
  zero errors.
- `dotnet test ...UnitTests.csproj --no-build --no-restore` passed 451 of 451.
- `git diff --check` passed.
- Scope validation found only the two new ProgramKit extension review
  directories; no existing runtime, parent-repository, or website path changed.

The full conformance executable did not complete within a clean bounded
124-second run and produced no test result; its orphaned process was stopped.
It is not cited as passing or failing product evidence. This design-only review
does not require runtime conformance closure; PKDT-W020 through W050 require the
focused and full acceptance evidence after approval.

The general Workbench Markdown renderer was invoked and returned `PKCLI004`
because its explicit adapter is not registered. Reviewer Markdown was therefore
authored as a projection and mechanically checked against the canonical design
and plan digests. Renderer availability is not cited as evidence.

## Provider authority and assumptions

Official Codex documentation currently defines trusted project-scoped
`.codex/config.toml`, MCP stdio configuration, server requirements, timeouts,
tool allow/deny lists, and approval modes. Stable MCP `2025-11-25` defines
tool discovery/call, schemas/results, stdio transport, cancellation, progress,
and security expectations. Exact URLs and governed facts are captured in
`provider-contract-evidence.json`.

Assumptions:

- the project remains trusted between isolated sessions;
- Codex and stable MCP contracts remain materially compatible at PKDT-W030;
- the current Console generator remains the approved proof baseline;
- exact local NuGet packages and controlled source mapping remain available.

Material provider drift is the one canonical open decision and blocks PKDT-W030.

## Deliberate deferrals

Deferred: provider-native binding, plugins, remote MCP, additional providers,
instructional skill workflow, Development Tool repository split, package-feed
publication, release, deployment, website projection, and any autonomous
behavior. Canonical technical documentation stays in ProgramKit or a later
owning Development Tool repository.

Implementation remains blocked until the human approves review set
`pkid:approval:program-kit:development-tools-review-set@1.0.0` and both exact
canonical digests.

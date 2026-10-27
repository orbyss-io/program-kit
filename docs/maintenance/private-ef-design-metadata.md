# Private EF Design metadata repair

`PrivateAssets=all` controls a dependency's exposure to downstream NuGet consumers.
It does not establish that the declaring feature can run without that dependency.
The descriptor producer and selected-root staging must preserve genuine private
runtime dependencies and transitives shared with runtime code.

Foundation.Build 0.3.2 infers host requirements from runtime DLL presence without
separating development roots. EF Design 10.0.13 contains runtime DLLs but declares
`developmentDependency=true`. Its exclusively tooling dependency branch can then
become a host requirement which native runtime staging correctly refuses to admit.
The maintained publisher repair belongs to Foundation.Build; Program Kit also
repairs its separate blanket exclusion of private direct runtime roots.

The corrected contract derives requirements from the exact selected restore
target, consumed runtime assets and verified package metadata. Development/build
roots do not independently seed runtime closure. Dependencies reachable from real
runtime roots remain required, including shared tooling transitives. Contradictory
runtime requirements and ambiguous identities remain errors. Explicit publisher
requirements retain their declaration authority.

Keep EF package/tool versions, native migration execution, immutable package bytes,
content hashes, freshness checks and final PKR014 closure validation intact. Do not
repair this by editing restored packages or completed archives, removing every
private dependency, or staging EF tooling to satisfy incorrect inferred metadata.

## Qualification and adoption

An unpublished Foundation.Build candidate is a development input only. Record its
exact package identity/hash and qualify its installed native task. Program Kit
adopts a public publisher release through the existing dependency-profile
maintenance owner, retaining historical profiles and consumer locks. A local
candidate feed or manually changed central pin is not profile qualification.

The repaired public publisher is Foundation.Build **0.3.3**. Its qualified default
profile is
`foundation-0.3.7-build-0.3.3-exporter-0.2.7-forms-0.2.1-localization-0.1.2`.
Foundation runtime 0.3.7, EF Design/tool 10.0.13 and other selected product pins
remain unchanged. Existing consumers retain their prior profile until its native
reviewed transition is accepted; the new default does not rewrite their locks.
See the [repair review](../reviews/private-ef-design-metadata-review.md) for exact
public package, qualification and installed-output evidence.

Use synthetic projects for graph and package regressions. Qualification must
inspect the descriptor inside a fresh native package, stage the ordinary selected
closure, run native EF migrations and activate the actual selected published Host.
Database migration success alone does not prove packaged Host activation. An
anonymous BFF endpoint proves that endpoint's activation, not login or browser
session acceptance.

The native EF 10.0.13 migration generator emits inline builder delegates/chains
that conflict with the selected authored-source readability rules. The focused
qualification retains the raw migration and checks its complete pinned baseline
before applying a readable, synthetic equivalent of the native operations. It
preserves the generated identity, designer and snapshot, then checks native SQL,
model drift and real database effects. This proves the reviewed migration path;
it does not claim the unmodified generated migration passes those analyzers.

The published Nuplane loader also has a separate fallback asset-admission issue:
an analyzer-only package can enter managed assembly discovery when it has no
ordinary runtime assets. EF Core's legitimate nuspec closure includes
`Microsoft.EntityFrameworkCore.Analyzers`, whose missing Roslyn dependency produces
a recoverable discovery warning. The native EF feature and BFF endpoints can still
activate. Preserve that warning as an upstream finding; do not add Roslyn runtime
requirements or remove a legitimate NuGet closure entry to silence it. The owning
[Nuplane loader](https://github.com/valence-works/nuplane/blob/f1d1dc2b7c2f22829c8bb8d053e875216f44889a/src/Nuplane.Loading/PackageLoader.cs)
and [CShells discovery](https://github.com/valence-works/cshells/blob/b7611aadb49789d3b282749df18ffe68d0eacec5/src/CShells/Features/FeatureDiscovery.cs)
define that behavior. This repair supplies no claim that all tooling DLLs are
excluded from runtime discovery.

The BFF baseline also selects `Orbyss.Foundation.Json.AspNetCore`, as required by
the selected BffCookie 0.3.7 descriptor. Verify emitted/installed shell selection as
well as package presence.

## Retiring a consumer pre-pack workaround

Retain an authorized local workaround until the corrected publisher release and
Program Kit integration have been qualified for that consumer. Preserve original
failure logs and repair audits.

1. Adopt the qualified maintenance update through ordinary owned-file/profile
   reconciliation, preserving authored project references and custom build targets.
2. In disposable synthetic qualification first, omit the local repair hook and
   regenerate build, package and staging outputs using the native owned commands.
   Confirm that the maintained producer creates the corrected descriptor itself.
3. Requalify the application in a consumer-owned isolated checkout with that local
   hook removed and the qualified publisher selection applied. Keep private
   application sources outside this repository. An old-version-specific repair
   script can intentionally refuse the new publisher; do not weaken its guard.
4. After successful consumer requalification, remove only the
   `CoverageRepairPrivateEfDesignMetadata` target from the reproduction consumer's
   `Directory.Build.targets`, then delete `eng/local_ef_design_metadata.py` if no
   other consumer target uses it. Preserve the Program Kit import, other consumer
   targets, EF Design `PrivateAssets` reference and native EF tooling. These names
   identify the scoped temporary repair; they are not product installation files.
5. Repack and inspect the resulting archive, stage it with integrity checks, run
   migrations and exercise the staged Host with the hook absent. Retain the new
   evidence separately from the original failure and workaround evidence.

Do not retire the workaround solely because a source change, graph test or
publisher release exists. Published, installed and consumer-qualified are distinct
outcomes.

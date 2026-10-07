# Application engineering

This directory is application engineering source/configuration. Keep it with the application.
Its commands do not import Spec Kit extensions, governance validators, decisions or AI workers.
The repository's native projects, dependency locks, analyzer configuration, contract baselines,
architecture policy and deployment inputs are the engineering authorities.

From the repository root (PowerShell and Python are normal engineering prerequisites):

```powershell
./eng/Restore.ps1 -LockedMode
./eng/Invoke-RepositoryVerification.ps1
python eng/openapi_pipeline.py --repository .
./eng/Build.ps1 -LockedMode
```

Restore uses the pinned SDK and repository NuGet routes. Verification runs the consumer's
eng/verify.ps1 when supplied, then compiled architecture checks; otherwise it runs the standard
build/tests. Build also stages the application release bundle for the selected published host.
Contract generation runs registered contracts and compares their baselines. A deliberately accepted
contract change can update its baseline explicitly; never bypass an unexpected compatibility failure.

Declare actual project roles and scoped dependency exceptions once in eng/architecture.json.
For affected design, include responsibilities with a meaningful name, kind, effects and optional
provided capability names. For example, a Core `NamePolicy` uses `pure-policy` with `effects: []`;
a persistence-calling `NotesService` uses `runtime` in an implementation project with
`effects: ["persistence"]`. Each supplied capability also needs its normal binding to that
implementation. Contract/pure-policy/pure-helper belong in Core; provider mechanics use a provider
project. Existing unrelated manifests retain their structural scope; review missing metadata in
the selected design before dependent source work. Metadata detects declared contradictions;
normal review must check the actual responsibilities and governing constraints.
Development uses explicit scopes rather than the acceptance pipeline at every checkpoint:

```powershell
./eng/Invoke-RepositoryVerification.ps1 -Scope Focused -Projects tests/Notes.Tests/Notes.Tests.csproj
./eng/Invoke-RepositoryVerification.ps1 -Scope Affected -ChangedFrom <implementation-base> -Plan
./eng/Invoke-RepositoryVerification.ps1 -Scope Affected -ChangedFrom <implementation-base>
```

Focused builds named test projects and runs their native MTP tests; `-TestArguments` accepts the
selected framework's filters as an argument array. Each selected module must execute at least one
test. Discovery/help, suppressed exits, hidden response files and zero-test overrides cannot turn
this into an empty green run. It does not pack, stage, start services or execute unrelated browser
tests. Use `-Restore` only for changed locks/packages or missing restore assets. Default compilation
is Debug for these development paths; acceptance retains the Release build.

Affected includes the complete Git comparison from the retained implementation baseline to the
current worktree, including committed, staged, unstaged, untracked, deleted and renamed inputs.
`-ChangedPaths` can instead supply the complete known delta. It selects reverse project dependencies,
tests for shared build inputs, and explicitly owned non-source inputs. A feature directory is context,
not evidence that other callers are unaffected. New and previously failing cases remain part of
the required development work. Inspect `-Plan` without executing tests; unknown ownership blocks
narrowing rather than silently invoking all tests. Reuse unchanged successful results honestly;
relevant external/runtime/environment changes can invalidate them independently of Git.
Ordinary Spec Kit design/checklist Markdown and constitution text are context rather than native
build inputs: checking off tasks does not select unrelated tests. Explicit test-group mappings
still take precedence. A context-only delta requests reuse/design review and executes no tests;
it never claims an empty test run passed. Delivered contracts and application guides need their
actual engineering mapping; arbitrary Markdown is not automatically excluded.

Ordinary literal project graphs need complete projectReferences in eng/architecture.json, checked
against project source. Dynamic/imported graphs, browser journeys, custom executable oracles and
provider provisioning can use an optional consumer-owned **eng/verify-scoped.ps1**, accepting Scope,
Projects, TestArguments, ChangedPaths, ChangedFrom, FeatureDirectory, Configuration, Restore and Plan.
That adapter must compute current evaluated dependencies, require actual selected tests, retain
failed results and preserve relevant contracts/provider/security checks. A scoped adapter never
replaces eng/verify.ps1 at full acceptance. Both are fixed contained regular file paths.

Only non-source mappings need optional eng/verification.json; it is ordinary test configuration,
not a feature proof or approval dossier. For example:

```json
{"schemaVersion":1,"testGroups":[{"id":"notes-wire","projects":["tests/Notes.Tests/Notes.Tests.csproj"],"inputs":["contracts/notes/**"]}]}
```

Progress saves, task batches, story checkpoints and resumes earn focused/affected checks, not full
acceptance. Complete feature/domain closure or formal review handoff runs the default command once.
The fallback builds the solution once and inspects its current assemblies without a second project
build loop. Opaque consumer eng/verify.ps1 scripts still receive an independent fresh graph build;
the wrapper cannot infer their actual build coverage safely. All original contract/package checks
remain in the full acceptance/build path. -Scope Acceptance cannot be combined with narrowing flags,
and -Mode Release cannot be combined with development scopes.

Before affected implementation, validate planned roles, edges and Core-owned capability bindings:
`python eng/repository_architecture.py --repository . --manifest eng/architecture.json --planned`.
This command performs no restore/build or receipt mutation. Keep Core, runtime implementations,
API and provider mechanisms in separate compilation projects; one bundle/deployment does not merge
their ownership. Namespace waivers and role relabeling cannot authorize a mixed project. List every
selected owned runtime capability binding; compiled verification also detects unlisted implementations.
Native MSBuild/compiled assemblies supply real dependencies. Separation applies when those
responsibilities exist; pure Core utilities and empty initial graphs remain valid. Graph passes
establish structure, while registration/resolution tests and semantic review assess behavior.
An exception needs a rationale and an
existing verification test. Record the substantive approval in normal review or an ADR. No document
hash or ratification receipt is needed to compile. Domain semantics and security behavior still need
application tests and code review; green analyzers alone cannot establish them.

Generated files, caches and logs belong under ignored artifacts/. Keep deployment source, native
locks, analyzer policy, tests and baselines in Git. A human can edit projects and run these commands
with no AI, .specify/, .program-kit/, specifications or governance documents installed.

## Application receiver handoff

Select stable identity and explicit component/package/API bindings in `eng/application-handoff.json`.
This consumer-owned input references existing authorities; it contains no configuration values or
feature definitions. New scaffolds deliberately leave identity and coverage unresolved. For existing
applications retain the exact ID from the last released application-bundle.json, even if a directory
was renamed. A missing/invalid ID blocks new description with PKH004; old descriptors retain schema
version 1 and remain readable. Never rewrite old released identities.

Author delivered guides under docs/application/ and declare each category included, missing or
not-applicable with a reason. Documentation/runtime/settings are required; assets and data migrations
are conditional. Components bind package IDs and registry contract identities, without specifying
processes. All staged runtime packages and registered APIs require bindings. Include actual static
assets/Dockerfiles only where the application owns them. Migration descriptors have `artifact`,
`owner`, `invocation`, `compatibility` strings, pointing to real contained artifacts.

Settings producers emit `eng/settings-metadata.schema.json` envelopes from source declarations:
owner, scope, complete flag, source-file SHA256 map, supported settings and semantic constraints.
Each setting supplies path/type/required/secret/constraints/binding/ordered precedence/reload/
description, and a supported non-secret default if available. Export through a separate offline
metadata code path sharing actual validation/default declarations; never start storage, discovery
or application initialization. The assembler reads files and checks sources; it dispatches no
exporter commands. Do not infer metadata from sample hostsettings values. Secret settings cannot
have exported defaults/examples. The selected SPA-PKCE structural schema is included when present,
but does not establish complete framework semantics. Publisher-owned Foundation/CShells/Nuplane
metadata is a required upstream dependency; absent coverage stays explicit and blocks ready output.
Declare application-owned and schema1 required owner/scopes in requiredSettingsScopes,
including each applicable shell. Schema2 package metadata also supplies source-bound
applicability: selected feature identities or configured section prefixes make its scopes
required, imported scopes remain required, and Host scopes always apply to the selected Host.
Do not delete required scopes simply to make a release green.

Build stages artifacts and runs the existing API compatibility/client pipeline; staging alone is
not a release. After native verification/build and ordinary offline settings export, describe the
bundle with the existing release_bundle.py command and the exact publicly verified host digest,
then assemble:

```powershell
python eng/public_availability.py --target . --catalog eng/building-blocks.catalog.json --evidence artifacts/building-block-public-availability.json
# release_bundle.py describe requires the exact host repository/tag/digest from this evidence.
python eng/application_handoff.py --repository .
python eng/verify_handoff.py artifacts/handoff/application-handoff.zip
```

The retained verifier is installed from the single maintained public_availability.py implementation.
The catalog is rendered through the existing dependency profile/selection mechanism; the existing
eng/building-blocks.lock.json remains authoritative. After a reviewed selection/profile transition,
sync retains that exact catalog under eng/. An empty legacy catalog requires reviewed selection
and sync; never substitute today's catalog or arbitrary version pins. Consumer mode does not use
`--all` or toolkit profile resolution. Release still checks public availability, exact host digest,
repository verification, closure/compatibility and attestation before publication.

`--draft` emits an explicitly incomplete inventory for review, requiring real described bundle
inputs; release never uses it. Ready assembly rejects missing/stale/conflicting references and
unsafe/secret-bearing inputs. The generated index/archive/checksum live under ignored artifacts/handoff/.
Runtime application-bundle.zip stays unchanged; the receiver archive accompanies it. CI uploads
source/contract inputs, without labeling those as a completed release. Release attests and distributes
both runtime and receiver outputs. Generation performs no publication.

Receivers verify the archive checksum against trusted delivery evidence, extract with ordinary ZIP
tools, then run `python verify_handoff.py application-handoff.zip` outside the source/toolkit. The
index paths are relative to the receiver archive; feature descriptors remain inside package files.
Hashes check integrity, not whether authored prose is true or whether a registry exhausts all APIs.
Review actual behavior/tests and maintain registrations when delivered interfaces change.

Packaged FeatureDescriptors remain the authority for feature identity, dependencies, routes and
publisher-required API coverage. The receiver index points to the canonical (or historical legacy)
descriptor member inside each package; it does not copy feature definitions into another registry.
Assembly rejects an activated `requiresContractCoverage` feature with no registered contract in its
shell. This lower bound cannot establish exhaustive registration of all implemented interfaces;
application review/tests still maintain that registry. The receiver archive also carries its format
schemas under format/ and ordinary engineering instructions when present.

For a publisher package containing Foundation Build settings companion schema 1,
list a consumer-owned JSON reference among category `settings.files`:

```json
{"schemaVersion":1,"kind":"foundation-package","packageId":"Orbyss.Foundation.Json","packageVersion":"<exact selected version>","packageSha256":"<sha256 of selected nupkg>","scope":"json-profile"}
```

Use `eng/settings-package-reference.schema.json`. Assembly reads the actual selected
runtime-closure package, verifies ID/version/hash and its compiled assembly binding,
and carries the unchanged publisher metadata under metadata/settings/ for readers.
Required settings ownership is the publisher package ID plus its declared scope.
Publisher source hashes are package-owned provenance, not paths in the application.
Json's code-construction scope does not satisfy applicable Host/shell/Nuplane requirements.
Historical schema1 metadata and references retain their original meaning.

Schema2 package references use the same fields with `schemaVersion: 2`. They admit
nullable and nested settings and imported defaults bound to the actual selected owning
package, metadata bytes and implementation assembly. Select only an independently
qualified Build/runtime release; adding format support alone does not change package pins.

The selected Foundation Host supplies its own offline binding metadata at
`/app/.orbyss-foundation/host-settings.json`. For each actual Host scope, include a
consumer-owned reference among `settings.files`:

```json
{"schemaVersion":2,"kind":"foundation-host-image","scope":"host-transport","evidencePath":"contracts/host-oci/evidence.json","evidenceSha256":"<sha256 of retained evidence>"}
```

The evidence names the exact descriptor's immutable Host image reference and selected
platform, plus contained paths/hashes for the OCI index when present, manifest, config
and every ordered layer. Its `nativePackages` records retain each native origin's exact
package ID/version, contained archive path and SHA256 separately from application
packages/component selections. Retain those bytes from that actual image and its
proven native package closure. The assembler and
independent receiver verify the hash chain, sizes, layer content and overwrite/whiteout
semantics, compiled Host/native origin assemblies and metadata source snapshots.
Host binding metadata is owned by Foundation's integration producer; vendor origins
identify their actual packages, source commits and source bytes. An extracted JSON file
or Docker image ID alone cannot establish this authority. Missing Host contracts or
unverified evidence keep the handoff incomplete; no sample defaults fill the gap.

Schema2 receiver archives include both `verify_handoff.py` and `handoff_contract.py`.
Keep them together when running the verifier outside the source/toolkit. The index
records the settings authority inputs so the receiver independently rechecks actual
package, Host and applicable/imported scope completeness.

Settings admission is bounded: 2 MiB metadata, 32 publisher contracts, 512 source hashes,
256 settings/default items, 128 semantic/precedence strings, 4 Ki-character declaration
text, 16 KiB constraints and 16 Ki-character string defaults. Oversized inputs fail rather
than becoming ready handoffs. Compiler-conditioned and skipped/design-time publisher
exports need supported owning semantics; the current source candidate explicitly rejects them.

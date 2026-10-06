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
Native MSBuild/compiled assemblies supply real dependencies. An exception needs a rationale and an
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
Declare every required owner/scope in requiredSettingsScopes, including each applicable shell.
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
Keep applicable host/shell/Nuplane requirements until their owners deliver coverage;
Json's code-construction scope does not satisfy those requirements. Build 0.2.0 is a
source candidate, not an available public dependency; no selection/version pins change here.

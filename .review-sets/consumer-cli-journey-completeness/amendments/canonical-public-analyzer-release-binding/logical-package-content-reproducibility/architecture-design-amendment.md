# Canonical public-analyzer logical package-content architecture amendment

Artifact identity:
`pkid:design-amendment:program-kit:canonical-public-analyzer-logical-package-content@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

This amendment preserves the exact approved Architecture Design
`pkid:design:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.3`
with SHA-256
`59315e450e33a79a39dc1079e1587d6a6747c3343714e3dd8957fff0dddd47d5`
and exact approved Implementation Plan
`pkid:plan:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.3`
with SHA-256
`3b49633d6bfecd0894cef27b5f5baddc71bb02ad492e7084e65b2fb48d9ccc30`
as historical authority. It changes only the package-output reproducibility
boundary for `PKRB-W030` and the dependent evidence semantics in
`PKRB-W040`, `PKRB-W060`, `PKRB-W070`, and `PKRB-W080`.

No implementation or publication is authorized by this artifact.

## Reason for the amendment

The first exact `PKRB-W030` verification run used the pinned .NET SDK
10.0.302 in two clean absolute roots. Every selected package's ordinary
entries, including its DLLs, portable PDBs, NuSpec, and payload resources,
were identical. The only observed differences were NuGet-generated Open
Packaging Convention bookkeeping:

- the random filename of the single
  `package/services/metadata/core-properties/*.psmdcp` part; and
- the corresponding relationship ID and target in `_rels/.rels`.

The core-properties document bytes themselves were identical. Reordering ZIP
entries and fixing their timestamps, attributes, and compression cannot remove
the difference because the random value occurs in an entry path and in XML
entry content.

The approved design requires the repository-owned canonical writer both to
make the complete nupkg byte-identical and to reject any change to an
SDK-produced entry path or content. SDK 10.0.302 cannot satisfy both
requirements. The existing GitHub publication boundary instead builds once,
attests one exact artifact, downloads the same artifact by ID, reverifies it,
and publishes it without rebuilding. That boundary is safe but was not
reflected in the stronger W030 raw-byte acceptance condition.

## Decision

Release identity is split into three deliberately different claims:

1. `candidatePackageSha256` identifies one exact unsigned candidate instance
   produced and attested by one canonical-build run. It is not claimed to be
   reproducible by a later independent SDK pack.
2. `packageContentDigest` identifies the validated logical package contents.
   It is reproducible across clean roots and remains comparable after
   NuGet.org adds its repository signature.
3. `publishedPackageSha256` identifies the exact repository-signed nupkg that
   NuGet.org serves to consumers.

The release workflow must publish the exact attested candidate instance; it
must never rebuild merely to recover the same `candidatePackageSha256`.
Independent clean-root verification proves compiler-output and logical
package-content reproducibility rather than equality of volatile unsigned ZIP
bytes.

## Logical package-content projection

The repository-owned package inspector computes `packageContentDigest` only
after all of the following fail-closed validation:

1. Every entry path is ordinally unique, forward-slash separated, relative,
   non-traversing, and free of empty path segments.
2. An unsigned candidate contains no `.signature.p7s` entry. A published
   package contains at most the exact supported repository-signature entry,
   which is excluded from the logical projection only after signature
   verification.
3. `_rels/.rels` is safe XML with DTD and external resolution disabled and
   contains exactly one internal core-properties relationship of the expected
   OPC relationship type.
4. That relationship resolves to exactly one contained
   `package/services/metadata/core-properties/*.psmdcp` entry. No second,
   unreferenced, external, escaping, or ambiguously cased core-properties part
   is accepted.
5. Every non-core relationship, non-volatile attribute, ordinary entry path,
   and ordinary entry byte remains exact.

The digest projection replaces only the validated physical core-properties
relationship ID and target with fixed logical tokens and assigns the resolved
core-properties document a fixed logical path. It hashes that document's
exact bytes and every other non-signature entry's exact ordinal path and bytes.
It does not drop `_rels/.rels` wholesale, ignore arbitrary XML differences, or
rewrite the nupkg merely to make its raw SHA-256 agree.

Any difference outside the finite volatile fields is a content mismatch and
fails. Any future SDK change that adds another volatile field is a material
finding, not an automatically ignored value.

## Candidate and manifest boundary

Each canonical-build run records the exact candidate filename, byte length,
`candidatePackageSha256`, and stable `packageContentDigest`. Its
`package-manifest.json`, `SHA256SUMS`, provenance, and attestations bind that
run's exact package instances.

Two-root verification compares:

- analyzer and representative first-party assembly and portable-PDB digests;
- the complete manifest-selected package ID/version/role/dependency closure;
- every package's `packageContentDigest`;
- a semantic manifest projection that excludes only run-specific raw nupkg
  hash and byte-length fields; and
- the finite observed raw-package differences, which must be attributable
  only to the validated OPC core-properties relationship identity.

The two per-run package manifests and checksum projections are not required to
be byte-identical because they honestly record different exact candidate
instances. They must each be internally exact and must project to the same
logical package inventory.

## Publication boundary

The integrated-main workflow remains the sole producer of the publishable
unsigned candidate instance. It:

1. performs the exact manifest-selected build and pack once;
2. validates and records exact candidate and logical-content identities;
3. closes provenance and attests every exact subject; and
4. uploads one immutable artifact without a packaging rebuild.

The later human-started publication workflow selects an exact successful main
run and artifact ID, verifies the artifact digest, internal provenance, exact
candidate hashes, and attestations, and publishes those same bytes. After
NuGet.org repository-signs the analyzer package, the workflow verifies the
signature, records `publishedPackageSha256`, and compares the normalized
logical package-content projection with the attested candidate before
finalizing the catalog or publishing any remaining package.

The existing analyzer-first partial-publication and mismatch-safe resumption
boundary remains unchanged. A retry accepts an already published analyzer only
when its signature, exact recorded published hash where available, and logical
content identity all agree.

## Security and assurance consequence

This amendment retains the properties that protect the consumer journey:

- byte-reproducible compiler outputs;
- one finite manifest-selected package closure;
- deterministic logical package contents;
- exact per-run candidate hashes and attestations;
- no build between candidate verification and publication;
- repository-signature verification and candidate-to-published content
  equivalence; and
- exact published-package identity in the installed selection catalog.

It deliberately relinquishes only the stronger claim that independently
running SDK 10.0.302 can recreate the same unsigned ZIP bytes. That claim adds
independent artifact reconstruction but does not change analyzer behavior,
NuGet restore behavior, package dependencies, or the repository-signed bytes
consumers download.

## Static-conformance disposition

Disposition: `extend-existing`.

The exact historical disposition
`pkid:static-conformance-disposition:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.2`
with SHA-256
`cd8adf3db8caf4f0b719fbc4e5ad7cdf730aac94802288535559e10d93c664a0`
is preserved. The established Program Kit private C# source-quality gate and
its active selection lock remain the correct owners for changed C# source.
No new analyzer or diagnostic family is justified.

For this amendment, the disposition's package-output reproducibility invariant
is narrowed from complete raw nupkg equality to complete logical
package-content equality plus immutable exact-candidate publication. Its layer
remains executable test. The release-path convergence invariant now means the
same exact attested candidate instance, selected by manifest and artifact ID,
flows from the integrated-main build to publication without rebuilding.

## Alternatives deliberately not selected

- Rewriting the OPC relationship and core-properties path would recover raw
  nupkg equality but would require custom mutation of NuGet-produced package
  internals contrary to the approved fail-closed content-preservation rule.
- Upgrading the pinned SDK could delegate deterministic packing to a newer
  NuGet implementation, but it broadens the toolchain change, requires local
  installation and full compatibility verification, and is not required for
  safe alpha.3 publication.
- Replacing SDK pack with a complete repository-owned packer would create an
  unnecessary package-format implementation and maintenance boundary.
- Ignoring `_rels/.rels` or all core-properties metadata during comparison is
  too broad; the finite semantic projection above validates the relationship
  before normalizing only its generated identity.

## Non-goals

This amendment does not authorize:

- package publication, workflow invocation, tagging, release creation,
  deployment, promotion, or unlisting alpha.2;
- installation of another SDK or the published Program Kit CLI;
- weakening compiler-output reproducibility;
- accepting package-set, NuSpec, dependency, payload, signature, or ordinary
  relationship differences;
- ambient package discovery or a second package-selection path;
- mutation of historical review artifacts or their literal historical paths;
  or
- implementation before exact design and plan amendment digest approval.

## Residual risks and stop conditions

- The publishable unsigned candidate depends on preservation of the exact
  attested GitHub artifact until publication. The workflow must fail if the
  selected artifact is absent, expired, replaced, or unverifiable.
- A future SDK can change OPC structure. Any structure outside the exact
  validated single core-properties relationship stops implementation for
  review.
- Cross-operating-system logical-content equality remains a release
  qualification obligation after two Windows roots agree.
- NuGet.org signature behavior and service availability remain external facts
  verified only in the later human-started workflow.
- If stable content equivalence requires excluding or normalizing any field
  beyond the finite relationship ID/target and resolved core-properties path,
  implementation stops for a new human decision.

## Approval boundary

Approval of this amendment supersedes only the raw-package reproducibility
requirements of the exact approved base plan. `PKRB-W010` and `PKRB-W020`
remain complete. `PKRB-W050` remains unchanged. `PKRB-W030`, `PKRB-W040`,
`PKRB-W060`, `PKRB-W070`, and `PKRB-W080` resume only under the separate exact
plan-amendment digest.


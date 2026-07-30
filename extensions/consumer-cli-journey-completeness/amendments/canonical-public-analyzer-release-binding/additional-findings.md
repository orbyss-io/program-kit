# Additional alignment audit

The consumer report exposed a release-binding problem broader than one missing
CLI field. The following related mismatches were found while tracing the
selection from compiler output through package publication and cold-consumer
verification.

## Controlled-packaging amendment findings

### Raw NuGet.org bytes are not locally reproducible

NuGet.org repository-signs every uploaded package and adds or countersigns
`.signature.p7s`. The raw repository-signed nupkg SHA-256 consumed from
NuGet.org therefore cannot equal the reproducible unsigned candidate SHA-256,
and a local builder cannot reproduce Microsoft's private-key signature.

The original acceptance language incorrectly required one raw digest to be
both locally reproducible and equal to NuGet.org's modified download. The
amendment splits:

- `candidatePackageSha256` for exact reproducible unsigned producer bytes;
- `packageContentDigest` for ordered signature-independent entry contents;
- `publishedPackageSha256` for exact NuGet.org repository-signed consumer
  bytes.

The gate's `packageSha256` uses the published digest. The workflow verifies the
repository signature and every non-signature entry before connecting that
published identity to the candidate.

### The deterministic-pack SDK assumption named unavailable functionality

The original design treated .NET SDK 10.0.400-or-later as an installable
implementation dependency even though the repository and supported public
toolchain currently stop at 10.0.302. That made `PKRB-W030` depend on a future
feature band.

The amendment keeps 10.0.302 pinned and owns canonical package-envelope
production in the repository. SDK pack remains responsible for valid package
contents and NuSpec relationships; the bounded canonical writer owns safe
entry validation, ordinal ordering, fixed timestamps and attributes, and
stored payload envelope bytes.

### A same-version CLI catalog creates a publication-time phase boundary

An alpha.3 CLI cannot contain the raw NuGet.org-signed alpha.3 analyzer digest
before that analyzer is uploaded and signed. Finalizing the catalog entirely
before publication is therefore impossible without either using a later CLI
version or changing package-digest semantics.

The selected lifecycle publishes or verifies the exact analyzer candidate
first, obtains and verifies the signed package, injects the final catalog into
the already-built CLI package, repeat-packs and cold-verifies the remaining
closure, then publishes the rest. This accepts explicit irreversible partial
alpha.3 state if a later phase fails; safe retry verifies exact existing bytes
before resuming.

## Included in the alpha.3 plan

### GitHub and NuGet alpha.2 identify different package bytes

The historical GitHub handoff evidence records analyzer nupkg SHA-256
`96cf2d7fd2cff80b4d10a00d11e2375318cec3639af89ed451070eb699e6b8b5`.
NuGet.org serves SHA-256
`282a10899e45c302cb0ba879b01f9ff6bf92bee0a73fd5c996ad77a4dee22a6c`
for the same package ID and alpha.2 version. A release manifest is therefore
not automatically a NuGet consumer authority. `PKRB-W060` makes both channels
bind one canonical unsigned candidate, one signature-independent content
identity, and the exact repository-signed NuGet.org package the consumer
downloads.

### Generator-revision references are shape-checked but not execution-linked

The gate currently validates and orders `receiptGeneratorRevisions`, but a
well-shaped caller-provided digest does not prove that the named generator
produced the generated output. This explains why a fabricated internal digest
can appear to work. `PKRB-W040` adds immutable dotnet-host descriptors and
requires generated-output evidence to match the declared revision.

### Compiler participation evidence changes the bytes it is meant to attest

A fresh random nonce enters generated source/hint identity, while absolute
source paths are not normalized. This makes the analyzer assembly and portable
PDB depend on invocation and checkout root. `PKRB-W020` moves freshness to
external evidence and normalizes compiler inputs.

### Local and workflow packing have different package-set authorities

The local release-manifest packer selects 29 source packages, while the GitHub
workflow enumerates source directories and separately invokes `nuget pack` for
the consumer meta-package. The manifest also omits that meta-package. The two
paths can therefore produce a different closure even if individual projects
are deterministic. `PKRB-W030` and `PKRB-W060` establish one complete
manifest-selected pack.

### The existing cold-consumer proof does not prove the published journey

The current proof substitutes a fake analyzer and supplies an internal digest.
It can validate plumbing while missing the precise consumer failure in this
report. `PKRB-W070` restores only public packages and exercises the real
describe, migration, lock, bind, and verify sequence.

### A schema descriptor exists without an operational migration path

The CLI calls alpha.1 legacy and describes the alpha.2 schema, but it does not
provide a loss-rejecting transition for an existing consumer document.
`PKRB-W050` assesses exact incompatibilities, preserves conforming data, and
materializes only when no information is lost.

### Historical conformance evidence must not be rewritten around the amendment

The exact approved static-conformance disposition and active selection lock
record the original future-SDK residual risk and original gate-design digest.
They are evidence for the already completed `PKRB-W010`, not mutable current
packaging instructions. Rewriting them would invalidate the exact selection
lock and require gate re-establishment.

The amended architecture, gate design, and `PKRB-W030` through `PKRB-W080`
supersede that implementation premise without changing the enforcement
allocation: the disposition remains `extend-existing`, while repository-owned
canonicalization on 10.0.302 replaces the future-SDK dependency. The amended
plan deliberately leaves `PKRB-W010` and `PKRB-W020` bound to the originally
approved architecture-design input digest. `PKRB-W010` also consumes the
amended gate-design digest so the current plan remains semantically closed;
renewed approval explicitly accepts the existing establishment evidence
against that mechanically amended, statically unchanged gate.

## Recorded follow-up, not a separate alpha.3 expansion

### Exact verification-profile references drift when the profile changes

The requested synchronization with current `origin/main` changed
`build/Invoke-CSharpGateTestPlan.ps1` from SHA-256
`80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`
to
`2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f`
without changing its identity or version. Every work unit in the approved plan
binds that file by exact digest, so the synchronized source made the approved
plan inadmissible even though the product architecture did not change.

The synchronized plan mechanically rebinds its eight references. The active
selection lock and completed W010/W020 evidence remain historical proof of the
profile used at execution time; they are not silently rewritten during design.
After exact synchronized-plan approval, implementation preflight must refresh
the derived active lock/evidence chain and rerun the gate before `PKRB-W030`.
This is another instance of the broader alignment risk: independently
versioned, digest-bound artifacts need an explicit regeneration or migration
path whenever their bytes change.

The public JSON validation command checks schemas, while repository-internal
typed validators enforce additional semantics. During this review, artifacts
could pass schema validation and still fail typed validation for identity,
version, or establishment-output rules. The alpha.3 artifacts are required to
pass both. A later consumer-journey review should decide whether the public
validation command should expose the same semantic checks for all supported
artifact families; that broader CLI contract is not silently added to this
release-binding amendment.

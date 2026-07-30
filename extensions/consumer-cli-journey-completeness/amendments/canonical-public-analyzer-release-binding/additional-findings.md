# Additional alignment audit

The consumer report exposed a release-binding problem broader than one missing
CLI field. The following related mismatches were found while tracing the
selection from compiler output through package publication and cold-consumer
verification.

## Included in the alpha.3 plan

### GitHub and NuGet alpha.2 identify different package bytes

The historical GitHub handoff evidence records analyzer nupkg SHA-256
`96cf2d7fd2cff80b4d10a00d11e2375318cec3639af89ed451070eb699e6b8b5`.
NuGet.org serves SHA-256
`282a10899e45c302cb0ba879b01f9ff6bf92bee0a73fd5c996ad77a4dee22a6c`
for the same package ID and alpha.2 version. A release manifest is therefore
not automatically a NuGet consumer authority. `PKRB-W060` makes both channels
use one selected package file.

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

### The pinned SDK cannot provide the planned deterministic pack semantics

The current pin resolves to .NET SDK 10.0.302. The deterministic package plan
requires the first approved 10.0.400-or-later SDK with the needed pack
normalization. This is an explicit implementation prerequisite, not an
implicit environment upgrade.

## Recorded follow-up, not a separate alpha.3 expansion

The public JSON validation command checks schemas, while repository-internal
typed validators enforce additional semantics. During this review, artifacts
could pass schema validation and still fail typed validation for identity,
version, or establishment-output rules. The alpha.3 artifacts are required to
pass both. A later consumer-journey review should decide whether the public
validation command should expose the same semantic checks for all supported
artifact families; that broader CLI contract is not silently added to this
release-binding amendment.

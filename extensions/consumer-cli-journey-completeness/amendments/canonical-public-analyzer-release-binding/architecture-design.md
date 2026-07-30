# Canonical public-analyzer release binding

Canonical source:
`architecture-design.json`

Canonical SHA-256:
`59315e450e33a79a39dc1079e1587d6a6747c3343714e3dd8957fff0dddd47d5`

State: amended and ready for human decision. `PKRB-W010` and `PKRB-W020`
remain completed and evidence-bound. No controlled package canonicalization,
published-evidence finalization, remaining product implementation, or
publication is claimed.

## Outcome

Program Kit alpha.3 will make a published analyzer selection an installed,
offline CLI capability. The unsigned producer package closure will be
reproducible without waiting for a future SDK, and the human-started GitHub
workflow will reconcile those controlled candidate bytes with NuGet.org's
repository-signed published bytes before it packs the same-version CLI. The
consumer receives exact, ready-to-embed published-package, assembly, and
generated-output generator-revision references without inventing Program
Kit-internal evidence.

The command boundary is:

```text
program-kit csharp-gate describe-public-analyzer-selection \
  --package-version <version> \
  --format json
```

The returned component contains the canonical `artifact` and
`receiptGeneratorRevisions` fields. The installed catalog owns the values; the
caller supplies only the selected published version.

## Architectural decisions

1. Keep alpha.2 listed and immutable. Backfill its catalog row from the actual
   NuGet.org package, not from a local rebuild or the historical GitHub
   handoff package.
2. Store the public selection catalog as installed command-line package data
   after the CLI assembly is finalized. This avoids a package self-digest
   cycle.
3. Model `pkid:generator:program-kit:dotnet-host` as its own immutable
   generator-revision descriptor. Its digest is the descriptor file SHA-256,
   and generated-output evidence must prove that the selected revision ran.
4. Remove random and absolute-path data from compiler-produced source, hint
   names, documents, assemblies, and portable PDBs. Preserve fresh invocation
   evidence outside compiler outputs.
5. Keep the supported .NET 10.0.302 SDK pinned. Pass every SDK-produced
   unsigned package through one repository-owned canonical profile using
   ordinal safe entry paths, the fixed `1980-01-01T00:00:00Z` ZIP timestamp,
   zero external attributes, and stored payloads. Reject signatures, duplicate
   or unsafe paths, and any changed entry content.
6. Record three distinct identities: reproducible unsigned
   `candidatePackageSha256`, signature-independent `packageContentDigest`, and
   the exact NuGet.org repository-signed `publishedPackageSha256` used as the
   gate's `packageSha256`.
7. Include the consumer meta-package in the same manifest-selected SDK-pack and
   canonicalization path.
8. After explicit human start, let GitHub Actions publish or verify the analyzer
   first, download and verify the NuGet.org-signed package, compare all
   non-signature content, finalize and repeat-pack the CLI catalog, run the cold
   proof, and only then publish the remaining package set.
9. Treat analyzer-first publication as an accepted irreversible phase:
   mismatch stops; a matching safe retry verifies and resumes; no workflow
   overwrites or rolls back a package.
10. Assess alpha.1 definitions rather than silently rewriting them: preserve
   already conforming fields, report exact incompatible paths, and produce no
   output on loss.
11. Extend the existing private C# source-quality gate and establish its
   negative fixtures before changing product behavior.
12. Keep publication outside implementation authority. The human runs the
   GitHub workflow only after candidate and workflow-conformance evidence are
   complete.

NuGet.org adds or countersigns `.signature.p7s` after upload. A local builder
therefore does not and cannot reproduce the raw repository-signed package
SHA-256. The workflow proves that the signed package contains the exact
canonical candidate content, then records both identities honestly.

## Historical alpha.2 authority

- NuGet analyzer nupkg:
  `sha256:282a10899e45c302cb0ba879b01f9ff6bf92bee0a73fd5c996ad77a4dee22a6c`
- Analyzer DLL within that nupkg:
  `sha256:7ec050ca9434657060b8e18400fc8d2db26424424e1840925abe383c4bc4e8e1`
- Historical GitHub handoff nupkg:
  `sha256:96cf2d7fd2cff80b4d10a00d11e2375318cec3639af89ed451070eb699e6b8b5`

The GitHub handoff digest names different alpha.2 bytes and is not a valid
substitute for a NuGet.org consumer binding.

## Approval boundary

The earlier approval remains the authority for completed `PKRB-W010` and
`PKRB-W020`. The human approved the amended product boundary against plan
digest
`0821ef64266769c79e68b5754a585ca9452aa6eb2b44e2b0668c50ae20fe88e5`.
The requested `origin/main` synchronization then changed only the exact
verification-profile input, so implementation remains paused pending approval
of synchronized plan digest
`3b49633d6bfecd0894cef27b5f5baddc71bb02ad492e7084e65b2fb48d9ccc30`.
That approval authorizes the amended `PKRB-W030` through `PKRB-W080` against
the exact canonical JSON digest above, the unchanged gate design digest
`c739d476e2d0589caa02e940b7f8257af190882602fa66f857bf6fee8c244e3c`,
and the `extend-existing` disposition digest
`cd8adf3db8caf4f0b719fbc4e5ad7cdf730aac94802288535559e10d93c664a0`.
It does not authorize package publication, tagging, release creation,
deployment, or promotion.

# Canonical public-analyzer release binding

Canonical source:
`architecture-design.json`

Canonical SHA-256:
`dee52330c5da79a68bc4869b8f140faed02347d36f49119e6fd673258170fdb1`

State: ready for human decision. No implementation or publication is claimed.

## Outcome

Program Kit alpha.3 will make a published analyzer selection an installed,
offline CLI capability and will make the package closure that supplies that
selection reproducible. The consumer receives exact, ready-to-embed package,
assembly, and generated-output generator-revision references without inventing
Program Kit-internal evidence.

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
5. Use explicit path mapping, deterministic compiler settings, a pinned
   10.0.400-or-later .NET SDK, a fixed ZIP-compatible package timestamp, and
   one manifest-selected package closure.
6. Include the consumer meta-package in that closure and make local
   qualification and GitHub Actions consume the same pack outputs and
   evidence.
7. Assess alpha.1 definitions rather than silently rewriting them: preserve
   already conforming fields, report exact incompatible paths, and produce no
   output on loss.
8. Extend the existing private C# source-quality gate and establish its
   negative fixtures before changing product behavior.
9. Keep publication outside implementation authority. The human runs the
   GitHub workflow only after candidate evidence is complete.

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

Approval authorizes implementation work units `PKRB-W010` through
`PKRB-W080` against the exact canonical JSON digest above, the gate design
digest
`f668b6746af54d64ea26bc5d56e91fa7c0dccffdd3e030ed7d92da08f87dcb70`,
and the `extend-existing` disposition digest
`cd8adf3db8caf4f0b719fbc4e5ad7cdf730aac94802288535559e10d93c664a0`.
It does not authorize package publication, tagging, release creation,
deployment, or promotion.

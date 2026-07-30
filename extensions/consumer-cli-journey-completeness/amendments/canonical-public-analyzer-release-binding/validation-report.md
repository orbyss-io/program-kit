# Design review validation report

Review set:
`pkid:review-set:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.3`

Source commit:
`a3c2fe174cd3511e9f3787acb4f7fd2ef59dba07`

Branch:
`codex/alpha3-canonical-analyzer-selection`

## Results

- PASS — previously completed `PKRB-W010` exhaustive solution gate: 857 total,
  856 passed, one explicit Linux-only skip, zero failed.
- PASS — completed `PKRB-W020` exhaustive solution gate: 860 total, 859 passed,
  one explicit Linux-only skip, zero failed.
- PASS — public CLI schema validation of `architecture-design.json`.
- PASS — public CLI schema validation of `implementation-plan.json`.
- PASS — public CLI schema validation of
  `static-conformance-disposition.json`.
- PASS — repository typed semantic validation of
  `ArchitectureDesignDocumentAlpha3`.
- PASS — repository typed semantic validation of
  `ImplementationPlanDocumentAlpha4`.
- PASS — repository typed semantic validation of
  `StaticConformanceDispositionAlpha2`.
- PASS — canonical amended design/plan/disposition/gate and amendment-input
  references resolve to the exact review-file SHA-256 values; completed
  `PKRB-W010` and `PKRB-W020` retain their exact historically approved
  architecture-design inputs, and current `PKRB-W010` traces the amended gate
  design whose enforcement allocation and controlled fixture categories are
  unchanged.
- PASS — all planned product and closure work reaches establishment unit
  `PKRB-W010` and final closure unit `PKRB-W080`; no parallel groups exist.
- PASS — static conformance remains the exact human-approved
  `extend-existing` disposition; the established policy, selection lock,
  activation evidence, and deterministic compiler evidence remain compatible
  with the amended product work.

The unchanged disposition and selection lock are historical authority for the
completed gate-establishment decision. Their original gate-design reference
and future-SDK residual-risk statement are intentionally not rewritten; the
amended architecture, gate design, and `PKRB-W030` through `PKRB-W080`
supersede those packaging mechanics without changing static enforcement
allocation.

The temporary typed-validation test used for the semantic checks was removed
after execution; it is not part of the review set.

## Independently checked alpha.2 facts

- NuGet.org analyzer nupkg SHA-256:
  `282a10899e45c302cb0ba879b01f9ff6bf92bee0a73fd5c996ad77a4dee22a6c`.
- Analyzer DLL SHA-256 within that NuGet package:
  `7ec050ca9434657060b8e18400fc8d2db26424424e1840925abe383c4bc4e8e1`.
- Historical GitHub handoff analyzer nupkg SHA-256:
  `96cf2d7fd2cff80b4d10a00d11e2375318cec3639af89ed451070eb699e6b8b5`.
- Local source rebuilding of alpha.2 does not reproduce the NuGet package or
  analyzer assembly bytes.
- The installed authoring catalog contains descriptive package-digest prose
  and no exact assembly or dotnet-host generator-revision digest.
- The current release manifest selects 29 source packages and omits the
  consumer meta-package, while the workflow also has its own enumeration and
  separate meta-package pack path.
- Current `receiptGeneratorRevisions` validation establishes reference shape
  and ordering, not correspondence to executed generated-output evidence.
- NuGet.org repository-signs uploaded packages and adds or countersigns
  `.signature.p7s`; a local builder therefore cannot reproduce the raw
  repository-signed nupkg SHA-256.
- The installed supported SDK is 10.0.302 with NuGet 7.6. The amended design
  no longer depends on unreleased SDK 10.0.400 functionality.

## Exact canonical review digests

- `design-input.json`:
  `9c47696376b9be8ae928087efc06d2f849a400a119274ce60a073a5bafeb3034`
- `design-amendment-input.json`:
  `d4fdea2e13118db2fbc0c66350f31e5d027478e9e976266512d9985d1fef01e6`
- `csharp-build-gate-design.md`:
  `c739d476e2d0589caa02e940b7f8257af190882602fa66f857bf6fee8c244e3c`
- `static-conformance-disposition.json`:
  `cd8adf3db8caf4f0b719fbc4e5ad7cdf730aac94802288535559e10d93c664a0`
- `architecture-design.json`:
  `59315e450e33a79a39dc1079e1587d6a6747c3343714e3dd8957fff0dddd47d5`
- `architecture-design.md`:
  `8bd6df22512691624404d8b7ca8303d1197f1e8f1cf64cee21007218125dea81`
- `implementation-plan.json`:
  `0821ef64266769c79e68b5754a585ca9452aa6eb2b44e2b0668c50ae20fe88e5`
- `implementation-plan.md`:
  `cda253830afb0fa5421f4982ef3020e9529f151350644bcd073758013aaa344a`
- `additional-findings.md`:
  `89fb6c66f4114be4e64feb23c824c6d40e5e9a6325f851a5405649efd6ef0ea0`
- `README.md`:
  `e683aed4f82e255bb15062876cc687bb1116a0121d5fde9ca6de753092430c2a`

## Deliberately not performed

No package version, product source beyond the already completed W010/W020
commits, schema, workflow, release asset, tag, or external state was changed by
this amendment design task. No alpha.3 package was pushed, uploaded, or
published. Repository-owned package canonicalization, published-package
reconciliation, safe workflow resumption, two-root candidate packing, and
cold-consumer acceptance remain implementation outcomes. The supported SDK
deliberately remains pinned to 10.0.302.

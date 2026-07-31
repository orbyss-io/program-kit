# Design review validation report

Review set:
`pkid:review-set:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.3`

Source commit:
`eabb9363c5a54666407c63a70a4bd7a92a287a31`

Branch:
`codex/alpha3-canonical-analyzer-selection`

## Results

- PASS — previously completed `PKRB-W010` exhaustive solution gate: 857 total,
  856 passed, one explicit Linux-only skip, zero failed.
- PASS — completed `PKRB-W020` exhaustive solution gate: 860 total, 859 passed,
  one explicit Linux-only skip, zero failed.
- PASS — synchronized source routine gate: 181 total, 180 passed, one explicit
  Linux-only skip, zero failed.
- PASS — synchronized source exhaustive gate: 23 total, 23 passed, zero
  skipped, zero failed.
- PASS — synchronized capability-bundle digest regression selection: two
  total, two passed, zero skipped, zero failed.
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
- PASS — the synchronized plan contains eight exact references to current
  `build/Invoke-CSharpGateTestPlan.ps1` SHA-256
  `2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f`
  and no reference to its pre-synchronization SHA-256
  `80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`.

The unchanged disposition and selection lock are historical authority for the
completed gate-establishment decision. Their original gate-design reference
and future-SDK residual-risk statement are intentionally not rewritten; the
amended architecture, gate design, and `PKRB-W030` through `PKRB-W080`
supersede those packaging mechanics without changing static enforcement
allocation.

The human approved the amended architecture, pre-synchronization plan, gate
design, unchanged disposition, W010/W020 evidence compatibility, and revised
W030-W080. That exact approval is recorded separately. Because the requested
source synchronization changed a digest-bound verification-profile input, the
mechanically synchronized plan has a new digest and requires its own exact
approval. Product implementation remains paused before W030. The historical
selection lock and W010/W020 evidence chain will be refreshed mechanically
during implementation preflight only after that approval.

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
  `9e9176fb96e4db4268dcc4d1f6718c58374e027e59b96f7fc732c739623cb835`
- `implementation-plan.json`:
  `3b49633d6bfecd0894cef27b5f5baddc71bb02ad492e7084e65b2fb48d9ccc30`
- `implementation-plan.md`:
  `961a052f42f6843d7094e02565d6a734512dda3983bf8351446c32a3398143f9`
- `additional-findings.md`:
  `169075f885c09535bb2cc283a951678f9ef6f328230e904563196581735499ed`
- `README.md`:
  `20b8687fd2d10a8541418ff5bdf98b93a4c4a5020f85354db2af024edbf5b436`
- `design-plan-controlled-packaging-approval.json`:
  `c5a33c8830428b3b17bdab6ff470f4b7db95ee39dc21498ab181b9eb047c6959`

## Deliberately not performed

No package version, analyzer/compiler/CLI product source, schema, workflow,
release asset, tag, or external publication state was changed by this
synchronization reconciliation. No alpha.3 package was pushed, uploaded, or
published. Repository-owned package canonicalization, published-package
reconciliation, safe workflow resumption, two-root candidate packing, and
cold-consumer acceptance remain implementation outcomes. The supported SDK
deliberately remains pinned to 10.0.302.

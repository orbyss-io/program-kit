# Design review validation report

Review set:
`pkid:review-set:program-kit:canonical-public-analyzer-release-binding@0.1.0-alpha.3`

Source commit:
`f555745e77ebce234f7e54665869a32cc555ba45`

Branch:
`codex/alpha3-canonical-analyzer-selection`

## Results

- PASS — `ProgramKit.sln` dependency restore.
- PASS — Debug build of `Orbyss.ProgramKit.CommandLine`; zero warnings and
  errors, including the active private-gate self-validation.
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
- PASS — canonical design/plan/disposition/gate references resolve to the
  exact review-file SHA-256 values.
- PASS — all planned product and closure work reaches establishment unit
  `PKRB-W010` and final closure unit `PKRB-W080`; no parallel groups exist.
- PASS — static conformance is the human-approved `extend-existing`
  disposition and declares prospective policy, selection-lock, and activation
  evidence outputs before product work.

The temporary typed-validator project used for the semantic checks was removed
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

## Exact canonical review digests

- `design-input.json`:
  `9c47696376b9be8ae928087efc06d2f849a400a119274ce60a073a5bafeb3034`
- `csharp-build-gate-design.md`:
  `f668b6746af54d64ea26bc5d56e91fa7c0dccffdd3e030ed7d92da08f87dcb70`
- `static-conformance-disposition.json`:
  `cd8adf3db8caf4f0b719fbc4e5ad7cdf730aac94802288535559e10d93c664a0`
- `architecture-design.json`:
  `dee52330c5da79a68bc4869b8f140faed02347d36f49119e6fd673258170fdb1`
- `architecture-design.md`:
  `afa48f9a54bda152641e72d6ec64b3904fafa53755edb8d3f75537646171bdc7`
- `implementation-plan.json`:
  `6735e42bb93d6c18ada00e0961fdb645f07864e9629c6a663e757a10b9020f3d`
- `implementation-plan.md`:
  `6ed7b3c846c6547d5e0daa199ba9c190db1f3b86c542c973c16b2f3817b4613c`
- `additional-findings.md`:
  `d8f72bf60a966c91a6735a29f91d6ab4b6b4d98a2a28bef7d682fd9d7828ffd4`
- `README.md`:
  `41cf0d43f4adfa8ebc8777deb37b6efcef6f8b47c4e8efacf7ec2b89a89f24a5`

## Deliberately not performed

No Program Kit product source, package version, schema, workflow, or release
asset was changed. No alpha.3 package was built, tagged, pushed, uploaded, or
published. Reproducible two-root packing and cold-consumer acceptance are
implementation outcomes, not design-review claims. The pinned SDK remains
10.0.302 until the approved implementation deliberately selects and verifies a
10.0.400-or-later SDK.

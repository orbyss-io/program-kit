# Program Kit integration and release provenance validation

## Result

The review candidate is structurally valid and ready for one exact human
design-and-plan decision. Product implementation, external GitHub
configuration and package publication have not started.

Canonical Architecture Design `0.1.0-alpha.2` instance:
`50f31d1ab276c3597d9ac5e004a1657f94ad6fe062ee200615e2b56462ceacae`.

Canonical Implementation Plan `0.1.0-alpha.3` instance:
`082fae48f202e61943066e10f0293edb1d90b6428f3a43c162d1865e059f714c`.

## Source truth

- Review base: Program Kit `main` at merge commit
  `8443998`.
- The current publication workflow rebuilds, tests, packs and publishes within
  one privileged job; it is replacement source truth, not evidence that the
  proposed separation exists.
- The repository already has a finite manifest-selected aggregate package
  builder that emits `package-manifest.json` and `SHA256SUMS`.
- Current private-gate profile bytes are exactly
  `2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f`.
- Official GitHub documentation for pull-request merge refs, merge groups,
  merge queue, required checks, immutable uploaded artifacts, artifact
  attestations and protected environments is recorded in
  `github-platform-evidence.json`.

## Static-conformance decision

The human explicitly approved `reuse-existing` for the current private Program
Kit C# gate. The exact decision source, non-circular design basis, valid
disposition, current gate, activation matrix, exhaustive profile, selection
lock and prior reusable-gate activation evidence are digest-bound.

No new analyzer is proposed. Workflow topology, package provenance,
permissions, no-rebuild behavior and contributor guidance remain executable
test and human-review obligations.

## Validation performed

- Every review JSON artifact parses successfully.
- `architecture-design.json` passes the Program Kit validator against
  `pkid:schema:program-kit:architecture-design@0.1.0-alpha.2`
  (`e94b5e1dab8292066669ccee5069f27a6e220962906051931fc1f1607fe2dbf7`).
- `implementation-plan.json` passes the Program Kit validator against
  `pkid:schema:program-kit:implementation-plan@0.1.0-alpha.3`
  (`774c6b945ac2b63c2e4beca0afab9c282669274f0c7d4eb4b9e936ba38460c7c`).
- `static-conformance-disposition.json` passes the Program Kit validator
  against
  `pkid:schema:program-kit:static-conformance-disposition@0.1.0-alpha.2`
  (`4c071112daf165a8e95462a325af9d52437f8c6e2a20639839e5f7ecfffcfd18`).
- The plan has exact requirement/trace equality, a linear known dependency
  graph, one closure work unit and exact gate, matrix, profile, selection-lock
  and activation-evidence references.
- `git diff --check` passes.

The repository `render` command was attempted for the reviewer projections and
correctly returned `PKCLI004`: no Workbench render adapter is registered. The
Markdown files are therefore explicitly identified as manually maintained
human-readable projections; only the validated JSON and exact digests are
approval authority.

## Authority and exclusions

The recorded static decision authorizes only reuse of the existing C# gate in
this candidate. Implementation requires a separate explicit human approval of
the exact canonical design and plan digests together.

Even that implementation approval will not authorize configuring repository
rulesets or environments, changing NuGet trusted publishing, merging the pull
request, dispatching publication, pushing packages, creating a tag or release,
refreshing the active provider-local capability copy, or mutating another
repository.

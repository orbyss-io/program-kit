# Program Kit integration and release provenance

State: awaiting exact human approval of the canonical design and implementation
plan.

This is the reviewer-oriented projection of `architecture-design.json`.
The canonical Architecture Design `0.1.0-alpha.2` instance has SHA-256
`50f31d1ab276c3597d9ac5e004a1657f94ad6fe062ee200615e2b56462ceacae`.

## Outcome

Repository CI becomes the shared integration authority for combined Program Kit
source. Development sessions continue to resolve real conflicts and run focused
checks for their own changes, but they no longer repeatedly merge `main` merely
to reproduce whole-repository integration.

The repository builds publication-eligible packages exactly once from a trusted
push to `main`. A later human-dispatched publication retrieves and verifies
those exact bytes; it does not restore, compile, test, generate, or pack again.

## Integration lifecycle

1. On `pull_request`, GitHub checks out its synthetic merge commit. One stable,
   read-only and secretless job runs the repository integration profile.
2. On `merge_group`, the same stable job proves current `main` together with the
   queued changes. The merge queue, rather than each development session,
   serializes integration.
3. On a successful push to `main`, the workflow runs the exhaustive profile,
   invokes the existing finite consumer-feed packer once, closes the provenance
   record, attests the package subjects, and uploads one canonical package
   artifact.
4. On explicit `workflow_dispatch`, a protected publication job accepts one
   exact canonical-build run ID. It verifies the source event, branch, commit,
   workflow, run result, hosted artifact identity, internal provenance,
   inventory, sizes and digests before requesting temporary NuGet credentials.
5. The publisher sends the verified package files unchanged and creates a tag
   and durable release assets at the canonical-build commit.

Pull-request and merge-group runs never create publication candidates and never
receive publication authority.

## Approval and execution evidence

The Planning contract gains two explicit binding modes:

- `approval-fixed` binds identity, version and digest because changing any of
  them changes the human-approved semantic obligation.
- `execution-resolved` binds the approved identity and compatibility policy.
  A trusted execution selects a compatible concrete version and digest and
  records those exact bytes in its receipt.

This distinction removes the false coupling that invalidated an approved
software plan whenever compatible gate-profile bytes changed. It does not make
semantic drift mechanical: changes to identity, authority, compatibility
policy, required outcomes, integration events, publication eligibility or the
no-rebuild rule still require renewed human approval.

## Package provenance

One canonical-build record closes over:

- repository, branch, event and exact source commit;
- workflow identity, workflow revision and run ID;
- exact integration-profile selection;
- the release-package manifest digest;
- the emitted package-manifest and `SHA256SUMS` digests;
- every package identity, version, size and SHA-256 digest;
- immutable hosted artifact identity and attestation subjects.

The verifier rejects an ineligible run, an artifact from another workflow or
event, a commit outside protected `main` history, missing or extra packages,
stale metadata, and any digest mismatch. Package-feed authentication occurs
only after the complete artifact passes verification.

## Authority and failure boundaries

Humans retain authority to approve the design, review and merge source,
configure repository protections, dispatch publication, approve the protected
environment, and recover from partial registry publication. CI supplies
evidence; it does not approve, merge, publish automatically, select an
alternate artifact, or retry a failed release.

Untrusted combined-source checks use least privilege and no secrets.
`pull_request_target`, self-hosted runners, arbitrary `workflow_run`
promotion, long-lived package-feed keys, hooks, watchers and autonomous agent
loops are excluded.

Superseded pull-request runs may be cancelled. Merge-group and publication runs
are not cancelled by unrelated newer events, and publication for one package
version is serialized. If an external registry fails after some package pushes,
the workflow reports the partial state and stops before tag or release
creation; it does not claim transactional rollback.

## Provider-neutral contributor lifecycle

Repository guidance describes roles and lifecycle boundaries, not model or
provider brands. Any supported development session:

- starts from current human intent and repository source truth;
- performs directly affected local verification;
- pushes a reviewable branch and observes the shared integration check;
- resolves actual source conflicts and material failures;
- relies on merge-group evidence for cross-branch compatibility;
- never treats CI success as human semantic or publication approval.

Provider-local capability projections remain full copied delivery artifacts,
refreshed only for a freshly initialized task or at explicit human request.
Contributor maintenance does not require the consumer Program Kit CLI and does
not refresh the currently active provider-local copy mid-task.

## Static conformance

Disposition: `reuse-existing`.

Program Kit-owned C# source continues to use private gate
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0` and activation
matrix
`pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`.
The current exhaustive profile is selected for this review candidate as
`pkid:profile:program-kit:private-csharp-gate-exhaustive@1.0.1`.

No new analyzer is justified. Workflow topology, package provenance,
permissions, no-rebuild publication and contributor guidance are verified by
executable CI, workflow, tamper and documentation tests plus human review.

## Human-owned activation after merge

The source patch will provide a finite setup handoff, but it will not mutate
GitHub or NuGet settings. The repository owner must:

- require the stable integration check for protected `main`;
- enable merge queue and require the same check for merge groups;
- configure the named publication environment, required reviewers,
  self-review policy and branch restriction;
- confirm `NUGET_USER` placement and the NuGet trusted-publishing binding to
  the unchanged publication workflow identity.

## Non-goals

This design does not automatically merge, release or publish; change package
identity, versions, contents or inventory merely to establish CI; make
multi-package NuGet publication atomic; mutate another repository; or create
provider-specific agent behavior.

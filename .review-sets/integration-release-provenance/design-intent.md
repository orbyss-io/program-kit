# Integration and release provenance intent

Artifact identity:
`pkid:intent:program-kit:integration-release-provenance@0.1.0-alpha.1`.

Source basis: Program Kit commit
`9d45a6ea9c625ec1fc638d2ef9674cfefc01fd9f`.

## Human outcome

Move repeated cross-branch integration work out of individual development
sessions and into repository-owned GitHub workflows:

- pull requests prove the proposed change against the current target branch;
- merge-queue groups prove multiple accepted changes together before merge;
- a successful trusted `main` run produces the one canonical package set;
- a later human-dispatched publication consumes those exact package bytes
  without restoring, rebuilding, testing, or repacking them.

Development sessions retain focused local verification and must still resolve
real source conflicts. They do not repeatedly merge `main` merely to refresh
mechanical digests or reproduce integration already owned by CI.

## Approval and execution evidence

Human approval binds semantic intent, architecture, allowed edits, authority,
and acceptance outcomes. Execution-time evidence binds the exact combined
commit, workflow definition, verification profile, package inventory, package
bytes, checksums, build run, and publication run.

A compatible execution-profile revision or a newly synthesized pull-request
or merge-group commit does not silently rewrite approved semantics. A change
to scope, authority, required outcomes, package selection, publication
boundary, or compatibility policy remains a material design change requiring
human review.

## Safety and authority

- Pull-request and merge-group workflows receive read-only repository
  permissions and no publication secrets.
- Canonical packages are produced only from a successful `push` run for the
  protected `main` branch.
- Publication is a separate `workflow_dispatch` operation that selects one
  exact successful canonical-build run and passes a protected environment.
- The publish job verifies source commit, workflow identity, artifact
  inventory, package manifest, and checksums before requesting temporary
  NuGet credentials.
- Publication never executes code from an untrusted pull-request artifact.
- No hook, watcher, autonomous retry, provider-specific behavior, or
  development-session capability activation is introduced.

## Administrative outcome

The repository owner will configure the required integration check, merge
queue, protected publication environment, and any trusted-publishing policy
that cannot be established by repository files. Those settings remain human
authority and are documented as explicit post-merge setup, not claimed by the
patch.

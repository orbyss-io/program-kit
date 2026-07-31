# Program Kit GitHub and NuGet administration handoff

This is a finite human-owned setup checklist for the source already committed
in this repository. None of these external settings is applied or confirmed by
the repository patch. A repository owner must review and perform each selected
item after the integration and publication workflows are present on `main`.

## Required integration and merge queue

- [ ] In the ruleset targeting `main`, require pull requests before merge.
- [ ] Require the status check named exactly `Program Kit integration`.
- [ ] Do not require a topic branch to be updated with `main` before entry to
  the queue. The required `merge_group` check proves the queued combined source.
- [ ] Enable merge queue for `main` and require the same `Program Kit
  integration` check for queue groups.
- [ ] Do not add workflow path filters. A required check must be reported for
  every pull request and merge group.
- [ ] Enable automatic deletion of merged head branches if that repository
  lifecycle is accepted.

Apply the required-check setting only after
[`program-kit-integration.yml`](workflows/program-kit-integration.yml) is on
the default branch and the `Program Kit integration` job has reported at least
once. Pull-request runs use GitHub's event-provided synthetic merge commit;
merge-queue runs use `merge_group` with `checks_requested`.

## Protected publication environment

- [ ] Create an environment named exactly `program-kit-publication`.
- [ ] Add at least one designated Program Kit release maintainer as a required
  reviewer. Select the actual reviewer identities in GitHub; do not infer them
  from repository source.
- [ ] Prevent self-review for protected environment deployments.
- [ ] Restrict deployment branches to `main` only.
- [ ] Store `NUGET_USER` as an environment secret in
  `program-kit-publication`. Its value is the NuGet.org profile name associated
  with the trusted-publishing policy; it is not an API key.
- [ ] Do not add a long-lived NuGet API key. The unchanged publication workflow
  filename requests a temporary OIDC credential only after verification.

The publication workflow is
[`publish-nuget.yml`](workflows/publish-nuget.yml). It must remain manual
(`workflow_dispatch`) and its protected `publish` job must keep
`environment: program-kit-publication`.

## NuGet trusted-publishing binding

- [ ] In the NuGet.org profile named by `NUGET_USER`, create or update the
  trusted-publishing policy with these exact subjects:
  - repository owner: `orbyss-io`;
  - repository: `program-kit`;
  - workflow filename: `publish-nuget.yml`;
  - environment: `program-kit-publication`.
- [ ] Confirm the policy issues only a temporary credential to that workflow
  and environment.

Preserving `.github/workflows/publish-nuget.yml` is intentional: the source
change replaces its behavior without changing the workflow identity used by
trusted publishing.

## Activation and first-use evidence

- [ ] Merge the reviewed workflow source through the normal protected path.
- [ ] Observe `Program Kit integration` for a pull request and a merge group
  before relying on it as the required check.
- [ ] Observe one successful push-to-`main` canonical build and record its exact
  run ID, source commit, artifact ID, artifact digest, and attestation result.
- [ ] Keep canonical-build artifact retention at 30 days or longer.
- [ ] When publication is actually intended, a human dispatches
  `publish-nuget.yml` from `main` and supplies that exact numeric run ID.
- [ ] Confirm environment approval occurs only after the read-only verification
  job passes.
- [ ] After publication, confirm every NuGet package version and every GitHub
  release asset maps to the selected source commit and verified package digest.

Do not treat a successful check, canonical artifact, or completed checklist
item as semantic approval. Do not enable automatic publication or retry a
partial multi-package publication. If any external setting differs from this
handoff, stop and review the trust boundary before dispatching a release.

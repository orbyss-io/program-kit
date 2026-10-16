# Separate public repair evidence repository

This directory is **source for provisioning**, not a deployed route or public
acceptance claim. Intended identity: `orbyss-io/program-kit-evidence`, public,
default branch main. Repair issues and implementation PRs remain in Program Kit.
Consumer evidence arrives through their own fork and evidence PR.

Prepare with `python scripts/prepare_evidence_repository.py --output <new-directory>`.
Review that exact tree, then separately authorize creating/configuring the public
repository. No provisioning command is automatically run by Program Kit tests.
The prepared tree includes trusted guardian code, the contract, workflow and this
procedure. No consumer/reporter source or artifacts are copied into it.

1. Publish only the reviewed prepared source, note its exact commit, and configure
   a repository/organization ruleset that requires the **specific workflow identity**
   `.github/workflows/guardian.yml` pinned at that trusted commit. Use an organization
   workflow rule with repository ID, workflow path and exact `sha`. Target this
   repository ID and refs/heads/main without bypass actors. A required
   status name alone is insufficient: same-name jobs must not impersonate it.
   If the account/plan cannot enforce required workflow identity, deployment is
   blocked pending an equivalent separately trusted GitHub App enforcement boundary.
2. Require a pull request, at least one maintainer approval, dismiss stale approvals,
   approval after latest push, code owner review and no bypass actors. Protect
   workflows, validator, contract and accepted evidence through this ruleset.
   `CODEOWNERS` names `@orbyss-io/maintainers`; verify that team exists and has the
   required role before provisioning (it is an intended value, not verified state).
3. Set `guardian-deployment.json` fields `validatorCommit` and
   `requiredWorkflowRulesetId` to the actual trusted commit/rule, preserving v1
   contract. This file records configuration; clients freshly read and validate
   the actual rules before mutation. Run `verify_evidence_repository.py` with the
   expected commit and record its read-only result. Never claim fixtures prove
   repository provisioning or maintainer permissions.
4. Guardian runs from the pinned trusted workflow commit, downloads exact PR blobs as **data** and
   never checks out the submitted branch, runs scripts, installs dependencies,
   builds projects, renders files or starts a coding agent. Its readonly token
   cannot publish anything. It binds proof to exact head, trusted validator commit
   and contract/guardian version. Main-only PRs add one request/revision inventory;
   changing workflows, policy, earlier evidence or unrelated files fails.
5. Merge only after that trusted workflow succeeds for the actual head and
   maintainer content review. Passing is contract-valid evidence, not verified
   diagnosis, publisher attestation or consumer acceptance. Retain accepted evidence
   as release references. No automatic deletion in v1; do not promise removal from
   Git history, forks, clones or caches.

Review the fork push contents before pushing: publication precedes the PR and
guardian. Prefer synthetic examples, sanitized selected excerpts and minimal proof.
Supported checks cannot decide whether arbitrary business/personal facts are safe.

Platform references rechecked 16 October 2026:
[CLI API/cache options](https://cli.github.com/manual/gh_api),
[trusted Actions usage](https://docs.github.com/en/actions/reference/security/secure-use),
[workflow rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

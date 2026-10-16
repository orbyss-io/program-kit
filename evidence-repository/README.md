# Separate public repair evidence repository

This tree is a provisioning proposal, not a deployed public route. Intended
identity: `orbyss-io/program-kit-evidence`, public, default branch `main`.
Repair issues and implementation PRs remain in Program Kit. Consumers submit
selected evidence through their own forks and PRs without upstream Write.

Prepare with `python scripts/prepare_evidence_repository.py --output <new-directory>`.
Review the exact output inventory before separately approving public setup.
No consumer artifacts or reporter history are copied. Tests make no public writes.

## GitHub Free enforcement

Use a repository ruleset and a dedicated organization-owned GitHub App named
`Program Kit Evidence Guardian` (intended slug `program-kit-evidence-guardian`).
Disable webhooks and user authorization; install it only on this evidence
repository. Grant Checks **write**, Contents **read**, Pull requests **read**,
and mandatory Metadata **read**. No organization permissions, contents write,
issue write, administration, merge or publication authority.

Create the `evidence-guardian` environment with selected deployment branch `main`
(branch rule, no tags). Keep its only secret `GUARDIAN_APP_PRIVATE_KEY` there,
never in repository/organization secrets. Environment variables:
`GUARDIAN_APP_CLIENT_ID` (assigned by GitHub) and `GUARDIAN_VALIDATOR_COMMIT`
(the reviewed seed source commit). Never print or store the key in this tree,
logs, review artifacts or chat. App-token action v3.2.0 is SHA-pinned and requests
only the current repository and those permissions; cleanup revokes its token.
Use GitHub-hosted ephemeral runners.

The workflow has only `workflow_dispatch`, restricted to repository identity and
`refs/heads/main`. A maintainer starts it with an evidence PR number. It checks out
the pinned validator commit, reads the current PR head/base through GitHub's API,
inspects submitted blobs as data, and creates `program-kit-evidence/guardian` on
that head using the App token. It never checks out or executes submitted code,
installs project dependencies, renders evidence, or starts a coding agent.
There is no `pull_request_target` trigger or event-policy exception.

The environment's main-only restriction also blocks a manually dispatched modified
feature-branch workflow from obtaining the App key. Keep the main workflow
identical to the pinned validator workflow. The fresh client verifier compares
trusted source blobs with main and checks the App identity/permissions.

Apply `repository-ruleset.template.json` to this repository after seeding and
configuration. Replace `integration_id: 0` with the actual dedicated App ID.
Require the exact check context **and** that App ID, strict latest-base checking,
PRs, at least one approval, stale-review dismissal, code owner review, approval
of the latest push, and resolved discussions. No bypass actors; block deletion
and force pushes. `CODEOWNERS` names verified organization administrator
`@joey-orbyss`; no unverified team is needed. A PR author cannot approve their own
submission. Ordinary consumer PRs can be reviewed by this maintainer; maintainer-
authored submissions need another eligible code owner before acceptance.

Record actual positive `githubAppId` and `repositoryRulesetId`, the actual App
slug and exact `validatorCommit` in `guardian-deployment.json`. Null seed IDs
intentionally fail verification. The later configuration commit changes only
deployment metadata; leave validator/workflow/code-owner bytes identical.
Before enabling submission, run the read-only verifier with actual main and
validator SHAs. It checks effective main rules rather than merely trusting the
configuration file. Secret/environment/installation boundaries additionally need
the owner's administrative inspection and operational tests; public metadata
alone cannot prove these private settings.

## Acceptance and upkeep

Dispatch the workflow from main after reviewing an incoming PR. A missing check,
API failure, interrupted run or rejected inventory never establishes acceptance.
A new head requires another dispatch and review. Strict status enforcement also
requires a fresh check after updating the PR to a changed base. Merge only after
the App check passes for the current head and a maintainer reviews the content.
Same-name GitHub Actions jobs or checks from other Apps cannot satisfy the rule.

The guardian permits additions for exactly one request revision; it rejects
workflow, policy and prior-evidence modifications. Policy/validator upgrades
therefore need a separately reviewed administrative maintenance operation and
new pinned source/environment/configuration verification. Never weaken rules
silently to merge a failed evidence submission.

Passing means contract-valid evidence, not independently reproduced diagnosis,
publisher attestation or consumer acceptance. Review fork contents before pushing:
publication precedes the PR and guardian. Supported checks cannot decide whether
arbitrary business/personal facts are safe. Retain accepted evidence as release
references, with no automatic deletion in v1. Do not promise removal from Git
history, forks, clones or caches.

Platform references checked 16 October 2026:
[App token action](https://github.com/actions/create-github-app-token/tree/bcd2ba49218906704ab6c1aa796996da409d3eb1),
[App-bound repository rules](https://docs.github.com/en/rest/repos/rules),
[main-only environment secrets](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

# Releasing Program Kit

Develop with [focused validation](validation.md). Maintainer review accepts reported
local behavioral execution and disclosed limitations. CI independently verifies package
construction and installation; it makes no claim to have witnessed local execution.
Dependency updates/profile qualification are separate maintenance, not a release ritual.
Known applicable product defects block publication. Missing coverage or inconclusive
harness results require a concrete maintainer decision in the PR/release discussion.

## Candidate packages

PRs call the same `qualify-candidate.yml` implementation as explicit candidates: fast
integrity, one publication archive build, exact-byte installation/entrypoint smokes on
Windows and Linux, and applicable immutable dependency security checks. There is no
broad main-push or tagged acceptance suite. A merge producing a different commit needs
its own exact-source package run. No build/test output from another source is reused.

After the implementation is committed and candidate preparation is authorized:

```powershell
python scripts/release_candidate.py find
gh workflow run qualify-candidate.yml --ref main -f expected_commit=<exact-main-SHA>
python scripts/release_candidate.py download --run-id <run-id> --output artifacts/verified/<unique>
python scripts/release_candidate.py verify-promotion --run-id <run-id> --output artifacts/promotion/<unique>
```

Reuse a successful matching exact-source candidate when available. The manifest binds
commit/tree/version/policy and all publication asset hashes; the verifier checks the
successful producer run and required jobs, artifact digest and safe extraction, then
the complete asset inventory. Missing/expired artifacts, mismatches, failed jobs or
security findings block promotion. Retention defaults to 14 days; security freshness
is separately bounded to 24 hours. A preflight/download never publishes anything.

Actions retains normal logs, source/package manifest and package/security artifacts.
No developer evidence commits, upload service, central developer log store, signed
readiness form, historical case ledger or separate assessment workflow is required.
Record a concise PR validation summary: checks, outcomes, relevant gaps and measured
cost. Local records stay ignored. No automatic PR-prose parsing recreates a receipt gate.

## One approval, before tagging or publishing

Configure the GitHub environment named `publication` with the maintainer as a required
reviewer. Allow self-review for sole-maintainer operation; configure branch protection
and required package status checks appropriate to the repository's GitHub plan. A PR
author cannot approve their own PR, so independent PR review is useful when available
but is not a fictional prerequisite for a sole maintainer. Environment review is the
explicit publication authority. Do not create an unprotected environment as a fallback.
The workflow checks that required reviewers exist and fails if approval is unconfigured.
Repository settings are an administrator operation, separate from source implementation.

When release execution is explicitly authorized, dispatch:

```powershell
gh workflow run release.yml --ref main -f expected_commit=<exact-main-SHA> -f run_id=<candidate-run>
```

The inspection job verifies packages/security and presents the exact commit, version,
package run, checksums and validation limitations in the run summary. The `publication`
environment then pauses for your native GitHub approval. That single decision accepts
the developer-reported validation and limitations and authorizes tag creation and
publication. After approval the workflow rechecks source, inspected package digest and
security freshness, creates the inspected version tag and promotes the original bytes. It neither
rebuilds packages nor reruns deterministic acceptance. An expired scan requires fresh
security before approval/publication; unchanged packages do not require rebuilding.

A green source implementation check is not a successful release. Tell consumers the
version is available only after public bytes and the supported installation
path are verified. Program Kit consumes already-public Foundation packages; it does
not republish Foundation from a Program Kit tag.

## Failure and recovery

Preserve failed-run evidence and inspect tags, release assets and immutable registries
before recovery. Never overwrite differing published bytes, silently move a tag or
conceal partial publication. Fix supported failures through focused local checks.
A corrected source needs its own successful candidate package run and exact-candidate
approval. If a stable tag escaped before a failed publication, retain the same stable
version and obtain explicit approval before correcting that tag. Disclose any immutable
artifact already produced from another source state; it cannot be erased by repointing.

## Optional live trials

Trial recommendations come from actual changes and known coverage gaps. They are not
mandatory release work, and publication preparation must not ask to run paid trials.
The repository release-readiness skill grants neither paid-worker nor publication
authority. Explicitly selected release trials may prepare a disposable consumer with
`release_candidate.py prepare-trial --run-id <run> --output <unique>`; preparation
verifies exact package bytes and actual local prerequisites but starts no agent.
Every actual paid phase still requires its exact unexpired one-use authorization and
checkpoint under the live harness. Development trials retain their separately labeled
trial receipts. Historical live evidence remains read-only; no run means no AI
acceptance claim. Do not copy supervisor credential handling into consumer bootstrap.

## Composition and complete tooling carriers

The package build emits `program-kit-<version>.zip` as a small native composition
manifest and `program-kit-tooling-<version>.zip` as the complete local/offline
updater and recovery source. Both belong to the exact same candidate inventory
and `SHA256SUMS`; publication must include both. Native catalogs retain the
composition name and existing component IDs/URLs. Use the tooling archive when
an operation needs scripts, templates or retained publisher inputs. Historical
release composites remain original recovery inputs; never rewrite their storage.

The builder checks native carriers at 512 entries, complete tooling at 8,192,
and each carrier at 10 MiB per member / 128 MiB total uncompressed, with canonical
paths, case-insensitive collision refusal and CRC verification. These engineering
ceilings bound the current distribution mechanisms; they do not create a pack ABI.
The complete payload now keeps loose original sources rather than aggregating
historical facts/examples solely to satisfy the native entry ceiling. Historical
packed-source readers remain supported and independently tested.

## Preview channel and re-onboarding

Product release identities support `1.0.0-preview.1`, `1.0.0-preview.2`, and later numeric previews.
All current manifests, archive names, checksums, initializer tags and catalog URLs must agree.
External software/profile versions retain their separate owners. The GitHub publisher marks previews
as prereleases with `--latest=false`; both creation and same-byte retries preserve that channel.
The stable published-release README block continues to describe the actual latest stable release.

Choose a preview explicitly through its tagged initializer URL. The first 1.0 preview deliberately
refuses in-place 0.x migration before writing files. Keep the original checkout and re-onboard in a
fresh checkout, using useful authored product/architecture documents as intake inputs. Historical
workflow state and approval receipts are not translated. No cumulative migration dossier is shipped
or required for this boundary. The release assets carry concise release notes and compatibility text.

Later optional toolkit refreshes use the downloaded complete new and previous preview sources:

```powershell
python <new-tooling>/scripts/upgrade_program_kit.py --release-root <new-tooling> --previous-release-root <previous-tooling> --target . --plan
python <new-tooling>/scripts/upgrade_program_kit.py --release-root <new-tooling> --previous-release-root <previous-tooling> --target .
```

This is native toolkit replacement, separate from authoring and application dependency migration.
It preserves authored documents, specifications, application code and native dependency locks.
Customized/unknown toolkit sources, generated native outputs, aliases or multiple native integration
owners are refused for explicit owner reconciliation. A failed native refresh rolls back its bounded
local toolkit/output changes. Exact-source package CI and native publication approval remain required.
Postpublication delivery verifies the actual tagged initializer and installed entrypoints; the first
preview does not pretend to demonstrate a semantic upgrade from 0.x.

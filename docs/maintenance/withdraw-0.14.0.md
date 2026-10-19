# Withdrawing Program Kit 0.14.0 and maintaining 0.13.x

This prepared procedure authorizes no withdrawal now. No release or tag is deleted
or moved during preparation. The source fallback is `maintenance/0.13.x`, starting
at successful v0.13.3, commit `effd130e7118f751e98d0fcf81e03e6b70c3a9b6`.
Its complete successful publication is [run 39059298881](https://github.com/orbyss-io/program-kit/actions/runs/39059298881).
The original tag, release and 39 public assets remain intact. Preparation downloaded
and verified all 39 asset digests in retained local
`artifacts/release-0.14.0/fallback/verified-assets.json`, alongside source archive,
release metadata and original publication logs. Preserve these ignored files separately
when moving machines. The remote maintenance branch is the inspectable source fallback.

## Preserve evidence before withdrawal

Inspect current remote state and create a fresh evidence directory. Record the exact
successful 0.14.0 source/tag, tree, release ID/body/timestamps, all asset IDs/sizes/hashes,
package-CI and publication run IDs/attempts, required job outcomes and logs. Download
package, security, inspection and public-delivery artifacts before their 14-day retention
expires. Preserve the candidate manifest, complete SHA256SUMS, original public bytes and
a Git source archive. Verify each public hash against the inspected publication manifest.
Keep failed runs and differing assets explicitly; a release page is insufficient evidence.

Read/download examples, substituting the exact recorded run IDs:

```powershell
gh api repos/orbyss-io/program-kit/releases/tags/v0.14.0
gh release download v0.14.0 --repo orbyss-io/program-kit --dir <new-evidence>/public
gh run view <package-run> --repo orbyss-io/program-kit --log
gh run download <package-run> --repo orbyss-io/program-kit --dir <new-evidence>/packages
gh run download <publication-run> --repo orbyss-io/program-kit --dir <new-evidence>/publication
git rev-parse 'v0.14.0^{commit}'
git archive --format=zip --output=<new-evidence>/source-v0.14.0.zip v0.14.0
```

Retain metadata and both streams using file redirection appropriate to the shell.
Preserve a remote branch at the exact published source before removing any reference.
Never upload private consumer histories or worker streams as public release assets.
Protect all retained consumers and original review evidence.

## Only on an explicit later withdrawal request

After the human requests withdrawal of the concrete release and its evidence is
verified, remove the GitHub release with:

```powershell
gh release delete v0.14.0 --repo orbyss-io/program-kit --yes
```

Do not add `--cleanup-tag`. Retain the tag by default as a separate historical reference
and record the withdrawal in guidance. A later tag deletion needs its own explicit decision
and evidence. Never move a successful tag or reuse a withdrawn successful version for
different contents. Release deletion removes its GitHub assets, not downloaded copies.

## Restore latest-release links and installation guidance

After withdrawal inspect the latest-release API and explicitly select the intended
still-successful fallback if needed:

```powershell
gh release edit v0.13.3 --repo orbyss-io/program-kit --latest
gh api repos/orbyss-io/program-kit/releases/latest --jq .tag_name
gh workflow run published-readme.yml --repo orbyss-io/program-kit --ref main
```

The maintained README updater verifies a complete successful publication at that tag
before changing the availability block and initializer/archive examples. Verify those
changes, `releases/latest`, both platform initializers and supported upgrade instructions.
Use a reviewed documentation PR to remove remaining 0.14.0 installation/adoption
recommendations and add a withdrawal notice, retaining historical migration/source records.
Do not imply that main's VERSION or catalogs are public 0.13.x packages. Pin fallback
instructions to v0.13.3 assets/catalogs until a new patch actually completes publication.

## Continue 0.13.x through the exact-main publisher

Develop scoped fixes from `maintenance/0.13.x`. Select a new unused patch only if needed;
retain original source ancestry, assets and qualifications. Avoid importing the 0.14.0
coding system accidentally. Run proportional maintained checks and inspect the whole
patch against the successful 0.13.x predecessor.

The publisher **cannot publish directly from the maintenance branch**. Candidate/source
verification requires workflow_dispatch on `main` at an exact source identity. The
compatible route is a later explicitly approved restoration PR on top of current main:
restore the reviewed maintenance tree as a normal new commit, with patch/version/notes,
exact predecessor witnesses and maintained publication controls. Preserve 0.14.0 on a
remote branch and in existing history; never reset or force-push main. Compare the
proposed tree against maintenance and current main, disclosing intentional workflow-only
differences. This changes main's active product line and needs concrete human approval
before performing it; this runbook does not authorize that restoration now.

After merging, obtain a new successful package run for the exact final main commit,
inspect its complete hashes/provenance and fresh security, dispatch `release.yml` for
that exact commit/run and retain native `publication` approval. Verify public bytes,
fresh installation and the supported 0.13.x predecessor upgrade. Neither historical
v0.13.3 CI nor maintenance-branch packages can substitute. Advance the maintenance branch
only with reviewed resulting source. Resuming 0.14.x later requires another reviewed
main integration and exact-source publication, never a successful-tag rewrite.

No policy change is needed for that route. Simultaneous direct publication from both
lines would be a **material release-policy change** to bring to the human first. A
concrete alternative would allowlist `maintenance/0.13.x` in source/dispatch validation,
retain exact workflow/source/policy binding, all required jobs and hashes, security
freshness, native approval and public smoke, and add independent rejection tests for
other refs. This alternative is not enabled by 0.14.0.

## Consumers already upgraded

GitHub deletion does not downgrade them. The updater rejects downgrade migrations;
no automatic 0.14.0-to-0.13.x rollback is supported. Preserve source, private patterns,
locks, generated ownership, accepted decisions, task/evaluation histories, failures and
live data before proposing action. Inventory use of new coding duties and retired
architecture behavior. Depending on the actual defect and owner decision, offer continued
use of exact retained 0.14.0 bytes with a bounded workaround or a later forward repair.
Restoring a verified pre-upgrade backup needs a separate reviewed plan for subsequent
code/data changes and uncertain effects. Never reset a consumer or promise lossless rollback.

## Other destinations and failed candidates

Inspect actual publication jobs/logs, credential destination scope, package/NuGet and
container registries before making removal claims. This Program Kit publisher ships
GitHub assets and consumes independently public Foundation packages. Deleting its release
does not erase upstream or immutable registry artifacts, cached images, mirrors or
downloads. Disclose partial publication and original source identities; never overwrite
differing published bytes.

For a failed candidate rather than a successful-release withdrawal, follow actual
AGENTS.md and docs/releasing.md: preserve failures/escaped assets, repair scoped causes,
obtain corrected exact-main package CI and verify promotion without publication. Obtain
explicit approval for any same-version failed-tag correction. The ordinary publisher
refuses differing tags; use a separately reviewed maintained recovery route. Do not
create tags/releases manually as a substitute for native approval, or increment merely
because a failed tag existed. A withdrawn successful version is never this exception.

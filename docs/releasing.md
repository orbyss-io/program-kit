# Releasing Program Kit

Ordinary work uses focused validators and `./scripts/Test-ProgramKit.ps1` Development.
Main CI selects Development plus affected expensive checks across the entire push and
prerequisites; unknown history/inputs select full coverage. PR coverage is preserved.
Local Release wrappers are retired and fail with migration guidance. Historical
receipts, profiles, logs and consumer locks remain read-only.

## Qualify an exact candidate in CI

Complete dependency maintenance under [the existing procedure](maintenance/dependency-review.md)
before selecting a release candidate. This maintenance change does not itself request
unrelated dependency upgrades. Freeze committed source on main and inspect the actual
changes since the previous successful public release.

Use the repository-only `$program-kit-release-readiness` skill or deterministic helpers:

```powershell
python scripts/release_candidate.py find
# If no complete matching qualification exists:
gh workflow run qualify-candidate.yml --ref main -f expected_commit=<exact-main-SHA>
python scripts/release_candidate.py download --run-id <run-id> --output artifacts/verified/<unique-name>
python scripts/release_candidate.py recommend --base <previous-successful-release-commit>
```

Dispatch asserts that the expected commit, workflow source and checkout agree. Reuse
an already-successful complete matching run; partial CI runs are not combined. The
workflow builds one authoritative payload, runs full Linux deterministic acceptance
with Chromium/Firefox/WebKit, focused Windows installation/upgrade/launcher/workflow/
worker compatibility, and scans the selected immutable Host image identities. Windows
imports those exact verified bytes and records preparation rather than a Windows build.
Fixtures never start paid coding agents. Browser/container acceptance remains in Linux.

Payload plus its file manifest and original build/Linux/Windows/security evidence are
uploaded first. A separate authenticated final qualification binds their immutable IDs
and digests, exact commit/tree/VERSION, inventory/policy, actual successful required jobs,
platform/browser coverage and original logs. It never contains its own enclosing upload
digest. SHA256SUMS alone does not authenticate a payload. Every indexed profile, evidence,
migration guide and release Markdown asset belongs to the complete hashed inventory.

The verifier checks GitHub run/attempt/job metadata, exact producer workflow/revision,
GitHub attestations and archive digests before extraction, then extracted asset hashes.
Digest mismatches are hard failures in the implemented downloader. Missing, expired,
incomplete, mismatched or untrusted evidence blocks publication: qualify the exact
candidate in CI again before tagging; no local or tagged-workflow fallback exists.
Artifact retention defaults to 14 days in `release-policy.json`.

## Security and reviewed local readiness

Security freshness defaults to 24 hours, independently of storage retention. A stale
scan needs only `refresh-candidate-security.yml` with the original qualification run,
exact candidate commit and SHA256 of authenticated qualification.json. It scans unchanged
immutable inputs and never builds packages or runs product acceptance. Later applicable
failed scans block promotion until a successful refresh explicitly supersedes their
run/attempt identity. Future timestamps and wrong target/candidate identities fail.
Recorders may run from newer trusted main while checking out the exact older candidate;
their attestation authenticates that recorder revision and their statement binds the
unchanged qualification. Main advancing does not invalidate an older exact qualified tag.

A candidate can require no local execution. Change-based recommendations identify relevant
optional trials and missing scenario/oracle coverage. The user selects trials. Release
preparation never automatically requests or starts paid runs. For an explicitly selected
trial, `release_candidate.py prepare-trial --run-id <id> --output artifacts/trial-preparation/<unique>`
verifies CI packages, checks actual local prerequisites and installs a disposable consumer.
It records a separate host/toolchain/preparation binding; it does not rebuild or repeat
acceptance. `New-LiveAcceptanceAuthorization.ps1 -CiPreparation <record>` retains exact
one-use phase/model/checkpoint/source/artifact/host bindings and workspace-write workers.
Development-learning `-TrialReceipt` remains separate. Preserve Windows Job Object cleanup,
stream draining/redaction and supervisor-only credentials.

Keep full trial manifests/logs/checkpoints internally. Record a concise versioned
assessment with recommendations, selection, scope, outcomes, manifest references/digests,
findings and attributable human review via `record-release-assessment.yml`. Submitted
outcomes are human-attested, not independently verified by the recorder. No trial means
no AI acceptance claim. Confirmed product defects block readiness until explicitly resolved;
harness failures/inconclusive outcomes need disposition. Later unresolved findings supersede
older readiness passes. Histories bind exact source and payload as well as qualification
identity: requalifying unchanged bytes cannot erase a failure or finding. The recorder changes no candidate commit or payload bytes and
uploads no full worker evidence automatically.

## Verify promotion and publish only when authorized

```powershell
python scripts/release_candidate.py verify-promotion --run-id <qualification-run> --output artifacts/promotion/<unique> --tag v<VERSION>
```

This command performs no publication. It requires the complete exact qualification,
authoritative fresh security history and reviewed readiness disposition. A successful
non-publishing check does not establish real publication/public-smoke acceptance.

After explicit approval of the exact commit and tag, tagged Release downloads the already
qualified payload and performs trust, source/tag/version, inventory, provenance, payload,
security and readiness checks. It never invokes the deterministic inventory or builder.
It attests publication, publishes exactly qualified asset bytes, appends the concise
assessment only as supplemental release-body information, and verifies newly public asset
hashes plus real public installation/upgrade using the tag's catalogs. Existing identical
assets can be retried; differing or unexpected public assets fail without clobbering.

Do not advertise availability until promotion and public installation/upgrade succeed.
Component registries belong to their publisher repositories. Credentials and publishing
authority remain scoped; this workflow grants no independent stable-tag publication route.

## Failed-tag recovery

Preserve failed-run evidence and inspect all public assets and immutable registries before
recovery. Disclose partial publication explicitly. Repair the failure and obtain complete
CI qualification for the exact corrected commit and verify promotion. Exact corrected-commit
and same-tag approval is still required before deleting/recreating/pushing a failed stable
tag. Never hide differing escaped assets, rewrite receipts or increment merely because a
failed candidate tag existed. A changed source cannot borrow another commit's qualification.
A pushed stable tag is a candidate until its promotion and public smoke succeed.

Routine upgrades use the release-owned updater's inspectable plan and deterministic
retry. They never restart completed bootstrap or dispatch architecture authoring.
Preserve existing application edits, architectural decisions and historical results;
run affected engineering checks against current software. Missing receipts and
unrelated unfinished features do not block installation or ordinary implementation.
See [consumer engineering](consumer-engineering.md) for the file classification,
independent engineering commands and bounded execution-history cleanup.

Packaged migration history starts at v0.12.5. Earlier source versions require actual
managed-layout inspection, not a version-only approval. Protect unsupported inputs
and substantive conflicts; do not manufacture missing historical migrations.
Version-specific operational runbooks remain in their original Git commits.

Legacy NuGet retirement availability is monitored in the separate weekly/manual
maintenance workflow; current selected dependency availability remains a release gate.

Qualify a new-project default independently from the Program Kit bundle version.
Preserve existing registered profiles and their qualification-entry hashes. Create
a new exact profile, regenerate and review the generic native fixture lock, then
run `tests/validate_default_dependency_profile.py --profile <profile-path>` and
`tests/validate_published_forms_browser.py --profile <profile-path> --engines <engines>`.
Run the existing `tests/validate_bootstrap_runtime.py --profile <profile-path>`
against the candidate's exact immutable published host image.
The native check covers publisher metadata and exporter admission; features marked
`composeForOpenApi=false` are not executed. Keep runtime and component acceptance
with the publishers and retain consumer integration checks here.

Materialize the candidate catalog and run the maintained public availability
checker against every candidate pin, including npm and the host image. Preserve
the generic native, Forms browser, and availability evidence directories. Build a
portable receipt with `scripts/build_dependency_qualification.py --profile <profile-path>
--native <native-evidence-directory> --browser <browser-evidence-directory>
--availability <availability-json> --host <host-evidence-directory> --output <qualification-json>`.
The builder verifies preserved stages and streams, binds the exact recipe and lock,
and excludes unexpected consumer-specific fields. Register the new profile with
the resulting hashes and scope only after these checks pass. Run the profile
regressions and Development suite before review. Changing the default affects new
projects only; existing projects use the separate reviewed dependency transition.
This scoped profile qualification does not replace complete Program Kit CI candidate qualification or consumer Delivery.

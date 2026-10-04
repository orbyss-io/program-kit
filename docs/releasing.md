# Program Kit release procedure

Develop with targeted checks and the bounded Development suite. PR CI selects
checks conservatively from the shared inventory; unknown inputs select full
coverage. Main runs Development and Windows integration. Tagged Release runs all
required deterministic checks with exact-source evidence before publication.
Linux may run four workers; resource locks serialize shared fixtures and services.
Windows remains sequential. Firefox acceptance belongs to CI on this host.

Write reviewed release notes and migration entries under `releases/`. Each entry
states affected versions, prerequisites, automatic changes, review decisions,
validation and recovery, including an explicit no-action statement where relevant.
Verify offline guidance and immutable links in the installed extension and bundle.
Historical operational runbooks are retained in Git history; extract durable
recovery guidance before retiring them.

Keep the candidate checkout frozen throughout Release validation. Concurrent edits
produce `PROGRAM_KIT_RELEASE_SOURCE_CHANGED`; preserve the failed journal and log.
Passing individual checks does not authorize synthesizing a clean receipt for mixed
source revisions. Never invoke the receipt writer alone to replace a failed suite.
On this Windows host, `./scripts/Invoke-LocalRelease.ps1 -PrepareOnly` verifies
cached exact tools without starting validation. In the user's terminal, the same
helper without `-PrepareOnly` runs the required Release command with a bounded
process PATH and restores the caller's environment. Windows native command lookup
requires PATH below 8191 characters; use invocation-scoped tools rather than
changing machine installations.

When the user decides the candidate should proceed toward publication, freeze clean
committed source and ask them to run in a user-owned terminal:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Inspect the preserved transcript, per-check journal, receipt and asset hashes.
Require green candidate CI and complete tagged Release, including public install
and upgrade checks, before reporting availability. Any publication failure must
disclose already-public assets. Paid workers are separately authorized.

Follow [the evidence reuse policy](../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes).
Preserve the original receipt unchanged. The tagged Release workflow still runs in full.
Failed-tag reuse requires proof that nothing was published from the failed candidate.
Exact corrected-commit and same-tag approval is still required.
If any reuse condition is unproven, obtain fresh local Release evidence.

Review GitHub release permissions and protected publication environments in the
repository that owns each component. Foundation, Forms and Localization own their
registries and immutable component versions. NuGet trusted-publishing policies
must name the actual publisher repository, workflow and environment; credentials
must not be copied between repositories. Program Kit's tagged Release keeps its
component availability gates and downstream publication jobs.

`scripts/build_release.py` produces reviewed release notes, cumulative migrations
and a migration index alongside the archives. Their exact bytes appear in
`SHA256SUMS` and the Release receipt. The governance archive and bundle also
contain the verified index and guides under `references/release-guidance`.
The release workflow uses the reviewed notes as the GitHub release body and
uploads each indexed guide. Verify those assets and immutable release URLs
before declaring availability. Do not edit assets from a successful published
release. Consumers can inspect applicable guidance with the updater's `--plan`
mode; a plan grants no approval or migration-completion authority.

Scoped dependency qualification assets also ship beside the bundle: a dependency
profile index, exact profiles and their qualification receipts. The Release receipt
verifies their bytes against the index and `SHA256SUMS`. Native consumer qualification
does not substitute for full Program Kit Release validation or consumer Delivery.
Preserve the source bundle commit and original evidence; do not relabel them to a
later shipping commit. Keep untested activations outside the qualified profile scope.

For post-bootstrap recovery, create a linked continuation only from an intact
completed source run. Preserve original intake, ratification, approvals, receipts
and the entire recovery lineage. Changed executable inputs require the supported
proof renewal step and a fresh changed-artifact review. If an existing child fails
after architecture authoring, verify document bytes and repair only stale hash
bindings before resuming that same child without `--post-bootstrap`; another child
would repeat worker execution. Carry new Accepted prerequisites through installed
feature intake and renew affected analysis. Future feature and Delivery obligations
remain open until their own evidence passes.

Support starts at v0.12.5. Earlier consumers require a reviewed bridge that names
their preserved source state, required decisions, verification and recovery.
Do not manufacture missing historical migrations. Version-specific operational
runbooks are retained by their original Git commits; current procedure lives here.

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
This qualification does not replace the full local and tagged Release gates.

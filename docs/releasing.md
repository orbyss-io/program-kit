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

Support starts at v0.12.5. Earlier consumers require a reviewed bridge that names
their preserved source state, required decisions, verification and recovery.
Do not manufacture missing historical migrations. Version-specific operational
runbooks are retained by their original Git commits; current procedure lives here.

Legacy NuGet retirement availability is monitored in the separate weekly/manual
maintenance workflow; current selected dependency availability remains a release gate.

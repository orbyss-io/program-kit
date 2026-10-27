# Dependency maintenance

Publisher source capture uses the maintained `PUBLISHER_GUIDANCE` allowlist in
`scripts/update_dependency_profiles.py`, together with package-owned sources and exported
package facts. Add new canonical usage guides deliberately; contributor plans, validation
journals and consumer feedback are not automatically product knowledge. This affects future
captures only. Preserve frozen profiles, source/package hashes and existing consumer locks;
any historical privacy remediation needs an explicit separate disposition.

Dependency discovery, upgrades and profile qualification are deliberate maintenance;
release preparation does not require upgrading every active dependency. A candidate
uses its declared qualified dependency set and passes applicable security checks.
An unrelated failed maintenance experiment does not block an otherwise qualified
candidate; an applicable unresolved defect/security finding or missing required
qualification does.

The **Update dependencies** workflow runs manually or weekly. It discovers publisher
versions, upgrades active pins, refreshes native locks, qualifies the new dependency
profile and promotes its exact captured contracts/knowledge together. Existing
consumer locks and supported historical profile identities remain available.
New external inputs belong in `maintenance-policy.json`. Foundation publishes
independently; Program Kit consumes public releases and never republishes an already
public Foundation artifact.

Foundation's analyzer may be released independently of its runtime family. Use
`python scripts/update_dependency_profiles.py prepare --tool Orbyss.Foundation.Analyzers`
to observe only that tool and retain every other selected package/Host pin. Preparation
records its exact version in the Foundation family's `toolVersions` and names the new
profile with `-analyzer-<version>` when it differs from the runtime. This does not edit
historical profiles or consumer locks. Normal preparation continues to discover all
maintained families and independent tools.

After public publication, qualify that returned candidate with the ordinary `qualify`
command and promote only successful evidence. An independently selected analyzer binds
its native restored archive, exact public NuGet archive and provenance through the
existing `officialTools` proof alongside Build/exporter. Its package-owned sources and
`docs/ef-migration-authoring.md` come from the analyzer's own publisher commit; runtime
guidance retains the selected runtime commit. This adds no supplier-wide acceptance gate.

Use `python scripts/update_dependencies.py --development` for fast integrity only.
Use `python scripts/update_dependencies.py --changed-from <base>` for affected update
checks. These commands do not refresh locks or install toolchains. Explicit
`--refresh-locks` updates native locks; `--upgrade` discovers pins and qualifies a new
profile. Those operations check their actual device prerequisites and may require
user-terminal toolchain updates under the maintained device policy. Agents never
install device software or substitute repository-local runtimes.

The unattended workflow provisions its own selected tools, explicitly qualifies a
changed profile, refreshes locks and runs affected contracts. Native/profile
qualification can remain expensive because it establishes a specific dependency
contract; it is not repeated for unrelated feature changes or every release.
The selected public profile also passes two bounded native producer/client checks:
the numeric JSON contract and the actual emitted operation. These run even when a
profile was already promoted on the input branch, so a no-op discovery cannot omit
its generated-client qualification. They do not stage the full application Host.
After selecting the upgraded Python and requirements, CI explicitly prepares the
project-local schema runtime. Checks that use it declare `runtime:json-schema` in
the validation inventory; ordinary integrity/affected validation never installs it.
Lookup, security and test failures stop maintenance and identify the repair. A timeout
or partial result is never accepted. Preserve actionable diagnostics in normal Actions
artifacts, then fix/reproduce the failed focused check before retrying.

Active maintenance inputs select the corresponding small update, generated-workflow,
scaffold, schema and API/tooling contracts. Pin propagation checks for optional viewer
and PDF/OCR examples do not claim execution of those products; their native/provider
investigations remain explicit. Unknown inputs and required coverage decisions still
stop automatic maintenance; they never select the full inventory or become success.

Passing maintenance pushes a new `codex/dependencies-*` branch and opens a PR; it does
not merge `main` or publish packages. A dedicated GitHub App supplies a short-lived,
repository-scoped token only for the final push and PR creation. Its native PR event
starts the existing package CI: one build, Windows/Linux installation and applicable
security checks. Review that separate CI result before merging. The built-in
`GITHUB_TOKEN` remains read-only and checkout does not persist it for Git pushes.
It cannot push workflow-file updates, and its PR events would be suppressed. There
is no duplicate manual CI dispatch. Exact-main qualification and native publication
approval remain in the release flow. See [GitHub's trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

Provision a dedicated GitHub App and install it **only on this repository**. Grant
repository **Contents: read/write**, **Pull requests: read/write**, and **Workflows:
read/write**; metadata read is implicit. No organization, administration, secrets,
environment or publication permissions are needed. Webhooks and user authorization
are not used. Save its public client ID as repository variable
`DEPENDENCY_UPDATES_APP_CLIENT_ID` and its PEM private key as repository Actions secret
`DEPENDENCY_UPDATES_APP_PRIVATE_KEY`. Keep the private key out of source, logs and chat.
The pinned token action requests only those three permissions for the current
repository, and revokes its installation token at job completion. Missing App
configuration stops the job before discovery/upgrades. Follow GitHub's
[App registration](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)
and [installation](https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app) procedures.

The native bundle retains Spec Kit's 512-entry limit. Publication compacts historical
publisher facts and qualification locks into a bounded indexed container, preserving
their original bytes and recipe hashes. Original repository files, registered profiles,
qualification evidence and existing consumer locks are retained. Installed readers
verify both the packed bytes and the selected recipe's lock authority; compaction
grants no new qualification claim.

An explicit maintainer disposition may retain the original Forms browser evidence
when its entire npm artifact set, reviewed browser fixture and selected Node/npm
inputs are unchanged. Use `update_dependency_profiles.py qualify --candidate <path>
--retain-unchanged-browser <qualified-historical-profile> --reason <disposition>`.
The producer compares all 17 fixture/toolchain inputs against their historical Git
revision. The new receipt preserves the original browser profile, run-stage hashes,
engines and npm availability records, with a separate `retainedFrom` reference and
the reason. It claims no new browser execution or fresh npm-registry lookup. Changed
npm versions, changed fixture inputs, altered evidence and retention chains fail.
Current Foundation native/exporter and public Host evidence remain required.

When a publisher-knowledge capture needs correction with unchanged package pins,
use `update_dependency_profiles.py prepare --refresh-publisher-knowledge --reason
"<concrete capture repair>"`. This prepares a distinct `-q-` identity and records the
reason in its existing candidate state. Normal unchanged preparation remains a no-op.
Prior profiles, captures and consumer locks remain immutable; the new candidate must
pass the ordinary qualification and promotion owners. A reason supplies no qualification
or publication authority. Exact-identity native/Host checks still govern any evidence reuse.

For an interrupted candidate qualification, explicit `--native-evidence <directory>`
and `--host-evidence <directory>` can select successful components for that exact
candidate. The ordinary portable builder revalidates their profile, recipe, locks,
every native stage/archive/provenance, actual Host cases and cleanup. A directory
name or prior success alone supplies no reuse. This is scoped dependency evidence;
it does not borrow CI qualification, authorize publication or alter historical proof.

Public Aqua repository metadata uses the policy's explicit anonymous lookup; other
GitHub lookups retain authentication. Unavailable releases and unresolved action tags
are failures, not silent fallbacks. See [validation](../validation.md) for adding a
capability edge and [releasing](../releasing.md) for exact candidate publication.

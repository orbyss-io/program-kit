# Dependency maintenance

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
Lookup, security and test failures stop maintenance and identify the repair. A timeout
or partial result is never accepted. Preserve actionable diagnostics in normal Actions
artifacts, then fix/reproduce the failed focused check before retrying.

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

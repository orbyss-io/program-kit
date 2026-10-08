# Device toolchain policy: local implementation review

Implemented as a direct local patch on `main`, based on
`528a3e1e115f645b19e3f1cd9aca128c90df0157` (resumable consumer upgrade).
The fetched `origin/main` matched that commit; there were no incoming commits.
The initially untracked `.agents/` directory remains untouched. At completion of
validation, no commit or push had been performed. No real consumer upgrade,
device software installation by the agent, publication, Release run or paid
worker was performed.

## Behavior and scope

The shared read-only `eng/device_toolchain.py` provider emits `PKT030` diagnostics
with required versions, pin authority, detected versions and executable paths,
user-terminal commands, persistence/privilege notes, refresh guidance and
verification commands. See the shipped
[device policy](../../extensions/program-kit-governance/references/device-toolchain-policy.md).
Installer syntax was checked against the official sources linked there.

Contributor validation, dependency qualification, engineering, governance setup
and consumer upgrades use the shared policy. Legacy remediation/approval flags
cannot authorize device installation. Repository-local SDK/Node/npm tools,
inactive manager caches and repository-local Spec Kit interpreters cannot establish
device readiness. Current executable selection is checked again before dependent
execution; old successful evidence is preserved but cannot bypass a stale PATH.

Both initializers check the selected release's core tools before Spec Kit init,
catalog registration or repository dependency setup. Standalone launchers fetch
only release-owned diagnostic sources and pin data. Missing data blocks setup.
Git/integration prerequisites and later profile-specific requirements retain their
existing checks. Future pin changes require fresh verification.

Shared user installations and persistent manager defaults are supported, as are
side-by-side SDKs selected by authoritative `global.json`. Project dependencies,
virtual environments, schema-library caches and disposable fixtures retain their
separate restoration behavior. CI/container provisioning remains unattended.
Approved project analysis-binary staging (oasdiff) remains separate from installing
device SDKs/runtimes and cannot bypass device readiness.

## Verification

After the user updated software in their own terminal, a fresh normal Windows
PowerShell process loading its persisted profile verified Node **26.11.1**, npm
**12.2.0**, .NET SDK **10.0.401**, Python **3.14.8** and shared Spec Kit **1.1.2**.
The old agent process retained stale Node selection; validation used a fresh
profile-enabled shell, without a temporary tool PATH override or repository copy.

- Final bounded Development command:
  `./scripts/Test-ProgramKit.ps1 -Suite Development -BrowserEngines 'chromium,webkit'`.
  Exit code 0; **82 steps, all exit code 0**. Per-step logs and hashes are in
  [the final journal](../../artifacts/validation-runs/20261008T221808Z-d5696c73/journal.json).
- `tests/validate_repository_toolchain.py`: **13 passing regressions**. Disposable
  fixtures cover missing/outdated tools, ignored local fallbacks, no installer
  execution, shared reuse across repositories/fresh processes, stale PATH,
  side-by-side SDK selection, local Python/Spec Kit interpreter rejection,
  unchanged project npm restoration and initialization pause/resume.
- Targeted JS, lifecycle, repository sync, shell preflight, validation runner,
  knowledge inventory, compatibility and consumer-upgrade checks passed.
- Built isolated local test archives with
  `scripts/build_release.py --output artifacts/device-policy-package`.
  The bundle contains **468 files**. SHA-256 of `program-kit-0.12.9.zip`:
  `66277cbcc87090359689e12286b473cce9f56b8d3869c331236769d0fd9f78e3`.
- `tests/validate_consumer_upgrade_install.py --archive
  artifacts/device-policy-package/program-kit-0.12.9.zip` passed packaged primitive
  installation, sequential updater convergence, destination activation and failed
  activation recovery in disposable consumers. See
  [the summary](../../artifacts/consumer-upgrade-install.json) and raw evidence in
  `artifacts/consumer-upgrade-package-runs/620b8db8c94a45c5b8d4f80e7df1f1ef/`.
  This test started no coding agents and does not establish real application acceptance.

Earlier failed Development evidence is preserved in
`artifacts/validation-runs/20261008T212910Z-f26655d2/` and
`artifacts/validation-runs/20261008T214539Z-0007f5fc/`. Repairs covered PowerShell
wrapped-output assertions, fixture mocks for independent device checks, tracked
scaffold inputs, policy knowledge routes and removed executable-override assumptions.
The final run above includes those repairs and the final Spec Kit shim check.

Exact pins, consumer-lock sources, historical profiles, version/catalog authority
and CI provisioning/browser matrix are unchanged. `git diff HEAD --check` passed.

## Material limits

Firefox cannot launch on this local Windows host; CI remains its acceptance
authority. Other OS installation commands were checked against documentation and
fixture-tested, not executed on real macOS/Linux devices. Custom managers/shells
still require inspection before prescribing commands.

These archives are local test builds, not published release artifacts. The new
standalone online initialization path requires its policy/helper files to ship
with the selected future release tag. Existing remote stable tags were not moved.
Early readiness reduces setup surprises; subsequent checks remain necessary when
pins, session state or selected profiles change.

# Program Kit 0.12.10

This patch adds the resumable consumer updater and an early, persistent device
toolchain readiness policy. It preserves consumer application edits, exact
dependency locks, historical profiles, architecture authority and existing
upgrade recovery.

## Device prerequisites and initialization

On human devices, initialization checks the selected release's Node.js, npm,
.NET SDK, Python and Spec Kit requirements before repository setup. Later
engineering, bootstrap, maintenance and upgrade steps verify the actual shared
executable selection again. Diagnostics show required versions and authoritative
pins, detected versions and paths, OS/manager commands, persistence and privilege
notes, session refresh and verification commands.

Users execute device installation/update commands in their own terminal. Agents
pause dependent work and verify paths and versions after completion. Legacy
remediation/approval flags cannot authorize device installation. Repository-local
SDK/Node/npm copies, inactive manager caches, temporary PATH masking and local uv
tool interpreters cannot establish device readiness. Supported shared user-level
managers and side-by-side SDKs remain valid; administrator-wide installation is
not required. Preserve other runtime versions and existing pins.

Project dependency restoration, node_modules, project virtual environments,
schema-library caches and disposable fixtures remain separate from installing
device software. CI/container-owned provisioning remains unattended. Follow
the shipped device-toolchain-policy reference, including fnm setup and persistent
default selection, or inspect the existing installation manager's official
documentation before prescribing another route.

## Consumer upgrades

The packaged updater supports inspectable plans, isolated preparation,
destination activation, deterministic retry and failed-activation recovery.
Do not restart completed bootstrap or manufacture new migration authority.
Retain existing application changes, architecture decisions and historical
evidence. A toolkit installation pass does not establish application acceptance.

## Migration, verification and recovery

No consumer code or architecture conversion is required solely by this patch.
Run the supported updater for the selected release and verify installation
coherence. Retain exact consumer dependencies unless adopting a separately
reviewed dependency transition. Run affected engineering checks against the
actual device tools and test changed application behavior independently.

If readiness fails, preserve the diagnostic and previous successful evidence,
complete user-terminal remediation, refresh the terminal/calling application
and retry. Do not install a repository-local fallback or change pins to match
the device. Preserve failed upgrade evidence and use the existing resumable
recovery rather than deleting installations or consumer artifacts.

Local release validation uses chromium and webkit on the documented Windows
host; CI owns Firefox acceptance. Publication requires the complete tagged
Release workflow, including public installation and upgrade checks.

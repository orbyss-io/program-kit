# Device toolchain updates

On a human device, an agent must pause execution that depends on missing or mismatched
software. Ask the user to install/update it in their own terminal. Never execute device
installation commands, including with approval, escalation, a supplied installer, or a
legacy `--remediate --approve` flag. This applies to contributor validation, dependency
maintenance, bootstrap/setup, consumer upgrades and ordinary engineering.

Use the shared `eng/device_toolchain.py` provider shipped by the .NET extension (governance
loads it through `package_execution.javascript_runtime().device`). `PKT030` diagnostics
contain the tool, required version, authoritative pin, detected version, executable path,
user commands, verification commands, privilege/persistence notes and official sources.
`eng/toolchain.py` records the same contract under `devicePolicy` in its evidence. Existing
satisfied evidence is preserved when renewal fails; it cannot grant current readiness.

Exact SDK, Node and npm authority comes from the selected profile/approved decision and
managed `global.json`, `.nvmrc`, `.npm-version`. Python's existing minimum is >=3.11;
an exact `.python-version`, when present, remains authoritative. The contributor Spec Kit
compatibility baseline remains >=1.1.1,<2, with 1.1.1 recommended for a baseline repair.
Contributors use the exact existing `specify-cli` pin in `.github/workflows/ci.yml`; diagnostics
read that file instead of substituting the compatibility minimum. Do not edit pins,
consumer locks, SDK roll-forward settings, or existing architecture authority to accommodate
whatever is installed. An existing supported override retains its normal decision contract.

Before proposing commands, inspect the user's OS, shell, resolved paths and existing
installation/version manager. Verify the exact syntax against its official documentation.
The provider covers fnm, Volta, POSIX nvm, nvm-windows, pyenv and shared uv/pipx tools.
Native/custom installations require an explicit check of their installer and architecture;
do not silently switch managers. Commands printed as recommendations are for the user.

## Initialization front door

Both human-owned `Initialize-ProgramKit.cmd` and `Initialize-ProgramKit.sh` run
`scripts/initialize_device.py` before Spec Kit initialization, catalog registration or repository
dependency setup. It reuses the same diagnostic provider and exact SDK/Node/npm pins from the
initializer's selected release tag. A source checkout/staged same-version release uses its files;
a standalone launcher fetches only diagnostic Python sources and pin data over HTTPS from that
exact tag into temporary storage outside the consumer. No device distribution is downloaded.
Failed lookup, missing tools or wrong selections block initialization without starting bootstrap.

The current release's core device requirements are checked even before profile intake. Git and
the chosen integration retain their existing prerequisites. Profile-specific providers (for
example a running container engine) are checked when selected. The user's terminal runs any
reported installation commands; the preflight never runs them. After completion, refresh the
shell/application and rerun initialization. Actual paths/versions must pass before setup continues.
Future pin changes require fresh verification rather than relying on an initialization receipt.

To check an explicitly staged release independently, use its
`python scripts/initialize_device.py --ref v<release-version> --release-root <release-directory>
--project-root <consumer-directory>`. This is a read-only device check, not a consumer upgrade,
bootstrap dispatch, paid phase or publication approval.

## No Node manager installed

On Windows, the recommended side-by-side user manager is fnm. Its package ID is
`Schniz.fnm`. In the user's PowerShell terminal:

```powershell
winget install Schniz.fnm
```

Open a new PowerShell terminal so WinGet's persistent PATH is visible. Preserve the existing
Node installation. In that terminal:

```powershell
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}
$loader = 'fnm env --shell powershell | Out-String | Invoke-Expression'
if (-not (Select-String -Path $PROFILE -SimpleMatch $loader -Quiet)) {
    Add-Content -Path $PROFILE -Value $loader
}
fnm env --shell powershell | Out-String | Invoke-Expression
fnm install <required-node-version>
fnm default <required-node-version>
fnm use <required-node-version>
```

Replace the placeholder with the exact selected pin. The `default` selection and profile
loader persist across repositories and fresh sessions. Windows PowerShell and PowerShell 7
have separate profiles: configure the profile of each shell you actually use. Agents launched
from applications must inherit the persistent selection; restart their parent application if
needed. fnm normally needs no administrator terminal; WinGet/device policy may request UAC.
If WinGet is unavailable, use the official Scoop route (`scoop install fnm`) when Scoop is
already installed, or the official release binary and persistent user PATH setup. Never choose
an elevation-bound package manager implicitly.

On macOS, use `brew install fnm` with an existing Homebrew installation. On Linux, the official
route is `curl -fsSL https://fnm.vercel.app/install | bash`; inspect the script first. Persist
`eval "$(fnm env --shell bash)"` in `~/.bashrc`, or the corresponding `--shell zsh` loader in
`~/.zshrc`. Fish uses `fnm env --shell fish | source` in `~/.config/fish/conf.d/fnm.fish`.
Then run the same `fnm install`, `fnm default`, and `fnm use` commands in the user terminal.
Identify an unfamiliar shell before proposing its profile commands.

Existing Volta users use `volta install node@<pin>` and `volta install npm@<pin>` (persistent
user defaults). POSIX nvm users use `nvm install <pin>`, `nvm alias default <pin>`, and
`nvm use <pin>`, retaining their shell loader. nvm-windows uses `nvm install <pin>` and
`nvm use <pin>`; its persistent symlink selection may require elevation. Inspect documented
MSI/PATH/symlink conflicts without deleting existing installations.

## npm, SDK, Python and Spec Kit

After selecting the required Node, inspect `npm config get prefix`. It must point to a shared
user/device or manager installation outside all repositories. Use the selected manager's npm
command, or `npm install --global npm@<required-npm-version>` in the user's terminal. A system
prefix may need administrator privileges; a shared user manager avoids this. Preserve strict
TLS/trust configuration. A repository prefix is never a device installation.

Install an exact .NET SDK alongside other required SDKs/runtimes using Microsoft's supported
installer into the existing shared root. The diagnostic also supplies Microsoft's exact-version
script arguments when that route is appropriate. A protected root needs elevation. For a new
user root, persist `DOTNET_ROOT` and PATH in user settings/shell startup files. An install script's
session-only PATH change is insufficient. Verify the installed SDK list and run `dotnet --version`
from the repository with its authoritative `global.json`; other repositories can select other SDKs.

Python may use an existing native installer or persistent version manager. With shared uv:
`uv python install <required-version> --default`, then `uv python update-shell`. `--default`
creates unversioned launchers and currently is experimental; do not use `--force` to replace a
non-uv Python. With pyenv, `pyenv install <version>` and `pyenv global <version>` persist the
selection. Do not replace OS-owned Python or discard other versions. If `.python-version` pins
a patch, use that exact version; a minimum requirement does not invent a patch pin.

Spec Kit's shared user uv installation is acceptable:
`uv tool install specify-cli==1.1.1 --force --no-python-downloads`, then `uv tool update-shell`.
For contributor validation, substitute the exact existing CI pin for 1.1.1 in that command.
Device Python must already be available. An existing pipx installation may use
`pipx install specify-cli==1.1.1 --force` and `pipx ensurepath`. For users without uv, the official
Windows command is `winget install --id=astral-sh.uv -e`; macOS with Homebrew uses
`brew install uv`; Linux uses `curl -LsSf https://astral.sh/uv/install.sh | sh`. Review scripts,
run outside the repository with default shared tool directories, and reopen the terminal before
using the newly installed manager. Retain a different existing installation method after checking
its official exact-version commands. No repository-local uv tool environment establishes readiness.

## Verification and scope

After the user reports completion, re-probe actual executable paths and versions. On Windows:

```powershell
Get-Command node,npm,dotnet,python,specify -All | Select-Object Name,Source
node --version
node -p "process.execPath"
npm --version
npm config get prefix
dotnet --list-sdks
dotnet --list-runtimes
dotnet --version
python --version
python -c "import sys; print(sys.executable); print(sys.base_prefix)"
specify version
```

On POSIX use `command -v` for each executable and the same version probes. Also verify in a
fresh terminal outside the repository. If the current process has stale PATH/environment state,
explain how to restart its shell/parent application. A fresh shell may load the user's persistent
manager profile normally. Do not inject temporary tool selections or install another copy.

`artifacts/tools`, repository SDK/Node/npm installations, virtual-environment interpreters,
local uv tools, manager caches that are not actively selected, and `PROGRAMKIT_*_EXECUTABLE`
overrides cannot silently establish device readiness. Never delete existing copies.

Project dependency restoration remains supported: `npm ci`, `node_modules`, project virtual
environments using an already installed interpreter, NuGet/.NET project tool restores, pinned
schema-library caches, Playwright test fixtures and explicitly reviewed project analysis binaries
such as oasdiff. Helper code may use Spec Kit's existing shared interpreter or a project venv for its libraries only
after independently checking device Python; it does not establish Python readiness by itself.
CI/container-owned toolchain provisioning remains unattended in its owning workflows/images.
This policy adds no publication, bootstrap, paid-worker, consumer-migration or recovery authority.

Official command sources checked for this implementation on 2026-10-08:
[fnm setup](https://github.com/Schniz/fnm/blob/master/README.md),
[fnm commands](https://github.com/Schniz/fnm/blob/master/docs/commands.md),
[Volta](https://docs.volta.sh/reference/install), [nvm](https://github.com/nvm-sh/nvm),
[nvm-windows](https://github.com/coreybutler/nvm-windows),
[npm](https://docs.npmjs.com/cli/v11/commands/npm-install/),
[Microsoft .NET](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script),
[uv installation](https://docs.astral.sh/uv/getting-started/installation/),
[uv Python](https://docs.astral.sh/uv/guides/install-python/),
[uv tools](https://docs.astral.sh/uv/concepts/tools/),
[pyenv](https://github.com/pyenv/pyenv), [Spec Kit](https://github.com/github/spec-kit).

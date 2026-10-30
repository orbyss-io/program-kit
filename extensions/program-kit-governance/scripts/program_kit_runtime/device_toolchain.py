"""Read-only device readiness and user-terminal remediation. Never runs installers.

This single provider is shipped with engineering and loaded by governance and contributors.
Project dependency caches/restores are deliberately outside this contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys

SOURCES = {
    'node': 'https://github.com/Schniz/fnm/blob/master/README.md',
    'npm': 'https://docs.npmjs.com/cli/v11/commands/npm-install/',
    'dotnet': 'https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script',
    'python': 'https://docs.astral.sh/uv/guides/install-python/',
    'specify': 'https://github.com/github/spec-kit',
    'git': 'https://git-scm.com/install/',
    'pwsh': 'https://learn.microsoft.com/powershell/scripting/install/install-powershell',
    'docker': 'https://docs.docker.com/get-started/get-docker/',
    'java': 'https://adoptium.net/installation/',
    'gh': 'https://github.com/cli/cli#installation',
}
REFRESH = ('After the user reports completion, open a fresh terminal and restart the calling '
           'application if its inherited PATH is stale. Re-run readiness and inspect actual paths '
           'and versions before dependent execution. Do not install another local copy or prepend '
           'a temporary PATH to mask an outdated selection.')


# Closed device names and actual owner constraints. No arbitrary executable or
# version strings are ever interpolated into a human installer script.
VERSION = re.compile(r'^(?:>=)?[0-9]+(?:\.[0-9]+){0,3}$')
EXTRA_TOOLS = {'git', 'pwsh', 'docker', 'java', 'gh'}


def host_windows() -> bool:
    return os.name == 'nt'


def validate_request(name: str, required: str) -> None:
    if name not in SOURCES or not isinstance(required, str) or not (
            required == 'available' or VERSION.fullmatch(required)):
        raise ValueError('PKT031 unknown device tool or unsafe/unrecognized version constraint')


def quote(value: str, windows: bool) -> str:
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        raise ValueError('PKT031 device script data contains a control character')
    return "'" + value.replace("'", "''") + "'" if windows else shlex.quote(value)


def extra_instructions(name, required, repository, detected_path):
    windows = host_windows()
    minimum = required.removeprefix('>=')
    commands, notes = [], []
    sources = [SOURCES[name]]
    # Existing installations with unknown ownership are never replaced merely
    # because a different package manager happens to be installed.
    if detected_path:
        notes.append('Retain the existing installation method. Verify its official update procedure; '
                     'no manager ownership was established, so no replacement command is prescribed.')
    elif windows and executable('winget', repository) and name in {'git', 'pwsh', 'gh', 'java'}:
        package = {'git': 'Git.Git', 'pwsh': 'Microsoft.PowerShell', 'gh': 'GitHub.cli'}.get(name)
        if name == 'java':
            # The C4 owner supplies a minimum major. Only documented Temurin LTS
            # package identities are emitted; an unknown major remains manual.
            if minimum in {'11', '21'}:
                package = 'EclipseAdoptium.Temurin.' + minimum + '.JDK'
        if package:
            commands = ['winget install --id ' + package + ' --exact --source winget']
    elif sys.platform == 'darwin' and executable('brew', repository) and name in {'git', 'gh'}:
        commands = ['brew install ' + name]
    elif sys.platform.startswith('linux') and name == 'git':
        try:
            distro = __import__('platform').freedesktop_os_release().get('ID', '')
        except (OSError, AttributeError):
            distro = ''
        if distro in {'ubuntu', 'debian'} and executable('apt-get', repository):
            commands = ['sudo apt-get update', 'sudo apt-get install git-all']
        elif distro == 'fedora' and executable('dnf', repository):
            commands = ['sudo dnf install git-all']
    if name == 'docker':
        notes.append('Install Docker using the official instructions for this OS/architecture and your chosen '
                     'Engine/Desktop provider. Review its prerequisites/license. Do not change daemon/socket '
                     'permissions or select another context to mask an access failure.')
    if name == 'java':
        notes.append('The requirement is supplied by the selected runtime owner, not a toolkit-wide Java pin. '
                     'Retain the existing JDK vendor/manager; verify persistent JAVA_HOME/PATH where applicable.')
    if not commands:
        notes.append('Manual installation/update step remains: use the linked official instructions for '
                     'the existing manager, OS and architecture, then run the verification script. '
                     'This handoff is not an install-ready recipe or a readiness claim.')
    verify = ['java -version'] if name == 'java' else [name + ' --version']
    if name == 'docker':
        verify += ['docker context show', 'docker version', 'docker info']
    location = f'Get-Command {name} -All | Select-Object Name,Source' if windows else f'command -v {name}'
    return {'commands': commands, 'verification': [location, *verify], 'notes': notes, 'sources': sources,
            'installationReady': bool(commands)}


def shared(path: Path, repository: Path) -> bool:
    """Reject repository installations, including fallbacks in another checkout."""
    path = path.resolve()
    if path.is_relative_to(repository.resolve()):
        return False
    return not any((parent / '.git').exists() for parent in path.parents)


def interpreter_binding(path: Path) -> Path | None:
    """A shared Spec Kit launcher can still point at a repository-local uv environment."""
    try:
        payload = path.read_bytes()
        marker = payload.rfind(b'#!') if path.suffix.casefold() == '.exe' else (0 if payload.startswith(b'#!') else -1)
        if marker < 0: return None
        line = payload[marker + 2:].splitlines()[0].decode('utf-8').strip().strip('"')
        candidate = Path(line)
        return candidate.resolve() if candidate.is_absolute() else None
    except (OSError, UnicodeError, IndexError):
        return None


def executable(name: str, repository: Path) -> Path | None:
    located = shutil.which(name)
    path = Path(located).resolve() if located else None
    if path and name == 'specify':
        interpreter = interpreter_binding(path)
        if interpreter and not shared(interpreter, repository): return None
    return path if path and shared(path, repository) else None


def probe(command: list[str], repository: Path) -> str | None:
    try:
        result = subprocess.run(command, cwd=repository, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=30, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def uv_setup(windows: bool) -> list[str]:
    return (['winget install --id=astral-sh.uv -e'] if windows else
            ['brew install uv'] if sys.platform == 'darwin' else
            ['curl -LsSf https://astral.sh/uv/install.sh | sh'])


def instructions(name: str, required: str, repository: Path, detected_path: str = '') -> dict:
    """Commands are data for the human, never a subprocess argument vector."""
    validate_request(name, required)
    if not host_windows() and sys.platform != 'darwin' and not sys.platform.startswith('linux'):
        return {'commands': [], 'verification': ['command -v ' + name,
                name + (' -version' if name == 'java' else ' version' if name == 'specify' else ' --version')],
            'notes': ['This inspected OS has no supported preparation recipe. Use the official OS/architecture '
                      'instructions manually, then rerun the original dependent check.'],
            'sources': [SOURCES[name]], 'installationReady': False}
    if name in EXTRA_TOOLS:
        return extra_instructions(name, required, repository, detected_path)
    windows = host_windows()
    if required == 'available' or (required.startswith('>=') and name != 'python'):
        location = f'Get-Command {name} -All | Select-Object Name,Source' if windows else f'command -v {name}'
        return {'commands': [], 'verification': [location, name + (' version' if name == 'specify' else ' --version')],
            'notes': ['The selected action requires this tool, but this layer supplies no exact installer selector. '
                      'Use the actual owning profile/minimum and existing manager; no version or installer was invented.'],
            'sources': [SOURCES[name]], 'installationReady': False}
    commands, notes, sources = [], [], [SOURCES[name]]
    verify = [f'{name} --version']
    location = f'Get-Command {name} -All | Select-Object Name,Source' if windows else f'command -v {name}'
    if name in {'node', 'npm'}:
        normalized = detected_path.replace('\\', '/').lower()
        owner = next((manager for manager, fragments in (
            ('volta', ('/.volta/', '/volta/')), ('fnm', ('/.fnm/', '/fnm/')),
            ('nvm', ('/.nvm/', '/nvm/'))) if any(fragment in normalized for fragment in fragments)), None)
        manager = owner if detected_path else next((item for item in ('fnm', 'volta', 'nvm') if executable(item, repository)), None)
        if detected_path and (not owner or (owner != 'nvm' and not executable(owner, repository))):
            return {'commands': [], 'verification': [location, name + ' --version'],
                'notes': [('First select the required shared Node. ' if name == 'npm' else '') +
                    'Retain the active native/manager installation. Its exact manager is unknown or unavailable; '
                    'do not select a different installed manager or create a local fallback.'],
                'sources': sources, 'installationReady': False}
        # POSIX nvm is a shell function, absent from shutil.which. Preserve a detected nvm install.
        if manager is None and (os.environ.get('NVM_DIR') or '/.nvm/' in detected_path):
            manager = 'nvm'
        if name == 'node':
            if manager is None:
                manager = 'fnm'
                commands.append('winget install Schniz.fnm' if windows else
                                ('brew install fnm' if sys.platform == 'darwin' else
                                 'curl -fsSL https://fnm.vercel.app/install | bash'))
                notes.append('Recommended side-by-side manager: fnm. Preserve the existing Node installation. '
                             'Reopen your terminal after installing the manager. Do not delete existing tools.')
            if manager == 'fnm':
                selected_shell = Path(os.environ.get('SHELL', '/bin/bash')).name
                if not windows and selected_shell not in {'bash', 'zsh'}:
                    return {'commands': [], 'verification': [location, 'node --version', 'npm --version'],
                        'notes': ['Retain the existing shell and fnm manager. Its persistent loader requires '
                                  'manual setup using the official instructions for this shell; no shell profile was guessed.'],
                        'sources': sources, 'installationReady': False}
                commands += [f'fnm install {required}', f'fnm default {required}', f'fnm use {required}']
                shell = 'powershell' if windows else ('zsh' if os.environ.get('SHELL', '').endswith('zsh') else 'bash')
                loader = ('fnm env --shell powershell | Out-String | Invoke-Expression' if windows else
                          f'eval "$(fnm env --shell {shell})"')
                setup = (['if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }',
                          f"if (-not (Select-String -Path $PROFILE -SimpleMatch '{loader}' -Quiet)) {{ Add-Content -Path $PROFILE -Value '{loader}' }}",
                          loader] if windows else
                         [f"printf '%s\\n' '{loader}' >> ~/.{shell}rc", loader])
                commands = commands[:-3] + setup + commands[-3:]
                notes.append(f'Persist this loader in your {"$PROFILE" if windows else "~/." + shell + "rc"}: {loader}. '
                             'Load it before fnm use, and ensure a fresh terminal resolves the manager before an older system Node.')
                sources.append('https://github.com/Schniz/fnm/blob/master/docs/commands.md')
            elif manager == 'volta':
                commands = [f'volta install node@{required}']
                sources.append('https://docs.volta.sh/reference/install')
                notes.append('volta install persists the user default. Ensure Volta shims are on persistent PATH.')
            elif windows:
                commands = [f'nvm install {required}', f'nvm use {required}']
                sources.append('https://github.com/coreybutler/nvm-windows')
                notes.append('nvm-windows use changes a persistent symlink and may require an administrator terminal. '
                             'Check its documented PATH/symlink conflicts with an existing MSI installation first; do not delete it.')
            else:
                commands = [f'nvm install {required}', f'nvm alias default {required}', f'nvm use {required}']
                sources.append('https://github.com/nvm-sh/nvm')
                notes.append('Keep the nvm loader in your shell startup file; the default alias persists across sessions.')
            verify = ['node --version', 'node -p "process.execPath"', 'npm --version']
        else:
            commands = [f'volta install npm@{required}' if manager == 'volta' else f'npm install --global npm@{required}']
            notes.append('First select the required shared Node. Check npm config get prefix: it must be a shared '
                         'user/device or manager directory, outside every repository. An administrator terminal may '
                         'be required for a system prefix; a persistent user manager avoids that requirement.')
            verify = ['npm --version', 'npm config get prefix']
            if manager == 'volta': sources.append('https://docs.volta.sh/reference/install')
    elif name == 'dotnet':
        if detected_path:
            return {'commands': [], 'verification': [location, 'dotnet --list-sdks', 'dotnet --list-runtimes', 'dotnet --version'],
                'notes': ['Retain the existing SDK installation method and side-by-side SDKs. An executable path '
                          'does not prove dotnet-install ownership; use its existing native/package-manager update procedure.'],
                'sources': sources, 'installationReady': False}
        # Install alongside other SDKs into the already selected shared root, never a per-repo root.
        root = Path(detected_path).parent if detected_path else Path.home() / '.dotnet'
        if not shared(root, repository):
            return {'commands': [], 'verification': [location, 'dotnet --list-sdks', 'dotnet --version'],
                'notes': ['Repository-local SDK roots cannot establish device readiness. Verify the shared device installation in a fresh terminal.'],
                'sources': sources, 'installationReady': False}
        root_text = quote(str(root), windows)
        if windows:
            commands = ['Invoke-WebRequest https://dot.net/v1/dotnet-install.ps1 -OutFile "$env:TEMP/dotnet-install.ps1"',
                        f'& "$env:TEMP/dotnet-install.ps1" -Version {required} -InstallDir {root_text} -NoPath']
        else:
            commands = ['curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh',
                        f'bash /tmp/dotnet-install.sh --version {required} --install-dir {root_text} --no-path']
        notes.append('Review the Microsoft script before running it. Add the SDK alongside existing SDKs/runtimes '
                     'in this shared root; do not uninstall them. A protected existing root requires administrator '
                     'privileges (sudo on POSIX). Microsoft recommends native installers for development; use the '
                     'exact-version installer from the official download page if that is your existing install method.')
        if not detected_path:
            if windows:
                commands += [f'[Environment]::SetEnvironmentVariable(\'DOTNET_ROOT\', {root_text}, \'User\')',
                             f'[Environment]::SetEnvironmentVariable(\'Path\', {quote(str(root) + chr(59), True)} + [Environment]::GetEnvironmentVariable(\'Path\', \'User\'), \'User\')']
            else:
                notes.append(f'Persist export DOTNET_ROOT=\'{root}\' and export PATH="$DOTNET_ROOT:$PATH" '
                             'in the startup file for your existing shell; reopen it.')
        verify = ['dotnet --list-sdks', 'dotnet --list-runtimes', 'dotnet --version']
        notes.append('Verify --version from the repository with its authoritative global.json; other repositories '
                     'can select their own installed SDKs. Never change rollForward or pins to accommodate PATH.')
    elif name == 'python':
        version = required.removeprefix('>=')
        if detected_path and not any(part in detected_path.replace('\\', '/').lower() for part in ('/pyenv/', '/.pyenv/', '/uv/python/')):
            return {'commands': [], 'verification': [location, 'python --version', 'python -c "import sys; print(sys.executable); print(sys.base_prefix)"'],
                'notes': ['Retain this existing Python installation method. Verify its official update procedure; '
                          'no replacement or manager switch was authorized by detecting another manager.'],
                'sources': sources, 'installationReady': False}
        normalized = detected_path.replace('\\', '/').lower()
        if detected_path and ('/pyenv/' in normalized or '/.pyenv/' in normalized) and not executable('pyenv', repository):
            return {'commands': [], 'verification': [location, 'python --version'],
                'notes': ['Restore/verify the existing pyenv manager before updating its Python; do not switch managers.'],
                'sources': sources, 'installationReady': False}
        if executable('pyenv', repository) and (not detected_path or '/pyenv/' in normalized or '/.pyenv/' in normalized):
            commands = [f'pyenv install {version}', f'pyenv global {version}']
            sources.append('https://github.com/pyenv/pyenv')
        else:
            commands = ([] if executable('uv', repository) else uv_setup(windows)) + [f'uv python install {version} --default', 'uv python update-shell']
            sources.append('https://docs.astral.sh/uv/getting-started/installation/')
            notes.append('If uv is new, reopen the terminal before running its commands. This is a persistent '
                         'shared Python installation alongside existing versions. If you maintain Python with '
                         'an OS/native installer, retain that method: consult https://www.python.org/downloads/ '
                         'and verify the exact OS/architecture command rather than switching managers implicitly.')
        notes.append('A minimum requirement is not an exact patch pin. Do not replace an existing non-manager '
                     'executable with --force. User-level installs require no administrator privileges; protected '
                     'system installs may. Project venvs and uv tool interpreters do not establish device Python readiness.')
        verify = ['python --version', 'python -c "import sys; print(sys.executable); print(sys.base_prefix)"']
    elif name == 'specify':
        normalized = detected_path.replace('\\', '/').lower()
        if detected_path and not any(part in normalized for part in ('/uv/tools/', '/pipx/venvs/')):
            return {'commands': [], 'verification': [location, 'specify version'],
                'notes': ['Retain the selected shared Spec Kit installer/manager. Its owner is unknown; '
                          'no replacement through an unrelated manager was prescribed.'],
                'sources': sources, 'installationReady': False}
        if executable('uv', repository) and (not detected_path or '/uv/tools/' in normalized):
            commands = [f'uv tool install specify-cli=={required} --force --no-python-downloads', 'uv tool update-shell']
            sources.append('https://docs.astral.sh/uv/concepts/tools/')
        elif executable('pipx', repository) and (not detected_path or '/pipx/venvs/' in normalized):
            commands = [f'pipx install specify-cli=={required} --force', 'pipx ensurepath']
            sources.append('https://pipx.pypa.io/stable/docs/')
        elif detected_path:
            return {'commands': [], 'verification': [location, 'specify version'],
                'notes': ['Restore/verify the existing tool manager before updating its shared Spec Kit environment; do not switch managers.'],
                'sources': sources, 'installationReady': False}
        else:
            commands = uv_setup(windows) + [f'uv tool install specify-cli=={required} --force --no-python-downloads', 'uv tool update-shell']
            sources += ['https://docs.astral.sh/uv/getting-started/installation/', 'https://docs.astral.sh/uv/concepts/tools/']
            notes.append('Recommended route when no tool manager is present: shared uv. Reopen the terminal after '
                         'installing it. If an existing installation uses a different manager, identify it and '
                         'verify its official exact-version update command first; do not overwrite unrelated tools.')
        notes.append('Run outside the repository with default shared tool directories. No administrator privileges '
                     'are needed for user-level tools. Python must already be ready; this command must not fetch another interpreter.')
        verify = ['specify version']
    return {'commands': commands, 'verification': [location, *verify], 'notes': notes, 'sources': sources}


def diagnostic(name: str, required: str, authority: str, actual: str | None,
               path: str | None, repository: Path) -> dict:
    validate_request(name, required)
    # Resolvers deliberately discard commands which failed readiness. Preserve
    # the active device path for diagnosis, never as an accepted execution path.
    if not path:
        observed = executable('npm.cmd' if name == 'npm' and os.name == 'nt' else name, repository)
        path = str(observed) if observed else None
    unknown_observation = actual is None
    if name == 'dotnet' and actual is None and path and shared(Path(path), repository):
        installed = probe([path, '--list-sdks'], repository)
        if installed:
            actual = 'installed SDKs: ' + installed.replace('\n', '; ')
    remedy = instructions(name, required, repository, path or '')
    verification_only = bool(path and unknown_observation)
    if verification_only:
        remedy['commands'] = []
        remedy['installationReady'] = False
        remedy['notes'] = ['An active shared executable was found but its selected version was not established. '
            'Verify access, launcher and version in your own terminal before prescribing an update. '
            'A failed probe is not evidence that installation or replacement is needed.']
    located = shutil.which('npm.cmd' if name == 'npm' and os.name == 'nt' else name)
    ignored = str(Path(located).resolve()) if located and not shared(Path(located), repository) else None
    if located and name == 'specify':
        binding = interpreter_binding(Path(located))
        if binding and not shared(binding, repository): ignored = str(Path(located).resolve()) + ' -> ' + str(binding)
    if ignored:
        remedy['notes'].append('Ignored repository-local executable (not device readiness): ' + ignored)
    return {'code': 'PKT030', 'status': 'user-terminal-verification-required' if verification_only else 'user-terminal-required', 'tool': name,
            'required': required, 'authority': authority, 'detected': actual,
            'executable': path, 'ignoredExecutable': ignored, 'remediation': remedy,
            'refresh': REFRESH, 'repository': str(repository.resolve())}


def preparation_script(value: dict, *, windows: bool | None = None) -> tuple[str, str]:
    """Serialize only a fresh, closed, owner-generated remedy. Never execute it."""
    name, required = value['tool'], value['required']
    validate_request(name, required)
    if windows is not None and windows != host_windows():
        raise ValueError('PKT031 prepare scripts only for the inspected host OS')
    windows = host_windows()
    # Recreate commands from known providers rather than accepting arbitrary
    # command arrays from an evidence JSON or caller-authored diagnostic.
    remedy = instructions(name, required, Path(value['repository']), value.get('executable') or '')
    verification_only = value.get('status') != 'user-terminal-required' or not value['remediation'].get('commands')
    commands = [] if verification_only else remedy['commands']
    notes = list(value['remediation'].get('notes', []))
    lines = ['# Human-run device preparation; never executed by Program Kit.',
             '# Tool: ' + name + '; requirement: ' + required,
             '# Re-run the original dependent readiness check in a fresh terminal afterwards.']
    lines += ['# ' + line for text in [*notes, *remedy['sources']] for line in str(text).splitlines()]
    if windows:
        lines += ["$ErrorActionPreference = 'Stop'"]
    else:
        lines = ['#!/usr/bin/env bash', 'set -euo pipefail', *lines]
    for command in commands:
        if windows:
            lines += ['$global:LASTEXITCODE = 0', command,
                      'if ($LASTEXITCODE -ne 0) { throw "Device preparation command failed; stop and inspect its output." }']
        else:
            lines.append(command)
    if not commands:
        message = 'Verification-only/manual handoff: no device installation or update command was selected.'
        lines += ['Write-Host ' + quote(message, True)] if windows else ["printf '%s\\n' " + quote(message, False)]
    for command in remedy['verification']:
        lines += (['$global:LASTEXITCODE = 0', command,
                   'if ($LASTEXITCODE -ne 0) { throw "Device verification failed; rerun the original check after repair." }']
                  if windows else [command])
    message = 'Preparation is not readiness. Refresh your terminal/application and rerun the original check; no acceptance was recorded.'
    lines += ['Write-Host ' + quote(message, True)] if windows else ["printf '%s\\n' " + quote(message, False)]
    if not commands:
        lines += ['exit 2']  # Manual/ambiguous verification never manufactures ready.
    return '\n'.join(lines) + '\n', '.ps1' if windows else '.sh'


def write_preparation_script(value: dict) -> Path:
    content, suffix = preparation_script(value)
    root = Path(value['repository']).resolve()
    target = root / 'artifacts/program-kit/device-preparation' / (value['tool'] + '-' + hashlib.sha256(content.encode()).hexdigest()[:12] + suffix)
    if not root.is_dir() or not target.resolve().is_relative_to(root):
        raise ValueError('PKT031 preparation artifact must stay in its existing repository')
    # Consumer ignore rules are owned by that repository. Do not silently add
    # them, assume our checkout's rules, or write device paths into tracked files.
    try:
        ignored = subprocess.run(['git', '-c', 'safe.directory=' + str(root), '-c', 'core.excludesFile=',
            'check-ignore', '--quiet', '--', target.relative_to(root).as_posix()], cwd=root,
            capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError('PKT031 cannot verify the preparation directory is ignored; use the inline script until its repository owner establishes ignore rules') from error
    if ignored.returncode != 0:
        raise ValueError('PKT031 preparation directory is not proven ignored; its repository owner must ignore artifacts/program-kit/device-preparation/ before file output')
    for parent in (target.parent, *target.parent.parents):
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('PKT031 aliased preparation artifact path requires owner reconciliation')
        if parent == root:
            break
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file() or target.is_symlink() or target.read_text(encoding='utf-8') != content:
            raise ValueError('PKT031 existing preparation artifact differs; preserve the human-edited file')
    else:
        with target.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
    return target


def render(value: dict) -> str:
    remedy = value['remediation']
    lines = [f"PKT030 pause dependent execution: {value['tool']} required={value['required']} "
             f"pin={value['authority']} detected={value['detected'] or 'missing'} "
             f"executable={value['executable'] or 'missing'}",
             'Ask the user to run these commands in their own terminal; the agent must never run them:',
             *remedy['commands'], *remedy['notes'], 'Verify in a fresh terminal:',
             *remedy['verification'], *remedy['sources'], value['refresh']]
    try:
        path = write_preparation_script(value)
        lines += ['Human preparation script (inspect, then run yourself): ' + str(path)]
    except (ValueError, OSError) as error:
        lines += ['Preparation script could not be written; preserve this diagnostic: ' + str(error)]
        content, suffix = preparation_script(value)
        lines += ['Inline human preparation script (' + suffix + '; no file written):', content]
    return '\n'.join(lines)


def require_tool(repository: Path, name: str, required: str = 'available', *, authority: str = 'Selected action prerequisite') -> dict:
    """Fresh read-only admission for a known selected tool, not every device tool."""
    validate_request(name, required)
    path = executable(name, repository)
    args = ['-version'] if name == 'java' else ['version'] if name == 'specify' else ['--version']
    result = None
    if path:
        try:
            result = subprocess.run([str(path), *args], cwd=repository, capture_output=True,
                text=True, encoding='utf-8', errors='replace', timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
    text = ((result.stdout or '') + '\n' + (result.stderr or '')) if result else ''
    match = re.search(r'(?<![0-9])([0-9]+(?:\.[0-9]+){0,3})', text)
    actual = match.group(1) if match else None
    compatible = bool(result and result.returncode == 0 and actual)
    if compatible and required != 'available':
        actual_parts = tuple(map(int, actual.split('.')))
        wanted = tuple(map(int, required.removeprefix('>=').split('.')))
        compatible = actual_parts[:len(wanted)] >= wanted if required.startswith('>=') else actual_parts == wanted
    if compatible:
        return {'tool': name, 'required': required, 'executable': str(path), 'version': actual}
    value = diagnostic(name, required, authority, actual, str(path) if path else None, repository)
    if path and (result is None or result.returncode != 0 or actual is None):
        value['status'] = 'user-terminal-verification-required'
        value['remediation']['commands'] = []
        value['remediation']['notes'] = ['The executable exists but a successful version probe was not available. '
            'Run the verification script in your own terminal first; access/daemon/probe failures are not evidence that software needs reinstalling.']
    raise ValueError(render(value))


def require_python(repository: Path, required: str | None = None, authority: str = 'Spec Kit / Program Kit Python >=3.11') -> Path:
    if required is None:
        pin = repository / '.python-version'
        required = pin.read_text(encoding='utf-8').strip() if pin.is_file() else '>=3.11'
        if pin.is_file(): authority = str(pin)
    selected = os.environ.get('PROGRAMKIT_DEVICE_PYTHON')
    if selected:
        candidate = Path(selected)
        path = candidate.resolve() if candidate.is_absolute() and candidate.is_file() and shared(candidate, repository) else None
    else:
        path = executable('python', repository)
    output = probe([str(path), '-I', '-c',
                    'import sys,json; print(json.dumps([sys.executable, sys.version.split()[0], sys.prefix == sys.base_prefix]))'], repository) if path else None
    try:
        actual_path, actual, base = json.loads(output or 'null')
        good = base and shared(Path(actual_path), repository)
        if required.startswith('>='):
            good = good and tuple(map(int, actual.split('.')[:2])) >= tuple(map(int, required[2:].split('.')[:2]))
        else:
            good = good and (actual == required if len(required.split('.')) == 3 else actual.startswith(required + '.'))
    except (ValueError, TypeError):
        actual, actual_path, good, base = None, str(path) if path else None, False, True
    if not good:
        value = diagnostic('python', required, authority, actual, actual_path, repository)
        if path and output is None:
            value['status'] = 'user-terminal-verification-required'
            value['remediation']['commands'] = []
            value['remediation']['notes'] = ['The executable was discovered but its read-only probe could not run. '
                'Ask the user to run the verification commands in their own terminal before prescribing an update. '
                'Sandbox/access failures do not establish that the device installation is outdated.']
        elif not base:
            value['status'] = 'user-terminal-verification-required'
            value['remediation']['commands'] = []
            value['remediation']['notes'] = ['A virtual environment is currently selected. Keep its project libraries, '
                'deactivate it or open a fresh user terminal, and independently verify the shared device Python. '
                'Do not prescribe another Python installation merely because a project venv is active.']
        raise ValueError(render(value))
    return Path(actual_path)


def contributor(repository: Path, *, python_only: bool = False,
                pins_directory: Path | None = None, exact_specify: bool = True) -> None:
    template = pins_directory or repository / 'extensions/program-kit-dotnet/templates/dotnet/files'
    require_python(repository)
    specify = executable('specify', repository)
    output = probe([str(specify), 'version'], repository) if specify else None
    match = re.search(r'CLI Version\s+(\d+\.\d+\.\d+)', output or '')
    actual = match.group(1) if match else None
    expected, authority = specify_requirement(repository) if exact_specify else ('1.1.1', 'Program Kit requires >=1.1.1,<2')
    if not specify_satisfied(actual, expected, exact_specify and is_contributor(repository)):
        value = diagnostic('specify', expected, authority, actual, str(specify) if specify else None, repository)
        if specify and actual is None:
            value['status'] = 'user-terminal-verification-required'
            value['remediation']['commands'] = []
            value['remediation']['notes'] = ['The selected Spec Kit executable did not provide a successful recognizable version probe. '
                'Verify access and the launcher in your own terminal; this is not evidence that reinstallation is required.']
        raise ValueError(render(value))
    if python_only: return
    import importlib.util
    spec = importlib.util.spec_from_file_location('device_js', template / 'scripts/js_toolchain.py')
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    required = {'node': (template / '.nvmrc').read_text().strip(),
                'npm': (template / '.npm-version').read_text().strip(),
                'dotnet': json.loads((template / 'global.json').read_text())['sdk']['version']}
    node, nv = runtime.resolve_node(repository, required['node'], 'node', 'auto')
    npm, pv = runtime.resolve_npm(repository, node, required['npm'], '') if node else (None, None)
    npm_path = executable('npm.cmd' if os.name == 'nt' else 'npm', repository)
    if pv is None and npm_path:
        pv = runtime.version([str(npm_path)], repository)
    dotnet = executable('dotnet', repository)
    # The template global.json selects an installed side-by-side SDK without changing the environment.
    dv = runtime.version([str(dotnet)], template) if dotnet else None
    commands = {'node': str(node) if node else shutil.which('node'),
                'npm': (npm or [shutil.which('npm.cmd' if os.name == 'nt' else 'npm')])[0],
                'dotnet': str(dotnet) if dotnet else None}
    pins = {'node': '.nvmrc', 'npm': '.npm-version', 'dotnet': 'global.json sdk.version'}
    failures = [render(diagnostic(key, required[key], str(template / pins[key]), actual, commands[key], repository))
                for key, actual in {'node': nv, 'npm': pv, 'dotnet': dv}.items() if actual != required[key]]
    if failures: raise ValueError('\n\n'.join(failures))


def specify_requirement(repository: Path) -> tuple[str, str]:
    ci = repository / '.github/workflows/qualify-candidate.yml'
    if is_contributor(repository):
        pins = set(re.findall(r'specify-cli==([0-9.]+)', ci.read_text(encoding='utf-8')))
        if len(pins) != 1:
            raise ValueError('PKT001 contributor CI must supply one exact Spec Kit pin')
        return pins.pop(), str(ci) + ' specify-cli pin'
    return '1.1.1', 'bundle.yml compatibility baseline >=1.1.1,<2 (repair version 1.1.1)'


def is_contributor(repository: Path) -> bool:
    return ((repository / '.github/workflows/ci.yml').is_file() and
            (repository / 'extensions/program-kit-dotnet/templates/dotnet/files').is_dir())


def specify_satisfied(actual: str | None, expected: str, exact: bool) -> bool:
    if actual is None: return False
    if exact: return actual == expected
    try:
        return (1, 1, 1) <= tuple(map(int, actual.split('.'))) < (2, 0, 0)
    except ValueError:
        return False


def specify_runtime(repository: Path) -> None:
    """Verify the shared Spec Kit interpreter used for library-based validators."""
    from importlib.metadata import version, PackageNotFoundError
    try:
        actual = version('specify-cli')
    except PackageNotFoundError:
        actual = None
    expected, authority = specify_requirement(repository)
    if not specify_satisfied(actual, expected, is_contributor(repository)):
        raise ValueError(render(diagnostic('specify', expected, authority, actual,
                                          sys.executable, repository)))
    if not shared(Path(sys.executable), repository):
        raise ValueError('PKT030 repository-local Spec Kit interpreter cannot establish device readiness')
    print('Spec Kit CLI library: ' + actual)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contributor', type=Path, required=True)
    parser.add_argument('--python-only', action='store_true')
    parser.add_argument('--specify-runtime', action='store_true')
    args = parser.parse_args()
    try:
        if args.specify_runtime:
            specify_runtime(args.contributor.resolve())
        else:
            contributor(args.contributor.resolve(), python_only=args.python_only)
        return 0
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

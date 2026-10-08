"""Read-only device readiness and user-terminal remediation. Never runs installers.

This single provider is shipped with engineering and loaded by governance and contributors.
Project dependency caches/restores are deliberately outside this contract.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SOURCES = {
    'node': 'https://github.com/Schniz/fnm/blob/master/README.md',
    'npm': 'https://docs.npmjs.com/cli/v11/commands/npm-install/',
    'dotnet': 'https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script',
    'python': 'https://docs.astral.sh/uv/guides/install-python/',
    'specify': 'https://github.com/github/spec-kit',
}
REFRESH = ('After the user reports completion, open a fresh terminal and restart the calling '
           'application if its inherited PATH is stale. Re-run readiness and inspect actual paths '
           'and versions before dependent execution. Do not install another local copy or prepend '
           'a temporary PATH to mask an outdated selection.')


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
    windows = os.name == 'nt'
    commands, notes, sources = [], [], [SOURCES[name]]
    verify = [f'{name} --version']
    location = f'Get-Command {name} -All | Select-Object Name,Source' if windows else f'command -v {name}'
    if name in {'node', 'npm'}:
        manager = next((item for item in ('fnm', 'volta', 'nvm') if executable(item, repository)), None)
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
        # Install alongside other SDKs into the already selected shared root, never a per-repo root.
        root = Path(detected_path).parent if detected_path else Path.home() / '.dotnet'
        if windows:
            commands = ['Invoke-WebRequest https://dot.net/v1/dotnet-install.ps1 -OutFile "$env:TEMP/dotnet-install.ps1"',
                        f'& "$env:TEMP/dotnet-install.ps1" -Version {required} -InstallDir \'{root}\' -NoPath']
        else:
            commands = ['curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh',
                        f'bash /tmp/dotnet-install.sh --version {required} --install-dir \'{root}\' --no-path']
        notes.append('Review the Microsoft script before running it. Add the SDK alongside existing SDKs/runtimes '
                     'in this shared root; do not uninstall them. A protected existing root requires administrator '
                     'privileges (sudo on POSIX). Microsoft recommends native installers for development; use the '
                     'exact-version installer from the official download page if that is your existing install method.')
        if not detected_path:
            if windows:
                commands += [f'[Environment]::SetEnvironmentVariable(\'DOTNET_ROOT\', \'{root}\', \'User\')',
                             f'[Environment]::SetEnvironmentVariable(\'Path\', \'{root};\' + [Environment]::GetEnvironmentVariable(\'Path\', \'User\'), \'User\')']
            else:
                notes.append(f'Persist export DOTNET_ROOT=\'{root}\' and export PATH="$DOTNET_ROOT:$PATH" '
                             'in the startup file for your existing shell; reopen it.')
        verify = ['dotnet --list-sdks', 'dotnet --list-runtimes', 'dotnet --version']
        notes.append('Verify --version from the repository with its authoritative global.json; other repositories '
                     'can select their own installed SDKs. Never change rollForward or pins to accommodate PATH.')
    elif name == 'python':
        version = required.removeprefix('>=')
        if executable('pyenv', repository):
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
        if executable('uv', repository):
            commands = [f'uv tool install specify-cli=={required} --force --no-python-downloads', 'uv tool update-shell']
            sources.append('https://docs.astral.sh/uv/concepts/tools/')
        elif executable('pipx', repository):
            commands = [f'pipx install specify-cli=={required} --force', 'pipx ensurepath']
            sources.append('https://pipx.pypa.io/stable/docs/')
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
    if name == 'dotnet' and actual is None and path and shared(Path(path), repository):
        installed = probe([path, '--list-sdks'], repository)
        if installed:
            actual = 'installed SDKs: ' + installed.replace('\n', '; ')
    remedy = instructions(name, required, repository, path or '')
    located = shutil.which('npm.cmd' if name == 'npm' and os.name == 'nt' else name)
    ignored = str(Path(located).resolve()) if located and not shared(Path(located), repository) else None
    if located and name == 'specify':
        binding = interpreter_binding(Path(located))
        if binding and not shared(binding, repository): ignored = str(Path(located).resolve()) + ' -> ' + str(binding)
    if ignored:
        remedy['notes'].append('Ignored repository-local executable (not device readiness): ' + ignored)
    return {'code': 'PKT030', 'status': 'user-terminal-required', 'tool': name,
            'required': required, 'authority': authority, 'detected': actual,
            'executable': path, 'ignoredExecutable': ignored, 'remediation': remedy,
            'refresh': REFRESH}


def render(value: dict) -> str:
    remedy = value['remediation']
    return '\n'.join([f"PKT030 pause dependent execution: {value['tool']} required={value['required']} "
                      f"pin={value['authority']} detected={value['detected'] or 'missing'} "
                      f"executable={value['executable'] or 'missing'}",
                      'Ask the user to run these commands in their own terminal; the agent must never run them:',
                      *remedy['commands'], *remedy['notes'], 'Verify in a fresh terminal:',
                      *remedy['verification'], *remedy['sources'], value['refresh']])


def require_python(repository: Path, required: str | None = None, authority: str = 'Spec Kit / Program Kit Python >=3.11') -> Path:
    if required is None:
        pin = repository / '.python-version'
        required = pin.read_text(encoding='utf-8').strip() if pin.is_file() else '>=3.11'
        if pin.is_file(): authority = str(pin)
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
        raise ValueError(render(diagnostic('specify', expected, authority, actual,
                                          str(specify) if specify else None, repository)))
    if python_only: return
    import importlib.util
    spec = importlib.util.spec_from_file_location('device_js', template / 'eng/js_toolchain.py')
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
    ci = repository / '.github/workflows/ci.yml'
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

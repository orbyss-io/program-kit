"""Setup and evidence for the human-owned intake TUI; never starts a coding agent."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from local_catalog_server import CatalogHandler

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('.agents/skills/speckit-program-kit-governance-product-intake/SKILL.md')
GRILLING = Path('.specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.grilling.md')
INSTRUCTIONS = """# Interactive intake evaluation

Read .agents/skills/speckit-program-kit-governance-product-intake/SKILL.md in full and
use that installed skill. Follow its routed references and Program Kit's own
grilling method, not an unrelated personal grilling skill. Use the human's opening
message as the starting product idea. If product-idea.md is supplied, read it as
additional user input. Ask the human questions in this conversation.
This is intake only: do not accept the founding baseline, install/update components, start
another agent, or implement the product. Stop after the intake review and handoff.
Keep the skill's compact question/decision record current, including partial
answers, corrections and pending questions. Do not claim user confirmation early.
If acceptance/ is present, read its fixed observable trial contracts during intake.
These describe what the later implementation must demonstrate; do not implement them now.
"""

CONSUMER_INSTRUCTIONS = """# Consumer trial

For the interactive intake task, read INTAKE-SESSION.md and follow its installed
intake skill. Those interview-only instructions apply only to that task.
For a separately authorized founding continuation or feature task, follow the installed
skill named by that task and its supplied context. Do not repeat the intake or
reread its skill unless the task explicitly returns to intake. This file grants
no approval, workflow execution, installation or paid-agent authorization.
"""


def save(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        value = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
        return value.hexdigest()


def run(command: list[str], workspace: Path, log: Path) -> int:
    result = subprocess.run(command, cwd=workspace, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=300)
    with log.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(command) + '\n' + result.stdout + result.stderr + '\n')
    return result.returncode


def release_assets(record: Path, supplied: Path | None = None) -> Path:
    """Use complete release-builder bytes; never package a second intake payload."""
    built = supplied is None
    if supplied is None:
        supplied = ROOT / 'artifacts/intake-packages' / uuid.uuid4().hex
        command = [sys.executable, str(ROOT / 'scripts/build_release.py'),
                   '--output', supplied.relative_to(ROOT).as_posix()]
        if run(command, ROOT, record / 'setup.log'):
            raise RuntimeError('Intake package build failed; see setup.log. No consumer was installed.')
    supplied = supplied.resolve(strict=True)
    from build_release import validate_distribution_archive
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    checksums = {}
    for line in (supplied / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected, name = line.split(maxsplit=1)
        name = name.lstrip('*')
        if len(expected) != 64 or Path(name).name != name or name in checksums:
            raise ValueError('Invalid or duplicate release checksum entry')
        checksums[name] = expected
    names = [f'{name}-{version}.zip' for name in (
        'program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet',
        'program-kit-governance-preset', 'program-kit', 'program-kit-tooling')]
    for name in names:
        path = supplied / name
        if checksums.get(name) != digest(path):
            raise ValueError('Release asset is missing or differs from SHA256SUMS: ' + name)
        validate_distribution_archive(path, tooling=name.startswith('program-kit-tooling-'))
    verify_source_assets(supplied, version)
    save(record / 'installation-inputs.json', {
        'schemaVersion': 1, 'version': version, 'origin': 'local-release-build' if built else 'supplied-assets',
        'assetsDirectory': str(supplied), 'sha256': {name: checksums[name] for name in names},
        'scope': 'Local package installation; no public release or consumer acceptance claim'})
    return supplied


def verify_source_assets(assets: Path, version: str) -> None:
    """Bind supplied package bytes to this source, including dirty candidate inputs."""
    from build_release import bundle_source_files
    from build_release_guidance import build as build_guidance
    with zipfile.ZipFile(assets / f'program-kit-tooling-{version}.zip') as archive:
        witness = json.loads(archive.read('program-kit-source-witness.json'))
        files = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                 if not name.endswith('/') and name != 'program-kit-source-witness.json'}
        encoded_files = (json.dumps(files, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        if witness.get('schemaVersion') != 1 or witness.get('files') != files or witness.get('fileSetSha256') != hashlib.sha256(encoded_files).hexdigest():
            raise ValueError('Release tooling source witness differs from actual archive bytes')
        expected = {relative.as_posix(): digest(ROOT / relative) for relative in bundle_source_files(ROOT)}
        for name, sha in expected.items():
            if files.get(name) != sha:
                raise ValueError('Release tooling differs from the current intake source: ' + name)
        with tempfile.TemporaryDirectory(prefix='intake-guidance-') as temporary:
            guidance = Path(temporary) / 'full'
            build_guidance(ROOT, guidance, version)
            generated = {'references/release-guidance/' + path.relative_to(guidance).as_posix(): path.read_bytes()
                         for path in guidance.rglob('*') if path.is_file()}
            tooling_guidance = Path(temporary) / 'tooling'
            build_guidance(ROOT, tooling_guidance, version, aggregates=False)
            expected.update({'extensions/program-kit-governance/references/release-guidance/' + path.relative_to(tooling_guidance).as_posix(): digest(path)
                             for path in tooling_guidance.rglob('*') if path.is_file()})
            if files != expected:
                raise ValueError('Release tooling has missing, changed or unexpected same-source members')
            for kind, identities in (('extensions', ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet')),
                                     ('presets', ('program-kit-governance-preset',))):
                for identity in identities:
                    prefix = kind + '/' + identity + '/'
                    wanted = {name[len(prefix):]: archive.read(name) for name in files if name.startswith(prefix)}
                    if identity == 'program-kit-governance': wanted.update(generated)
                    with zipfile.ZipFile(assets / f'{identity}-{version}.zip') as component:
                        actual = {name: component.read(name) for name in component.namelist() if not name.endswith('/')}
                        if actual != wanted:
                            raise ValueError('Component archive differs from same-source tooling: ' + identity)
        with zipfile.ZipFile(assets / f'program-kit-{version}.zip') as bundle:
            if bundle.read('bundle.yml') != archive.read('bundle.yml'):
                raise ValueError('Native composition differs from same-source tooling')


@contextmanager
def candidate_catalogs(record: Path, assets: Path | None = None):
    """Serve exact release archives through the normal native catalog installers."""
    assets = release_assets(record, assets)
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    directory = record / 'candidate-catalogs'
    directory.mkdir()
    class Handler(CatalogHandler):
        def log_message(self, *_args):
            pass
    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0), functools.partial(Handler, directory=str(directory)))
    thread = None
    process = None
    server_log = None
    try:
        base = f'http://127.0.0.1:{server.server_port}'
        for kind, names in (
            ('extensions', ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet')),
            ('presets', ('program-kit-governance-preset',)),
        ):
            catalog = json.loads((ROOT / f'catalogs/{kind}.json').read_text(encoding='utf-8'))
            catalog['catalog_url'] = f'{base}/{kind}.json'
            for name in names:
                shutil.copyfile(assets / f'{name}-{version}.zip', directory / f'{name}.zip')
                catalog[kind][name]['download_url'] = f'{base}/{name}.zip'
                catalog[kind][name]['sha256'] = digest(directory / f'{name}.zip')
            save(directory / f'{kind}.json', catalog)
        shutil.copyfile(assets / f'program-kit-{version}.zip', directory / 'program-kit.zip')
        bundle = json.loads((ROOT / 'catalogs/bundles.json').read_text(encoding='utf-8'))
        bundle['catalog_url'] = f'{base}/bundles.json'
        bundle['bundles']['program-kit']['download_url'] = f'{base}/program-kit.zip'
        bundle['bundles']['program-kit']['sha256'] = digest(directory / 'program-kit.zip')
        save(directory / 'bundles.json', bundle)
        expected = json.loads((record / 'installation-inputs.json').read_text(encoding='utf-8'))['sha256']
        for name in ('program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet',
                     'program-kit-governance-preset', 'program-kit'):
            if digest(directory / f'{name}.zip') != expected[f'{name}-{version}.zip']:
                raise ValueError('Release asset changed during transport preparation: ' + name)
        if os.name == 'nt':
            # Windows archive transfers need the same isolated server process used by live setup.
            port = server.server_port
            server.server_close()
            server_log = (record / 'catalog-server.log').open('w', encoding='utf-8')
            process = subprocess.Popen(
                [sys.executable, str(ROOT / 'scripts/local_catalog_server.py'), str(port), '--directory', str(directory)],
                stdin=subprocess.DEVNULL, stdout=server_log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            deadline = time.monotonic() + 10
            while True:
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError('Candidate catalog server did not start; see catalog-server.log.')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
        else:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
        yield base
    finally:
        if thread is not None:
            server.shutdown()
            thread.join(timeout=10)
        server.server_close()
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if server_log is not None:
            server_log.close()


def install_components(specify: str, git: str, workspace: Path, record: Path, assets: Path | None = None) -> None:
    launcher = [specify]
    if os.name == 'nt':
        # Reuse the existing uv/OpenSSL compatibility bridge, only for these owned
        # loopback installation children. Do not change the user's or Codex's environment.
        from invoke_specify import uv_windows_specify_environment
        environment = uv_windows_specify_environment([specify])
        if environment is not None:
            launcher = [sys.executable, str(ROOT / 'scripts/invoke_specify.py'),
                        '--site-packages', str(environment[1]), '--loopback-http-only', '--']
    with candidate_catalogs(record, assets) as base:
        steps = [
            [git, 'init', '.'],
            [specify, 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'],
            [specify, 'extension', 'catalog', 'add', f'{base}/extensions.json', '--name', 'intake-candidate', '--priority', '1', '--install-allowed'],
            [specify, 'preset', 'catalog', 'add', f'{base}/presets.json', '--name', 'intake-candidate', '--priority', '1', '--install-allowed'],
            [specify, 'bundle', 'catalog', 'add', f'{base}/bundles.json', '--id', 'intake-candidate', '--policy', 'install-allowed'],
            [specify, 'bundle', 'install', 'program-kit', '--integration', 'codex'],
            [specify, 'bundle', 'catalog', 'remove', 'intake-candidate'],
            [specify, 'extension', 'catalog', 'remove', 'intake-candidate'],
            [specify, 'preset', 'catalog', 'remove', 'intake-candidate'],
        ]
        for index, command in enumerate(steps, 1):
            print(f'Installing consumer components ({index}/{len(steps)})...', flush=True)
            bundle_install = command[1:3] == ['bundle', 'install']
            if command[0] == specify:
                command = launcher + command[1:]
            log = record / 'setup.log'
            # Only retry an owned local transfer when the native bundle transaction
            # explicitly reports rollback. Never retry agents, approvals or arbitrary
            # setup failures; retain each diagnostic and keep the attempt count bounded.
            for attempt in range(3):
                offset = log.stat().st_size if log.exists() else 0
                code = run(command, workspace, log)
                if code == 0:
                    break
                if not bundle_install or not log.is_file():
                    raise RuntimeError(f'Installation failed at step {index}; see {log}')
                with log.open('rb') as stream:
                    stream.seek(offset)
                    diagnostic = stream.read().decode('utf-8', errors='replace')
                transient = ('[WinError 10054]' in diagnostic or 'timed out' in diagnostic)
                rolled_back_download = ('Failed to install bundle' in diagnostic
                                        and 'No changes were recorded' in diagnostic and transient)
                if not rolled_back_download or attempt == 2:
                    raise RuntimeError(f'Installation failed at step {index}; see {log}')
                message = f'Local bundle transfer interrupted; native rollback confirmed. Retrying setup transfer ({attempt + 2}/3); no coding agent has started.'
                with log.open('a', encoding='utf-8') as stream:
                    stream.write(message + '\n')
                print(message, flush=True)


def workspace_parent() -> Path:
    # Reserve room for native compiler cwd and nested compatibility fixtures.
    # A long-path-aware Python runtime cannot remove native process cwd limits.
    default = Path.home() / 'ProgramKitTrials/workspaces' if os.name == 'nt' else Path(tempfile.gettempdir())
    return Path(os.environ.get('PROGRAM_KIT_TRIAL_ROOT', str(default))).expanduser().resolve()


def require_short_workspace_parent(parent: Path) -> None:
    if os.name == 'nt' and len(str(parent).encode('utf-16-le')) // 2 > 90:
        raise RuntimeError('INTAKE_PATH_TOO_DEEP: set PROGRAM_KIT_TRIAL_ROOT to a shorter user-owned directory '
                           'before installation, and retain it for finish/cleanup; no worker started.')


def initialize_owner_access(workspace: Path) -> str:
    """A human-created disposable root explicitly retains its creator after worker replacements."""
    if os.name != 'nt':
        return 'not-required'
    if os.environ.get('CODEX_THREAD_ID') or os.environ.get('CI'):
        return 'human-terminal-required; no persistent access grant from agent preparation'
    if workspace.is_symlink() or list(workspace.iterdir()) != [workspace / '.intake-session-owner']:
        raise RuntimeError('INTAKE_ACCESS_SCOPE: permission initialization requires the new empty owned workspace.')
    script = '''$ErrorActionPreference='Stop'
$path=$env:PROGRAM_KIT_NEW_TRIAL_ROOT
$acl=Get-Acl -LiteralPath $path
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
$rule=[System.Security.AccessControl.FileSystemAccessRule]::new($sid,'Modify','ContainerInherit,ObjectInherit','None','Allow')
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $path -AclObject $acl
'''
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
        env={**os.environ, 'PROGRAM_KIT_NEW_TRIAL_ROOT': str(workspace)}, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('INTAKE_ACCESS_SCOPE: could not retain the human creator on the new disposable root; '
                           'inspect its permissions before continuing. No worker started.')
    return 'creator-only inherited Modify on new disposable root'


def prepare(record: Path, idea_file: Path | None = None, acceptance_contracts: Path | None = None,
            assets: Path | None = None) -> None:
    if idea_file is not None and (not idea_file.is_file() or not idea_file.read_text(encoding='utf-8').strip()):
        raise ValueError('The supplied idea file must contain the initial product request.')
    if acceptance_contracts is not None:
        if not acceptance_contracts.is_dir() or not checked_files(acceptance_contracts):
            raise ValueError('Acceptance contracts must be a nonempty document directory.')
        if any(p.suffix not in {'.md', '.json'} for p in checked_files(acceptance_contracts)):
            raise ValueError('Acceptance context is restricted to Markdown and JSON contracts, without implementation files.')
    specify = shutil.which('specify')
    git = shutil.which('git')
    if not specify or not git:
        raise RuntimeError('INTAKE_TOOL_MISSING: specify and git must be on PATH; no global configuration is changed.')
    record.mkdir(parents=True, exist_ok=False)
    parent = workspace_parent()
    require_short_workspace_parent(parent)
    parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='program-kit-intake-', dir=parent)).resolve()
    nonce = uuid.uuid4().hex
    (workspace / '.intake-session-owner').write_text(nonce, encoding='utf-8')
    state = {'schemaVersion': 1, 'id': record.name, 'workspace': str(workspace),
             'tempParent': str(workspace.parent), 'workspaceParentKind': 'short-trial-root', 'owner': nonce, 'source': str(ROOT),
             'startedAt': datetime.now(timezone.utc).isoformat(), 'status': 'preparing',
             'codexHome': str(Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).resolve())}
    save(record / 'session.json', state)
    state['ownerAccess'] = initialize_owner_access(workspace)
    save(record / 'session.json', state)
    print(f'Isolated consumer: {workspace}\nReview evidence: {record}', flush=True)
    source_git = [git, '-c', f'safe.directory={ROOT.as_posix()}', '-c', 'core.excludesFile=' if os.name == 'nt' else 'core.excludesFile=/dev/null']
    for key, args in [('sourceCommit', ['rev-parse', 'HEAD']), ('sourceChanges', ['status', '--porcelain'])]:
        result = subprocess.run(source_git + args, cwd=ROOT, capture_output=True, text=True, timeout=30)
        state[key] = result.stdout.strip() if result.returncode == 0 else 'unavailable'
    # The actual command sources are saved too: a commit alone cannot identify dirty candidates.
    shutil.copy2(ROOT / 'VERSION', record / 'VERSION')
    source_commands = ROOT / 'extensions/program-kit-governance/commands'
    for name in ('speckit.program-kit-governance.product-intake.md', 'speckit.program-kit-governance.grilling.md'):
        shutil.copy2(source_commands / name, record / name)
    save(record / 'session.json', state)
    if assets is None:
        install_components(specify, git, workspace, record)
    else:
        install_components(specify, git, workspace, record, assets)
    # Native init may create its initial Git commit. Supplied consumer material
    # must not exist in that repository until installation has finished.
    if idea_file is not None:
        shutil.copyfile(idea_file, workspace / 'product-idea.md')
        state['initialIdea'] = {'source': str(idea_file.resolve()), 'sha256': digest(workspace / 'product-idea.md')}
    if acceptance_contracts is not None:
        shutil.copytree(acceptance_contracts, workspace / 'acceptance')
        state['acceptanceContracts'] = {p.relative_to(acceptance_contracts).as_posix(): digest(p) for p in checked_files(acceptance_contracts)}
    save(record / 'session.json', state)
    runtime = workspace / '.specify/extensions/program-kit-governance/scripts/schema_runtime.py'
    for action in ('setup', 'record-copy'):
        if run([sys.executable, str(runtime), action], workspace, record / 'setup.log'):
            raise RuntimeError(f'Intake schema tool {action} failed; see setup.log.')
    for tool, arguments in ((specify, ['version']), (shutil.which('codex'), ['--version'])):
        if tool:
            run([tool, *arguments], workspace, record / 'setup.log')
    installed_skill = workspace / SKILL
    if not installed_skill.is_file() or 'speckit.program-kit-governance.grilling' not in installed_skill.read_text(encoding='utf-8'):
        raise RuntimeError('Installed intake skill does not route to Program Kit grilling.')
    if digest(workspace / GRILLING) != digest(source_commands / GRILLING.name):
        raise RuntimeError('Installed Program Kit grilling differs from the candidate.')
    validator = workspace / '.specify/extensions/program-kit-governance/scripts/governance_state.py'
    if run([sys.executable, str(validator), 'validate-installation'], workspace, record / 'setup.log'):
        raise RuntimeError('Installed component coherence check failed; see setup.log.')
    (workspace / 'INTAKE-SESSION.md').write_text(INSTRUCTIONS, encoding='utf-8')
    # This is a consumer root, outside the contributor repository and its ancestor instructions.
    (workspace / 'AGENTS.md').write_text(
        CONSUMER_INSTRUCTIONS + '\nFor every Git command use git -c safe.directory=' + workspace.as_posix()
        + (' -c core.excludesFile= ' if os.name == 'nt' else ' -c core.excludesFile=/dev/null ')
        + '<command>. Do not persist global Git exceptions.\n', encoding='utf-8')
    state['status'] = 'ready'
    save(record / 'session.json', state)


def checked_files(workspace: Path) -> list[Path]:
    """Reject links/junctions before archive or deletion; never follow them out of the consumer."""
    files = []
    for directory, dirs, names in os.walk(workspace, followlinks=False):
        for name in dirs + names:
            path = Path(directory) / name
            info = path.lstat()
            if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise RuntimeError(f'Refusing linked/reparse path; workspace retained: {path}')
            if path.resolve().is_relative_to(workspace) is False:
                raise RuntimeError(f'Path escaped consumer: {path}')
            if path.is_file():
                files.append(path)
    return files


def owned_workspace(state: dict) -> Path:
    workspace = Path(state['workspace'])
    if (workspace.is_symlink() or workspace.resolve() != workspace or
            workspace.parent != Path(state['tempParent']) or
            workspace.parent != (workspace_parent() if state.get('workspaceParentKind') == 'short-trial-root'
                                 else Path(tempfile.gettempdir()).resolve()) or
            not workspace.name.startswith('program-kit-intake-')):
        raise RuntimeError('Refusing unexpected cleanup target.')
    if (workspace / '.intake-session-owner').read_text(encoding='utf-8') != state['owner']:
        raise RuntimeError('Consumer ownership marker differs; refusing cleanup.')
    return workspace


def export_conversation(state: dict, record: Path) -> list[str]:
    """Only copy sessions whose metadata binds the exact unique consumer cwd.

    Rollout storage is version-dependent. Missing/unsupported history is explicit,
    never a fabricated transcript or a reason to remove the remaining workspace.
    """
    session_ids = []
    messages = []
    session_root = Path(state['codexHome']) / 'sessions'
    started = datetime.fromisoformat(state['startedAt']).timestamp()
    for path in session_root.rglob('*.jsonl'):
        if path.stat().st_mtime < started:
            continue
        with path.open(encoding='utf-8') as stream:
            try:
                metadata = json.loads(stream.readline())
            except (ValueError, UnicodeError):
                continue
            payload = metadata.get('payload', {})
            if metadata.get('type') != 'session_meta' or not payload.get('cwd'):
                continue
            if Path(payload['cwd']).resolve() != Path(state['workspace']):
                continue
        # Copy only this session, never auth.json, config, or unrelated conversation bodies.
        target = record / path.name
        shutil.copy2(path, target)
        session_ids.append(str(payload.get('id', path.stem)))
        with target.open(encoding='utf-8') as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                body = event.get('payload', {})
                if event.get('type') == 'response_item' and body.get('type') == 'message' and body.get('role') in ('user', 'assistant'):
                    text = '\n'.join(item.get('text', '') for item in body.get('content', []) if isinstance(item, dict))
                    if text:
                        messages.append(f'## {body["role"]}\n\n{text}\n')
    if messages:
        (record / 'conversation.md').write_text('\n'.join(messages), encoding='utf-8')
    return session_ids


def finish(record: Path, exit_code: int, keep: bool = False, prepare_only: bool = False) -> dict:
    state = json.loads((record / 'session.json').read_text(encoding='utf-8'))
    workspace = owned_workspace(state)
    files = checked_files(workspace)
    state.update(exitCode=exit_code, finishedAt=datetime.now(timezone.utc).isoformat(), cleanup='retained')
    # Preserve a full restorable consumer, including its exact installed skills and local Git state.
    # The archive is local, ignored evidence; it may contain private product information.
    archive = record / 'consumer.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in files:
            output.write(path, path.relative_to(workspace).as_posix())
    with zipfile.ZipFile(archive) as saved:
        if saved.testzip() is not None:
            raise RuntimeError('Consumer archive verification failed; keeping workspace.')
        for path in files:
            if hashlib.sha256(saved.read(path.relative_to(workspace).as_posix())).hexdigest() != digest(path):
                raise RuntimeError('Consumer changed during preservation; keeping workspace.')
    for relative in ('docs/architecture', '.specify/memory/constitution.md', 'product-idea.md'):
        path = workspace / relative
        if path.is_dir():
            shutil.copytree(path, record / relative, dirs_exist_ok=True)
        elif path.is_file():
            (record / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, record / relative)
    state['sessionIds'] = []
    state['transcriptStatus'] = 'not-requested' if prepare_only else 'unavailable'
    if not prepare_only:
        try:
            state['sessionIds'] = export_conversation(state, record)
            if (record / 'conversation.md').is_file():
                state['transcriptStatus'] = 'captured'
        except (OSError, ValueError) as error:
            state['transcriptError'] = str(error)
    intent = workspace / 'docs/architecture/project-intent.md'
    state['intakeStatus'] = 'absent'
    for retired in ('observedWorkflows', 'intakeValidation', 'validationError'):
        state.pop(retired, None)
    if intent.is_file():
        try:
            state['intakeStatus'] = 'recorded' if intent.read_text(encoding='utf-8').strip() else 'empty'
        except (OSError, UnicodeError) as error:
            state['intakeStatus'] = 'unreadable'
            state['intakeReadError'] = str(error)
    inspector = workspace / '.specify/extensions/program-kit-governance/scripts/product_intake.py'
    state['contextInspection'] = 'unavailable'
    if inspector.is_file():
        try:
            code = run([sys.executable, '-B', str(inspector), 'inspect'], workspace, record / 'validation.log')
            state['contextInspection'] = 'passed' if code == 0 else 'failed'
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            state['contextInspection'] = 'error'
            state['inspectionError'] = str(error)
    state['archiveSha256'] = digest(archive)
    state['historicalWorkflowState'] = 'preserved-in-archive; not-interpreted' if (workspace / '.specify/workflows').exists() else 'absent'
    state['status'] = 'setup-only' if prepare_only else 'needs-human-review'
    save(record / 'session.json', state)
    # All copies and diagnostics must complete before the narrowly scoped deletion.
    if not keep and (prepare_only or (exit_code == 0 and state['transcriptStatus'] == 'captured')):
        owned_workspace(state)
        checked_files(workspace)
        shutil.rmtree(workspace)
        state['cleanup'] = 'removed-after-verified-archive'
        save(record / 'session.json', state)
    report = f"""# Intake session review

- Candidate: {state.get('sourceCommit', 'unavailable')}
- Product intent: {state['intakeStatus']} (document presence supplies no human confirmation or interview-quality acceptance)
- Optional context inspection: {state['contextInspection']}
- Conversation: {state['transcriptStatus']}
- Codex session IDs: {', '.join(state['sessionIds']) or 'unavailable'}
- CLI exit: {exit_code}
- Workspace: {workspace}
- Cleanup: {state['cleanup']}
- Historical workflow files: {state['historicalWorkflowState']} (no current completion or acceptance is inferred)

Return to the Program Kit development conversation and ask to review this folder:
{record}

Review conversation.md and the matched rollout JSONL (when captured), docs/architecture,
the preserved constitution, validation.log (when an installed inspector exists), setup.log, session.json, and consumer.zip.
The zip preserves the installed candidate and full consumer for recovery; it is not
a bootstrap checkpoint or a Release/live-acceptance receipt. The intake launcher itself starts no workflow.
Missing conversation history is a review limitation, not an interview pass.
If the workspace was removed, extract consumer.zip into a new empty directory to recover it.
Evidence may contain private product details and conversation/tool output: do not publish it.
"""
    (record / 'REVIEW.md').write_text(report, encoding='utf-8')
    print(f"Intake: {state['intakeStatus']}; conversation: {state['transcriptStatus']}\nCleanup: {state['cleanup']}\nReturn here with: {record / 'REVIEW.md'}", flush=True)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'finish'))
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--exit-code', type=int, default=1)
    parser.add_argument('--keep-workspace', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--idea-file', type=Path)
    parser.add_argument('--acceptance-contracts', type=Path)
    parser.add_argument('--assets-dir', type=Path, help='Exact same-version release-builder assets with SHA256SUMS; defaults to a fresh local release build')
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(args.record.resolve(), args.idea_file.resolve() if args.idea_file else None,
                    args.acceptance_contracts.resolve() if args.acceptance_contracts else None,
                    args.assets_dir.resolve() if args.assets_dir else None)
        else:
            finish(args.record.resolve(), args.exit_code, args.keep_workspace, args.prepare_only)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'INTAKE_SESSION_ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

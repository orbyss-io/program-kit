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

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('.agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md')
GRILLING = Path('.specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.grilling.md')
INSTRUCTIONS = """# Interactive intake evaluation

Read .agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md in full and
use that installed skill. Follow its routed references and Program Kit's own
grilling method, not an unrelated personal grilling skill. Read product-idea.md
as the user's starting idea. Ask the human questions in this conversation.
This is intake only: do not run bootstrap, install/update components, start
another agent, or implement the product. Stop after the intake review and handoff.
Keep the skill's compact question/decision record current, including partial
answers, corrections and pending questions. Do not claim user confirmation early.
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


@contextmanager
def candidate_catalogs(record: Path):
    """Serve only candidate archives, on loopback, for the real bundle installer."""
    directory = record / 'candidate-catalogs'
    directory.mkdir()
    class Handler(http.server.SimpleHTTPRequestHandler):
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
                source = ROOT / kind / name
                with zipfile.ZipFile(directory / f'{name}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                    for path in checked_files(source):
                        if '__pycache__' not in path.parts and path.suffix != '.pyc':
                            archive.write(path, path.relative_to(source).as_posix())
                catalog[kind][name]['download_url'] = f'{base}/{name}.zip'
            save(directory / f'{kind}.json', catalog)
        if os.name == 'nt':
            # Windows archive transfers need the same isolated server process used by live setup.
            port = server.server_port
            server.server_close()
            server_log = (record / 'catalog-server.log').open('w', encoding='utf-8')
            process = subprocess.Popen(
                [sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(directory)],
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


def install_components(specify: str, git: str, workspace: Path, record: Path) -> None:
    launcher = [specify]
    if os.name == 'nt':
        # Reuse the existing uv/OpenSSL compatibility bridge, only for these owned
        # loopback installation children. Do not change the user's or Codex's environment.
        from upgrade_program_kit import uv_windows_specify_environment
        environment = uv_windows_specify_environment([specify])
        if environment is not None:
            launcher = [sys.executable, str(ROOT / 'scripts/invoke_specify.py'),
                        '--site-packages', str(environment[1]), '--loopback-http-only', '--']
    with candidate_catalogs(record) as base:
        steps = [
            [git, 'init', '.'],
            [specify, 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'],
            [specify, 'extension', 'catalog', 'add', f'{base}/extensions.json', '--name', 'intake-candidate', '--priority', '1', '--install-allowed'],
            [specify, 'preset', 'catalog', 'add', f'{base}/presets.json', '--name', 'intake-candidate', '--priority', '1', '--install-allowed'],
            # Spec Kit requires workflow preinstallation. Let the bundle contribute the other
            # components itself: preinstalling everything omits their bundle provenance.
            [specify, 'workflow', 'add', str(ROOT / 'workflows/program-kit-bootstrap'), '--dev'],
            [specify, 'bundle', 'install', str(ROOT / 'bundle.yml'), '--integration', 'codex'],
            [specify, 'extension', 'catalog', 'remove', 'intake-candidate'],
            [specify, 'preset', 'catalog', 'remove', 'intake-candidate'],
        ]
        for index, command in enumerate(steps, 1):
            print(f'Installing consumer components ({index}/{len(steps)})...', flush=True)
            if command[0] == specify:
                command = launcher + command[1:]
            if run(command, workspace, record / 'setup.log'):
                raise RuntimeError(f'Installation failed at step {index}; see {record / "setup.log"}')


def prepare(record: Path) -> None:
    specify = shutil.which('specify')
    git = shutil.which('git')
    if not specify or not git:
        raise RuntimeError('INTAKE_TOOL_MISSING: specify and git must be on PATH; no global configuration is changed.')
    record.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix='program-kit-intake-')).resolve()
    nonce = uuid.uuid4().hex
    (workspace / '.intake-session-owner').write_text(nonce, encoding='utf-8')
    state = {'schemaVersion': 1, 'id': record.name, 'workspace': str(workspace),
             'tempParent': str(workspace.parent), 'owner': nonce, 'source': str(ROOT),
             'startedAt': datetime.now(timezone.utc).isoformat(), 'status': 'preparing',
             'codexHome': str(Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).resolve())}
    save(record / 'session.json', state)
    print(f'Isolated consumer: {workspace}\nReview evidence: {record}', flush=True)
    source_git = [git, '-c', f'safe.directory={ROOT.as_posix()}', '-c', 'core.excludesFile=' if os.name == 'nt' else 'core.excludesFile=/dev/null']
    for key, args in [('sourceCommit', ['rev-parse', 'HEAD']), ('sourceChanges', ['status', '--porcelain'])]:
        result = subprocess.run(source_git + args, cwd=ROOT, capture_output=True, text=True, timeout=30)
        state[key] = result.stdout.strip() if result.returncode == 0 else 'unavailable'
    # The actual command sources are saved too: a commit alone cannot identify dirty candidates.
    shutil.copy2(ROOT / 'VERSION', record / 'VERSION')
    source_commands = ROOT / 'extensions/program-kit-governance/commands'
    for name in ('speckit.program-kit-governance.bootstrap.md', 'speckit.program-kit-governance.grilling.md'):
        shutil.copy2(source_commands / name, record / name)
    save(record / 'session.json', state)
    install_components(specify, git, workspace, record)
    runtime = workspace / '.specify/extensions/program-kit-governance/scripts/schema_runtime.py'
    for action in ('setup', 'record-copy'):
        if run([sys.executable, str(runtime), action], workspace, record / 'setup.log'):
            raise RuntimeError(f'Intake schema tool {action} failed; see setup.log.')
    for tool, arguments in ((specify, ['version']), (shutil.which('codex'), ['--version'])):
        if tool:
            run([tool, *arguments], workspace, record / 'setup.log')
    installed_skill = workspace / SKILL
    if not installed_skill.is_file() or GRILLING.as_posix() not in installed_skill.read_text(encoding='utf-8'):
        raise RuntimeError('Installed intake skill does not route to Program Kit grilling.')
    if digest(workspace / GRILLING) != digest(source_commands / GRILLING.name):
        raise RuntimeError('Installed Program Kit grilling differs from the candidate.')
    validator = workspace / '.specify/extensions/program-kit-governance/scripts/governance_state.py'
    if run([sys.executable, str(validator), 'validate-installation'], workspace, record / 'setup.log'):
        raise RuntimeError('Installed component coherence check failed; see setup.log.')
    (workspace / 'INTAKE-SESSION.md').write_text(INSTRUCTIONS, encoding='utf-8')
    # This is a consumer root, outside the contributor repository and its ancestor instructions.
    (workspace / 'AGENTS.md').write_text(
        INSTRUCTIONS + '\nFor every Git command use git -c safe.directory=' + workspace.as_posix()
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
            workspace.parent != Path(tempfile.gettempdir()).resolve() or
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
    for relative in ('docs/architecture', 'product-idea.md'):
        path = workspace / relative
        if path.is_dir():
            shutil.copytree(path, record / relative, dirs_exist_ok=True)
        elif path.is_file():
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
    intake = workspace / 'docs/architecture/bootstrap-intake.json'
    state['intakeStatus'] = 'absent'
    if intake.is_file():
        try:
            document = json.loads(intake.read_text(encoding='utf-8'))
            status = document.get('status') if isinstance(document, dict) else None
            command = 'validate-draft' if status == 'draft' else 'validate'
            validator = workspace / '.specify/extensions/program-kit-governance/scripts/bootstrap_intake.py'
            code = run([sys.executable, str(validator), command, '--json'], workspace, record / 'validation.log')
            state['intakeStatus'] = ('valid-draft' if status == 'draft' else 'valid-confirmed') if code == 0 else 'invalid'
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            state['intakeStatus'] = 'validation-error'
            state['validationError'] = str(error)
    state['archiveSha256'] = digest(archive)
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
- Intake: {state['intakeStatus']} (schema validity is not interview-quality acceptance)
- Conversation: {state['transcriptStatus']}
- Codex session IDs: {', '.join(state['sessionIds']) or 'unavailable'}
- CLI exit: {exit_code}
- Workspace: {workspace}
- Cleanup: {state['cleanup']}

Return to the Program Kit development conversation and ask to review this folder:
{record}

Review conversation.md and the matched rollout JSONL (when captured), docs/architecture,
validation.log (when an intake exists), setup.log, session.json, and consumer.zip.
The zip preserves the installed candidate and full consumer for recovery; it is not
a bootstrap checkpoint or a Release/live-acceptance receipt. No workflow was launched.
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
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(args.record.resolve())
        else:
            finish(args.record.resolve(), args.exit_code, args.keep_workspace, args.prepare_only)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'INTAKE_SESSION_ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

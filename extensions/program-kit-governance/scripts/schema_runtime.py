"""Explicit project-local dependency provisioning and installed-tool provenance."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

SCRIPTS = Path(__file__).resolve().parent
FILES = ('json_schema.py', 'schema_runtime.py', 'json-schema-requirements.txt', 'contract_shapes.py')
EXTENSION = Path('.specify/extensions/program-kit-governance/scripts')
RECORD = Path('.specify/program-kit-schema-tools.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_root():
    for parent in SCRIPTS.parents:
        if parent.name == '.specify':
            return parent.parent
    return SCRIPTS.parents[2]


def runtime_path(root=None):
    root = Path(root or project_root()).resolve()
    key = digest(SCRIPTS / 'json-schema-requirements.txt')[:16]
    tag = f'{sys.implementation.cache_tag}-{sys.platform}-{platform.machine()}'
    return root / '.program-kit/cache/json-schema' / f'{key}-{tag}'


def activate():
    path = runtime_path()
    if not (path / '.ready').is_file():
        raise RuntimeError(f'SCHEMA_RUNTIME_MISSING: run "{sys.executable}" "{SCRIPTS / "schema_runtime.py"}" setup')
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def setup(root=None, offline=False, wheelhouse=None):
    target = runtime_path(root)
    if (target / '.ready').is_file():
        return target
    if target.exists():
        raise RuntimeError(f'Refusing incomplete runtime directory: {target}')
    if offline and wheelhouse is None:
        raise RuntimeError(f'SCHEMA_RUNTIME_MISSING: offline setup requires --wheelhouse PATH; '
                           f'otherwise run "{sys.executable}" "{SCRIPTS / "schema_runtime.py"}" '
                           f'setup --project-root "{Path(root or project_root()).resolve()}" first.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='setup-', dir=target.parent) as temporary:
        staged = Path(temporary) / 'packages'
        if importlib.util.find_spec('pip') is not None:
            command = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check']
            pip_version = tuple(int(part) for part in importlib.metadata.version('pip').split('.')[:2])
            if sys.platform == 'win32' and (22, 2) <= pip_version < (24, 2):
                command += ['--use-feature=truststore']  # Verified system roots, never a TLS bypass.
        elif shutil.which('uv'):
            command = [shutil.which('uv'), 'pip', 'install', '--python', sys.executable]
            if sys.platform == 'win32':
                command += ['--native-tls']
        else:
            raise RuntimeError('SCHEMA_INSTALLER_MISSING: setup requires pip for this Python or uv on PATH.')
        command += ['--only-binary=:all:', '--no-deps', '--target', str(staged),
                    '-r', str(SCRIPTS / 'json-schema-requirements.txt')]
        if offline:
            command += ['--no-index']
        if wheelhouse:
            command += ['--find-links', str(Path(wheelhouse).resolve())]
        subprocess.run(command, check=True, timeout=300)
        subprocess.run([sys.executable, '-I', '-c',
                        'import sys; sys.path.insert(0, sys.argv[1]); from jsonschema import Draft202012Validator; '
                        'Draft202012Validator.check_schema({"type":"object"})', str(staged)], check=True)
        (staged / '.ready').write_text(digest(SCRIPTS / 'json-schema-requirements.txt'), encoding='utf-8')
        staged.rename(target)
    return target


def check_copy(root):
    root = Path(root).resolve()
    scripts = root / EXTENSION
    record = root / RECORD
    if not record.exists():
        if (scripts / 'json_schema.py').exists():
            raise RuntimeError('SCHEMA_TOOL_BASELINE_MISSING: preserve and review installed tools before upgrading.')
        return []  # Pre-tool Program Kit installation.
    value = json.loads(record.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('version') != 1:
        raise RuntimeError('SCHEMA_TOOL_BASELINE_INVALID: unsupported baseline format.')
    hashes = value.get('files', {})
    if not isinstance(hashes, dict) or set(hashes) != set(FILES):
        raise RuntimeError('SCHEMA_TOOL_BASELINE_INVALID: expected the complete tool inventory.')
    changed = [name for name in FILES if not (scripts / name).is_file() or digest(scripts / name) != hashes[name]]
    if changed:
        raise RuntimeError('SCHEMA_TOOLS_LOCALLY_EDITED: upgrade stopped before replacement: ' + ', '.join(changed)
                           + '. Preserve your edits and restore the installed version before upgrading.')
    return []


def record_copy(root):
    root = Path(root).resolve()
    scripts = root / EXTENSION
    record = root / RECORD
    record.parent.mkdir(parents=True, exist_ok=True)
    value = {'version': 1, 'files': {name: digest(scripts / name) for name in FILES}}
    temporary = record.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('setup', 'check-copy', 'record-copy'))
    parser.add_argument('--project-root', type=Path, default=project_root())
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--wheelhouse', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'setup':
            print(setup(args.project_root, args.offline, args.wheelhouse))
        elif args.command == 'check-copy':
            check_copy(args.project_root)
        else:
            record_copy(args.project_root)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

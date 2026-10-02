"""Bind native steps and worker instructions to one product Python runtime."""
from __future__ import annotations
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def selected(root: Path) -> str:
    record = root / '.specify/python-runtime.json'
    saved = json.loads(record.read_text(encoding='utf-8')) if record.is_file() else {}
    if not isinstance(saved, dict) or (saved and saved.get('contractVersion') != 1):
        raise ValueError('WORKFLOW_RUNTIME_PREFLIGHT: unsupported or invalid core Python runtime record')
    executable = os.environ.get('SPECKIT_PYTHON') or saved.get('executable') or shutil.which('python')
    if not isinstance(executable, str) or not executable or not Path(executable).is_absolute() or not Path(executable).is_file():
        raise ValueError('WORKFLOW_RUNTIME_PREFLIGHT: python is unavailable; select an absolute SPECKIT_PYTHON executable')
    if saved and os.path.normcase(os.path.abspath(executable)) != os.path.normcase(saved['executable']):
        raise ValueError('WORKFLOW_RUNTIME_PREFLIGHT: runtime differs from generated core instructions; regenerate them explicitly')
    return executable


def resolve(root: Path) -> str:
    executable = selected(root)
    probe = 'import sys,yaml; assert sys.version_info >= (3,11), "Python >=3.11 is required"; assert int(yaml.__version__.split(".")[0]) >= 6, "PyYAML >=6 is required"; print(sys.executable)'
    result = subprocess.run([executable, '-c', probe], capture_output=True,
        encoding='utf-8', errors='replace', timeout=30, check=False)
    if result.returncode:
        raise ValueError(f'WORKFLOW_RUNTIME_PREFLIGHT: {executable} failed before agent dispatch: {result.stderr or result.stdout}')
    return os.path.abspath(result.stdout.strip())


@contextlib.contextmanager
def environment(root: Path):
    executable = resolve(root)
    previous = {key: os.environ.get(key) for key in ('SPECKIT_PYTHON', 'PATH')}
    os.environ['SPECKIT_PYTHON'] = executable
    os.environ['PATH'] = str(Path(executable).parent) + os.pathsep + (previous['PATH'] or '')
    try:
        selected = shutil.which('python')
        if not selected or not os.path.samefile(selected, executable):
            raise ValueError('WORKFLOW_RUNTIME_PREFLIGHT: selected runtime must provide python beside its executable for native steps')
        yield executable
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

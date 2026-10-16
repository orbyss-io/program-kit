"""Select and scope Program Kit's native Python runtime; core generation stays upstream-owned."""
from __future__ import annotations
import contextlib
import os
from pathlib import Path
import shutil
import subprocess


def device_preflight(root: Path) -> None:
    import package_execution
    package_execution.javascript_runtime().device.require_python(root)


def contract():
    from dotnet_adapter import bootstrap
    bootstrap()
    import python_runtime_contract
    return python_runtime_contract


def selected(root: Path) -> str:
    device_preflight(root)
    try:
        executable = contract().select(root)
    except (ValueError, OSError) as error:
        raise ValueError('WORKFLOW_RUNTIME_PREFLIGHT: ' + str(error)) from error
    if os.name == 'nt' and not (root / '.specify/python-runtime.json').is_file():
        from windows_workflow_path import canonical_python
        executable = canonical_python(executable)
    return executable


def resolve(root: Path) -> str:
    executable = selected(root)
    try:
        return os.path.abspath(contract().verify(root, executable, purpose='workflow')['executable'])
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        raise ValueError('WORKFLOW_RUNTIME_PREFLIGHT: ' + str(error)) from error


@contextlib.contextmanager
def environment(root: Path):
    executable = resolve(root)
    previous = {key: os.environ.get(key) for key in ('SPECKIT_PYTHON', 'PATH')}
    values = invocation_values(executable)
    os.environ['SPECKIT_PYTHON'] = values['SPECKIT_PYTHON']
    os.environ['PATH'] = values['PATH']
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


def invocation_values(executable: str) -> dict[str, str]:
    """Preview the exact scoped runtime environment without probing or changing it."""
    values = dict(os.environ)
    values['SPECKIT_PYTHON'] = executable
    from windows_workflow_path import prepare_path
    values['PATH'] = prepare_path(values.get('PATH', ''), executable)
    return values

"""Applicable Python identity/dependency admission; never provisions a runtime."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PURPOSES = {'engineering': (), 'workflow': ('yaml',)}


def select(repository: Path, executable: str | None = None) -> str:
    record = repository / '.specify/python-runtime.json'
    saved = json.loads(record.read_text(encoding='utf-8')) if record.is_file() else {}
    if not isinstance(saved, dict) or (saved and (saved.get('contractVersion') != 1
            or not isinstance(saved.get('executable'), str) or not Path(saved['executable']).is_absolute())):
        raise ValueError('unsupported or invalid core Python runtime record')
    selected = executable or os.environ.get('SPECKIT_PYTHON') or saved.get('executable') or shutil.which('python')
    if not isinstance(selected, str) or not Path(selected).is_absolute() or not Path(selected).is_file():
        raise ValueError('Python is unavailable; select an installed absolute SPECKIT_PYTHON executable')
    if saved and os.path.normcase(os.path.abspath(selected)) != os.path.normcase(os.path.abspath(saved['executable'])):
        raise ValueError('SPECKIT_PYTHON differs from generated core instructions; regenerate them explicitly')
    return os.path.abspath(selected)


def verify(repository: Path, executable: str | None = None, *, purpose: str = 'engineering') -> dict:
    if purpose not in PURPOSES:
        raise ValueError('unknown Python readiness purpose')
    selected = select(repository, executable)
    # Only workflow entry points require PyYAML. Engineering scripts use stdlib;
    # version/platform-specific schema caches have their own explicit admission.
    probe = '''import importlib,json,os,sys
assert sys.version_info >= (3,11), 'Python >=3.11 is required'
assert os.path.samefile(sys.argv[1],sys.executable), 'Interpreter identity changed'
modules={}
for name in json.loads(sys.argv[2]):
 module=importlib.import_module(name)
 if name=='yaml': assert int(module.__version__.split('.')[0])>=6, 'PyYAML >=6 is required'
 modules[name]=getattr(module,'__version__',None)
print(json.dumps({'executable':sys.executable,'version':'.'.join(map(str,sys.version_info[:3])),'modules':modules}))
'''
    result = subprocess.run([selected, '-I', '-c', probe, selected, json.dumps(PURPOSES[purpose])],
                            cwd=repository, capture_output=True, encoding='utf-8', errors='replace',
                            timeout=30, check=False)
    if result.returncode:
        raise ValueError(f'{purpose} readiness failed for {selected}; prepare its required dependencies '
                         f'in the selected environment explicitly, then retry. No acquisition was attempted. '
                         + (result.stderr or result.stdout)[-3000:])
    value = json.loads(result.stdout)
    pin = repository / '.python-version'
    if pin.is_file() and value['version'] != pin.read_text(encoding='utf-8').strip():
        raise ValueError(f'Interpreter version {value["version"]} differs from .python-version')
    value['purpose'] = purpose
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--executable')
    parser.add_argument('--purpose', choices=tuple(PURPOSES), default='engineering')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.repository.resolve(), args.executable, purpose=args.purpose)))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('PKV005 Python runtime readiness: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

"""Fast syntax and validation-definition integrity, without SDK/network setup."""
import ast
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_validation


def main():
    from sync_shared_runtime import sync
    sync(ROOT)
    definition = run_validation.load_definition()
    files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    count = 0
    for name in files:
        path = ROOT / name
        if not path.is_file() or not name.startswith(('scripts/', 'extensions/', '.github/scripts/', 'tests/')):
            continue
        if path.suffix == '.py' and '/fixtures/' not in name and '/bootstrap-seed/' not in name:
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=name)
            count += 1
        elif path.suffix == '.json' and '/fixtures/' not in name and not name.startswith('tests/'):
            json.loads(path.read_text(encoding='utf-8-sig'))
            count += 1
    for check in definition['checks']:
        command = check['command']
        if len(command) > 1 and command[0] in ('{python}', '{powershell}'):
            offset = command.index('-File') + 1 if '-File' in command else 1
            if not (ROOT / command[offset]).is_file():
                raise ValueError('Missing validation entrypoint: ' + check['id'])
    # Validate all dependency DAGs, including optional investigations, without executing.
    run_validation.closure(definition['checks'], [c['id'] for c in definition['checks']])
    print(f'Source/configuration syntax: {count} files; validation definition and entrypoints coherent.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

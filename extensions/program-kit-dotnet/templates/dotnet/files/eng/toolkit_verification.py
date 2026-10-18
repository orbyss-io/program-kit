"""Named Python toolkit checks; results never count as native application tests."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

from retained_inputs import canonical, contained, file_hash, read_json, require


def declarations(root, config):
    rows = config.get('toolkitChecks', [])
    require(isinstance(rows, list) and len(rows) <= 256, 'toolkitChecks must be a bounded array')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'id', 'script', 'arguments', 'inputs', 'timeoutSeconds'},
                'toolkit check requires id, script, arguments, exact inputs and timeoutSeconds')
        name = row['id']
        require(isinstance(name, str) and re.fullmatch('[a-z][a-z0-9-]{0,63}', name) and name not in result,
                'toolkit check identity must be unique and stable')
        script = canonical(row['script'])
        require(script.endswith('.py') and contained(root, script).is_file(), 'toolkit check script must be a current contained Python file')
        require(isinstance(row['arguments'], list) and len(row['arguments']) <= 64
                and all(isinstance(arg, str) and len(arg) <= 4096 and '\x00' not in arg for arg in row['arguments']),
                'toolkit arguments must be a bounded literal array')
        require(isinstance(row['inputs'], list) and 0 < len(row['inputs']) <= 4096
                and all(isinstance(path, str) for path in row['inputs']), 'toolkit checks need exact bounded input ownership')
        paths = [canonical(path) for path in [script, *row['inputs']]]
        require(len({path.casefold() for path in row['inputs']}) == len(row['inputs']), 'toolkit input aliases are not admitted')
        for path in paths:
            contained(root, path)
        require(type(row['timeoutSeconds']) is int and 1 <= row['timeoutSeconds'] <= 900, 'toolkit timeout must be 1..900 seconds')
        result[name] = {**row, 'inputs': sorted(set(paths))}
    return result


def pending(root):
    """Removed checks cannot silently erase a failed or interrupted obligation."""
    unresolved = set()
    rows = []
    for path in (root / 'artifacts/tests/toolkit-runs').glob('*/result.json'):
        value, _ = read_json(path)
        require(value.get('schemaVersion') == 1 and isinstance(value.get('outcomes'), list), 'unsupported toolkit result history')
        rows.append((value.get('startedAtUtc', ''), str(path), path, value))
    for _, _, path, value in sorted(rows):
        for outcome in value['outcomes']:
            name = outcome['check']
            valid = evidence_valid(root, path, outcome)
            if valid:
                unresolved.discard(name)
            else:
                unresolved.add(name)
    return unresolved


def evidence_valid(root, path, outcome):
    """Retained execution integrity only; current fingerprints belong to the planner."""
    if (path.name != 'result.json' or path.parent.parent != root / 'artifacts/tests/toolkit-runs'
            or outcome.get('status') != 'completed' or outcome.get('exitCode') != 0 or not outcome.get('fingerprint')):
        return False
    logs = outcome.get('evidence', {})
    if not isinstance(logs, dict) or len(logs) != 2 or {Path(p).name.split('.')[-2] for p in logs} != {'stdout', 'stderr'}:
        return False
    for relative, expected in logs.items():
        target = contained(root, relative)
        if not target.is_relative_to(path.parent) or not target.is_file() or file_hash(target) != expected:
            return False
    return True


def fingerprint(root, row):
    inputs = {path: file_hash(contained(root, path)) if contained(root, path).is_file() else None for path in row['inputs']}
    state = {'declaration': row, 'inputs': inputs, 'python': sys.version,
             'runner': file_hash(Path(__file__)), 'configuration': {}}
    for relative in ('eng/verification.json', 'eng/verification.setup.json'):
        target = contained(root, relative)
        state['configuration'][relative] = file_hash(target) if target.is_file() else None
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def execute(root, selected, declarations):
    if not selected:
        return None
    directory = root / 'artifacts/tests/toolkit-runs' / uuid.uuid4().hex
    directory.mkdir(parents=True)
    value = {'schemaVersion': 1, 'status': 'running', 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
             'acceptanceEstablished': False, 'outcomes': [{'check': name, 'status': 'pending'} for name in selected]}
    def save():
        (directory / 'result.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    save()
    try:
        for index, outcome in enumerate(value['outcomes']):
            row = declarations[outcome['check']]
            before = fingerprint(root, row)
            outcome.update(status='running', fingerprint=before); save()
            stdout, stderr = directory / f'{index}.stdout.log', directory / f'{index}.stderr.log'
            try:
                with stdout.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
                    native = subprocess.run([sys.executable, '-E', '-s', str(contained(root, row['script'])), *row['arguments']],
                                            cwd=root, stdout=out, stderr=err, timeout=row['timeoutSeconds'])
                outcome['exitCode'] = native.returncode
                require(native.returncode == 0, 'toolkit check failed: ' + outcome['check'] + '; inspect ' + str(directory))
                require(before == fingerprint(root, row), 'toolkit inputs changed during execution; rerun ' + outcome['check'])
                outcome['status'] = 'completed'
            finally:
                outcome['evidence'] = {path.relative_to(root).as_posix(): file_hash(path) for path in (stdout, stderr) if path.is_file()}
                save()
        value['status'] = 'completed'
    except BaseException as error:
        value.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed', diagnostic=str(error))
        for outcome in value['outcomes']:
            if outcome['status'] != 'completed':
                outcome['status'] = value['status']
        raise
    finally:
        value['finishedAtUtc'] = datetime.now(timezone.utc).isoformat(); save()
    return {'run': (directory / 'result.json').relative_to(root).as_posix(), 'result': value}

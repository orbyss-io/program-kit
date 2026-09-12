"""Core delivery authority seam. Disabled consumers need no extension or credentials."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

BINDING = Path('.program-kit/delivery/binding.json')
HISTORY = Path('.program-kit/delivery/history.json')


class DeliveryError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DeliveryError('PKD_CONFIG_INVALID duplicate key: ' + key)
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    except (OSError, ValueError) as error:
        raise DeliveryError(f'PKD_CONFIG_INVALID {path}: {error}') from error


def inside(root, relative):
    candidate = root / relative
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise DeliveryError('PKD_CONFIG_INVALID delivery paths must remain in the repository')
    return candidate


def prior_history(root):
    """Recover the last committed history even after ordinary working-file deletion."""
    if not (root / '.git').exists():
        return None
    prefix = ['git', '-c', 'safe.directory=' + root.as_posix(), '-c', 'core.excludesFile=']
    try:
        tip = subprocess.run(prefix + ['log', '-1', '--diff-filter=AM', '--format=%H', '--', HISTORY.as_posix()],
            cwd=root, capture_output=True, text=True, timeout=10)
        if tip.returncode:
            raise DeliveryError('PKD_PROVENANCE_UNAVAILABLE cannot inspect delivery Git history')
        if not tip.stdout.strip():
            return None
        previous = subprocess.run(prefix + ['show', tip.stdout.strip() + ':' + HISTORY.as_posix()],
            cwd=root, capture_output=True, text=True, timeout=10)
        if previous.returncode:
            raise DeliveryError('PKD_PROVENANCE_UNAVAILABLE cannot read established delivery history')
        value = json.loads(previous.stdout)
        if not isinstance(value, dict) or not isinstance(value.get('records'), list):
            raise DeliveryError('PKD_PROVENANCE_UNAVAILABLE established delivery history is malformed')
        return value
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        raise DeliveryError('PKD_PROVENANCE_UNAVAILABLE delivery history cannot be established') from error


def runtime(root):
    path = root / '.specify/extensions/program-kit-delivery/scripts/delivery_contract.py'
    source_root = Path(__file__).resolve().parents[3]
    if root == source_root and (root / 'bundle.yml').is_file():
        path = root / 'extensions/program-kit-delivery/scripts/delivery_contract.py'
    if not path.is_file():
        raise DeliveryError('PKD_EXTENSION_MISSING restore the matching delivery extension; authority remains configured')
    spec = importlib.util.spec_from_file_location('program_kit_delivery_contract', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect(root):
    root = Path(root).resolve()
    binding_path, history_path = inside(root, BINDING), inside(root, HISTORY)
    previous = prior_history(root)
    if not binding_path.exists() and not history_path.exists():
        if previous and previous.get('records'):
            raise DeliveryError('PKD_CONFIG_MISSING restore prior activation/disconnect history and binding')
        return {'state': 'disabled', 'authority': 'local', 'admission': 'local-governance'}
    if not binding_path.is_file() or not history_path.is_file():
        raise DeliveryError('PKD_CONFIG_MISSING binding and history must be retained together')
    binding, history = read(binding_path), read(history_path)
    try:
        runtime(root).validate_configuration(root, binding, history)
    except ValueError as error:
        raise DeliveryError(str(error)) from error
    if previous:
        old = previous.get('records', [])
        if history['records'][:len(old)] != old:
            raise DeliveryError('PKD_HISTORY_CHANGED preserve committed activation history')
    if history['records'] and history['records'][-1]['action'] == 'disconnect':
        raise DeliveryError('PKD_DISCONNECT_UNAVAILABLE Phase 1 cannot verify provider disconnect evidence; '
                            'a hand-written history record cannot restore local authority')
    enabled = binding['state'] == 'enabled'
    return {'state': binding['state'], 'authority': 'platform' if enabled else 'local',
            'admission': 'adapter-unavailable' if enabled else 'local-governance',
            'provider': binding.get('provider'), 'space': binding.get('space')}


def require_admission(root, activity):
    status = inspect(root)
    if status['authority'] == 'platform':
        raise DeliveryError(f'PKD_ADAPTER_UNAVAILABLE {activity} requires current provider admission; '
                            'Phase 1 supplies configuration and technical validation only')
    return status

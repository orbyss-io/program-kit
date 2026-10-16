"""Repair feedback v1: deterministic, dependency-free contract and data guardian.

Never imports, executes or renders submitted evidence. Error messages contain
codes and field names, never submitted values or file contents.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import unicodedata

VERSION = '1.0'
GUARDIAN = 'repair-guardian-1'
UPSTREAM = 'orbyss-io/program-kit'
EVIDENCE = 'orbyss-io/program-kit-evidence'
MAX_FILES = 24
MAX_FILE = 256 * 1024
MAX_TOTAL = 1024 * 1024
TYPES = {'.md', '.json', '.txt', '.log', '.patch', '.diff', '.py', '.cs', '.ts', '.js', '.sh', '.ps1', '.yml', '.yaml', '.png', '.pdf'}
BINARY = {'.png', '.pdf'}
SECTIONS = ('context', 'expectation', 'observation', 'resources', 'decision', 'remedy', 'results', 'lesson')
CLASSES = ('reported', 'inspected', 'independently-reproduced', 'unknown')
EXPLANATIONS = ('recorded', 'retrospective', 'unknown')
COMPONENTS = ('governance', 'bootstrap', 'knowledge', 'building-blocks', 'dotnet', 'upgrade', 'tooling', 'unclassified')
LIFECYCLE = ('evidenceAccepted', 'assessed', 'confirmedRepair', 'implemented', 'validated', 'released', 'confirmedInConsumer')
ID = r'rf-[0-9a-f]{32}'
HEX = r'[0-9a-f]{64}'


def require(ok, code):
    if not ok:
        raise ValueError('PKRF ' + code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def digest(value):
    return sha(encoded(value))


def load(data):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'duplicate-json-field')
            value[key] = item
        return value
    return json.loads(data, object_pairs_hook=unique, parse_constant=lambda _: require(False, 'nonfinite-json'))


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= value.keys()
            and value.keys() <= set(required) | set(optional), 'invalid-fields')


def text(value):
    require(isinstance(value, str) and 0 < len(value) <= 16000, 'invalid-text')


def request(value):
    fields(value, ('contractVersion', 'requestId', 'revision', 'supersedes', 'projectId', 'createdAt',
                   'component', 'title', 'originalAccount', 'diagnostics', 'unclassified', 'evidence', 'omissions'))
    require(value['contractVersion'] == VERSION, 'unsupported-contract-preserve-original-use-explicit-mapping')
    require(isinstance(value['requestId'], str) and re.fullmatch(ID, value['requestId']), 'request-id')
    require(type(value['revision']) is int and value['revision'] >= 1, 'revision')
    previous = value['supersedes']
    require((value['revision'] == 1 and previous is None) or
            (value['revision'] > 1 and isinstance(previous, str) and re.fullmatch(HEX, previous)), 'supersedes-hash')
    for key in ('projectId', 'createdAt', 'title', 'originalAccount'):
        text(value[key])
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', value['projectId']), 'stable-public-project-pseudonym')
    require(len(value['title']) <= 160 and value['component'] in COMPONENTS, 'title-or-component')
    require(isinstance(value['diagnostics'], dict) and set(value['diagnostics']) == set(SECTIONS), 'diagnostic-sections')
    for section in value['diagnostics'].values():
        fields(section, ('answer', 'evidenceClass', 'explanationKind', 'references'))
        text(section['answer'])
        require(section['evidenceClass'] in CLASSES and section['explanationKind'] in EXPLANATIONS, 'diagnostic-enum')
        require(isinstance(section['references'], list) and all(isinstance(x, str) for x in section['references']), 'references')
    for key in ('unclassified', 'omissions'):
        require(isinstance(value[key], list) and all(isinstance(x, str) for x in value[key]), 'string-list')
    fields(value['evidence'], ('programKitVersion', 'profileVersion', 'knowledgeVersion', 'sourceCommit', 'dirtyState', 'members'))
    for key in ('programKitVersion', 'profileVersion', 'knowledgeVersion', 'sourceCommit', 'dirtyState'):
        text(value['evidence'][key])
    require(isinstance(value['evidence']['members'], list), 'evidence-members')
    for member in value['evidence']['members']:
        fields(member, ('path', 'purpose', 'provenance', 'bytes', 'sha256', 'transformations', 'qualification'))
        safe_name(member['path'])
        for key in ('purpose', 'provenance', 'qualification'):
            text(member[key])
        require(type(member['bytes']) is int and 0 <= member['bytes'] <= MAX_FILE, 'member-bytes')
        require(isinstance(member['sha256'], str) and re.fullmatch(HEX, member['sha256']), 'member-hash')
        require(isinstance(member['transformations'], list) and
                all(isinstance(x, str) for x in member['transformations']), 'transformations')
    return value


def safe_name(name):
    require(isinstance(name, str) and len(name) <= 200 and
            re.fullmatch(r'[a-zA-Z0-9.][a-zA-Z0-9_./-]*', name) and
            all(p not in ('', '.', '..') and not p.endswith(('.', ' ')) and
                p.split('.')[0].upper() not in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(10)), *('LPT'+str(i) for i in range(10))}
                for p in name.split('/')), 'unsafe-path')
    require(not name.startswith('/') and '\\' not in name and ':' not in name, 'unsafe-path')


def inside(root, name):
    safe_name(name)
    root = Path(root).absolute()
    target = root / name
    for path in (root, target, *target.parents):
        require(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(), 'linked-path')
    require(target.resolve().is_relative_to(root.resolve()), 'path-escape')
    return target


def sensitive(data):
    # Conservative supported patterns, not a guarantee about business/personal facts.
    require(not re.search(rb'(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:authorization\s*:\s*bearer\s+\S+)|(?i:(?:password|client_secret|access_token)\s*[:=]\s*["\']?[^\s"\']{4,}))', data), 'sensitive-content-review-required')


def inventory(root):
    root = Path(root)
    result = {}
    aliases = set()
    total = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            inside(root, relative)
            alias = unicodedata.normalize('NFC', relative).casefold()
            require(alias not in aliases, 'path-alias')
            aliases.add(alias)
            if name in files:
                info = path.stat()
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'nonregular-or-hardlink')
                require(info.st_size <= MAX_FILE, 'per-file-budget')
                total += info.st_size
                require(len(result) < MAX_FILES and total <= MAX_TOTAL, 'inventory-budget')
                result[relative] = path.read_bytes()
    require(len(result) <= MAX_FILES and sum(map(len, result.values())) <= MAX_TOTAL, 'inventory-budget')
    return result


def guard(root, submitted_commit='local', validator_commit='local'):
    files = inventory(root)
    require('request.json' in files and 'report.md' in files, 'request-and-report-required')
    try:
        value = request(load(files['request.json']))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError('PKRF invalid-json') from None
    require(files['request.json'] == encoded(value), 'request-canonical-bytes-run-prepare')
    expected = {m['path']: m for m in value['evidence']['members']}
    require(len(expected) == len(value['evidence']['members']) and 'request.json' not in expected
            and set(files) == {'request.json', *expected}, 'exact-manifest-inventory')
    for name, data in files.items():
        suffix = Path(name).suffix.lower()
        require(suffix in TYPES and (name in ('request.json', 'report.md') or name.startswith('evidence/')), 'unsupported-type-or-location')
        sensitive(data)
        if suffix in BINARY:
            require(expected[name]['qualification'] != 'unknown' and
                    ((suffix == '.png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or
                     (suffix == '.pdf' and data.startswith(b'%PDF-'))), 'binary-qualification-or-signature')
        else:
            try:
                data.decode('utf-8')
            except UnicodeError:
                raise ValueError('PKRF utf8-required') from None
            require(b'\x00' not in data, 'binary-in-text')
        if name != 'request.json':
            require(expected[name]['bytes'] == len(data) and expected[name]['sha256'] == sha(data), 'member-identity')
    return {'guardianVersion': GUARDIAN, 'contractVersion': VERSION, 'submittedCommit': submitted_commit,
            'validatorCommit': validator_commit, 'requestId': value['requestId'], 'revision': value['revision'],
            'requestSha256': sha(files['request.json']), 'inventorySha256': digest({n: sha(d) for n, d in files.items()}),
            'meaning': 'contract-valid evidence; maintainer acceptance required; diagnosis and publisher unverified'}

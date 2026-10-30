"""Read original supported preservation records; never execute historical inputs or mint acceptance."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from owned_scratch import filesystem_path

INDEX = 'config/program-kit/retained-inputs.json'
MAX_JSON = 1_048_576
MAX_ROWS = 256
MAX_FILE = 67_108_864


def require(value, message):
    if not value:
        raise ValueError('PKD001 ' + message)


def canonical(value):
    require(isinstance(value, str) and value and len(value) <= 1024 and '\\' not in value and ':' not in value
            and not any(ord(character) < 32 or ord(character) == 127 or character in '<>"|?*{}[]' for character in value),
            'use literal canonical repository-relative retained paths')
    parsed = PurePosixPath(value)
    require(not parsed.is_absolute() and parsed.as_posix() == value and all(part not in ('', '.', '..') for part in parsed.parts),
            'retained path traversal or alias is not admitted')
    require(all(not part.endswith(('.', ' ')) and not re.fullmatch(r'(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part)
                for part in parsed.parts), 'retained Windows device/trailing-dot aliases are not admitted')
    return value


def contained(root, relative):
    target = root / canonical(relative)
    for part in (target, *target.parents):
        if not part.is_relative_to(root):
            continue
        try:
            info = os.lstat(filesystem_path(part))
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400), 'retained input aliases/reparse points are not admitted: ' + relative)
    require(target.resolve().is_relative_to(root), 'retained input escapes the repository')
    return target


@contextmanager
def regular_file(path, maximum):
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    descriptor = os.open(filesystem_path(path), flags)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, 'retained input must be a bounded regular file')
        yield stream
        after = os.fstat(stream.fileno())
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'retained input changed during observation')


def file_hash(path):
    value = hashlib.sha256()
    with regular_file(path, MAX_FILE) as stream:
        total = 0
        for chunk in iter(lambda: stream.read(65536), b''):
            total += len(chunk)
            require(total <= MAX_FILE, 'retained input grew beyond its finite hash budget')
            value.update(chunk)
    return value.hexdigest()


def _pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, 'duplicate retention JSON field')
        result[key] = value
    return result


def read_json(path, expected_sha=None):
    with regular_file(path, MAX_JSON) as stream:
        raw = stream.read(MAX_JSON + 1)
    require(len(raw) <= MAX_JSON, 'retention JSON exceeds its bounded input budget')
    digest = hashlib.sha256(raw).hexdigest()
    require(expected_sha is None or digest == expected_sha, 'original preservation record changed: ' + str(path.name))
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_pairs,
                       parse_constant=lambda _: require(False, 'non-finite retention JSON value'))
    require(isinstance(value, dict), 'retention JSON must be an object')
    return value, digest


def snapshot(root):
    root = Path(root).resolve()
    index_path = contained(root, INDEX)
    if not Path(filesystem_path(index_path)).exists():
        return {'schemaVersion': 1, 'configured': False, 'frozen': {}, 'activeDocuments': [], 'inputs': {}}
    data, index_hash = read_json(index_path)
    require({'schemaVersion', 'records', 'protected', 'activeDocuments'} <= set(data)
            <= {'schemaVersion', 'records', 'protected', 'activeDocuments', 'archives', 'retiredLocks'} and type(data['schemaVersion']) is int and data['schemaVersion'] == 1,
            'unsupported retained-input ownership index')
    require(all(isinstance(data[key], list) and len(data[key]) <= MAX_ROWS for key in ('records', 'protected', 'activeDocuments')),
            'retention inventories must be bounded arrays')
    records, inputs, seen = {}, {INDEX: index_hash}, set()
    for row in data['records']:
        require(isinstance(row, dict) and set(row) == {'id', 'path', 'sha256'}
                and isinstance(row['id'], str) and re.fullmatch('[a-z][a-z0-9-]{0,63}', row['id'])
                and row['id'] not in records and isinstance(row['sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['sha256']),
                'preservation records need unique identities and exact original hashes')
        target = contained(root, row['path'])
        require(row['path'].casefold() not in seen, 'duplicate/aliased preservation record')
        seen.add(row['path'].casefold())
        value, _ = read_json(target, row['sha256'])
        require(value.get('status') in ('abandoned', 'deleted') and isinstance(value.get('preserved'), dict)
                and 0 < len(value['preserved']) <= 4096, 'bind an executed supported feature-reset preservation result, not a preview or a fresh claim')
        for relative, digest in value['preserved'].items():
            canonical(relative)
            require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'original preservation record has an invalid hash')
        require(len({relative.casefold() for relative in value['preserved']}) == len(value['preserved']),
                'original preservation record contains portable path aliases')
        records[row['id']] = (row, value)
        inputs[row['path']] = row['sha256']
    frozen = {}
    for row in data['protected']:
        require(isinstance(row, dict) and set(row) == {'path', 'record'} and isinstance(row['record'], str) and row['record'] in records,
                'protected input must bind a declared original preservation record')
        relative = canonical(row['path'])
        require(relative.casefold() not in {path.casefold() for path in frozen}, 'duplicate/aliased protected input')
        authority, result = records[row['record']]
        require(relative in result['preserved'], 'protected input has no original preserved-byte provenance: ' + relative)
        digest = result['preserved'][relative]
        require(file_hash(contained(root, relative)) == digest, 'frozen historical input changed: ' + relative)
        frozen[relative] = {'sha256': digest, 'record': row['record'], 'recordPath': authority['path'], 'recordSha256': authority['sha256']}
    active, seen = [], {relative.casefold() for relative in frozen}
    for row in data['activeDocuments']:
        require(isinstance(row, dict) and set(row) == {'path', 'supersedes'} and isinstance(row['supersedes'], list)
                and row['supersedes'] and all(isinstance(relative, str) for relative in row['supersedes'])
                and len(set(row['supersedes'])) == len(row['supersedes'])
                and all(relative in frozen for relative in row['supersedes']), 'active document must link exact preserved evidence')
        relative = canonical(row['path'])
        contained(root, relative)
        require(relative.endswith('.md') and relative.casefold() not in seen, 'a frozen document cannot become a mutable target; use a distinct current index/versioned proposal')
        seen.add(relative.casefold()); active.append(row)
    from retained_archives import verify
    archives, archive_inputs = verify(root, data.get('archives', []), records)
    inputs.update(archive_inputs)
    from retained_locks import verify as verify_locks
    retired_locks, lock_inputs = verify_locks(root, data.get('retiredLocks', []), records)
    inputs.update(lock_inputs)
    return {'schemaVersion': 1, 'configured': True, 'indexSha256': inputs[INDEX], 'frozen': frozen,
            'archives': archives, 'retiredLocks': retired_locks, 'activeDocuments': active, 'inputs': inputs}


def preserve_basis(previous, current):
    if previous is not None:
        require(isinstance(previous, dict) and previous.get('schemaVersion') == 1 and isinstance(previous.get('frozen'), dict),
                'unsupported retained document planning basis')
        for relative, binding in previous['frozen'].items():
            require(current['frozen'].get(relative) == binding,
                    'frozen ownership/anchor changed since drafting: ' + relative + '; retain its original record and create a linked active proposal')
        require(all(row in current.get('archives', []) for row in previous.get('archives', [])),
                'archive ownership/anchor changed since drafting; preserve original reset evidence')
        require(all(current.get('retiredLocks', {}).get(path) == binding for path, binding in previous.get('retiredLocks', {}).items()),
                'retired lock ownership/anchor changed since drafting; preserve original reset evidence')
    return current


def summary(value):
    return {'configured': value['configured'], 'index': INDEX if value['configured'] else None,
            'indexSha256': value.get('indexSha256'), 'frozenInputs': len(value['frozen']),
            'activeProposals': [row['path'] for row in value['activeDocuments']],
            'retainedArchives': value.get('archives', []),
            'retiredLocks': value.get('retiredLocks', {}),
            'inspectionCommand': 'python scripts/retained_inputs.py inspect --repository .', 'freshProductAcceptance': False}


def drafting_basis(content):
    markers = re.findall(r'^<!-- program-kit:tasks-draft (.+) -->$', content, re.M)
    require(len(markers) <= 1, 'ambiguous retained task drafting basis')
    if not markers:
        return None
    require(len(markers[0].encode('utf-8')) <= MAX_JSON, 'retained drafting basis exceeds its bounded input budget')
    value = json.loads(markers[0], object_pairs_hook=_pairs,
                       parse_constant=lambda _: require(False, 'non-finite drafting basis'))
    require(isinstance(value, dict), 'invalid retained task drafting basis')
    return value.get('documentOwnership')


def validate_document_outputs(root, content, previous=None):
    recorded = drafting_basis(content)
    require(previous is None or recorded is None or previous == recorded, 'conflicting retained document planning bases')
    previous = previous if previous is not None else recorded
    value = preserve_basis(previous, snapshot(root))
    frozen_paths = {relative.casefold(): relative for relative in value['frozen']}
    rows = {}
    sections = re.finditer(r'^## Document outputs\s*\n(.*?)(?=^## |\Z)', content, re.M | re.S)
    tasks = {match[0]: match[1] for match in re.findall(r'^- \[[ xX]\] (T\d+) (.+)$', content, re.M)}
    pending = {match[0]: match[1] for match in re.findall(r'^- \[ \] (T\d+) (.+)$', content, re.M)}
    for section in sections:
        for line in section[1].splitlines():
            if not line.startswith('|'):
                continue
            cells = [cell.strip().strip('`') for cell in line.strip('|').split('|')]
            if cells[0] in ('Task', 'Task ID') or all(re.fullmatch(r'[: -]+', cell) for cell in cells):
                continue
            require(len(cells) == 3 and cells[0] in tasks and cells[2] in ('read', 'write'),
                    'Document outputs rows require actual Task, Path and read/write Mode')
            relative = canonical(cells[1]); key = (cells[0], relative.casefold())
            require(key not in rows, 'duplicate document output intent')
            rows[key] = cells[2]
            require(cells[0] not in pending or relative.casefold() not in frozen_paths or cells[2] == 'read',
                    'task targets frozen historical bytes: ' + relative + '; select a linked current index/versioned proposal')
    for task, description in pending.items():
        for folded, relative in frozen_paths.items():
            if re.search(r'(?<![A-Za-z0-9_./-])' + re.escape(relative) + r'(?![A-Za-z0-9_./-])', description, re.I):
                require(rows.get((task, folded)) == 'read', 'declare frozen input ' + relative
                        + ' as read in Document outputs; route edits to a distinct active proposal')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'verify'))
    parser.add_argument('--repository', type=Path, default=Path('.'))
    parser.add_argument('--path', help='Inspect one exact frozen/current document path')
    args = parser.parse_args()
    value = snapshot(args.repository)
    result = summary(value)
    if args.command == 'inspect':
        result['frozen'] = value['frozen'] if args.path is None else {args.path: value['frozen'].get(args.path)}
        result['activeDocuments'] = value['activeDocuments']
    print(json.dumps(result))


if __name__ == '__main__':
    main()

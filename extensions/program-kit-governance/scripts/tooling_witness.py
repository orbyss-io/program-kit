"""Durable exact source witnesses. Retained source is data, never executable authority.

An original installation/attempt receipt anchors the record hash. A publisher
identity is authenticated by the enclosing verified package, never by this JSON
file or its content-addressed filename. No downloads or patch execution occur.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import uuid
import zipfile

PACKAGED = 'program-kit-source-witness.json'
DIRECTORIES = ('scripts', 'extensions', 'presets', 'workflows', 'releases')
ROOT_FILES = ('VERSION', 'bundle.yml', 'README.md', 'LICENSE', 'THIRD-PARTY-NOTICES.md')
EXCLUDED = {'__pycache__', 'bin', 'obj', 'node_modules', 'playwright-report', 'test-results', '.auth'}
MAX_FILES, MAX_FILE, MAX_TOTAL = 8192, 32 * 1_048_576, 256 * 1_048_576


def require(value, diagnostic):
    if not value:
        raise ValueError('PKU145 ' + diagnostic)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def filesystem(path):
    # Load the current shipped helper only, never a helper in retained source.
    helper = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files/eng/owned_scratch.py'
    require(helper.is_file(), 'current shared filesystem adapter is missing')
    spec = importlib.util.spec_from_file_location('tooling_witness_owned_paths', helper)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return Path(module.filesystem_path(Path(path).absolute()))


def relative(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name
            and not any(ord(c) < 32 for c in name), 'invalid witness path')
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name
            and all(part not in {'.', '..'} for part in path.parts), 'noncanonical witness path')
    return name


def contained(root, name):
    path = root / relative(name)
    require(not any(part.is_symlink() or getattr(part, 'is_junction', lambda: False)()
                    for part in (path, *path.parents)), 'linked witness location: ' + name)
    require(path.resolve().is_relative_to(root.resolve()), 'witness location escaped its owner')
    return path


def inventory(root):
    root = filesystem(root)
    require(root.is_dir(), 'source location is missing')
    files, size = {}, 0
    for directory in DIRECTORIES:
        parent = contained(root, directory)
        for path in sorted(parent.rglob('*')) if parent.is_dir() else []:
            name = path.relative_to(root).as_posix()
            if EXCLUDED.intersection(Path(name).parts) or path.suffix in {'.pyc', '.pyo'}:
                continue
            contained(root, name)
            if not path.is_file():
                require(path.is_dir(), 'unsupported source entry: ' + name)
                continue
            length = path.stat().st_size; size += length
            require(length <= MAX_FILE and size <= MAX_TOTAL and len(files) < MAX_FILES, 'source witness exceeds finite bounds')
            files[name] = sha(path.read_bytes())
    for name in ROOT_FILES:
        path = contained(root, name)
        if name in {'VERSION', 'bundle.yml'}:
            require(path.is_file(), 'required release source is missing: ' + name)
        if path.is_file():
            size += path.stat().st_size
            require(path.stat().st_size <= MAX_FILE and size <= MAX_TOTAL and len(files) < MAX_FILES,
                    'source root file exceeds finite bounds')
            files[name] = sha(path.read_bytes())
    require(len({p.casefold() for p in files}) == len(files), 'source case aliases are not admitted')
    return files


def fingerprint(files, platform=None):
    # The updater's original exact byte order/algorithm, including optional roots.
    platform = platform or ('windows' if os.name == 'nt' else 'posix')
    require(platform in {'windows', 'posix'}, 'unsupported original fingerprint platform')
    ordering = PureWindowsPath if platform == 'windows' else PurePosixPath
    digest = hashlib.sha256()
    for directory in DIRECTORIES:
        for name in sorted((p for p in files if p.startswith(directory + '/')), key=ordering):
            digest.update(name.encode() + b'\0' + bytes.fromhex(files[name]))
    for name in ROOT_FILES:
        if name in files:
            digest.update(name.encode() + b'\0' + bytes.fromhex(files[name]))
    return digest.hexdigest()


def package_record(root, source_identity):
    """Packaging supplies actual expanded bytes, including generated guides/packs.

    This manifest is not a signature. Qualification/promotion authenticates its
    enclosing archive and exact producer before a caller can claim public origin.
    """
    files = inventory(root)
    return {'schemaVersion': 1, 'files': files, 'fileSetSha256': sha(encoded(files)),
            'releaseFingerprints': {platform: fingerprint(files, platform) for platform in ('windows', 'posix')},
            'sourceIdentity': source_identity,
            'components': {name: {path: value for path, value in files.items() if path.startswith(name + '/')}
                           for name in ('extensions/program-kit-governance', 'extensions/program-kit-building-blocks',
                                        'extensions/program-kit-dotnet', 'presets/program-kit-governance-preset',
                                        'workflows/program-kit-bootstrap')}}


def source_record(source, expected):
    root = filesystem(source); files = inventory(root)
    require(fingerprint(files) == expected, 'source differs from original release fingerprint')
    package = root / PACKAGED
    identity = {'kind': 'explicit-local-source', 'publicOriginEstablished': False}
    package_sha = None
    if package.is_file():
        require(package.stat().st_size <= 4 * 1_048_576, 'packaged source witness exceeds bounds')
        value = json.loads(package.read_bytes())
        require(value.get('schemaVersion') == 1 and value.get('files') == files
                and value.get('fileSetSha256') == sha(encoded(files)),
                'packaged source witness is partial or differs from actual release bytes')
        require(value == package_record(root, value.get('sourceIdentity')), 'packaged component inventory differs')
        identity = value['sourceIdentity']; package_sha = sha(package.read_bytes())
    return {'schemaVersion': 1, 'files': files, 'releaseInputsSha256': expected,
            'fingerprintPlatform': 'windows' if os.name == 'nt' else 'posix',
            'sourceIdentity': identity, 'packagedManifestSha256': package_sha,
            'originalLocation': str(Path(source).absolute()),
            'scope': 'Original exact source only; public origin requires verified enclosing publication. No local deviation or application acceptance is established.'}


def check_tree(source, record):
    require(inventory(source) == record['files'], 'existing source is partial or modified; recovery cannot conceal it')
    packaged = filesystem(source) / PACKAGED
    require((sha(packaged.read_bytes()) if packaged.is_file() else None) == record['packagedManifestSha256'],
            'original packaged source witness changed')


def reference(root, binding):
    require(isinstance(binding, dict) and set(binding) == {'record', 'sha256', 'releaseInputsSha256'}, 'invalid original witness binding')
    require(re.fullmatch('[a-f0-9]{64}', binding['sha256'] or '') is not None, 'invalid original witness digest')
    require(binding['record'] == '.program-kit/tooling-witnesses/sha256/' + binding['sha256'] + '/record.json',
            'witness record must use its exact owned address')
    path = contained(filesystem(root), binding['record'])
    require(path.is_file() and path.stat().st_size <= 4 * 1_048_576 and sha(path.read_bytes()) == binding['sha256'],
            'original witness record is missing or modified; retain the receipt and recover exact original evidence')
    record = json.loads(path.read_bytes())
    require(record.get('schemaVersion') == 1 and record.get('releaseInputsSha256') == binding['releaseInputsSha256']
            and isinstance(record.get('files'), dict) and 0 < len(record['files']) <= MAX_FILES,
            'original witness record has unsupported authority')
    require(fingerprint(record['files'], record.get('fingerprintPlatform')) == binding['releaseInputsSha256'],
            'original source inventory differs from receipt')
    for name, digest in record['files'].items():
        relative(name); require(re.fullmatch('[a-f0-9]{64}', digest or '') is not None, 'invalid original source hash')
    return path, record


def copy_original(source, destination, record):
    source = filesystem(source)
    require(not destination.exists(), 'witness destination already exists')
    # Preserve data inside one finite archive. Loose historical projects/props
    # must never enter consumer dependency/build discovery as active inputs.
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, expected in {**record['files'], **({PACKAGED: record['packagedManifestSha256']} if record['packagedManifestSha256'] else {})}.items():
            raw = contained(source, name).read_bytes()
            require(sha(raw) == expected, 'source changed while retaining witness: ' + name)
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); info.external_attr = 0o644 << 16
            archive.writestr(info, raw)
    with destination.open('r+b') as stream: stream.flush(); os.fsync(stream.fileno())
    check_tree(source, record); read_archive(destination, record)


def read_archive(path, record):
    require(path.is_file() and path.stat().st_size <= MAX_TOTAL + 8 * 1_048_576,
            'retained source archive is missing or exceeds bounds')
    expected = {**record['files'], **({PACKAGED: record['packagedManifestSha256']} if record['packagedManifestSha256'] else {})}
    result = {}; total = 0
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)) == len(expected) and set(names) == set(expected),
                    'retained source archive is partial or has unbound entries')
            for name in names:
                relative(name); entry = archive.getinfo(name)
                require(entry.file_size <= MAX_FILE and not entry.is_dir() and entry.compress_type == zipfile.ZIP_STORED,
                        'unsupported or oversized retained source entry')
                with archive.open(entry) as stream: raw = stream.read(MAX_FILE + 1)
                total += len(raw)
                require(len(raw) <= MAX_FILE and total <= MAX_TOTAL and sha(raw) == expected[name],
                        'retained source bytes differ from original witness: ' + name)
                result[name] = raw
    except (zipfile.BadZipFile, OSError) as error:
        raise ValueError('PKU145 retained source archive is partial or modified') from error
    return result


def retain(root, source, expected):
    root = filesystem(root); source = filesystem(source)
    require(not source.resolve().is_relative_to(root.resolve()), 'release witness source must be outside the consumer')
    record = source_record(source, expected); raw = encoded(record); digest = sha(raw)
    name = '.program-kit/tooling-witnesses/sha256/' + digest + '/record.json'
    path = contained(root, name)
    if path.parent.exists():
        require(path.is_file() and path.read_bytes() == raw, 'partial or changed retained witness; preserve and inspect it')
        read_archive(path.parent / 'source.zip', record)
    else:
        temporary = path.parent.with_name('.partial-' + uuid.uuid4().hex)
        temporary.mkdir(parents=True)
        copy_original(source, temporary / 'source.zip', record)
        (temporary / 'record.json').write_bytes(raw)
        temporary.rename(path.parent)
    return {'record': name, 'sha256': digest, 'releaseInputsSha256': expected}


def select(root, binding):
    path, record = reference(root, binding)
    original = filesystem(record['originalLocation'])
    if original.exists():
        check_tree(original, record)  # Never hide an existing edited/partial original.
    retained = path.parent / 'source.zip'; read_archive(retained, record)
    return {'status': 'original-and-retained' if original.exists() else 'retained-original-missing',
            'sourceArchive': str(retained), 'recordSha256': binding['sha256'],
            'publicOriginEstablished': False, 'applicationAcceptanceEstablished': False}


def recover(root, binding, candidate):
    path, record = reference(root, binding)
    original = filesystem(record['originalLocation'])
    if original.exists():
        check_tree(original, record)
    destination = path.parent / 'source.zip'
    require(not destination.exists(), 'retained source exists; modified/partial source requires explicit inspection, never overwrite')
    check_tree(candidate, record)
    temporary = path.parent / ('.recovery-' + uuid.uuid4().hex + '.zip')
    copy_original(candidate, temporary, record)
    temporary.rename(destination)
    event = {'schemaVersion': 1, 'recordSha256': binding['sha256'], 'candidateLocation': str(Path(candidate).absolute()),
             'candidateFingerprint': binding['releaseInputsSha256'], 'outcome': 'exact-original-recovered',
             'historicalReceiptRewritten': False, 'publicOriginEstablished': False}
    events = contained(filesystem(root), '.program-kit/tooling-witnesses/recovery'); events.mkdir(parents=True, exist_ok=True)
    (events / (uuid.uuid4().hex + '.json')).write_bytes(encoded(event))
    return select(root, binding)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'recover'))
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--receipt', required=True, help='Original project-relative installation/attempt receipt; never a newly invented fingerprint.')
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args(); root = filesystem(args.project_root)
    receipt = contained(root, args.receipt)
    require(receipt.is_file() and receipt.stat().st_size <= 8 * 1_048_576, 'original receipt is missing or exceeds bounds')
    value = json.loads(receipt.read_bytes()); binding = value.get('toolingWitness')
    require(binding is not None and value.get('releaseInputsSha256') == binding.get('releaseInputsSha256'),
            'receipt lacks an original bound witness; authenticate original release inputs before migration, never backfill history')
    require(args.action != 'recover' or args.candidate is not None, 'exact original --candidate is required for recovery')
    result = recover(root, binding, args.candidate) if args.action == 'recover' else select(root, binding)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

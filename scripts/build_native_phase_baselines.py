"""Capture immutable installer source hashes for the supported migration lineage.

These hashes authenticate installed toolkit sources; they define no consumer wire
schema, dependency profile, release acceptance or publication authority.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'extensions/program-kit-governance/references/native-phase-source-baselines.json'
COMPONENTS = (
    ('extensions', 'program-kit-governance', 'extension.yml'),
    ('extensions', 'program-kit-building-blocks', 'extension.yml'),
    ('extensions', 'program-kit-dotnet', 'extension.yml'),
    ('presets', 'program-kit-governance-preset', 'preset.yml'),
    ('workflows', 'program-kit-bootstrap', 'workflow.yml'))


def capture(root, reference):
    """Exact Git bytes and the historical Windows checkout representation."""
    commit = subprocess.run(['git', 'rev-parse', reference + '^{commit}'], cwd=root,
                            capture_output=True, check=True, text=True).stdout.strip()
    directories = subprocess.run(['git', 'ls-tree', '-d', '--name-only', commit, 'extensions', 'presets', 'workflows'],
                                 cwd=root, capture_output=True, check=True, text=True).stdout.splitlines()
    archive = subprocess.run(['git', 'archive', '--format=zip', commit, *directories],
                             cwd=root, capture_output=True, check=True).stdout
    components = []
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        for kind, identity, manifest_name in COMPONENTS:
            prefix = kind + '/' + identity + '/'
            source = {name[len(prefix):]: package.read(name) for name in package.namelist()
                      if name.startswith(prefix) and not name.endswith('/')}
            if manifest_name not in source:
                continue
            version = yaml.safe_load(source[manifest_name])[kind[:-1]]['version']
            for encoding in ('git-bytes', 'windows-text-crlf'):
                def payload(raw, name):
                    if encoding == 'windows-text-crlf' and Path(name).suffix not in {'.pack', '.zip', '.png', '.jpg'}:
                        try:
                            raw.decode('utf-8')
                            if b'\x00' not in raw:
                                return raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
                        except UnicodeError:
                            pass
                    return raw
                files = {name: hashlib.sha256(payload(raw, name)).hexdigest() for name, raw in sorted(source.items())}
                components.append({'kind': kind, 'id': identity, 'version': str(version),
                    'manifestSha256': files[manifest_name], 'sourceCommit': commit, 'sourceEncoding': encoding,
                    'files': files})
    return components


def validate_previous(root, table=None):
    """Packaging must carry an exact original for its immediate supported predecessor.

    This is a local source check, not a network lookup or permission to admit a
    component assembled from individually matching files across witnesses.
    """
    from native_phase_ownership import machine_source_path
    history = json.loads((root / 'releases/history.json').read_text(encoding='utf-8'))
    current = (root / 'VERSION').read_text(encoding='utf-8').strip()
    entry = next(row for row in history['entries'] if row['version'] == current)
    previous = entry['previous']
    if previous is None:
        return
    if table is None:
        table = json.loads((root / OUTPUT.relative_to(ROOT)).read_text(encoding='utf-8'))
    rows = table['components']
    try:
        originals = capture(root, 'v' + previous)
    except subprocess.CalledProcessError as error:
        raise ValueError('Previous-release source history is unavailable: v' + previous
                         + '; fetch the supported release tag and its commit before packaging') from error
    for expected in originals:
        if expected['sourceEncoding'] != 'git-bytes':
            continue
        identity = ('kind', 'id', 'version', 'manifestSha256', 'sourceCommit')
        files = {name: sha for name, sha in expected['files'].items() if machine_source_path(name)}
        if not any(all(row.get(key) == expected[key] for key in identity)
                   and {name: sha for name, sha in row.get('files', {}).items() if machine_source_path(name)} == files
                   for row in rows):
            raise ValueError('Missing exact previous-release native source witness: '
                             + expected['id'] + ' ' + previous
                             + '; regenerate scripts/build_native_phase_baselines.py before packaging')


def build():
    history = json.loads((ROOT / 'releases/history.json').read_text(encoding='utf-8'))
    current = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    references = ['v' + entry['version'] for entry in history['entries'] if entry['version'] != current]
    references.extend(('v0.14.3',  # Last workflow-bearing stable release; retained only for safe removal.
                       '711293b2dda187616891df11fe760a3d5d0cf5f5',
                       '4b90dc7ea6458fc2fbd6a5ae7e35c552426ad9e8'))
    # Previously recorded source witnesses are immutable. New exact captures append;
    # regeneration must never replace an older row or reorder its historical inputs.
    components = json.loads(OUTPUT.read_text(encoding='utf-8'))['components'] if OUTPUT.is_file() else []
    for reference in references:
        for row in capture(ROOT, reference):
            if row not in components:
                components.append(row)
    value = {'schemaVersion': 1, 'supportedFrom': history['supportedFrom'],
             'authorityScope': 'Immutable source-byte witnesses for installer ownership; no publication or consumer authority.',
             'components': components}
    OUTPUT.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Captured {len(components)} native component witnesses: {OUTPUT}')


if __name__ == '__main__':
    build()

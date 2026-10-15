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


def build():
    history = json.loads((ROOT / 'releases/history.json').read_text(encoding='utf-8'))
    references = ['v' + entry['version'] for entry in history['entries']]
    references.append('711293b2dda187616891df11fe760a3d5d0cf5f5')
    components = []
    for reference in references:
        commit = subprocess.run(['git', 'rev-parse', reference + '^{commit}'], cwd=ROOT,
                                capture_output=True, check=True, text=True).stdout.strip()
        archive = subprocess.run(['git', 'archive', '--format=zip', commit, 'extensions', 'presets'],
                                 cwd=ROOT, capture_output=True, check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            for kind, identity, manifest_name in (
                ('extensions', 'program-kit-governance', 'extension.yml'),
                ('extensions', 'program-kit-building-blocks', 'extension.yml'),
                ('extensions', 'program-kit-dotnet', 'extension.yml'),
                ('presets', 'program-kit-governance-preset', 'preset.yml')):
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
    value = {'schemaVersion': 1, 'supportedFrom': history['supportedFrom'],
             'authorityScope': 'Immutable source-byte witnesses for installer ownership; no publication or consumer authority.',
             'components': components}
    OUTPUT.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Captured {len(components)} native component witnesses: {OUTPUT}')


if __name__ == '__main__':
    build()

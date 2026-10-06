"""Verify an application handoff with Python's standard library, outside its source/toolkit."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path


def verify(path: Path, *, allow_draft: bool = False) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        seen = set()
        for info in archive.infolist():
            name = info.filename
            if (not name or '\\' in name or ':' in name or name.startswith('/')
                    or any(p in {'', '.', '..'} or p.endswith(('.', ' ')) for p in name.split('/'))
                    or any(ord(c) < 32 for c in name)
                    or any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.I) for p in name.split('/'))
                    or name.casefold() in seen or stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1):
                raise ValueError('PKH002 unsafe receiver archive entry')
            seen.add(name.casefold())
        if sum(i.file_size for i in archive.infolist()) > 1024*1024*1024:
            raise ValueError('PKH002 oversized archive')
        index = json.loads(archive.read('index.json'))
        if index.get('schemaVersion') != 1 or index.get('status') not in {'ready', 'incomplete'}:
            raise ValueError('PKH012 invalid receiver index')
        if not allow_draft and (index['status'] != 'ready' or index['missing']):
            raise ValueError('PKH011 incomplete handoff is not receiver-ready')
        rows = index['files']
        if len({x['path'] for x in rows}) != len(rows) or set(names) != {'index.json'} | {x['path'] for x in rows}:
            raise ValueError('PKH012 receiver inventory mismatch')
        for row in rows:
            if hashlib.sha256(archive.read(row['path'])).hexdigest() != row['sha256']:
                raise ValueError('PKH012 receiver hash mismatch: '+row['path'])
        bundle = json.loads(archive.read(index['bundle']))
        if bundle['application'] != index['application'] or bundle['hostImage'] != index['hostImage']:
            raise ValueError('PKH008 receiver bundle identity mismatch')
        paths = {x['path'] for x in rows}
        if any(x['path'] not in paths for x in list(index['packages'].values())+list(index['contracts'].values())):
            raise ValueError('PKH009 unresolved receiver reference')
        for category in index['categories'].values():
            if any('inputs/'+name not in paths for name in category['files']):
                raise ValueError('PKH009 unresolved category reference')
        return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--allow-draft', action='store_true')
    args = parser.parse_args()
    try:
        index = verify(args.archive, allow_draft=args.allow_draft)
        print(index['application']['id']+' '+index['application']['version']+': '+index['status']+'; all receiver hashes verified')
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        parser.exit(2, str(error)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())

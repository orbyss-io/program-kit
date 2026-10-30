"""Verify an application handoff with Python's standard library, outside its source/toolkit."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
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
        if sum(i.file_size for i in archive.infolist()) > 2*1024*1024*1024 or len(names)>100000:
            raise ValueError('PKH002 oversized archive')
        raw_index=archive.read('index.json')
        if len(raw_index)>2097152:raise ValueError('PKH012 oversized receiver index')
        index = json.loads(raw_index)
        if index.get('schemaVersion') not in (1,2) or type(index.get('schemaVersion')) is not int or index.get('status') not in {'ready', 'incomplete'}:
            raise ValueError('PKH012 invalid receiver index')
        if index['schemaVersion']==1 and set(index)!={'schemaVersion','status','missing','application','hostImage','bundle','components','packages','contracts','categories','files'}:
            raise ValueError('PKH012 schema1 cannot carry receiver2 authority fields')
        if not allow_draft and (index['status'] != 'ready' or index['missing']):
            raise ValueError('PKH011 incomplete handoff is not receiver-ready')
        rows = index['files']
        if len({x['path'] for x in rows}) != len(rows) or set(names) != {'index.json'} | {x['path'] for x in rows}:
            raise ValueError('PKH012 receiver inventory mismatch')
        for row in rows:
            hashed=hashlib.sha256()
            with archive.open(row['path']) as stream:
                for block in iter(lambda:stream.read(65536),b''):hashed.update(block)
            if hashed.hexdigest() != row['sha256']:
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
        if index['schemaVersion']==2:
            helper=Path(__file__).with_name('handoff_contract.py')
            if not helper.is_file():raise ValueError('PKH012 receiver2 requires its retained handoff_contract.py verifier')
            expected_helper=next((row['sha256'] for row in rows if row['path']=='handoff_contract.py'),None)
            if expected_helper is None or hashlib.sha256(helper.read_bytes()).hexdigest()!=expected_helper:
                raise ValueError('PKH012 receiver2 helper differs from retained verifier bytes')
            spec=importlib.util.spec_from_file_location('receiver_authority',helper)
            kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)
            index=kernel.loads(raw_index.decode('utf-8-sig'))
            kernel.verify_receiver_settings(archive,index,bundle,allow_draft=allow_draft)
        else:
            for category in index['categories'].values():
                for name in category['files'] if category is index['categories']['settings'] else []:
                    if json.loads(archive.read('inputs/'+name)).get('schemaVersion')==2:
                        raise ValueError('PKH012 settings authority2 cannot be downgraded to receiver1')
            for row in index['packages'].values():
                if row.get('settingsDescriptor'):
                    import io
                    with zipfile.ZipFile(io.BytesIO(archive.read(row['path']))) as package:
                        if json.loads(package.read(row['settingsDescriptor'])).get('schemaVersion')==2:
                            raise ValueError('PKH012 package authority2 cannot be downgraded to receiver1')
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

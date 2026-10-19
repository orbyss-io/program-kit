"""Bounded logical source assets, loose or packed; no code loading or implicit extraction."""
from pathlib import Path
import base64
import hashlib
import json
import re

PACK='.program-kit-sources.json'
ROOTS={'examples','templates/ui-experience','references/examples','references/release-guidance'}


def require(condition,message):
    if not condition:raise ValueError('PKU143 '+message)


def safe(relative):
    require(isinstance(relative,str) and re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*',relative)
            and not {'.','..'}&set(relative.split('/')),'unsafe logical source path')
    return relative


def packed(component):
    path=component/PACK
    if not path.exists():return {}
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=8_388_608,'missing/aliased/oversized source asset pack')
    def unique(pairs):
        value={}
        for key,item in pairs:
            require(key not in value,'duplicate source pack member');value[key]=item
        return value
    value=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique)
    require(isinstance(value,dict) and set(value)=={'schemaVersion','files'} and type(value['schemaVersion']) is int
            and value['schemaVersion']==1 and isinstance(value['files'],dict) and 0<len(value['files'])<=256,
            'unsupported source asset pack')
    result={};total=0
    require(len({name.casefold() for name in value['files']})==len(value['files']),'case-colliding logical source assets')
    for relative,record in value['files'].items():
        safe(relative)
        require(not {'.git','bin','obj','node_modules','__pycache__','.composed','.dev-cache'}&set(Path(relative).parts)
                and Path(relative).suffix not in ('.pyc','.pyo'),'source pack cannot contain generated caches')
        require(any(relative.startswith(root+'/') for root in ROOTS),'source pack cannot replace executable owner scripts or manifests')
        require(isinstance(record,dict) and set(record)=={'sha256','base64'} and isinstance(record['sha256'],str)
                and re.fullmatch('[0-9a-f]{64}',record['sha256']) and isinstance(record['base64'],str),'invalid source asset identity')
        data=base64.b64decode(record['base64'],validate=True);total+=len(data)
        require(len(data)<=1_048_576 and total<=4_194_304 and hashlib.sha256(data).hexdigest()==record['sha256'],
                'source asset bytes differ from their original identity or exceed their bound')
        target=component/relative
        require(not target.exists(),'loose and packed source assets collide; preserve both for reconciliation')
        result[relative]=data
    return result


def owner(path):
    for component in path.parents:
        if (component/PACK).is_file():
            require((component/'extension.yml').is_file(),'source pack has no native extension owner')
            return component
    return None


def read(path):
    """Read original bytes; never create a file or execute a packed source."""
    path=Path(path)
    component=owner(path)
    if component is None:return path.read_bytes()
    for entry in (path,*path.parents):
        if entry==component:break
        require(not entry.is_symlink() and not getattr(entry,'is_junction',lambda:False)(),'aliased logical source asset')
    relative=path.relative_to(component).as_posix()
    values=packed(component)
    return values[relative] if relative in values else path.read_bytes()


def tree(directory):
    """Read a complete finite logical subtree, preserving exact filenames and bytes."""
    directory=Path(directory)
    component=owner(directory/'placeholder')
    excluded={'.git','bin','obj','node_modules','__pycache__','.composed','.dev-cache'}
    result={file.relative_to(directory).as_posix():file.read_bytes() for file in directory.rglob('*')
            if file.is_file() and not excluded&set(file.relative_to(directory).parts) and file.suffix not in ('.pyc','.pyo')}
    if component:
        prefix=directory.relative_to(component).as_posix()+'/'
        for relative,data in packed(component).items():
            if relative.startswith(prefix):result[relative[len(prefix):]]=data
    require(len(result)<=256,'logical source subtree exceeds finite capacity')
    return result


def encoded(files):
    """Maintainer packaging representation; logical source bytes stay identical."""
    value={'schemaVersion':1,'files':{safe(name):{'sha256':hashlib.sha256(data).hexdigest(),
            'base64':base64.b64encode(data).decode('ascii')} for name,data in sorted(files.items())}}
    raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    require(len(raw)<=8_388_608,'source pack exceeds its finite byte capacity')
    return raw


def main():
    import argparse
    import uuid
    parser=argparse.ArgumentParser(description='Export exact optional source assets to a new owned artifact directory; no execution or tool acquisition.')
    parser.add_argument('--repository',type=Path,default=Path.cwd())
    parser.add_argument('--component',required=True,choices=('program-kit-governance','program-kit-dotnet'))
    parser.add_argument('--subtree',required=True)
    args=parser.parse_args()
    relative=safe(args.subtree)
    require(any(relative==root or relative.startswith(root+'/') for root in ROOTS),'select one supported optional source subtree')
    root=args.repository.resolve()
    component=root/'.specify/extensions'/args.component
    require(component.is_dir() and component.resolve().is_relative_to(root),'co-installed component is unavailable')
    files=tree(component/relative)
    require(files,'optional source subtree is unavailable')
    output=root/'artifacts/program-kit/source-assets'/uuid.uuid4().hex
    require(output.resolve().is_relative_to(root),'source export escaped the repository')
    for entry in output.parents:
        if entry==root:break
        require(not entry.is_symlink() and not getattr(entry,'is_junction',lambda:False)(),'source export has an aliased parent')
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        safe(name);target=output/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
    print(str(output))
    return 0


if __name__=='__main__':raise SystemExit(main())

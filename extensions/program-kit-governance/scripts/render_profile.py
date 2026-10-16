"""Original native generation inputs; historical rendering never probes an old executable."""
from __future__ import annotations
from contextlib import contextmanager, nullcontext
import hashlib
import json
import os
from pathlib import Path
import re
import platform
import sys
import uuid
from unittest.mock import patch


class RenderProfileError(ValueError):
    pass


def require(condition,message):
    if not condition:raise RenderProfileError('PKU142 '+message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def inside(root,relative):
    require(isinstance(relative,str) and relative and not Path(relative).is_absolute()
            and not re.match(r'^[A-Za-z]:',relative) and '\\' not in relative
            and not {'.','..'}&set(relative.split('/')),'unsafe native render profile path')
    path=root/relative
    require(path.resolve().is_relative_to(root.resolve()),'native render profile escaped its owner')
    for item in (path,*path.parents):
        if item==root:break
        require(not item.is_symlink() and not getattr(item,'is_junction',lambda:False)(),'aliased native render profile input')
    return path


def read(path):
    require(path.is_file() and path.stat().st_size<=8_388_608,'missing or oversized original native render profile')
    def unique(pairs):
        value={}
        for name,item in pairs:
            require(name not in value,'duplicate original render profile field')
            value[name]=item
        return value
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique,
                      parse_constant=lambda _:require(False,'nonfinite render input'))


def producer():
    """Bind the actual installed native producer and its bundled template inputs."""
    import specify_cli
    root=Path(specify_cli.__file__).parent
    files={file.relative_to(root).as_posix():sha(file.read_bytes()) for file in sorted(root.rglob('*'))
           if file.is_file() and '__pycache__' not in file.parts and file.suffix not in ('.pyc','.pyo')}
    require(files and len(files)<=4096,'unsupported native producer input inventory')
    return {'kind':'installed-specify-cli-tree','files':files,'platform':platform.system(),'osName':os.name,
            'pythonImplementation':sys.implementation.name,'pythonVersion':list(sys.version_info[:3])}


def outputs(root):
    """Discover native-owned output surfaces; only writes during this call are captured."""
    candidates=set()
    for manifest in (root/'.specify/integrations').glob('*.manifest.json'):
        candidates.update(read(manifest).get('files',{}))
    from specify_cli.agents import CommandRegistrar
    registrar=CommandRegistrar(root)
    from specify_cli import _get_skills_dir
    state=root/'.specify/integration.json'
    keys=set()
    if state.is_file():
        data=read(state)
        keys.update(data.get('installed_integrations',[]))
        keys.update(key for key in (data.get('integration'),data.get('default_integration')) if key)
    registry=root/'.specify/extensions/.registry'
    if registry.is_file():
        for entry in read(registry).get('extensions',{}).values():keys.update(entry.get('registered_commands',{}))
    for agent in keys:
        require(agent in registrar.AGENT_CONFIGS,'unsupported native render integration')
        for directory in (registrar._resolve_agent_dir(agent,registrar.AGENT_CONFIGS[agent],root),_get_skills_dir(root,agent)):
            require(directory.resolve().is_relative_to(root.resolve()),'external native output needs explicit generation owner')
            candidates.update(file.relative_to(root).as_posix() for file in directory.rglob('*') if file.is_file())
    candidates.update(file.relative_to(root).as_posix() for file in (root/'.github/prompts').glob('*.md'))
    require(len(candidates)<=4096,'native output inventory exceeds finite profile capacity')
    result={}
    for relative in candidates:
        file=inside(root,relative)
        if file.is_file():result[relative]=(sha(file.read_bytes()),file.stat().st_mtime_ns)
    return result


def history(root):
    directory=inside(root,'.specify/program-kit/render-profiles')
    head=directory/'head.json'
    if not head.exists():
        require(not directory.exists() or not list(directory.iterdir()),'render history lost its original head; preserve and reconcile it')
        return [],None
    link=read(head)
    records=[];seen=set()
    while link is not None:
        require(isinstance(link,dict) and set(link)=={'path','sha256'} and isinstance(link['sha256'],str)
                and re.fullmatch('[0-9a-f]{64}',link['sha256']) and link['path'] not in seen and len(records)<4096,
                'invalid/cyclic or exhausted original render history')
        path=inside(root,link['path'])
        require(path.parent==directory and path.is_file() and sha(path.read_bytes())==link['sha256'],'original render profile changed or disappeared')
        record=read(path)
        require(type(record.get('schemaVersion')) is int and record['schemaVersion']==1
                and record.get('kind')=='native-generation-profile' and record.get('status')=='succeeded'
                and isinstance(record.get('outputs'),dict),'unsupported original native generation profile')
        records.append(record);seen.add(link['path']);link=record['previous']
    require({file.name for file in directory.iterdir()}=={'head.json',*(Path(name).name for name in seen)},
            'render history contains detached/partial records; preserve and reconcile the original chain')
    return records,read(head)


def generation_inputs(root):
    """Retain original native generation source hashes for attribution, without widening later scope."""
    result={}
    for relative in ('.specify/init-options.json','.specify/integration.json'):
        file=inside(root,relative)
        if file.is_file():result[relative]=sha(file.read_bytes())
    for relative in ('.specify/templates','.specify/extensions','.specify/presets'):
        for file in inside(root,relative).rglob('*'):
            parts=file.relative_to(root).parts
            if file.is_file() and not {'__pycache__','.composed','.dev-cache','node_modules','bin','obj'}&set(parts):
                if file.suffix in ('.md','.yml','.yaml','.py','.json'):
                    result[file.relative_to(root).as_posix()]=sha(file.read_bytes())
    require(len(result)<=8192,'native generation source inventory exceeds its finite capacity')
    return result


class Reader:
    """One immutable inspection snapshot; do not reuse it across native mutations."""
    def __init__(self,root):
        self.root=Path(root).resolve()
        self.records,_=history(self.root)
        self.producer=producer() if self.records else None

    def profile(self,relative):
        inside(self.root,relative)
        record=next((record for record in self.records if relative in record['outputs']),None)
        if record is None:return None
        require(record['producer']==self.producer,'historical native producer changed; retain its exact original producer for reconciliation')
        choice=record['pythonInterpreter']
        require(choice is None or isinstance(choice,str) and 0<len(choice)<=4096 and '\n' not in choice and '\r' not in choice
                and '\x00' not in choice,'unsupported historical interpreter literal')
        require(isinstance(record['outputs'][relative],str) and re.fullmatch('[0-9a-f]{64}',record['outputs'][relative]),
                'invalid original rendered output identity')
        return {'interpreter':choice,'sha256':record['outputs'][relative]}


def profile(root,relative):
    return Reader(root).profile(relative)


@contextmanager
def rendering(root,relative):
    """Only pure native rendering uses the recorded selection; never execute it."""
    value=profile(root,relative)
    from specify_cli.integrations.base import IntegrationBase
    with (patch.object(IntegrationBase,'resolve_python_interpreter',return_value=value['interpreter'])
          if value and value['interpreter'] is not None else nullcontext()):
        yield value


@contextmanager
def writer(root):
    lock=inside(root,'.program-kit/native-render.lock')
    lock.parent.mkdir(parents=True,exist_ok=True)
    try:stream=lock.open('xb')
    except FileExistsError as error:
        raise RenderProfileError('PKU142 native generation already owned or interrupted; inspect the original lock and stopped process before recovery') from error
    identity=(stream.fileno(),lock.stat().st_ino)
    try:
        stream.write(canonical({'pid':os.getpid(),'scope':'native generation profile writer'}));stream.flush();os.fsync(stream.fileno())
        yield
    finally:
        stream.close()
        require(lock.is_file() and lock.stat().st_ino==identity[1],'native generation lock changed; preserve it for reconciliation')
        lock.unlink()


@contextmanager
def capture(root,arguments):
    """Observe a real successful native CLI call, without changing its resolver."""
    root=Path(root).resolve()
    # Read-only/catalog invocations must not create installation evidence.
    mutation=bool(arguments) and not {'--help','--version'}&set(arguments) and (arguments[0]=='init' or len(arguments)>1 and
        (arguments[0],arguments[1]) in {('extension','add'),('extension','update'),('extension','remove'),
            ('preset','add'),('preset','remove'),('preset','update'),('integration','install'),('integration','upgrade'),
            ('integration','use'),('bundle','install'),('bundle','update')})
    if not mutation:
        yield
        return
    from specify_cli.integrations.base import IntegrationBase
    with writer(root):
        _,previous=history(root)
        before=outputs(root)
        original=IntegrationBase.resolve_python_interpreter
        original_producer=producer()
        choices=set()
        def observe(project_root=None):
            value=original(project_root)
            require(project_root is None or Path(project_root).samefile(root),'generation root differs from recorded native CLI root')
            choices.add(value)
            return value
        succeeded=False
        try:
            with patch.object(IntegrationBase,'resolve_python_interpreter',side_effect=observe):yield
            succeeded=True
        except SystemExit as error:
            succeeded=error.code in (None,0)
            raise
        finally:
            if succeeded:
                after=outputs(root)
                changed={relative:value[0] for relative,value in after.items() if before.get(relative)!=value}
                if changed:
                    require(len(choices)<=1,'ambiguous native interpreter choices; no historical profile manufactured')
                    require(history(root)[1]==previous,'native render history changed during generation')
                    require(producer()==original_producer,'native producer changed during generation')
                    directory=inside(root,'.specify/program-kit/render-profiles');directory.mkdir(parents=True,exist_ok=True)
                    value={'schemaVersion':1,'kind':'native-generation-profile','status':'succeeded','previous':previous,
                           'producer':original_producer,'captureSha256':sha(Path(__file__).read_bytes()),
                           'sourceSha256':generation_inputs(root),
                           'pythonInterpreter':next(iter(choices)) if choices else None,'outputs':changed,
                           'operation':arguments[:2],'scope':'Observed native generation, not current executable readiness'}
                    target=directory/(uuid.uuid4().hex+'.json')
                    with target.open('xb') as stream:stream.write(canonical(value));stream.flush();os.fsync(stream.fileno())
                    link={'path':target.relative_to(root).as_posix(),'sha256':sha(target.read_bytes())}
                    temporary=directory/(uuid.uuid4().hex+'.tmp')
                    with temporary.open('xb') as stream:stream.write(canonical(link));stream.flush();os.fsync(stream.fileno())
                    temporary.replace(directory/'head.json')

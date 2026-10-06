"""Consumer identity and contained reference helpers. No toolkit/runtime initialization."""
from __future__ import annotations
import base64
import hashlib
import gzip
import io
import json
import math
import re
import stat
import tarfile
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

DECLARATION = 'eng/application-handoff.json'
CATEGORIES = {'documentation', 'runtime', 'settings', 'assets', 'migrations'}
SETTINGS_MEMBER = 'orbyss-foundation/settings.json'
MAX_METADATA = 2_097_152
MAX_ASSEMBLY = 268_435_456
HOST_SCOPES = {'host-transport','host-boot','host-cshells-binding','host-nuplane-binding'}


def finite_graph(value, *, max_nodes=4096) -> None:
    """Admit a static JSON graph before encoding or recursively retaining its children."""
    remaining = max_nodes
    def visit(item, depth):
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 16:
            raise ValueError('PKH007 settings graph exceeds admitted depth/node limit')
        if item is None or type(item) in (bool, int):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError('PKH007 nonfinite settings number')
        elif isinstance(item, str):
            if len(item) > 16384:
                raise ValueError('PKH007 setting string exceeds admitted limit')
        elif isinstance(item, (list, dict)):
            if len(item) > 256:
                raise ValueError('PKH007 settings graph exceeds admitted field/item limit')
            if isinstance(item, dict):
                if any(not isinstance(k, str) or not k or len(k) > 4096 for k in item):
                    raise ValueError('PKH007 invalid settings graph key')
                children = item.values()
            else:
                children = item
            for child in children:
                visit(child, depth+1)
        else:
            raise ValueError('PKH007 unsupported settings value')
    visit(value, 0)


def reject_secret_constraint_values(value, secret=False) -> None:
    """Schema descriptions may name secret children but never carry their values."""
    if isinstance(value,dict):
        secret=secret or value.get('secret') is True
        if secret and {'default','example','examples','const','enum'} & value.keys():
            raise ValueError('PKH006 secret settings cannot export defaults or examples')
        for child in value.values():reject_secret_constraint_values(child,secret)
    elif isinstance(value,list):
        for child in value:reject_secret_constraint_values(child,secret)


def validate_settings_metadata(value: dict) -> None:
    fields = {'schemaVersion','owner','scope','complete','sources','settings','semanticConstraints'}
    if isinstance(value,dict) and value.get('schemaVersion')==2:
        fields.add('appliesTo')
        if 'typeName' in value:fields.add('typeName')
    if (not isinstance(value, dict) or set(value) != fields or type(value['schemaVersion']) is not int
            or value['schemaVersion'] not in (1,2) or type(value['complete']) is not bool):
        raise ValueError('PKH007 invalid settings metadata envelope')
    if value['schemaVersion']==2:
        if 'typeName' in value and (not isinstance(value['typeName'],str) or not value['typeName'].strip() or len(value['typeName'])>4096):
            raise ValueError('PKH007 invalid named settings type identity')
        applicability=value['appliesTo']
        if (not isinstance(applicability,dict) or set(applicability)!={'kind','features','configuration'}
                or applicability['kind'] not in ('shell','host','code')):
            raise ValueError('PKH007 invalid settings applicability')
        for key in ('features','configuration'):
            items=applicability[key]
            if (not isinstance(items,list) or len(items)>128 or len(set(items))!=len(items)
                    or any(not isinstance(x,str) or not x.strip() or len(x)>4096 for x in items)):
                raise ValueError('PKH007 invalid settings applicability selectors')
        if applicability['kind']=='shell' and not (applicability['features'] or applicability['configuration']):
            raise ValueError('PKH007 shell settings require actual activation/configuration selectors')
    for key in ('owner','scope'):
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > 4096:
            raise ValueError('PKH007 settings owner/scope required')
    sources=value['sources']
    if not isinstance(sources,dict) or not 1 <= len(sources) <= 512:
        raise ValueError('PKH007 settings require 1 to 512 source hashes')
    for name, expected in sources.items():
        safe_name(name); sha256_value(expected)
    if (not isinstance(value['settings'],list) or len(value['settings'])>256
            or not isinstance(value['semanticConstraints'],list) or len(value['semanticConstraints'])>128
            or any(not isinstance(x,str) or not x or len(x)>4096 for x in value['semanticConstraints'])):
        raise ValueError('PKH007 settings or semantic constraints exceed admitted limit')
    seen=set(); setting_fields={'path','type','required','secret','constraints','binding','precedence','reload','description'}
    types={'string':str,'integer':int,'number':(int,float),'boolean':bool,'array':list,'object':dict}
    for item in value['settings']:
        if not isinstance(item,dict) or not setting_fields <= set(item) or set(item)-setting_fields-{'default'}:
            raise ValueError('PKH007 invalid setting metadata fields')
        if (not isinstance(item['path'],str) or not item['path'] or item['path'].casefold() in seen
                or item['type'] not in types or type(item['required']) is not bool or type(item['secret']) is not bool
                or item['reload'] not in ('restart','reload','immutable') or not isinstance(item['constraints'],dict)
                or not isinstance(item['precedence'],list) or not 1 <= len(item['precedence']) <= 128
                or any(not isinstance(x,str) or not x.strip() or len(x)>4096 for x in item['precedence'])
                or any(not isinstance(item[k],str) or not item[k].strip() or len(item[k])>4096 for k in ('path','binding','description'))):
            raise ValueError('PKH007 invalid or conflicting setting metadata')
        finite_graph(item['constraints'])
        reject_secret_constraint_values(item['constraints'],item['secret'])
        if len(json.dumps(item['constraints'],ensure_ascii=False).encode('utf-8'))>16384:
            raise ValueError('PKH007 constraints exceed admitted limit')
        seen.add(item['path'].casefold())
        if item['secret'] and ('default' in item or {'default','example','examples','const','enum'} & item['constraints'].keys()):
            raise ValueError('PKH006 secret settings cannot export defaults or examples')
        if 'default' in item:
            default=item['default']; finite_graph(default)
            nullable=value['schemaVersion']==2 and item['constraints'].get('nullable') is True
            if default is None and nullable:
                continue
            if not isinstance(default,types[item['type']]) or (item['type'] in ('integer','number') and isinstance(default,bool)):
                raise ValueError('PKH007 default differs from declared setting type')


def sha256_value(value: str) -> str:
    if not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{64}',value):
        raise ValueError('PKH007 invalid SHA256 authority binding')
    return value


def has_jwt_material(text: str) -> bool:
    """Scan tokens once for JSON algorithm headers or oversized encoded-object candidates."""
    for candidate in re.finditer(r'[A-Za-z0-9_.-]+',text):
        start,end=candidate.span()
        first=text.find('.',start,end)
        if first<start+2:
            continue
        second=text.find('.',first+1,end)
        if second<=first+1 or text.find('.',second+1,end)!=-1:
            continue
        oversized=first-start>4096
        if oversized and second+1==end:
            continue
        header=text[start:min(first,start+4096)]
        try:
            raw=base64.b64decode(header+'='*(-len(header)%4),altchars=b'-_',validate=True)
            if oversized:
                # A three-segment encoded object cannot bypass credential admission
                # by exceeding the finite header parser. Never decode the full token.
                prefix=raw.lstrip()
                if not prefix or prefix.startswith(b'{'):
                    return True
                continue
            value=loads(raw.decode('utf-8'))
        except (ValueError,UnicodeError,RecursionError):
            continue
        if isinstance(value,dict) and isinstance(value.get('alg'),str) and value['alg'].strip():
            return True
    return False


def secret_source_placeholder(key: str, value: str) -> bool:
    """Admit explicit fictitious source references in prose, never JSON secret values/defaults."""
    if len(value)>256:
        return False
    kind={'password':'password','clientsecret':'client-secret','apikey':'api-key','accesstoken':'access-token'}[
        re.sub(r'[_-]','',key.casefold())]
    source=r'(?:user-secrets|keyvault|environment-variables)'
    return re.fullmatch('your-'+kind+'-from-'+source+'(?:-or-'+source+'){0,2}',value) is not None


def fictional_connection_template(text: str, assignment) -> bool:
    """Recognize only the complete fixed fictional C# sample around this assignment span."""
    sample='Host=myserver;Username=mylogin;Password=mypass;Database=mydatabase'
    literal='"'+sample+'"'
    start=assignment.start()-sample.index('Password=')-1
    if start<0 or not text.startswith(literal,start):
        return False
    before=start-1
    if before>=0 and text[before]=='@':
        before-=1
    for _ in range(256):
        if before<0 or text[before] not in ' \t':
            break
        before-=1
    if before<0 or text[before] not in '=(':
        return False
    if text[before]=='(':
        # A method's first argument is supported; grouping and JSON array
        # elements cannot claim this C# literal context.
        cursor=before-1
        while cursor>=max(0,before-256) and text[cursor] in ' \t':
            cursor-=1
        end=cursor+1
        while cursor>=max(0,before-256) and text[cursor] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_':
            cursor-=1
        if cursor+1==end or not (text[cursor+1].isalpha() or text[cursor+1]=='_'):
            return False
    after=start+len(literal)
    for _ in range(256):
        if after==len(text) or text[after] not in ' \t\r\n':
            break
        after+=1
    return after<len(text) and text[after] in ';),'


def reject_secrets(payload: bytes, name: str) -> None:
    """Reject credential shapes; prose alone is not a token and explicit source placeholders hold no value."""
    text=payload.decode('utf-8-sig',errors='replace')
    token=r'[A-Za-z0-9._~+/-]+=*'
    bearer=(re.search(r'(?im)\bAuthorization[\x22\x27]?[ \t]*[:=]\s*[\x22\x27]?Bearer\s+'+token,text)
            or re.search(r'(?im)(?<![A-Za-z0-9_-])[A-Za-z_][A-Za-z0-9_-]*[\x22\x27]?[ \t]*[:=][ \t]*[\x22\x27]?Bearer[ \t]+'
                         +token+r'(?=[ \t]*(?:[\x22\x27`,;}\]#\r\n]|$))',text)
            or re.search(r'(?im)^[ \t]*Bearer\s+'+token+r'[ \t]*\r?$',text)
            or re.search(r'(?i)([\x22\x27`])Bearer\s+'+token+r'\1',text))
    if (bearer or has_jwt_material(text)
            or re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|https?://[^\s/:]+:[^\s/@]+@',text)):
        raise ValueError('PKH006 credential material in '+name)
    for assignment in re.finditer(r'(?im)\b(password|clientsecret|api[_-]?key|access[_-]?token)\s*[:=]\s*'
                                  r'([\x22\x27]?)(?!\$\{|<|null\b|false\b|true\b)([A-Za-z0-9][^\s,;\x22\x27]+)',text):
        if fictional_connection_template(text,assignment):
            continue
        placeholder=secret_source_placeholder(assignment[1],assignment[3])
        end=assignment.end(3)
        if placeholder and assignment[2]:
            placeholder=end<len(text) and text[end]==assignment[2]
            end+=1
        # The exception is for a complete literal, never its first whitespace-
        # separated fragment or an expression that appends credential material.
        while placeholder and end<len(text) and text[end] in ' \t':
            end+=1
        if not placeholder or (end<len(text) and text[end] not in ',;})]\r\n'):
            raise ValueError('PKH006 credential assignment in '+name)
    if name.lower().endswith('.json'):
        root=loads(text)
        def secret_schema(value):
            fields={'type','nullable','secret','description','format','properties','required','additionalProperties','items',
                    'minLength','maxLength','minItems','maxItems','minProperties','maxProperties','minimum','maximum',
                    'exclusiveMinimum','exclusiveMaximum','pattern','enumNames','mapKey','acceptedShapes'}
            if not isinstance(value,dict) or value.get('secret') is not True or set(value)-fields:
                return False
            if value.get('type') not in ('string','integer','number','boolean','array','object'):
                return False
            def has_values(node):
                if isinstance(node,dict):
                    return bool({'default','example','examples','const','enum'} & node.keys()) or any(has_values(v) for v in node.values())
                if isinstance(node,list):return any(has_values(v) for v in node)
                return False
            return not has_values(value)
        def visit(value,parent=None,in_constraints=False):
            if isinstance(value,dict):
                for key,child in value.items():
                    sensitive=re.search(r'password|clientsecret|apikey|access.?token|privatekey|connectionstrings|credentials',key,re.I)
                    source_hash=parent in ('sources','sourceSha256','sourceInputs','files') and isinstance(child,str) and re.fullmatch(r'[a-f0-9]{64}',child)
                    source_mapping=parent=='sourceFiles' and isinstance(child,str) and child.startswith('.orbyss-foundation/settings-sources/') and child.endswith('.txt')
                    schema_only=(root.get('schemaVersion')==2 and in_constraints and parent=='properties' and secret_schema(child))
                    if sensitive and child not in (None,'',{},[]) and not (source_hash or source_mapping or schema_only):raise ValueError('PKH006 secret value in '+name)
                    visit(child,key,in_constraints or key=='constraints')
            elif isinstance(value,list):
                for child in value:visit(child,parent,in_constraints)
        visit(root)


def bounded_read(stream, maximum: int, label: str) -> bytes:
    payload=stream.read(maximum+1)
    if len(payload)>maximum:
        raise ValueError('PKH007 authority exceeds admitted size: '+label)
    return payload


def stream_sha256(stream, maximum: int, label: str) -> str:
    result=hashlib.sha256(); count=0
    for block in iter(lambda:stream.read(65536),b''):
        count+=len(block)
        if count>maximum:
            raise ValueError('PKH007 authority exceeds admitted size: '+label)
        result.update(block)
    return result.hexdigest()


def package_parts(package):
    """Only immutable package metadata/native bytes are read; no assembly is loaded."""
    with zipfile.ZipFile(package) as archive:
        seen=set(); total=0; nuspecs=[]
        for entry in archive.infolist():
            name=safe_name(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
            if name.casefold() in seen or stat.S_ISLNK(entry.external_attr>>16) or entry.flag_bits&1:
                raise ValueError('PKH002 unsafe package authority entry')
            seen.add(name.casefold());total+=entry.file_size
            if total>1024**3 or len(seen)>100000:
                raise ValueError('PKH007 oversized package authority')
            if name.endswith('.nuspec'):nuspecs.append(name)
        if len(nuspecs)!=1:raise ValueError('PKH007 package requires one native nuspec')
        with archive.open(nuspecs[0]) as stream:spec=ET.fromstring(bounded_read(stream,MAX_METADATA,'nuspec'))
        namespace={'n':spec.tag.split('}')[0][1:]} if spec.tag.startswith('{') else {}
        prefix='n:' if namespace else ''
        metadata=spec.find(prefix+'metadata',namespace)
        identity=metadata.findtext(prefix+'id',namespaces=namespace)
        version=metadata.findtext(prefix+'version',namespaces=namespace)
        repository=metadata.find(prefix+'repository',namespace)
        origin={} if repository is None else dict(repository.attrib)
        if not identity or not version:raise ValueError('PKH007 invalid native package identity')
        def member(name,maximum):
            if name not in archive.namelist():raise ValueError('PKH007 selected publisher has no required member: '+name)
            if archive.getinfo(name).file_size>maximum:raise ValueError('PKH007 oversized package member: '+name)
            with archive.open(name) as stream:return bounded_read(stream,maximum,name)
        payload=member(SETTINGS_MEMBER,MAX_METADATA) if SETTINGS_MEMBER in archive.namelist() else None
        assembly_hashes={}
        for name in archive.namelist():
            if name.startswith('lib/net10.0/') and name.endswith('.dll'):
                if archive.getinfo(name).file_size>MAX_ASSEMBLY:raise ValueError('PKH007 oversized packed assembly')
                with archive.open(name) as stream:assembly_hashes[name.rsplit('/',1)[-1]]=stream_sha256(stream,MAX_ASSEMBLY,name)
        return identity,version,origin,payload,assembly_hashes


def publisher_metadata(package, packages: dict, *, stack=()) -> tuple[dict,bytes]:
    identity,version,_,payload,assemblies=package_parts(package)
    if payload is None:raise ValueError('PKH007 selected publisher has no settings companion')
    envelope=loads(payload.decode('utf-8-sig'))
    reject_secrets(payload,SETTINGS_MEMBER)
    fields={'schemaVersion','packageId','packageVersion','sourceSha256','contracts','assembly'}
    if envelope.get('schemaVersion')==2:fields.add('imports')
    if (set(envelope)!=fields or type(envelope['schemaVersion']) is not int or envelope['schemaVersion'] not in (1,2)
            or envelope['packageId']!=identity or envelope['packageVersion']!=version
            or not isinstance(envelope['contracts'],list) or not 1<=len(envelope['contracts'])<=32):
        raise ValueError('PKH007 invalid publisher settings companion envelope')
    assembly=envelope['assembly'];validate_assembly_binding(assembly)
    if assemblies.get(assembly['name'])!=assembly['sha256']:
        raise ValueError('PKH005 settings companion differs from packed compiled assembly')
    scopes={}
    for contract in envelope['contracts']:
        validate_settings_metadata(contract)
        if (contract['schemaVersion']!=envelope['schemaVersion'] or contract['owner']!=identity
                or contract['sources']!=envelope['sourceSha256'] or contract['scope'] in scopes):
            raise ValueError('PKH007 publisher owner/source/scope conflict')
        if envelope['schemaVersion']==2 and not contract.get('typeName'):
            raise ValueError('PKH007 publisher settings scope requires compiled named type identity')
        scopes[contract['scope']]=contract
    if identity in stack or len(stack)>=16:raise ValueError('PKH007 recursive publisher settings import')
    imports=envelope.get('imports',[])
    if not isinstance(imports,list) or len(imports)>128:raise ValueError('PKH007 excessive publisher settings imports')
    seen=set()
    for item in imports:
        fields={'typeName','packageId','packageVersion','scope','metadataSha256','assembly'}
        if (not isinstance(item,dict) or set(item)!=fields
                or any(not isinstance(item[k],str) or not item[k] or len(item[k])>4096 for k in ('typeName','packageId','packageVersion','scope'))):
            raise ValueError('PKH007 invalid publisher settings import')
        key=(item['packageId'],item['scope'],item['typeName'])
        if key in seen:raise ValueError('PKH007 duplicate publisher settings import')
        seen.add(key);sha256_value(item['metadataSha256']);validate_assembly_binding(item['assembly'])
        dependency=packages.get(item['packageId'])
        if dependency is None:raise ValueError('PKH007 imported settings owner is outside selected closure')
        child,child_payload=publisher_metadata(dependency,packages,stack=stack+(identity,))
        if (child['packageVersion']!=item['packageVersion'] or hashlib.sha256(child_payload).hexdigest()!=item['metadataSha256']
                or child['assembly']!=item['assembly'] or not any(c['scope']==item['scope'] and c.get('typeName')==item['typeName'] and c['complete'] for c in child['contracts'])):
            raise ValueError('PKH005 imported settings package/version/metadata/assembly/scope differs from selected authority')
    return envelope,payload


def validate_assembly_binding(assembly):
    if not isinstance(assembly,dict) or set(assembly)!={'name','sha256'}:
        raise ValueError('PKH007 settings assembly binding required')
    safe_name(assembly['name']);sha256_value(assembly['sha256'])
    if '/' in assembly['name'] or not assembly['name'].endswith('.dll'):
        raise ValueError('PKH007 settings assembly name invalid')


def package_reference(reference, package, packages):
    fields={'schemaVersion','kind','packageId','packageVersion','packageSha256','scope'}
    if (not isinstance(reference,dict) or set(reference)!=fields or type(reference['schemaVersion']) is not int
            or reference['schemaVersion'] not in (1,2) or reference['kind']!='foundation-package'):
        raise ValueError('PKH007 invalid packaged settings reference')
    sha256_value(reference['packageSha256'])
    with open(package,'rb') as stream:actual=stream_sha256(stream,1024**3,'selected package')
    envelope,payload=publisher_metadata(package,packages)
    if (envelope['schemaVersion']!=reference['schemaVersion'] or envelope['packageId']!=reference['packageId']
            or envelope['packageVersion']!=reference['packageVersion'] or actual!=reference['packageSha256']):
        raise ValueError('PKH005 packaged settings identity/version/hash differs from selected package')
    selected=next((c for c in envelope['contracts'] if c['scope']==reference['scope']),None)
    if selected is None:raise ValueError('PKH007 selected settings scope is not published by the owner')
    return selected,payload


def image_member_name(value: str, *, directory: bool = False) -> str:
    """Canonical Linux layer name, used only in memory; never an extraction path."""
    if (not isinstance(value,str) or not value or value.startswith('/')
            or '\\' in value or any(ord(char)<32 for char in value)):
        raise ValueError('PKH002 unsafe OCI relative path: '+repr(value))
    if value.startswith('./'):value=value[2:]
    if directory:value=value.rstrip('/')
    if value in ('','.'):
        if directory:return ''
        raise ValueError('PKH002 unsafe OCI relative path: '+repr(value))
    if any(part in ('','.','..') for part in value.split('/')):
        raise ValueError('PKH002 unsafe OCI relative path: '+repr(value))
    if len(value)>4096 or len(value.encode('utf-8'))>4096:
        raise ValueError('PKH007 OCI path exceeds admitted size')
    return value


def image_metadata(evidence: dict, host_reference: str, opener, packages: dict) -> tuple[dict, bytes]:
    """Reconstruct app authority from the selected immutable OCI bytes, without running the image."""
    fields={'schemaVersion','hostImageReference','platform','manifest','config','layers','nativePackages'}
    if 'index' in evidence:fields.add('index')
    if (not isinstance(evidence,dict) or set(evidence)!=fields or type(evidence['schemaVersion']) is not int
            or evidence['schemaVersion']!=2 or evidence['hostImageReference']!=host_reference
            or not re.fullmatch(r'ghcr\.io/orbyss-io/foundation-host@sha256:[a-f0-9]{64}',host_reference)):
        raise ValueError('PKH008 invalid or mismatched Host image authority')
    platform=evidence['platform']
    if (not isinstance(platform,dict) or set(platform)!={'os','architecture'} or platform['os']!='linux'
            or platform['architecture'] not in ('amd64','arm64')):
        raise ValueError('PKH007 unsupported Host authority platform')
    def binding(row, media=False):
        if not isinstance(row,dict) or set(row)!=({'path','sha256','mediaType'} if media else {'path','sha256'}):
            raise ValueError('PKH007 invalid OCI blob binding')
        safe_name(row['path']);sha256_value(row['sha256'])
    def blob(row):
        binding(row)
        with opener(row['path']) as stream:payload=bounded_read(stream,MAX_METADATA,'OCI JSON')
        if hashlib.sha256(payload).hexdigest()!=row['sha256']:raise ValueError('PKH005 changed OCI JSON blob')
        return loads(payload.decode('utf-8'))
    manifest=blob(evidence['manifest']);config=blob(evidence['config'])
    top=host_reference.rsplit(':',1)[-1]
    if 'index' in evidence:
        index=blob(evidence['index'])
        if evidence['index']['sha256']!=top or index.get('schemaVersion')!=2 or not isinstance(index.get('manifests'),list):
            raise ValueError('PKH005 OCI index differs from selected Host digest')
        matches=[d for d in index['manifests'] if d.get('platform')==platform]
        if len(matches)!=1 or matches[0].get('digest')!='sha256:'+evidence['manifest']['sha256']:
            raise ValueError('PKH005 selected platform manifest is outside exact OCI index')
    elif evidence['manifest']['sha256']!=top:
        raise ValueError('PKH005 OCI manifest differs from selected Host digest')
    if (manifest.get('schemaVersion')!=2 or manifest.get('config',{}).get('digest')!='sha256:'+evidence['config']['sha256']
            or config.get('os')!=platform['os'] or config.get('architecture')!=platform['architecture']):
        raise ValueError('PKH005 OCI config/platform chain differs')
    layers=evidence['layers'];descriptors=manifest.get('layers');diffids=config.get('rootfs',{}).get('diff_ids')
    if (not isinstance(layers,list) or not 1<=len(layers)<=128 or not isinstance(descriptors,list)
            or not isinstance(diffids,list) or len(layers)!=len(descriptors) or len(layers)!=len(diffids)
            or config.get('rootfs',{}).get('type')!='layers'):
        raise ValueError('PKH007 incomplete ordered OCI layer proof')
    app={}; compressed_total=0;uncompressed_total=0;retained_total=0
    media_types={'application/vnd.oci.image.layer.v1.tar+gzip':True,'application/vnd.docker.image.rootfs.diff.tar.gzip':True,
                 'application/vnd.oci.image.layer.v1.tar':False,'application/vnd.docker.image.rootfs.diff.tar':False}
    class Counted:
        def __init__(self,stream):self.stream=stream;self.count=0;self.hash=hashlib.sha256()
        def read(self,size=-1):
            block=self.stream.read(min(size if size>=0 else 65536,65536));self.count+=len(block)
            if self.count>1024**3:raise ValueError('PKH007 decompressed OCI layer exceeds limit')
            self.hash.update(block);return block
    def entry_name(entry):
        return image_member_name(entry.name,directory=entry.isdir())
    def erase(name):
        for key in list(app):
            if key==name or key.startswith(name+'/'):del app[key]
    for row,descriptor,diffid in zip(layers,descriptors,diffids):
        binding(row,True)
        if (row['mediaType'] not in media_types or descriptor.get('mediaType')!=row['mediaType']
                or descriptor.get('digest')!='sha256:'+row['sha256']):
            raise ValueError('PKH005 ordered OCI layer descriptor mismatch')
        with opener(row['path']) as stream:
            digestor=hashlib.sha256();length=0
            for block in iter(lambda:stream.read(65536),b''):
                length+=len(block)
                if length>256*1024**2:raise ValueError('PKH007 compressed OCI layer exceeds limit')
                digestor.update(block)
        compressed_total+=length
        if compressed_total>1024**3 or descriptor.get('size')!=length or digestor.hexdigest()!=row['sha256']:
            raise ValueError('PKH005 OCI layer bytes/size differ from manifest')
        # Whiteouts are applied to the lower filesystem before same-layer writes, regardless of tar order.
        for apply in (False,True):
            with opener(row['path']) as raw:
                decoded=gzip.GzipFile(fileobj=raw) if media_types[row['mediaType']] else raw
                counted=Counted(decoded);seen=set();whiteouts=[]
                with tarfile.open(fileobj=counted,mode='r|') as archive:
                    for entry in archive:
                        name=entry_name(entry)
                        if not name:continue
                        if name in seen or len(seen)>=1000000:raise ValueError('PKH002 duplicate/excessive OCI tar entries')
                        seen.add(name)
                        tail=name.rsplit('/',1)[-1];parent=name.rpartition('/')[0]
                        # Root whiteouts can remove app or make the root opaque.
                        # Admit them before restricting retained files to app.
                        if tail.startswith('.wh.') and (not parent or name.startswith('app/')):
                            if not entry.isfile() or entry.size!=0:raise ValueError('PKH002 invalid OCI whiteout')
                            if not apply:
                                if tail=='.wh..wh..opq':
                                    prefix=parent+'/' if parent else ''
                                    for key in list(app):
                                        if key.startswith(prefix):del app[key]
                                else:erase((parent+'/' if parent else '')+tail[4:])
                            continue
                        if name!='app' and not name.startswith('app/'):continue
                        if not apply:continue
                        if entry.isdir():
                            app.pop(name,None)
                            continue
                        if not entry.isfile():raise ValueError('PKH002 linked/device Host app layer entry')
                        if len(app)>100000:raise ValueError('PKH007 Host app inventory exceeds limit')
                        image_name=name[4:] if name.startswith('app/') else ''
                        if not image_name:raise ValueError('PKH002 Host app root is not a directory')
                        if any('/'.join(name.split('/')[:i]) in app for i in range(1,len(name.split('/')))):
                            raise ValueError('PKH002 Host app entry traverses a regular file')
                        source_snapshot=image_name.startswith('.orbyss-foundation/settings-sources/') and image_name.endswith('.txt')
                        maximum=MAX_METADATA if source_snapshot or image_name=='.orbyss-foundation/host-settings.json' else (4*1024**2 if image_name.endswith('.deps.json') else MAX_ASSEMBLY)
                        if entry.size>maximum:raise ValueError('PKH007 Host app entry exceeds admitted limit')
                        with archive.extractfile(entry) as stream:
                            retain=source_snapshot or image_name in ('.orbyss-foundation/host-settings.json','Orbyss.Foundation.Host.deps.json')
                            if retain:
                                retained_total+=entry.size
                                if retained_total>32*1024**2:raise ValueError('PKH007 retained Host metadata/sources exceed limit')
                                payload=bounded_read(stream,maximum,image_name);actual=hashlib.sha256(payload).hexdigest()
                            else:payload=None;actual=stream_sha256(stream,maximum,image_name)
                        erase(name)
                        app[name]={'sha256':actual,'payload':payload}
                while counted.read(65536):pass
                if counted.hash.hexdigest()!=diffid.removeprefix('sha256:') or not re.fullmatch(r'sha256:[a-f0-9]{64}',diffid):
                    raise ValueError('PKH005 decompressed OCI layer differs from config diffID')
                if apply:
                    uncompressed_total+=counted.count
                    if uncompressed_total>2*1024**3:raise ValueError('PKH007 cumulative OCI layer expansion exceeds limit')
    metadata=app.get('app/.orbyss-foundation/host-settings.json',{}).get('payload')
    if metadata is None:raise ValueError('PKH007 selected image has no Host settings producer')
    envelope=loads(metadata.decode('utf-8-sig'))
    reject_secrets(metadata,'host-settings.json')
    fields={'schemaVersion','packageId','packageVersion','sourceSha256','sourceFiles','contracts','assembly','imports','origins'}
    if (set(envelope)!=fields or type(envelope['schemaVersion']) is not int or envelope['schemaVersion']!=2
            or envelope['packageId']!='Orbyss.Foundation.Host'
            or not isinstance(envelope['packageVersion'],str) or not envelope['packageVersion']
            or not isinstance(envelope['contracts'],list) or not 1<=len(envelope['contracts'])<=32):
        raise ValueError('PKH007 invalid Host integration metadata envelope')
    validate_assembly_binding(envelope['assembly'])
    if envelope['assembly']['name']!='Orbyss.Foundation.Host.dll' or app.get('app/'+envelope['assembly']['name'],{}).get('sha256')!=envelope['assembly']['sha256']:
        raise ValueError('PKH005 Host metadata differs from actual image assembly')
    sources=envelope['sourceSha256'];source_files=envelope['sourceFiles']
    if not isinstance(source_files,dict) or not isinstance(sources,dict) or set(source_files)!=set(sources) or len(set(source_files.values()))!=len(source_files):
        raise ValueError('PKH007 incomplete or ambiguous Host source mapping')
    def source_matches(name,expected):
        safe_name(name);sha256_value(expected)
        if not name.startswith('.orbyss-foundation/settings-sources/') or not name.endswith('.txt'):
            raise ValueError('PKH002 invalid Host metadata source snapshot path')
        payload=app.get('app/'+name,{}).get('payload')
        if payload is None:raise ValueError('PKH005 missing image-bound owning source snapshot')
        normalized=payload.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').encode('utf-8')
        if hashlib.sha256(normalized).hexdigest()!=expected:raise ValueError('PKH005 stale image-bound owning source snapshot')
    for name,path in source_files.items():safe_name(name);source_matches(path,sources[name])
    scopes=set()
    for contract in envelope['contracts']:
        validate_settings_metadata(contract)
        if (contract['schemaVersion']!=2 or contract['owner']!=envelope['packageId'] or contract['sources']!=sources
                or contract['scope'] in scopes):raise ValueError('PKH007 Host owner/source/scope conflict')
        scopes.add(contract['scope'])
    if not HOST_SCOPES <= scopes:
        raise ValueError('PKH007 current Host settings producer must cover transport/boot/CShells/Nuplane')
    if envelope['imports']!=[]:raise ValueError('PKH007 Host imports must use native origins rather than package settings defaults')
    verify_native_origins(envelope,app,evidence['nativePackages'],opener,source_matches)
    return envelope,metadata


def verify_native_origins(envelope,app,records,opener,source_matches):
    origins=envelope['origins'];seen=set()
    if not isinstance(origins,list) or not 1<=len(origins)<=32:raise ValueError('PKH007 native Host origins required')
    deps_payload=app.get('app/Orbyss.Foundation.Host.deps.json',{}).get('payload')
    if deps_payload is None:raise ValueError('PKH005 missing actual Host dependency graph')
    libraries=loads(deps_payload.decode('utf-8'))['libraries']
    native={key for key in libraries if key.startswith(('CShells','Nuplane'))}
    if not isinstance(records,list) or not 1<=len(records)<=64:
        raise ValueError('PKH007 explicit captured native Host archives required')
    by_id={};aggregate=0
    with tempfile.TemporaryDirectory(prefix='handoff-host-native-') as temporary:
        root=Path(temporary)
        for row in records:
            if (not isinstance(row,dict) or set(row)!={'packageId','packageVersion','path','sha256'}
                    or not isinstance(row['packageId'],str) or not row['packageId'] or row['packageId'] in by_id):
                raise ValueError('PKH007 invalid or repeated captured native archive')
            safe_name(row['path']);sha256_value(row['sha256']);name=safe_name(Path(row['path']).name)
            if not name.endswith('.nupkg') or (root/name).exists():raise ValueError('PKH002 invalid or ambiguous native archive path')
            destination=root/name;hasher=hashlib.sha256();count=0
            with opener(row['path']) as source,destination.open('wb') as target:
                for block in iter(lambda:source.read(65536),b''):
                    count+=len(block);aggregate+=len(block)
                    if count>1024**3 or aggregate>1024**3:raise ValueError('PKH007 captured native archives exceed aggregate limit')
                    hasher.update(block);target.write(block)
            if hasher.hexdigest()!=row['sha256']:raise ValueError('PKH005 captured native archive bytes changed')
            by_id[row['packageId']]=(row,destination)
        if set(by_id)!={o.get('packageId') for o in origins if isinstance(o,dict)}:
            raise ValueError('PKH007 captured native archive identity set differs from Host origins')
        for origin in origins:
            verify_origin(origin,by_id,app,seen,source_matches)
    if seen!=native:raise ValueError('PKH007 native Host origin coverage differs from actual dependency graph')
    if 'Orbyss.Foundation.Host/'+envelope['packageVersion'] not in libraries:
        raise ValueError('PKH005 Host metadata version differs from actual native dependency graph')


def verify_origin(origin,by_id,app,seen,source_matches):
        if not isinstance(origin,dict) or set(origin)!={'packageId','packageVersion','archive','assembly','source'}:
            raise ValueError('PKH007 invalid native Host origin')
        key=origin['packageId']+'/'+origin['packageVersion']
        if key in seen:raise ValueError('PKH007 repeated native Host origin')
        seen.add(key);binding_archive=origin['archive'];source=origin['source']
        if (not isinstance(binding_archive,dict) or set(binding_archive)!={'name','sha256'}
                or not isinstance(source,dict) or set(source)!={'repository','commit','files'}):raise ValueError('PKH007 native archive/source binding required')
        safe_name(binding_archive['name']);sha256_value(binding_archive['sha256']);validate_assembly_binding(origin['assembly'])
        record,package=by_id[origin['packageId']]
        with open(package,'rb') as stream:archive_hash=stream_sha256(stream,1024**3,'native package')
        identity,version,nuspec,_,assemblies=package_parts(package)
        if (identity!=origin['packageId'] or version!=origin['packageVersion'] or record['packageVersion']!=version
                or record['sha256']!=binding_archive['sha256'] or Path(package).name!=binding_archive['name']
                or archive_hash!=binding_archive['sha256'] or nuspec.get('url')!=source['repository'] or nuspec.get('commit')!=source['commit']
                or not re.fullmatch(r'[a-f0-9]{40}',source['commit']) or not isinstance(source['files'],dict) or not 1<=len(source['files'])<=512
                or assemblies.get(origin['assembly']['name'])!=origin['assembly']['sha256']
                or app.get('app/'+origin['assembly']['name'],{}).get('sha256')!=origin['assembly']['sha256']):
            raise ValueError('PKH005 native Host origin differs from exact archive/assembly/source authority')
        for name,expected in source['files'].items():source_matches(name,expected)


def applicable_settings(envelopes: list[dict], configuration: dict, explicitly_required: set) -> set:
    """Derive applicability from the delivered native configuration and owning declarations."""
    shells=configuration.get('shells',{}).get('CShells',{}).get('Shells',{})
    if not isinstance(shells,dict):raise ValueError('PKH007 invalid delivered settings activation')
    active={feature for shell in shells.values() for feature,value in shell.get('Features',{}).items() if value is not False}
    roots=[configuration.get('hostsettings',{})]+[shell.get('Configuration',{}) for shell in shells.values()]
    def configured(prefix):
        parts=prefix.split(':')
        if any(not part for part in parts):raise ValueError('PKH007 invalid settings configuration selector')
        for root in roots:
            node=root
            for part in parts:
                if not isinstance(node,dict):break
                matches=[value for key,value in node.items() if key.casefold()==part.casefold()]
                if len(matches)!=1:break
                node=matches[0]
            else:return True
        return False
    required=set(explicitly_required)
    for envelope in envelopes:
        applicable=False
        for contract in envelope['contracts']:
            if contract['schemaVersion']!=2:continue
            selected=contract['appliesTo'];key=(contract['owner'],contract['scope'])
            needed=(selected['kind']=='host' or key in required or (selected['kind']=='shell'
                    and (bool(active & set(selected['features'])) or any(configured(x) for x in selected['configuration']))))
            if needed:required.add(key);applicable=True
        if applicable:
            required.update((item['packageId'],item['scope']) for item in envelope.get('imports',[]))
    # Imported scopes may themselves have imports; finite closure is already validated by the publisher reader.
    previous=None
    while previous!=required:
        previous=set(required)
        for envelope in envelopes:
            if any((c['owner'],c['scope']) in required for c in envelope['contracts']):
                required.update((i['packageId'],i['scope']) for i in envelope.get('imports',[]))
    return required


def host_reference(reference: dict, host: str, opener, packages: dict):
    if (not isinstance(reference,dict) or set(reference)!={'schemaVersion','kind','scope','evidencePath','evidenceSha256'}
            or type(reference['schemaVersion']) is not int or reference['schemaVersion']!=2 or reference['kind']!='foundation-host-image'):
        raise ValueError('PKH007 invalid Host image settings reference')
    safe_name(reference['evidencePath']);sha256_value(reference['evidenceSha256'])
    with opener(reference['evidencePath']) as stream:payload=bounded_read(stream,MAX_METADATA,'Host image evidence')
    if hashlib.sha256(payload).hexdigest()!=reference['evidenceSha256']:raise ValueError('PKH005 stale Host image evidence')
    evidence=loads(payload.decode('utf-8-sig'))
    envelope,metadata=image_metadata(evidence,host,opener,packages)
    contract=next((c for c in envelope['contracts'] if c['scope']==reference['scope']),None)
    if contract is None:raise ValueError('PKH007 selected Host settings scope is not emitted')
    return contract,envelope,metadata,evidence


def verify_receiver_settings(archive, index, bundle, *, allow_draft=False):
    """Receiver2 rechecks source/package/OCI authority, applicability, imports and coverage."""
    fields={'schemaVersion','status','missing','application','hostImage','bundle','components','packages','contracts','categories','files','settingsAuthorities','requiredSettingsScopes'}
    if set(index)!=fields:raise ValueError('PKH012 invalid receiver2 authority index')
    paths={row['path'] for row in index['files']}
    authorities=index['settingsAuthorities']
    if not isinstance(authorities,list) or len(authorities)>512 or len(set(authorities))!=len(authorities):
        raise ValueError('PKH007 invalid receiver settings authority inventory')
    expected={'inputs/'+name for name in index['categories']['settings']['files']}
    if set(authorities)!=expected:raise ValueError('PKH007 omitted or added receiver settings authority')
    def read_member(name,maximum=MAX_METADATA):
        safe_name(name)
        if name not in paths:raise ValueError('PKH009 unresolved settings authority: '+name)
        if archive.getinfo(name).file_size>maximum:raise ValueError('PKH007 oversized receiver authority')
        with archive.open(name) as stream:return bounded_read(stream,maximum,name)
    # Validate native configuration against the retained bundle bytes before trusting applicability.
    bundle_archive=index['bundle'].removesuffix('.json')+'.zip'
    if bundle_archive not in paths or archive.getinfo(bundle_archive).file_size>1024**3:
        raise ValueError('PKH007 missing or excessive retained runtime bundle')
    # Native ZIP needs a seekable stream. Spool bounded bytes to an owned temporary
    # file instead of retaining a potentially large deployment bundle in memory.
    with tempfile.TemporaryFile() as spooled:
        count=0
        with archive.open(bundle_archive) as source:
            for block in iter(lambda:source.read(65536),b''):
                count+=len(block)
                if count>1024**3:raise ValueError('PKH007 excessive retained runtime bundle')
                spooled.write(block)
        spooled.seek(0)
        with zipfile.ZipFile(spooled) as runtime:
            declared={row['file']:row['sha256'] for row in bundle['files']}
            if len(set(runtime.namelist()))!=len(runtime.namelist()) or set(runtime.namelist())!={'application-bundle.json'}|set(declared):
                raise ValueError('PKH005 runtime bundle inventory differs')
            with runtime.open('application-bundle.json') as stream:
                if loads(bounded_read(stream,MAX_METADATA,'bundle descriptor').decode('utf-8'))!=bundle:
                    raise ValueError('PKH008 runtime bundle descriptor differs')
            for name,expected_hash in declared.items():
                safe_name(name)
                with runtime.open(name) as stream:
                    if stream_sha256(stream,1024**3,name)!=expected_hash:raise ValueError('PKH005 runtime bundle artifact differs')
            for key,name in [('shells','shells.json'),('hostsettings','hostsettings.json')]:
                with runtime.open(name) as stream:
                    if loads(bounded_read(stream,MAX_METADATA,name).decode('utf-8-sig'))!=bundle['configuration'][key]:
                        raise ValueError('PKH005 native applicability configuration differs')
    with tempfile.TemporaryDirectory(prefix='handoff-receiver-authority-') as temporary:
        root=Path(temporary);packages={};envelopes=[]
        for identity,row in index['packages'].items():
            name=safe_name(Path(row['path']).name);destination=root/name
            if destination.exists():raise ValueError('PKH007 ambiguous retained package names')
            with archive.open(row['path']) as source,destination.open('wb') as target:
                total=0
                for block in iter(lambda:source.read(65536),b''):
                    total+=len(block)
                    if total>1024**3:raise ValueError('PKH007 oversized retained package')
                    target.write(block)
            native_id,version,_,payload,_=package_parts(destination)
            if native_id!=identity or version!=row['version']:raise ValueError('PKH005 receiver package identity differs')
            if ('orbyss-foundation/settings.json' if payload is not None else None)!=row.get('settingsDescriptor'):
                raise ValueError('PKH005 receiver package settings descriptor differs')
            packages[identity]=destination
        for package in packages.values():
            _,_,_,payload,_=package_parts(package)
            if payload is not None and loads(payload.decode('utf-8-sig')).get('schemaVersion')==2:
                envelope,_=publisher_metadata(package,packages);envelopes.append(envelope)
        owners=set();setting_keys=set();host_envelope=None
        for name in authorities:
            reference=loads(read_member(name).decode('utf-8-sig'))
            if reference.get('kind')=='foundation-package':
                package=packages.get(reference.get('packageId'))
                if package is None:raise ValueError('PKH007 receiver package settings owner is outside closure')
                metadata,payload=package_reference(reference,package,packages)
                if read_member('metadata/settings/'+reference['packageId']+'.json')!=payload:
                    raise ValueError('PKH005 retained publisher settings differ from archive member')
            elif reference.get('kind')=='foundation-host-image':
                metadata,envelope,payload,_=host_reference(reference,index['hostImage']['reference'],
                    lambda n:archive.open('inputs/'+safe_name(n)),packages)
                if host_envelope is not None and host_envelope!=envelope:raise ValueError('PKH007 conflicting Host image authorities')
                host_envelope=envelope
                if read_member('metadata/settings/Orbyss.Foundation.Host.json')!=payload:
                    raise ValueError('PKH005 retained Host metadata differs from image authority')
            else:
                metadata=reference;validate_settings_metadata(metadata)
                reject_secrets(read_member(name),name)
                for source,expected_hash in metadata['sources'].items():
                    with archive.open('inputs/'+safe_name(source)) as stream:
                        if stream_sha256(stream,MAX_METADATA,source)!=expected_hash:raise ValueError('PKH005 stale application-owned settings source')
            if metadata['complete']:owners.add((metadata['owner'],metadata['scope']))
            for setting in metadata['settings']:
                key=(metadata['scope'],setting['path'].casefold())
                if key in setting_keys:raise ValueError('PKH007 conflicting receiver setting paths')
                setting_keys.add(key)
        if host_envelope is None:
            if not allow_draft or index['status']=='ready':raise ValueError('PKH011 missing exact selected Host image authority')
        else:envelopes.append(host_envelope)
        requirements=index['requiredSettingsScopes']
        if not isinstance(requirements,dict) or not requirements or any(not isinstance(v,list) or not v for v in requirements.values()):
            raise ValueError('PKH007 missing explicit owner/scope requirements')
        required={(owner,scope) for owner,scopes in requirements.items() for scope in scopes}
        required=applicable_settings(envelopes,bundle['configuration'],required)
        if required-owners and (index['status']=='ready' or not allow_draft):
            raise ValueError('PKH011 receiver settings owner/scope coverage is incomplete: '+str(sorted(required-owners)))


def loads(text: str) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'PKH001 ambiguous duplicate JSON key: {key}')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f'PKH001 non-JSON numeric constant: {value}')
    value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(value, dict):
        raise ValueError('PKH001 expected JSON object')
    return value


def read(path: Path) -> dict:
    return loads(path.read_text(encoding='utf-8-sig'))


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            result.update(block)
    return result.hexdigest()


def safe_name(value: str) -> str:
    if (not isinstance(value, str) or not value or any(c in value for c in '\\:<>|?*')
            or any(ord(c) < 32 for c in value)):
        raise ValueError(f'PKH002 unsafe relative path: {value!r}')
    parts = value.split('/')
    if (any(p in {'', '.', '..'} or p.endswith(('.', ' ')) for p in parts)
            or any(re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.I) for p in parts)
            or PurePosixPath(value).is_absolute()):
        raise ValueError(f'PKH002 unsafe relative path: {value!r}')
    return value


def contained(root: Path, name: str, *, exists: bool = True) -> Path:
    safe_name(name)
    root = root.resolve()
    path = root / name
    current = path
    while current != root:
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError(f'PKH002 linked input: {name}')
        current = current.parent
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'PKH002 escaped input: {name}')
    if exists and not path.is_file():
        raise ValueError(f'PKH003 missing required input: {name}')
    return path


def declaration(root: Path) -> dict:
    path = root / DECLARATION
    if not path.is_file():
        raise ValueError('PKH004 stable identity is missing. Create eng/application-handoff.json; '
                         'for an existing application explicitly retain its last released descriptor ID. '
                         'Never derive a new release identity from a renamed checkout.')
    value = read(path)
    if set(value) != {'schemaVersion', 'applicationId', 'components', 'bundleDescriptor', 'openapiRegistry', 'categories', 'requiredSettingsScopes'} or value.get('schemaVersion') != 1:
        raise ValueError('PKH001 invalid application handoff declaration envelope')
    identity = value.get('applicationId')
    if not isinstance(identity, str) or not identity.strip() or identity != identity.strip() or any(ord(c) < 32 for c in identity) or any(c in identity for c in '/\\:'):
        raise ValueError('PKH004 explicitly select applicationId in eng/application-handoff.json; '
                         'retain the historical released ID when migrating')
    for key in ('bundleDescriptor', 'openapiRegistry'):
        safe_name(value[key])
    if set(value['categories']) != CATEGORIES:
        raise ValueError('PKH001 explicitly declare every applicable category (or explain not-applicable/missing)')
    for key, category in value['categories'].items():
        if (set(category) != {'status', 'reason', 'files'} or category['status'] not in {'included', 'not-applicable', 'missing'}
                or not isinstance(category['reason'], str) or not category['reason'].strip()
                or not isinstance(category['files'], list)
                or (category['status'] == 'included') != bool(category['files'])):
            raise ValueError(f'PKH001 invalid category: {key}')
        if key in {'documentation', 'runtime', 'settings'} and category['status'] == 'not-applicable':
            raise ValueError(f'PKH001 {key} is required for an application handoff')
        for name in category['files']:
            safe_name(name)
    scopes = value['requiredSettingsScopes']
    if (not isinstance(scopes, dict) or not scopes
            or any(not isinstance(owner, str) or not owner or not isinstance(items, list) or not items
                   or any(not isinstance(x, str) or not x for x in items) or len(set(items)) != len(items)
                   for owner, items in scopes.items())):
        raise ValueError('PKH001 requiredSettingsScopes must explicitly identify owner/scope coverage')
    components = value['components']
    if not isinstance(components, list) or not components:
        raise ValueError('PKH001 explicit component/artifact bindings are required')
    ids = set()
    for component in components:
        if (set(component) != {'id', 'packages', 'contracts'} or not isinstance(component['id'], str)
                or not component['id'] or component['id'] in ids):
            raise ValueError('PKH001 invalid or repeated component identity')
        ids.add(component['id'])
        for key in ('packages', 'contracts'):
            items = component[key]
            if not isinstance(items, list) or any(not isinstance(x, str) or not x for x in items) or len(set(items)) != len(items):
                raise ValueError('PKH001 invalid component references')
    return value


def application_identity(root: Path) -> str:
    path = root / DECLARATION
    if not path.is_file():
        raise ValueError('PKH004 stable identity missing: create eng/application-handoff.json with '
                         'an explicit applicationId, retaining the last historical descriptor ID; '
                         'old descriptors remain readable and must not be rewritten')
    value = read(path)
    identity = value.get('applicationId')
    if value.get('schemaVersion') != 1 or not isinstance(identity, str) or not identity.strip() or identity != identity.strip() or any(ord(c) < 32 for c in identity) or any(c in identity for c in '/\\:'):
        raise ValueError('PKH004 explicitly select applicationId; preserve the last released ID when migrating')
    return identity


def source_inputs(repository: Path) -> dict[str, str]:
    """Bind producer evidence to current native source, not agent state or generated caches."""
    generated = set()
    registry = repository / 'eng/openapi-contracts.json'
    if registry.is_file():
        for name in read(registry).get('contracts', []):
            contract = read(contained(repository, name))
            output = contract.get('generator', {}).get('generatedTypes')
            if output:
                generated.add(contained(repository, output, exists=False))
    candidates = [p for p in (repository / 'src').rglob('*') if p.is_file() and p not in generated
                  and not {'bin', 'obj', 'node_modules', 'dist'}.intersection(p.relative_to(repository).parts)]
    candidates += [repository / name for name in ('VERSION', 'Directory.Packages.props',
                    'Directory.Build.props', 'Directory.Build.targets', 'shells.json', 'hostsettings.json',
                    'nuplane.settings.json', 'eng/web-profile.shells.json', 'eng/.config/dotnet-tools.json')
                   if (repository / name).is_file()]
    return {p.relative_to(repository).as_posix(): digest(contained(repository, p.relative_to(repository).as_posix()))
            for p in sorted(candidates)}

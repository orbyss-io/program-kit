"""Bounded offline package/import/OCI/portable authority seam negatives; no image startup."""
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import unittest
import zipfile
from validate_application_handoff import HandoffTests, handoff, handoff_contract, bundle, verify_handoff


class SettingsAuthorities(HandoffTests):
    def blob(self,payload):
        sha=hashlib.sha256(payload).hexdigest();name='contracts/oci/'+sha
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
        return {'path':name,'sha256':sha}

    def authority(self,changes=None):
        native=self.root/'artifacts/packages/Native.Options.4.5.6.nupkg'
        native_dll=b'offline native origin seam; not a compiled publisher qualification'
        with zipfile.ZipFile(native,'w') as archive:
            archive.writestr('Native.Options.nuspec','<package><metadata><id>Native.Options</id><version>4.5.6</version><repository type="git" url="https://example.invalid/native" commit="'+'c'*40+'" /></metadata></package>')
            archive.writestr('lib/net10.0/Native.Options.dll',native_dll)
        source=b'public class HostSettings { public int Limit {get;set;}=4; }\n'
        source_sha=hashlib.sha256(source).hexdigest();host_dll=b'offline Host image seam'
        contract=copy.deepcopy(self.metadata)
        contract.update(schemaVersion=2,owner='Orbyss.Foundation.Host',scope='host-transport',sources={'HostSettings.cs':source_sha},appliesTo={'kind':'host','features':[],'configuration':[]})
        contracts=[]
        for scope in sorted(handoff_contract.HOST_SCOPES):
            child=copy.deepcopy(contract);child['scope']=scope;contracts.append(child)
        envelope={'schemaVersion':2,'packageId':'Orbyss.Foundation.Host','packageVersion':'9.8.7','sourceSha256':contract['sources'],
                  'sourceFiles':{'HostSettings.cs':'.orbyss-foundation/settings-sources/host/HostSettings.cs.txt'},'contracts':contracts,
                  'assembly':{'name':'Orbyss.Foundation.Host.dll','sha256':hashlib.sha256(host_dll).hexdigest()},'imports':[],
                  'origins':[{'packageId':'Native.Options','packageVersion':'4.5.6','archive':{'name':native.name,'sha256':handoff.digest(native)},
                              'assembly':{'name':'Native.Options.dll','sha256':hashlib.sha256(native_dll).hexdigest()},
                              'source':{'repository':'https://example.invalid/native','commit':'c'*40,'files':{'.orbyss-foundation/settings-sources/vendor/Options.cs.txt':source_sha}}}]}
        entries={'app/.orbyss-foundation/host-settings.json':json.dumps(envelope).encode(),
                 'app/.orbyss-foundation/settings-sources/host/HostSettings.cs.txt':source,
                 'app/.orbyss-foundation/settings-sources/vendor/Options.cs.txt':source,
                 'app/Orbyss.Foundation.Host.dll':host_dll,'app/Native.Options.dll':native_dll,
                 'app/Orbyss.Foundation.Host.deps.json':json.dumps({'libraries':{'Orbyss.Foundation.Host/9.8.7':{},'Native.Options/4.5.6':{}}}).encode()}
        if changes:changes(envelope,entries)
        raw=io.BytesIO()
        with tarfile.open(fileobj=raw,mode='w') as archive:
            for name,payload in entries.items():
                info=tarfile.TarInfo(name);info.size=len(payload);archive.addfile(info,io.BytesIO(payload))
        tar=raw.getvalue();layer=self.blob(gzip.compress(tar,mtime=0));layer['mediaType']='application/vnd.oci.image.layer.v1.tar+gzip'
        config=self.blob(json.dumps({'os':'linux','architecture':'amd64','rootfs':{'type':'layers','diff_ids':['sha256:'+hashlib.sha256(tar).hexdigest()]}}).encode())
        manifest=self.blob(json.dumps({'schemaVersion':2,'mediaType':'application/vnd.oci.image.manifest.v1+json','config':{'digest':'sha256:'+config['sha256'],'size':(self.root/config['path']).stat().st_size},
                        'layers':[{'digest':'sha256:'+layer['sha256'],'mediaType':layer['mediaType'],'size':(self.root/layer['path']).stat().st_size}]}).encode())
        reference='ghcr.io/orbyss-io/foundation-host@sha256:'+manifest['sha256']
        evidence={'schemaVersion':2,'hostImageReference':reference,'platform':{'os':'linux','architecture':'amd64'},'manifest':manifest,'config':config,'layers':[layer],
                  'nativePackages':[{'packageId':'Native.Options','packageVersion':'4.5.6','path':native.relative_to(self.root).as_posix(),'sha256':handoff.digest(native)}]}
        return evidence,reference,{'Native.Options':native},envelope

    def image_read(self,evidence,host,packages):
        return handoff_contract.image_metadata(evidence,host,lambda name:(self.root/name).open('rb'),packages)

    def test_oci_hash_native_source_and_owner_proof(self):
        evidence,host,packages,envelope=self.authority()
        # Use a native family name to establish complete dependency-owner projection, not arbitrary extras.
        with self.assertRaisesRegex(ValueError,'origin coverage'):self.image_read(evidence,host,packages)
        # Real fixture below owns CShells.Options instead, exercising the native family predicate.
        evidence,host,packages,envelope=self.native_authority()
        self.assertEqual(self.image_read(evidence,host,packages)[0],envelope)
        for mutate in [lambda v:v.update(schemaVersion=2.0),
                       lambda v:v.update(hostImageReference='ghcr.io/orbyss-io/foundation-host@sha256:'+'0'*64),
                       lambda v:v['manifest'].update(sha256='0'*64),lambda v:v['config'].update(sha256='0'*64),
                       lambda v:v['layers'][0].update(sha256='0'*64),lambda v:v['layers'].clear(),
                       lambda v:v['layers'][0].update(path='../outside'),lambda v:v['platform'].update(architecture='arm64')]:
            bad=copy.deepcopy(evidence);mutate(bad)
            with self.assertRaisesRegex(ValueError,'PKH002|PKH005|PKH007|PKH008'):self.image_read(bad,host,packages)

    def test_native_archive_authority_exact_set_and_record_drift(self):
        evidence,host,packages,_=self.native_authority()
        for mutate in [lambda v:v['nativePackages'].clear(),lambda v:v['nativePackages'].append(copy.deepcopy(v['nativePackages'][0])),
                       lambda v:v['nativePackages'][0].update(packageId='Other'),lambda v:v['nativePackages'][0].update(packageVersion='4.5.7'),
                       lambda v:v['nativePackages'][0].update(path='../outside'),lambda v:v['nativePackages'][0].update(sha256='0'*64)]:
            bad=copy.deepcopy(evidence);mutate(bad)
            with self.assertRaisesRegex(ValueError,'PKH002|PKH005|PKH007'):self.image_read(bad,host,packages)
        path=packages['CShells.Options']
        with zipfile.ZipFile(path) as archive:members={n:archive.read(n) for n in archive.namelist()}
        for member,payload in [('CShells.Options.nuspec',members['CShells.Options.nuspec'].replace(b'c'*40,b'd'*40)),
                               ('lib/net10.0/CShells.Options.dll',b'changed native bytes')]:
            changed=dict(members);changed[member]=payload
            with zipfile.ZipFile(path,'w') as archive:
                for name,data in changed.items():archive.writestr(name,data)
            bad=copy.deepcopy(evidence);bad['nativePackages'][0]['sha256']=handoff.digest(path)
            with self.assertRaisesRegex(ValueError,'PKH005'):self.image_read(bad,host,packages)

    def native_authority(self,changes=None):
        # Replace a synthetic nuspec/assembly name before constructing the actual tar and hash chain.
        original=self.authority
        evidence,host,packages,envelope=original()
        old=packages['Native.Options'];new=old.with_name('CShells.Options.4.5.6.nupkg')
        with zipfile.ZipFile(old) as archive:members={n:archive.read(n) for n in archive.namelist()}
        with zipfile.ZipFile(new,'w') as archive:
            for name,payload in members.items():archive.writestr(name.replace('Native.Options','CShells.Options'),payload.replace(b'Native.Options',b'CShells.Options'))
        def replace(env,entries):
            env['origins'][0]['packageId']='CShells.Options';env['origins'][0]['archive']={'name':new.name,'sha256':handoff.digest(new)}
            env['origins'][0]['assembly']['name']='CShells.Options.dll'
            entries['app/CShells.Options.dll']=entries.pop('app/Native.Options.dll')
            entries['app/Orbyss.Foundation.Host.deps.json']=json.dumps({'libraries':{'Orbyss.Foundation.Host/9.8.7':{},'CShells.Options/4.5.6':{}}}).encode()
            if changes:changes(env,entries)
            entries['app/.orbyss-foundation/host-settings.json']=json.dumps(env).encode()
        evidence,host,_,envelope=original(replace)
        evidence['nativePackages']=[{'packageId':'CShells.Options','packageVersion':'4.5.6','path':new.relative_to(self.root).as_posix(),'sha256':handoff.digest(new)}]
        return evidence,host,{'CShells.Options':new},envelope

    def test_fully_rehashed_image_semantic_forgery_rejects(self):
        mutations=[lambda v,e:v.update(schemaVersion=2.0),lambda v,e:v['assembly'].update(sha256='0'*64),
                   lambda v,e:v['origins'][0]['assembly'].update(sha256='0'*64),
                   lambda v,e:v['origins'][0]['archive'].update(sha256='0'*64),
                   lambda v,e:v['origins'][0]['source'].update(commit='0'*40),
                   lambda v,e:v.update(origins=[]),lambda v,e:v['contracts'][0].update(owner='Pretend.Vendor'),
                   lambda v,e:v.update(contracts=[c for c in v['contracts'] if c['scope']!='host-boot']),
                   lambda v,e:e.update({'app/.orbyss-foundation/settings-sources/vendor/Options.cs.txt':b'changed owning source'}),
                   lambda v,e:e.pop('app/Orbyss.Foundation.Host.dll')]
        for i,mutate in enumerate(mutations):
            with self.subTest(case=i):
                evidence,host,packages,_=self.native_authority(mutate)
                with self.assertRaisesRegex(ValueError,'PKH005|PKH007'):self.image_read(evidence,host,packages)

    def additional_layer(self,evidence,entries):
        raw=io.BytesIO()
        with tarfile.open(fileobj=raw,mode='w') as archive:
            for name,payload,kind in entries:
                info=tarfile.TarInfo(name);info.size=len(payload)
                if kind=='link':info.type=tarfile.SYMTYPE;info.linkname='/outside';info.size=0
                archive.addfile(info,io.BytesIO(payload) if kind!='link' else None)
        tar=raw.getvalue();layer=self.blob(gzip.compress(tar,mtime=0));layer['mediaType']='application/vnd.oci.image.layer.v1.tar+gzip'
        result=copy.deepcopy(evidence);result['layers'].append(layer)
        config=json.loads((self.root/evidence['config']['path']).read_bytes())
        config['rootfs']['diff_ids'].append('sha256:'+hashlib.sha256(tar).hexdigest());result['config']=self.blob(json.dumps(config).encode())
        manifest=json.loads((self.root/evidence['manifest']['path']).read_bytes())
        manifest['config']={'digest':'sha256:'+result['config']['sha256'],'size':(self.root/result['config']['path']).stat().st_size}
        manifest['layers'].append({'digest':'sha256:'+layer['sha256'],'mediaType':layer['mediaType'],'size':(self.root/layer['path']).stat().st_size})
        result['manifest']=self.blob(json.dumps(manifest).encode())
        result['hostImageReference']='ghcr.io/orbyss-io/foundation-host@sha256:'+result['manifest']['sha256']
        return result

    def test_later_layer_whiteout_overwrite_and_links_are_rechecked(self):
        evidence,host,packages,_=self.native_authority()
        for entries in [[('app/.orbyss-foundation/.wh.host-settings.json',b'','file')],
                        [('app/.orbyss-foundation/.wh..wh..opq',b'','file')],
                        [('app/Orbyss.Foundation.Host.dll',b'changed compiled authority','file')],
                        [('app/.orbyss-foundation/settings-sources/vendor/Options.cs.txt',b'changed','file')],
                        [('app/.orbyss-foundation',b'','link')],
                        [('../escaped',b'changed','file')]]:
            changed=self.additional_layer(evidence,entries)
            with self.assertRaisesRegex(ValueError,'PKH002|PKH005|PKH007'):
                self.image_read(changed,changed['hostImageReference'],packages)
        # An unrelated later file preserves the exact authoritative app payload.
        changed=self.additional_layer(evidence,[('tmp/safe-example',b'none','file')])
        self.assertEqual(self.image_read(changed,changed['hostImageReference'],packages)[0]['packageId'],'Orbyss.Foundation.Host')

    def test_root_whiteouts_remove_lower_app_but_preserve_same_layer_replacement(self):
        evidence,host,packages,_=self.native_authority()
        for whiteout in ('.wh.app','.wh..wh..opq'):
            changed=self.additional_layer(evidence,[(whiteout,b'','file')])
            with self.subTest(whiteout=whiteout):
                with self.assertRaisesRegex(ValueError,'selected image has no Host settings producer'):
                    self.image_read(changed,changed['hostImageReference'],packages)
        # OCI whiteouts remove only the lower filesystem, independent of tar
        # ordering; a complete app replacement in that same layer remains valid.
        with gzip.open(self.root/evidence['layers'][0]['path'],'rb') as compressed:
            with tarfile.open(fileobj=compressed,mode='r|') as archive:
                entries=[(item.name,archive.extractfile(item).read(),'file') for item in archive if item.isfile()]
        for whiteout in ('.wh.app','.wh..wh..opq'):
            for replacement in ([(whiteout,b'','file')]+entries,entries+[(whiteout,b'','file')]):
                changed=self.additional_layer(evidence,replacement)
                self.assertEqual(self.image_read(changed,changed['hostImageReference'],packages)[0]['packageId'],'Orbyss.Foundation.Host')

    def test_linux_os_layer_colon_names_preserve_the_exact_app_authority(self):
        evidence,_,packages,envelope=self.native_authority()
        changed=self.additional_layer(evidence,[('var/lib/dpkg/info/gcc-14-base:amd64.list',b'native Linux filename','file')])
        self.assertEqual(self.image_read(changed,changed['hostImageReference'],packages)[0],envelope)
        with self.assertRaisesRegex(ValueError,'unsafe relative path'):
            handoff_contract.safe_name('contracts/gcc-14-base:amd64.list')

    def test_posix_image_member_traversal_controls_and_app_links_still_reject(self):
        evidence,_,packages,_=self.native_authority()
        for name in ('../outside','app/../outside','/app/absolute','app//alias','app/./alias','app\\..\\outside','app/control\nname'):
            changed=self.additional_layer(evidence,[(name,b'changed','file')])
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'PKH002'):
                self.image_read(changed,changed['hostImageReference'],packages)
        for name in ('app/linked:authority','app/.orbyss-foundation'):
            changed=self.additional_layer(evidence,[(name,b'','link')])
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'linked/device'):
                self.image_read(changed,changed['hostImageReference'],packages)
        for name in ('x'*4097,'app/'+'\u00e9'*2047):
            with self.assertRaisesRegex(ValueError,'OCI path exceeds admitted size'):
                handoff_contract.image_member_name(name)

    def test_posix_colon_names_cannot_alias_app_or_relax_receiver_source_paths(self):
        evidence,_,packages,envelope=self.native_authority()
        changed=self.additional_layer(evidence,[('app:outside/Orbyss.Foundation.Host.dll',b'unowned','file'),
                                                ('app/linux:opaque.data',b'ordinary native data','file')])
        self.assertEqual(self.image_read(changed,changed['hostImageReference'],packages)[0],envelope)
        for name in ('contracts/native:proof.json','.orbyss-foundation/settings-sources/host/source:owner.cs.txt'):
            with self.assertRaisesRegex(ValueError,'unsafe relative path'):handoff_contract.safe_name(name)

    def test_receiver_two_rechecks_actual_image_scope_coverage(self):
        evidence,host,packages,envelope=self.native_authority()
        self.selected['components'][0]['packages'].append('CShells.Options')
        for scope in sorted(handoff_contract.HOST_SCOPES):self.selected['categories']['settings']['files'].append('contracts/'+scope+'.json')
        self.write('eng/application-handoff.json',self.selected)
        self.write('contracts/oci/evidence.json',evidence)
        for scope in sorted(handoff_contract.HOST_SCOPES):
            self.write('contracts/'+scope+'.json',{'schemaVersion':2,'kind':'foundation-host-image','scope':scope,'evidencePath':'contracts/oci/evidence.json','evidenceSha256':handoff.digest(self.root/'contracts/oci/evidence.json')})
        # Remove the intentionally extraneous non-native archive from this selected closure.
        (self.packages/'Native.Options.4.5.6.nupkg').unlink()
        # The selected runtime declares the native authority it needs. An unrelated
        # archive beside pack output is not a package-selection mechanism.
        runtime_package = self.packages/'Example.App.1.2.3.nupkg'
        with zipfile.ZipFile(runtime_package) as archive:
            members = {name:archive.read(name) for name in archive.namelist()}
        members['Example.App.nuspec'] = members['Example.App.nuspec'].replace(
            b'</metadata>', b'<dependencies><dependency id="CShells.Options" version="[4.5.6]"/></dependencies></metadata>')
        with zipfile.ZipFile(runtime_package,'w') as archive:
            for name,payload in members.items(): archive.writestr(name,payload)
        self.write('NuGet.config', '<configuration><packageSources><clear/><add key="fixture" value="'+self.packages.as_posix()+'"/></packageSources></configuration>')
        self.produce()
        bundle.describe(self.root,self.stage,'ghcr.io/orbyss-io/foundation-host','v9.8.7','sha256:'+host.rsplit(':',1)[-1],self.root/'artifacts/application-bundle.json')
        index=handoff.assemble(self.root)
        self.assertEqual(index['schemaVersion'],2);self.assertEqual(index['status'],'ready')
        receiver=self.root.parent/'receiver2';receiver.mkdir();path=self.root/'artifacts/handoff/application-handoff.zip'
        with zipfile.ZipFile(path) as archive:
            for name in ('verify_handoff.py','handoff_contract.py'):(receiver/name).write_bytes(archive.read(name))
        result=subprocess.run([sys.executable,'-I',str(receiver/'verify_handoff.py'),str(path)],cwd=receiver,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        # A self-consistent receiver inventory cannot turn omitted actual Host scope into ready output.
        with zipfile.ZipFile(path) as archive:members={name:archive.read(name) for name in archive.namelist()}
        bad=copy.deepcopy(index);bad['settingsAuthorities'].remove('inputs/contracts/host-boot.json')
        bad['categories']['settings']['files'].remove('contracts/host-boot.json')
        members['index.json']=json.dumps(bad).encode()
        forged=receiver/'omitted-owner.zip'
        with zipfile.ZipFile(forged,'w') as archive:
            for name,payload in members.items():archive.writestr(name,payload)
        with self.assertRaisesRegex(ValueError,'PKH011'):verify_handoff.verify(forged)
        downgraded=copy.deepcopy(index);downgraded['schemaVersion']=1
        downgraded.pop('settingsAuthorities');downgraded.pop('requiredSettingsScopes')
        members['index.json']=json.dumps(downgraded).encode()
        with zipfile.ZipFile(forged,'w') as archive:
            for name,payload in members.items():archive.writestr(name,payload)
        with self.assertRaisesRegex(ValueError,'PKH012.*downgraded'):verify_handoff.verify(forged)
        # The retained independent verifier cannot silently use another adjacent authority helper.
        (receiver/'handoff_contract.py').write_text('raise AssertionError("untrusted adjacent helper")')
        result=subprocess.run([sys.executable,'-I',str(receiver/'verify_handoff.py'),str(path)],cwd=receiver,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('helper differs',result.stderr)

    def test_package_two_imports_bind_selected_metadata_and_implementation(self):
        def contract(owner,scope):
            value=copy.deepcopy(self.metadata)
            value.update(schemaVersion=2,owner=owner,scope=scope,typeName=owner+'.TypedOptions',appliesTo={'kind':'code','features':[],'configuration':[]})
            return value
        def pack(identity,metadata,dll=b'bounded compiled seam'):
            path=self.packages/(identity+'.1.2.3.nupkg')
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr(identity+'.nuspec','<package><metadata><id>'+identity+'</id><version>1.2.3</version></metadata></package>')
                archive.writestr('lib/net10.0/'+identity+'.dll',dll)
                archive.writestr(handoff_contract.SETTINGS_MEMBER,json.dumps(metadata).encode())
            return path
        def envelope(identity,scope):
            value=contract(identity,scope)
            return {'schemaVersion':2,'packageId':identity,'packageVersion':'1.2.3','sourceSha256':value['sources'],'contracts':[value],
                    'assembly':{'name':identity+'.dll','sha256':hashlib.sha256(b'bounded compiled seam').hexdigest()},'imports':[]}
        child=envelope('Options.Core','code-options');child_path=pack('Options.Core',child)
        parent=envelope('Options.Binder','shell-binding')
        parent['contracts'][0]['appliesTo']={'kind':'shell','features':['Admission'],'configuration':['Foundation:Options']}
        parent['imports']=[{'typeName':'Options.Core.TypedOptions','packageId':'Options.Core','packageVersion':'1.2.3','scope':'code-options',
                            'metadataSha256':hashlib.sha256(json.dumps(child).encode()).hexdigest(),'assembly':child['assembly']}]
        parent_path=pack('Options.Binder',parent);packages={'Options.Core':child_path,'Options.Binder':parent_path}
        ref={'schemaVersion':2,'kind':'foundation-package','packageId':'Options.Binder','packageVersion':'1.2.3','packageSha256':handoff.digest(parent_path),'scope':'shell-binding'}
        self.assertEqual(handoff.packaged_settings(ref,parent_path,packages)[0]['scope'],'shell-binding')
        for mutate in [lambda v:v['imports'][0].update(metadataSha256='0'*64),lambda v:v['imports'][0].update(packageVersion='1.2.4'),
                       lambda v:v['imports'][0]['assembly'].update(sha256='0'*64),lambda v:v['imports'][0].update(scope='unpublished'),
                       lambda v:v['imports'][0].update(packageId='Missing.Owner'),lambda v:v['imports'][0].update(typeName='Options.Core.SameShapedOtherOptions'),
                       lambda v:v['imports'].append(copy.deepcopy(v['imports'][0]))]:
            bad=copy.deepcopy(parent);mutate(bad);parent_path=pack('Options.Binder',bad);ref['packageSha256']=handoff.digest(parent_path)
            with self.assertRaisesRegex(ValueError,'PKH005|PKH007'):handoff.packaged_settings(ref,parent_path,packages)
        parent_path=pack('Options.Binder',parent);ref['packageSha256']=handoff.digest(parent_path)
        wrong_child=copy.deepcopy(child);wrong_child['contracts'][0]['typeName']='Options.Core.SameShapedOtherOptions'
        pack('Options.Core',wrong_child)
        wrong_parent=copy.deepcopy(parent);wrong_parent['imports'][0]['metadataSha256']=hashlib.sha256(json.dumps(wrong_child).encode()).hexdigest()
        parent_path=pack('Options.Binder',wrong_parent);ref['packageSha256']=handoff.digest(parent_path)
        with self.assertRaisesRegex(ValueError,'PKH005'):handoff.packaged_settings(ref,parent_path,packages)
        pack('Options.Core',child);parent_path=pack('Options.Binder',parent);ref['packageSha256']=handoff.digest(parent_path)
        pack('Options.Core',child,b'changed actual implementation')
        with self.assertRaisesRegex(ValueError,'PKH005'):handoff.packaged_settings(ref,parent_path,packages)
        pack('Options.Core',child)
        required=handoff_contract.applicable_settings([parent,child],{'shells':{'CShells':{'Shells':{'first':{'Features':{'Admission':{}}}}}}},set())
        self.assertEqual(required,{('Options.Binder','shell-binding'),('Options.Core','code-options')})
        self.assertEqual(handoff_contract.applicable_settings([parent,child],{'shells':{'CShells':{'Shells':{'first':{'Features':{}}}}}},set()),set())
        required=handoff_contract.applicable_settings([parent,child],{'shells':{'CShells':{'Shells':{'first':{'Features':{},'Configuration':{'Foundation':{'Options':{}}}}}}}},set())
        self.assertIn(('Options.Binder','shell-binding'),required)

    def test_secret_child_schema_has_no_values_and_requires_explicit_classification(self):
        metadata=copy.deepcopy(self.metadata);metadata.update(schemaVersion=2,appliesTo={'kind':'code','features':[],'configuration':[]})
        item=metadata['settings'][0];item.update(type='object',default={},constraints={'properties':{'Credentials':{'type':'object','nullable':True,'secret':True,'properties':{'Password':{'type':'string','secret':True}}}}})
        handoff.reject_secrets(json.dumps(metadata).encode(),'settings.json')
        mutations=[lambda v:v['settings'][0]['constraints']['properties']['Credentials'].pop('secret'),
                   lambda v:v['settings'][0]['constraints']['properties']['Credentials'].update(default=None),
                   lambda v:v['settings'][0]['constraints']['properties']['Credentials'].update(examples=['secret-value']),
                   lambda v:v['settings'][0]['constraints']['properties']['Credentials']['properties']['Password'].update(default='leaked'),
                   lambda v:v['settings'][0].update(default={'Credentials':{'Password':'leaked'}})]
        for mutate in mutations:
            bad=copy.deepcopy(metadata);mutate(bad)
            with self.assertRaisesRegex(ValueError,'PKH006'):handoff.reject_secrets(json.dumps(bad).encode(),'settings.json')
        with self.assertRaisesRegex(ValueError,'PKH006'):
            handoff.reject_secrets(b'{"Credentials":{"type":"object","secret":true}}','ordinary-input.json')

    def test_public_bearer_prose_is_not_material_but_complete_credentials_still_reject(self):
        import base64
        docs=b'<member><summary>Options class provides information needed to control Bearer Authentication handler behavior</summary></member>'
        handoff.reject_secrets(docs,'lib/net10.0/Microsoft.AspNetCore.Authentication.JwtBearer.xml')
        handoff.reject_secrets(docs,'ordinary-guide.md')
        handoff.reject_secrets(b'The Bearer Authentication handler validates credentials.\nMicrosoft.AspNetCore.Authentication.JwtBearer', 'ordinary-guide.md')
        encode=lambda value:base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b'=')
        jwt=encode({'alg':'HS256','typ':'JWT'})+b'.'+encode({'sub':'private-account'})+b'.c2lnbmF0dXJl'
        cases=[b'Authorization: Bearer actual-secret',b'authorization = "Bearer a"',b'{"Authorization":"Bearer actual-secret"}',
               b'Bearer abcdefghijkl',b'Bearer abcDEF+/123==',b'"Bearer abcdefghijkl"',b"'Bearer actual-secret'",b'`Bearer actual-secret`',
               jwt,b'token='+jwt,b'Bearer '+jwt,b'-----BEGIN PRIVATE KEY-----',b'-----BEGIN RSA PRIVATE KEY-----',
               b'https://account:private-password@example.invalid/resource',b'password: actual-password',b'ClientSecret="actual-secret"',
               b'{"AccessToken":"actual-secret"}',b'{"Credentials":{"Password":"actual-secret"}}']
        for payload in cases:
            with self.subTest(shape=payload[:25]),self.assertRaisesRegex(ValueError,'PKH006'):
                handoff.reject_secrets(payload,'input.json' if payload.startswith(b'{') else 'input.txt')
        # A single linear token scan avoids retrying bounded JWT-header patterns
        # at every position in an ordinary long alphabetic source fragment.
        handoff.reject_secrets(b'plainletters'*100000,'ordinary-source.txt')

    def test_bearer_crlf_assignments_and_oversized_jwt_header_reject(self):
        import base64
        encode=lambda value:base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b'=')
        large=encode({'alg':'HS256','pad':'A'*5000})+b'.e30.c2ln'
        for payload in (b'Bearer opaque-token\r\n',b'AUTH_HEADER=Bearer opaque-token',large,b'opaque='+large):
            with self.subTest(shape=payload[:30]),self.assertRaisesRegex(ValueError,'PKH006'):
                handoff.reject_secrets(payload,'ordinary-input.txt')
        for payload in (b'Bearer Authentication handler behavior\r\n',
                        b'Description: Bearer Authentication handler behavior',
                        b'A'*100000+b'.Namespace.Member',
                        b'ordinary-name-'*10000,
                        b'TypeName'+b'A'*5000+b'.Nested.Member'):
            handoff.reject_secrets(payload,'ordinary-source.txt')

    def test_explicit_secret_source_placeholders_do_not_admit_actual_values(self):
        placeholder=b'your-client-secret-from-user-secrets-or-keyvault'
        sample=b'ClientSecret = "'+placeholder+b'"'
        handoff.reject_secrets(sample,'PACKAGE.md')
        handoff.reject_secrets(sample,'ordinary-guide.txt')
        for payload in (b'ClientSecret="'+placeholder+b'-actual-value"',
                        b'ClientSecret="your-password-from-user-secrets"',
                        b'ClientSecret="your-client-secret-from-arbitrary-vault"',
                        b'ClientSecret="your-client-secret-from-keyvault-actual-value"',
                        b'ClientSecret="actual-secret-from-keyvault"',
                        b'password="your-client-secret-from-user-secrets"',
                        b'{"ClientSecret":"'+placeholder+b'"}'):
            with self.subTest(shape=payload[:50]),self.assertRaisesRegex(ValueError,'PKH006'):
                handoff.reject_secrets(payload,'input.json' if payload.startswith(b'{') else 'input.txt')
        metadata=copy.deepcopy(self.metadata)
        metadata['settings'][0].update(secret=True,default=placeholder.decode())
        with self.assertRaisesRegex(ValueError,'PKH006'):
            handoff.validate_settings_metadata(metadata)

    def test_secret_placeholder_covers_complete_literal_and_jwt_prefix_limit(self):
        import base64
        placeholder=b'your-client-secret-from-keyvault'
        oversized=base64.urlsafe_b64encode(b' '*4096+b'{"alg":"HS256"}').rstrip(b'=')+b'.e30.c2ln'
        for payload in (b'ClientSecret="'+placeholder+b' actual-secret"',
                        b'ClientSecret="'+placeholder+b'\tactual-secret"',
                        b'ClientSecret="'+placeholder+b';actual-secret"',
                        b'ClientSecret="'+placeholder+b',actual-secret"',
                        b'ClientSecret="'+placeholder+b'" + "actual-secret"',
                        b'ClientSecret="'+placeholder+b'"actual-secret',
                        b'ClientSecret="'+placeholder+b"'",
                        b'ClientSecret="'+placeholder,
                        b'ClientSecret='+placeholder+b' actual-secret',
                        b'ClientSecret="'+placeholder+b'\\" actual-secret"',
                        oversized):
            with self.subTest(shape=payload[:60]),self.assertRaisesRegex(ValueError,'PKH006'):
                handoff.reject_secrets(payload,'ordinary-input.txt')
        for payload in (b'ClientSecret="'+placeholder+b'",',
                        b'ClientSecret="'+placeholder+b'";\r\n',
                        b"ClientSecret='"+placeholder+b"'",b'ClientSecret='+placeholder):
            handoff.reject_secrets(payload,'ordinary-guide.txt')

    def test_complete_fictional_connection_literal_never_admits_credentials_or_json(self):
        sample='Host=myserver;Username=mylogin;Password=mypass;Database=mydatabase'
        forms=['var connString = "'+sample+'";', 'optionsBuilder.UseNpgsql(@"'+sample+'");']
        for text in forms:
            handoff.reject_secrets(text.encode(),'README.md')
            handoff.reject_secrets(text.encode(),'ordinary-input.txt')
        changed=[sample.replace('myserver','actual-server'),sample.replace('mylogin','actual-login'),
                 sample.replace('mypass','actual-password'),sample.replace('mydatabase','actual-database'),
                 sample+';Timeout=3',sample+'actual-secret',sample.replace(';Database=mydatabase',''),
                 'Password=mypass;Host=myserver;Username=mylogin;Database=mydatabase']
        cases=['var connString = "'+text+'";' for text in changed]
        cases+=['Password=mypass',sample,'"'+sample+'"', 'var cs = "'+sample+'" + "actual-secret";',
                'var cs = "'+sample+'"\n + "actual-secret";', 'var cs = ("'+sample+'") + "actual-secret";',
                'var cs = $"'+sample+'";', 'var cs = "'+sample+'\\"actual-secret";',
                forms[0]+'\nPassword="actual-secret";']
        json_cases=[{'ConnectionStrings':{'Main':sample}},{'default':['before',sample,'after']},
                    {'default':sample},{'default':forms[0]}]
        for text in cases+[json.dumps(value) for value in json_cases]:
            for name in ('ordinary-input.txt','ordinary-guide.md'):
                with self.subTest(shape=text[:80],name=name),self.assertRaisesRegex(ValueError,'PKH006'):
                    handoff.reject_secrets(text.encode(),name)

    def test_secret_constraint_values_are_rejected_at_every_nested_schema_depth(self):
        from validate_application_handoff import ROOT,TEMPLATE
        sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
        import json_schema
        schema=TEMPLATE/'eng/settings-metadata.schema.json'
        validator,_=json_schema.engine(json_schema.load(schema),schema)
        metadata=copy.deepcopy(self.metadata)
        item=metadata['settings'][0];item.pop('default',None);item['secret']=True
        for key in ('default','example','examples','const','enum'):
            for constraints in ({'items':{key:'value-must-not-export'}},
                                {'properties':{'ordinary-name':{'items':{key:None}}}}):
                item['constraints']=constraints
                with self.assertRaisesRegex(ValueError,'PKH006'):
                    handoff_contract.validate_settings_metadata(metadata)
                self.assertTrue(list(validator.iter_errors(metadata)),'Portable format schema admitted nested secret values.')
        item['secret']=False;item['constraints']={'properties':{'ordinary-name':{'secret':True,'items':{'examples':['value']}}}}
        with self.assertRaisesRegex(ValueError,'PKH006'):
            handoff_contract.validate_settings_metadata(metadata)
        self.assertTrue(list(validator.iter_errors(metadata)))
        item['constraints']={'properties':{'ordinary-name':{'type':'string','secret':True,'maxLength':128}}}
        handoff_contract.validate_settings_metadata(metadata)
        self.assertFalse(list(validator.iter_errors(metadata)))

    def test_actual_fixture_preflight_preserves_existing_evidence_and_rejects_unqualified_inputs(self):
        from types import SimpleNamespace
        import validate_w3_packaged_handoff as native
        output=self.root/'native-evidence';output.mkdir();sentinel=output/'retained.txt';sentinel.write_text('immutable prior evidence')
        args=SimpleNamespace(output=output,f6_result=self.root/'missing.json')
        with self.assertRaisesRegex(ValueError,'NEW'):native.inputs(args)
        self.assertEqual(sentinel.read_text(),'immutable prior evidence')
        args.output=self.root/'new-evidence';args.f6_result=self.root/'f6/result.json'
        self.write('f6/result.json',{'status':'passed','version':'0.3.0-contracts.test.1','actualHost':True})
        self.write('f6/inputs.json',{'version':'0.3.0-contracts.test.1'})
        with self.assertRaisesRegex(ValueError,'Actual matching packaged'):native.inputs(args)
        self.assertFalse(args.output.exists())

    def test_native_cli_paths_preserve_input_identity_across_child_working_directory(self):
        import validate_w3_packaged_handoff as native
        from types import SimpleNamespace
        from unittest.mock import patch
        parent=self.root/'caller';parent.mkdir();child=self.root/'owned-consumer';child.mkdir()
        files=('f6_result','published_tools_result','image_evidence','dotnet','oasdiff')
        directories=('image_root','host_native_packages')
        paths={name:parent/name for name in files+directories+('output',)}
        for name in files:paths[name].write_bytes(('same immutable input '+name).encode())
        for name in directories:paths[name].mkdir()
        args=SimpleNamespace(**{name:Path(name) for name in paths})
        # Resolve against the caller exactly once; the child must receive an
        # absolute path rather than reinterpret the same text under its cwd.
        previous=Path.cwd()
        try:
            os.chdir(parent);native.resolve_cli_paths(args)
            before={name:handoff.digest(getattr(args,name)) for name in files}
            os.chdir(child)
            self.assertEqual({name:handoff.digest(getattr(args,name)) for name in files},before)
            self.assertEqual({name:getattr(args,name) for name in paths},paths)
            exporter=getattr(args,'published_tools_result').parent/'official-tool-cache/exporter.dll'
            self.assertTrue(exporter.is_absolute());self.assertEqual(exporter.parent,parent/'official-tool-cache')
            self.assertFalse(args.output.exists(),'Boundary normalization must not create or qualify output.')
        finally:os.chdir(previous)
        # Exercise the actual CLI boundary without launching native stages.
        unresolved=SimpleNamespace(**{name:Path(name) for name in paths})
        with patch.object(native.argparse.ArgumentParser,'parse_args',return_value=unresolved),patch.object(native,'qualify') as qualify:
            self.assertEqual(native.main(),0)
        admitted=qualify.call_args.args[0]
        self.assertTrue(all(getattr(admitted,name).is_absolute() for name in paths))

    def test_actual_fixture_native_timeout_closes_owned_descendants(self):
        import validate_w3_packaged_handoff as native
        log=self.root/'owned-native.log';heartbeat=self.root/'owned-child.txt'
        child="import pathlib,sys,time\np=pathlib.Path(sys.argv[1])\nwhile True:\n p.write_text(str(time.monotonic()))\n time.sleep(.03)\n"
        parent="import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]])\nprint('owned descendant started',flush=True)\ntime.sleep(30)\n"
        with self.assertRaisesRegex(ValueError,'Native W3 command failed'):
            native.run([sys.executable,'-c',parent,child,str(heartbeat)],self.root,log,dict(os.environ),timeout=1)
        self.assertTrue(heartbeat.is_file(),log.read_text())
        retained=heartbeat.read_text();time.sleep(.15)
        self.assertEqual(heartbeat.read_text(),retained,'Owned descendant remained active after bounded supervisor returned.')
        result=json.loads(log.with_suffix('.process.json').read_text())
        self.assertEqual(result['exitCode'],124)
        self.assertTrue(result['cleanupPolicyApplied'])
        self.assertEqual(result['descendantCleanupObserved'],os.name=='nt')
        native.run([sys.executable,'-c',"print('ordinary native stage accepted')"],self.root,log,dict(os.environ),timeout=10)
        self.assertEqual(json.loads(log.with_suffix('.process.json').read_text())['exitCode'],0)

    def test_native_process_receipt_does_not_infer_unobserved_posix_descendant_exit(self):
        import validate_w3_packaged_handoff as native
        from types import SimpleNamespace
        from unittest.mock import patch
        for code in (0,17,124):
            packets={}
            for platform in ('nt','posix'):
                log=self.root/('receipt-'+platform+'-'+str(code)+'.log')
                # This receipt seam starts no child. The separate actual timeout
                # test establishes the maintained supervisor's Windows cleanup.
                with patch.object(native,'os',SimpleNamespace(name=platform,environ=dict(os.environ))),patch.object(native,'bounded_run',return_value=code):
                    if code:
                        with self.assertRaisesRegex(ValueError,'Native W3 command failed'):
                            native.run(['synthetic-receipt-only'],self.root,log,dict(os.environ),timeout=1)
                    else:native.run(['synthetic-receipt-only'],self.root,log,dict(os.environ),timeout=1)
                packets[platform]=json.loads(log.with_suffix('.process.json').read_text())
            windows=packets['nt'];posix=packets['posix']
            self.assertFalse(posix['descendantCleanupObserved'])
            self.assertTrue(windows['cleanupPolicyApplied']);self.assertTrue(windows['descendantCleanupObserved'])
            self.assertEqual(windows['cleanupObservation'],'windows-job-and-handles')
            self.assertTrue(posix['cleanupPolicyApplied'])
            self.assertEqual(posix['cleanupObservation'],'posix-signal-and-root-wait')
            self.assertEqual(posix['boundedTimeout'],code==124)
            self.assertNotIn('operatorCancellation',posix)

    def test_sdk_and_application_export_capture_use_bounded_receipt_paths(self):
        import ast
        import inspect
        import validate_w3_packaged_handoff as native
        from unittest.mock import patch
        tree=ast.parse(inspect.getsource(native.qualify))
        raw=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
             and isinstance(node.func.value,ast.Name) and node.func.value.id=='subprocess' and node.func.attr=='run']
        self.assertEqual(raw,[],'SDK/version or application export bypasses retained bounded supervision.')
        captured=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                  and node.func.id=='native_output']
        self.assertEqual(len(captured),2,'Both native observation paths must use the same retained-output adapter.')
        for label,payload in [('sdk','10.0.202\n'),('application-metadata','{"schemaVersion":1}\n')]:
            log=self.root/(label+'.log')
            def supervisor(command,**kwargs):
                self.assertEqual(command,['synthetic-'+label]);self.assertEqual(kwargs['stderr'],subprocess.STDOUT)
                self.assertEqual(kwargs['timeout'],600);kwargs['stdout'].write(payload);return 0
            with patch.object(native,'bounded_run',side_effect=supervisor):
                self.assertEqual(native.native_output(['synthetic-'+label],self.root,log,dict(os.environ)),payload.strip())
            receipt=json.loads(log.with_suffix('.process.json').read_text())
            self.assertEqual(receipt['exitCode'],0);self.assertTrue(receipt['cleanupPolicyApplied'])
            self.assertEqual(log.read_text(),payload)
            failed=self.root/(label+'-failure.log')
            def failure(command,**kwargs):kwargs['stdout'].write('retained native failure\n');return 124
            with patch.object(native,'bounded_run',side_effect=failure):
                with self.assertRaisesRegex(ValueError,'Native W3 command failed'):
                    native.native_output(['synthetic-'+label],self.root,failed,dict(os.environ))
            self.assertEqual(failed.read_text(),'retained native failure\n')
            receipt=json.loads(failed.with_suffix('.process.json').read_text())
            self.assertEqual(receipt['exitCode'],124);self.assertTrue(receipt['boundedTimeout'])
            self.assertNotIn('operatorCancellation',receipt)
        oversized=self.root/'oversized-native-observation.log'
        def expansion(command,**kwargs):kwargs['stdout'].write('x'*(handoff_contract.MAX_METADATA+1));return 0
        with patch.object(native,'bounded_run',side_effect=expansion):
            with self.assertRaisesRegex(ValueError,'authority exceeds admitted size'):
                native.native_output(['synthetic-native-expansion'],self.root,oversized,dict(os.environ))
        self.assertTrue(oversized.is_file());self.assertTrue(oversized.with_suffix('.process.json').is_file())

    def test_actual_fixture_pins_require_observed_exact_package_selection(self):
        import validate_w3_packaged_handoff as native
        from xml.etree import ElementTree as ET
        path=self.root/'Directory.Packages.props'
        original='<Project><ItemGroup><PackageVersion Include="Orbyss.Foundation.Json" Version="[$(FoundationRuntimeVersion)]"/><PackageVersion Include="CShells.Abstractions" Version="[0.0.29-preview.147]"/></ItemGroup></Project>'
        observed={'Orbyss.Foundation.Json':'0.3.0-contracts.fixture.6','CShells.Abstractions':'0.0.29-preview.147'}
        path.write_text(original)
        native.native_fixture_pins(path,observed,{'Orbyss.Foundation.Json'},observed['Orbyss.Foundation.Json'])
        self.assertEqual({item.get('Include'):item.get('Version') for item in ET.parse(path).iter('PackageVersion')},observed)
        mutations=[original.replace('[0.0.29-preview.147]','[0.0.29-preview.148]'),
                   original.replace('$(FoundationRuntimeVersion)','$(UnownedVersion)'),
                   original.replace('[0.0.29-preview.147]','[0.0.29-preview.147,0.0.29-preview.148)'),
                   original.replace('</ItemGroup>','<PackageVersion Include="cshells.abstractions" Version="0.0.29-preview.147"/></ItemGroup>')]
        for changed in mutations:
            path.write_text(changed);before=path.read_bytes()
            with self.assertRaises(ValueError):native.native_fixture_pins(path,observed,{'Orbyss.Foundation.Json'},observed['Orbyss.Foundation.Json'])
            self.assertEqual(path.read_bytes(),before,'Rejected native fixture pins replaced the retained inputs.')
        path.write_text(original)
        with self.assertRaisesRegex(ValueError,'outside selected'):
            native.native_fixture_pins(path,observed,set(),observed['Orbyss.Foundation.Json'])

    def native_selection_fixture(self):
        import shutil
        feed=self.root/'selection-f6';closure=self.root/'selection-api';feed.mkdir();closure.mkdir()
        version='0.3.0-contracts.fixture.6';candidates={'Orbyss.Foundation.Json','Orbyss.Foundation.Collections.Core'}
        def package(directory,identity,selected,content=b'bounded synthetic archive'):
            path=directory/(identity+'.'+selected+'.nupkg')
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr(identity+'.nuspec','<package><metadata><id>'+identity+'</id><version>'+selected+'</version></metadata></package>')
                archive.writestr('lib/net10.0/'+identity+'.dll',content)
            return path
        for identity in candidates:package(feed,identity,version)
        shutil.copy2(feed/('Orbyss.Foundation.Json.'+version+'.nupkg'),closure)
        for identity in ('PublishedTools.Contract.Api','PublishedTools.Contract.Core'):package(closure,identity,'1.0.0-fixture.1')
        package(feed,'External.Native','10.0.4');selected=package(feed,'External.Native','10.0.11');shutil.copy2(selected,closure)
        package(feed,'Unrelated.F6.Fixture','1.0.0-fixture.1')
        return feed,closure,candidates,version,package

    def test_exact_consumer_selection_preserves_full_f6_alternate_versions(self):
        import validate_w3_packaged_handoff as native
        feed,closure,candidates,version,package=self.native_selection_fixture()
        before={p.name:handoff.digest(p) for p in feed.glob('*.nupkg')}
        observed,selected=native.selected_consumer_packages(feed,closure,candidates,version)
        self.assertEqual(set(selected),candidates|{'PublishedTools.Contract.Api','PublishedTools.Contract.Core','External.Native'})
        self.assertEqual(observed['External.Native'],'10.0.11');self.assertNotIn('Unrelated.F6.Fixture',selected)
        self.assertEqual({p.name:handoff.digest(p) for p in feed.glob('*.nupkg')},before)
        wrong=package(closure,'Orbyss.Foundation.Json',version,b'changed same identity/version')
        with self.assertRaisesRegex(ValueError,'identity/version/bytes conflict'):
            native.selected_consumer_packages(feed,closure,candidates,version)
        import shutil
        shutil.copy2(feed/wrong.name,wrong)
        ambiguous=package(feed,'Orbyss.Foundation.Json','0.3.0-contracts.other.1')
        with self.assertRaisesRegex(ValueError,'ambiguous exact Foundation'):
            native.selected_consumer_packages(feed,closure,candidates,version)
        ambiguous.unlink();duplicate=package(closure,'External.Native','10.0.4')
        with self.assertRaisesRegex(ValueError,'Ambiguous qualified consumer'):
            native.selected_consumer_packages(feed,closure,candidates,version)
        duplicate.unlink();(feed/('Orbyss.Foundation.Collections.Core.'+version+'.nupkg')).unlink()
        with self.assertRaisesRegex(ValueError,'archive is missing'):
            native.selected_consumer_packages(feed,closure,candidates,version)

    def test_native_root_project_and_actual_assets_archive_binding(self):
        import validate_w3_packaged_handoff as native
        import shutil
        from xml.etree import ElementTree as ET
        feed,closure,candidates,version,package=self.native_selection_fixture()
        observed,selected=native.selected_consumer_packages(feed,closure,candidates,version)
        roots=candidates|{'PublishedTools.Contract.Api','PublishedTools.Contract.Core'}
        project=self.root/'native-closure/RuntimeClosure.csproj';native.closure_project(project,roots,observed)
        model=ET.parse(project)
        self.assertEqual(model.findtext('.//RestoreEnablePackagePruning'),'false')
        self.assertEqual(model.findtext('.//RestorePackagesWithLockFile'),'true')
        self.assertEqual({p.get('Include'):p.get('Version') for p in model.iter('PackageReference')},
                         {identity:'['+observed[identity]+']' for identity in roots})
        cache=self.root/'owned-native-cache';cache.mkdir();libraries={}
        for identity in roots|{'External.Native'}:
            selected_version=observed[identity];relative=identity.lower()+'/'+selected_version
            folder=cache/relative;folder.mkdir(parents=True)
            shutil.copy2(selected[identity],folder/(identity.lower()+'.'+selected_version+'.nupkg'))
            libraries[identity+'/'+selected_version]={'type':'package','path':relative}
        assets=self.root/'native-assets.json';self.write('native-assets.json',{'libraries':libraries,'packageFolders':{str(cache):{}}})
        output=self.root/'native-selected';output.mkdir()
        rows=native.retain_native_closure(assets,cache,roots,observed,selected,(feed,closure),output)
        self.assertEqual(set(rows),roots|{'External.Native'});self.assertEqual(rows['External.Native']['version'],'10.0.11')
        self.assertFalse(any('10.0.4' in p.name for p in output.iterdir()))
        drift=cache/'external.native/10.0.11/external.native.10.0.11.nupkg';package(drift.parent,'External.Native','10.0.11',b'changed cache bytes').replace(drift)
        changed=self.root/'native-changed';changed.mkdir()
        with self.assertRaisesRegex(ValueError,'input/cache/assets'):
            native.retain_native_closure(assets,cache,roots,observed,selected,(feed,closure),changed)
        self.write('native-assets.json',{'libraries':libraries,'packageFolders':{str(self.root/'outside-cache'):{}}})
        with self.assertRaisesRegex(ValueError,'owned cold'):
            native.retain_native_closure(assets,cache,roots,observed,selected,(feed,closure),changed)

    def test_private_host_compilation_contracts_require_actual_archive_dll_bindings(self):
        import validate_w3_packaged_handoff as native
        feed,_,_,_,package=self.native_selection_fixture();host_dir=self.root/'selected-host';host_dir.mkdir()
        host=host_dir/'Orbyss.Foundation.Host.dll';host.write_bytes(b'synthetic host')
        bindings=[]
        for identity in ('CShells.Abstractions','CShells.AspNetCore.Abstractions'):
            packed=package(feed,identity,'0.0.29-preview.147');name=identity+'.dll';(host_dir/name).write_bytes(b'bounded synthetic archive')
            bindings.append({'identity':identity.casefold(),'version':'0.0.29-preview.147','archive':packed.name,
                             'archiveSha256':handoff.digest(packed),'assemblyPath':'lib/net10.0/'+name,'hostAssembly':name,
                             'assemblySha256':handoff.digest(host_dir/name),'omittedRuntimeRoot':True})
        self.assertEqual({v[0] for v in native.host_compilation_packages(bindings,feed,host)},
                         {'CShells.Abstractions','CShells.AspNetCore.Abstractions'})
        for mutate in (lambda v:v.pop(),lambda v:v[0].update(version='0.0.29-preview.148'),
                       lambda v:v[0].update(archiveSha256='0'*64),lambda v:v[0].update(assemblySha256='0'*64)):
            bad=copy.deepcopy(bindings);mutate(bad)
            with self.assertRaises(ValueError):native.host_compilation_packages(bad,feed,host)


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(loader.loadTestsFromName('SettingsAuthorities.'+name,module=sys.modules[__name__])
                              for name in SettingsAuthorities.__dict__ if name.startswith('test_'))


if __name__=='__main__':unittest.main()

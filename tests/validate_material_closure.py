"""Conservative story closure: actual native SDK outcomes and explicit unsupported boundaries."""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
import material_closure as closure
import review_material as material


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='material-closure-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve()
        self.solution=self.root/'Application.slnx'
        self.solution.write_text('<Solution><Project Path="src/StoryA/StoryA.csproj"/></Solution>')
        shutil.copyfile(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json',self.root/'global.json')
        self.write_project('StoryA',False)
        self.write_project('StoryB',True)

    def write_project(self,name,private):
        directory=self.root/'src'/name;directory.mkdir(parents=True,exist_ok=True)
        project=directory/(name+'.csproj')
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
                           '<IsPackable>'+('false' if private else 'true')+'</IsPackable></PropertyGroup></Project>')
        (directory/'Value.cs').write_text('public static class '+name+'Value { public const int Value = 1; }')
        return project

    def project(self):return closure.solution(self.root,self.solution,['src/StoryA/StoryA.csproj'])

    def test_unrelated_private_addition_is_omitted_but_own_new_source_enters_closure(self):
        before=self.project()
        self.solution.write_text('<Solution><Project Path="src/StoryA/StoryA.csproj"/><Project Path="src/StoryB/StoryB.csproj"/></Solution>')
        self.assertEqual(before,self.project())
        (self.root/'src/StoryA/Additional.cs').write_text('public record Additional(int Value);')
        self.assertNotEqual(before,self.project())

    def test_dependency_forward_closure_and_shared_policy_are_material(self):
        project=self.root/'src/StoryA/StoryA.csproj'
        project.write_text(project.read_text().replace('</Project>','<ItemGroup><ProjectReference Include="../StoryB/StoryB.csproj"/></ItemGroup></Project>'))
        before=self.project()
        self.assertIn('src/StoryB/Value.cs',before['sources'])
        (self.root/'src/StoryB/Value.cs').write_text('public static class StoryBValue { public const int Value = 2; }')
        self.assertNotEqual(before,self.project())
        before=self.project()
        (self.root/'Directory.Build.props').write_text('<Project><PropertyGroup><DefineConstants>CHANGED</DefineConstants></PropertyGroup></Project>')
        self.assertNotEqual(before,self.project())

    def test_unknown_member_pack_runtime_import_and_global_policy_fail_closed(self):
        self.solution.write_text('<Solution><Project Path="src/StoryA/StoryA.csproj"/><Project Path="src/StoryB/StoryB.csproj"/></Solution>')
        project=self.root/'src/StoryB/StoryB.csproj';original=project.read_text()
        for changed in (original.replace('<IsPackable>false','<IsPackable>true'),
                        original.replace('</PropertyGroup>','<OutputType>Exe</OutputType></PropertyGroup>'),
                        original.replace('</Project>','<Import Project="custom.targets"/></Project>'),
                        original.replace('</Project>','<Target Name="Prepare" BeforeTargets="Build"/></Project>')):
            project.write_text(changed)
            with self.assertRaises(ValueError):self.project()
        project.write_text(original)
        shared=self.root/'Directory.Solution.targets'
        shared.write_text('<Project><Target Name="Custom" BeforeTargets="Build"/></Project>')
        with self.assertRaisesRegex(ValueError,'shared imports/targets'):self.project()
        shared.unlink()
        response=self.root/'Directory.Build.rsp';response.write_text('-p:DefineConstants=CHANGED')
        with self.assertRaisesRegex(ValueError,'response-file policy'):self.project()
        response.unlink()
        self.solution.write_text('<Solution><Configurations/></Solution>')
        with self.assertRaisesRegex(ValueError,'configurations'):self.project()

    def test_unknown_future_verification_policy_is_bound_or_rejected(self):
        (self.root/'eng').mkdir()
        path=self.root/'eng/verification.json'
        value={'schemaVersion':1,'testGroups':[{'id':'a','projects':['tests/A.csproj'],'inputs':['src/A/**']}],
               'toolkitChecks':[],'unmappedInputs':[],'reason':'owned'}
        path.write_text(json.dumps(value))
        scope={'schemaVersion':1,'inputs':[{'path':'eng/verification.json','kind':'verification','version':1,'projects':['tests/A.csproj']}]}
        before=material.basis(self.root,scope,['eng/verification.json'])
        value['toolkitChecks']=[{'id':'new-owner'}];path.write_text(json.dumps(value))
        self.assertNotEqual(before,material.basis(self.root,scope,['eng/verification.json']))
        value['futureIgnoredPolicy']=True;path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'unknown verification'):material.basis(self.root,scope,['eng/verification.json'])

    def test_architecture_uses_native_validated_fixed_point_and_global_authority(self):
        import validate_bootstrap_semantics as native
        intent=self.root/'docs/architecture/project-intent.md';intent.parent.mkdir(parents=True)
        intent.write_text('Synthetic two story architecture intent')
        value=native.semantic_model(intent)
        path=self.root/'docs/architecture/architecture-map.json'
        path.write_text(json.dumps(value))
        before=closure.architecture(self.root,value,['form-design'])
        value['elements'].append(native.element('private-peer','infrastructure-node','Private peer','Independent later story implementation.','price-calculator'))
        path.write_text(json.dumps(value))
        self.assertEqual(material.digest(before),material.digest(closure.architecture(self.root,value,['form-design'])))
        self.assertTrue(before['strategic_model']['capability_bindings'])
        value['strategic_model']['capability_bindings'][0]['provider_selection']='Changed actual provider selection'
        path.write_text(json.dumps(value))
        self.assertNotEqual(material.digest(before),material.digest(closure.architecture(self.root,value,['form-design'])))
        value['configuration']['properties']['authentication-policy']='changed'
        path.write_text(json.dumps(value))
        self.assertNotEqual(material.digest(before),material.digest(closure.architecture(self.root,value,['form-design'])))
        value['inventedIgnoredPolicy']=True;path.write_text(json.dumps(value))
        with self.assertRaises(Exception):closure.architecture(self.root,value,['form-design'])

    def test_actual_native_two_story_build_pack_runtime_and_accepted_scope(self):
        import validate_story_delivery as stories
        evidence=ROOT/'artifacts/material-closure'/uuid.uuid4().hex;evidence.mkdir(parents=True)
        files=[Path(__file__),Path(closure.__file__),Path(material.__file__),
               ROOT/'extensions/program-kit-governance/scripts/feature_knowledge.py',
               ROOT/'extensions/program-kit-governance/scripts/architecture_map.py',
               ROOT/'extensions/program-kit-governance/scripts/task_draft.py',
               ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json']
        source={file.relative_to(ROOT).as_posix():closure.file_hash(file) for file in files}
        steps=[]
        env=dict(os.environ,NUGET_PACKAGES=str(self.root/'artifacts/nuget'),MSBUILDDISABLENODEREUSE='1',DOTNET_CLI_USE_MSBUILD_SERVER='0')
        empty=self.root/'empty-feed';empty.mkdir()
        def run(*arguments):
            command=['dotnet',*arguments]
            result=subprocess.run(command,cwd=self.root,env=env,capture_output=True,text=True,encoding='utf-8',timeout=120)
            label=str(len(steps))
            for stream in ('stdout','stderr'):(evidence/(label+'.'+stream+'.log')).write_text(getattr(result,stream),encoding='utf-8')
            steps.append({'command':command,'exitCode':result.returncode})
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            return result.stdout.strip()
        try:
            project=self.root/'src/StoryA/StoryA.csproj'
            project.write_text(project.read_text().replace('</PropertyGroup>','<OutputType>Exe</OutputType><ImplicitUsings>enable</ImplicitUsings></PropertyGroup>'))
            (self.root/'src/StoryA/Value.cs').write_text('#if CHANGED\nConsole.WriteLine("changed");\n#else\nConsole.WriteLine("baseline");\n#endif')
            props=self.root/'Directory.Build.props';props.write_text('<Project><PropertyGroup><DefineConstants>BASELINE</DefineConstants></PropertyGroup></Project>')
            def qualify(label):
                run('restore','Application.slnx','--source',str(empty),'--disable-build-servers')
                run('build','Application.slnx','--no-restore','-c','Release','--disable-build-servers','-m:1')
                run('pack','src/StoryA/StoryA.csproj','--no-build','--no-restore','-c','Release','-o','artifacts/'+label)
                archive=next((self.root/'artifacts'/label).glob('*.nupkg'))
                with zipfile.ZipFile(archive) as contents:
                    payload={name:hashlib.sha256(contents.read(name)).hexdigest() for name in contents.namelist()}
                return {'assembly':closure.file_hash(self.root/'src/StoryA/bin/Release/net10.0/StoryA.dll'),
                        'packagePayload':payload,'runtime':run('src/StoryA/bin/Release/net10.0/StoryA.dll')}
            before=qualify('package-before');self.assertEqual('baseline',before['runtime'])
            feature=self.root/'specs/001-fixture';feature.mkdir(parents=True);stories.seed(self.root,feature)
            tasks=feature/'tasks.md';tasks.write_text(tasks.read_text().replace('- [ ] T001','- [X] T001').replace('- [ ] T002','- [X] T002'))
            scope={'schemaVersion':1,'inputs':[{'path':'Application.slnx','kind':'solution-closure','version':1,'projects':['src/StoryA/StoryA.csproj']}]}
            stories.delivery.transition(self.root,feature,{'action':'present','checkpoint':'US1','checks':['artifacts/passing.json'],
                'basisPaths':['Application.slnx'],'materialScope':scope,'entryPoint':'synthetic CLI','preparedData':'synthetic',
                'walkthrough':'run StoryA','expected':'baseline','limitations':'Simulated reviewer; native checks retained separately'},now=0)
            stories.delivery.transition(self.root,feature,{'action':'decision','checkpoint':'US1','actor':'requester','verdict':'accepted',
                'source':'simulated explicit fixture reviewer'},now=0)
            original=copy.deepcopy(stories.delivery.load_delivery(feature)['checkpoints']['US1'])
            basis=material.basis(self.root,scope,['Application.slnx'])
            self.solution.write_text('<Solution><Project Path="src/StoryA/StoryA.csproj"/><Project Path="src/StoryB/StoryB.csproj"/></Solution>')
            after=qualify('package-after');self.assertEqual(before,after)
            self.assertEqual(basis,material.basis(self.root,scope,['Application.slnx']))
            diagnostic=material.explain(self.root,original);self.assertTrue(diagnostic['materialUnchanged'])
            self.assertEqual(original,stories.delivery.load_delivery(feature)['checkpoints']['US1'])
            props.write_text('<Project><PropertyGroup><DefineConstants>CHANGED</DefineConstants></PropertyGroup></Project>')
            self.assertFalse(material.explain(self.root,original)['materialUnchanged'])
            changed=qualify('package-changed');self.assertEqual('changed',changed['runtime'])
            self.assertNotEqual(before['assembly'],changed['assembly'])
            self.assertEqual(source,{file.relative_to(ROOT).as_posix():closure.file_hash(file) for file in files})
            (evidence/'results.json').write_text(json.dumps({'status':'passed','before':before,'afterUnrelatedStory':after,
                'afterSharedPolicy':changed,'steps':steps,'sourceSha256':source,
                'scope':'Actual native build/pack/runtime; fictional reviewer only; no application/human acceptance'},indent=2))
        finally:
            (evidence/'commands.json').write_text(json.dumps(steps,indent=2))
            print('Native material closure evidence: '+str(evidence))


if __name__=='__main__':unittest.main()

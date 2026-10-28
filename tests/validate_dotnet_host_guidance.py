"""Synthetic emitted host review/profile routing, not agent or runtime acceptance."""
import json
import re
import shutil
from pathlib import Path
import subprocess
import sys
import unittest
from owned_fixture import FixtureDirectory
from validate_native_phases import snapshot

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'extensions/program-kit-governance/scripts'
BLOCKS=ROOT/'extensions/program-kit-building-blocks/scripts'
sys.path.insert(0,str(SCRIPTS))
import phase_obligations as phase

class HostGuidance(unittest.TestCase):
    def fixture(self, root, plan, intent='A requester submits requests.'):
        feature=root/'specs/001-request';feature.mkdir(parents=True)
        (feature/'spec.md').write_text('# Submit a request\n'+plan,encoding='utf-8')
        (feature/'plan.md').write_text('# Plan\n'+plan,encoding='utf-8')
        path=root/'docs/architecture/project-intent.md';path.parent.mkdir(parents=True)
        path.write_text(intent,encoding='utf-8')
        return feature

    def test_dotnet_react_default_is_visible_before_focused_lookup_without_state(self):
        for technology in ('.NET', 'ASP.NET Core'):
            with self.subTest(technology=technology),FixtureDirectory() as name:
                root=Path(name);feature=self.fixture(root, technology+' backend, React UI and Minimal APIs. No dynamic activation requirements.')
                before=snapshot(root)
                value=phase.check(root,feature,'after-plan')
                first=phase.text_page(phase.render(value,'after-plan'),1)
                self.assertIn('dotnet',value['responsibilities'])
                for text in ('Orbyss.Foundation.Host','CShells and Nuplane','ghcr.io/orbyss-io/foundation-host',
                             'managed OpenAPI exporter','unresolved choice','Proposed ADR','candidate metadata'):
                    self.assertIn(text,first)
                self.assertIn('program-kit-governance/references/tool-selection.md',first)
                self.assertNotIn('dotnet-host:conventional',value['responsibilities'])
                detailed=phase.render(value,'after-plan',True)
                self.assertEqual(1,detailed.count('Selecting .NET selects `Orbyss.Foundation.Host`'))
                self.assertEqual(before,snapshot(root))

    def test_proposed_custom_host_is_not_adoption_or_optout(self):
        with FixtureDirectory() as name:
            root=Path(name);feature=self.fixture(root,'.NET with React; propose a consumer-owned host and custom exporter. See docs/architecture/decisions/host.md.')
            adr=root/'docs/architecture/decisions/host.md';adr.parent.mkdir()
            adr.write_text('# Conventional host\nStatus: Proposed\nAssistant proposal only; human has not decided.\n',encoding='utf-8')
            before=snapshot(root)
            value=phase.check(root,feature,'after-plan');text=phase.render(value,'after-plan')
            self.assertIn('An assistant-authored Proposed ADR',text)
            self.assertIn('Accepted\nlabel alone cannot establish human consent',text)
            self.assertNotIn('dotnet-host:conventional',value['responsibilities'])
            self.assertEqual(before,snapshot(root))

    def test_explicit_human_optout_remains_an_ordinary_local_choice(self):
        with FixtureDirectory() as name:
            root=Path(name);feature=self.fixture(root,'.NET with React; conventional ASP.NET Core host.',
                'Synthetic human decision: explicitly opt out of Foundation hosting for a fixed appliance.\n'
                'Human accepted a conventional host and its deployment/composition responsibilities.\n')
            before=snapshot(root)
            value=phase.check(root,feature,'planning');text=phase.render(value,'planning')
            self.assertIn('docs/architecture/project-intent.md',value['localGuidance'])
            self.assertIn('Preserve a real human opt-out',text)
            self.assertIn('without a qualification ceremony',text)
            self.assertNotIn('blocked',value)
            self.assertEqual(before,snapshot(root))

    def publisher(self,root,*args):
        result=subprocess.run([sys.executable,str(BLOCKS/'publisher_knowledge.py'),'--target',str(root),*args],
            cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        header,body=result.stdout.split('\n',1)
        count=int(re.search(r'page 1/(\d+)',header)[1])
        for page in range(2,count+1):
            more=subprocess.run([sys.executable,str(BLOCKS/'publisher_knowledge.py'),'--target',str(root),*args,'--page',str(page)],
                cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=30)
            self.assertEqual(0,more.returncode,more.stderr)
            body+=more.stdout.split('\n',1)[1]
        return header,body

    def test_fresh_profile_lookup_reads_index_and_labels_candidate_before_facts(self):
        with FixtureDirectory() as name:
            root=Path(name);before=snapshot(root)
            index=json.loads((BLOCKS.parent/'references/dependency-profiles/index.json').read_text())
            header,listing=self.publisher(root)
            self.assertEqual(index['default'],json.loads(listing)['profile'])
            self.assertIn('source: qualified-default',header)
            self.assertIn('candidate metadata, not consumer adoption or restoration',header)
            header,package=self.publisher(root,'--package','Orbyss.Foundation.OpenApi.Exporter')
            self.assertIn(index['default'],header)
            profile=json.loads((BLOCKS.parent/'references/dependency-profiles'/index['profiles'][index['default']]['path']).read_text())
            self.assertEqual(profile['artifacts']['nuget:Orbyss.Foundation.OpenApi.Exporter'],json.loads(package)['version'])
            self.assertEqual(before,snapshot(root))

    def test_standalone_installed_governance_shows_default_without_dotnet_adapter(self):
        with FixtureDirectory() as name:
            root=Path(name);feature=self.fixture(root,'ASP.NET Core with React and Minimal APIs.')
            installed=root/'.specify/extensions/program-kit-governance'
            shutil.copytree(SCRIPTS.parent,installed,ignore=shutil.ignore_patterns('__pycache__'))
            result=subprocess.run([sys.executable,str(installed/'scripts/phase_obligations.py'),'check',
                '--feature-dir',str(feature.relative_to(root)),'--phase','after-plan'],cwd=root,capture_output=True,
                text=True,encoding='utf-8',timeout=30)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertIn('Orbyss.Foundation.Host',result.stdout)
            self.assertIn('CShells and Nuplane',result.stdout)
            self.assertIn('Proposed ADR',result.stdout)
            self.assertFalse((root/'.specify/extensions/program-kit-dotnet').exists())

    def test_captured_profile_is_preserved_even_when_index_default_is_newer(self):
        sys.path.insert(0,str(BLOCKS));import building_blocks as blocks
        with FixtureDirectory() as name:
            root=Path(name);identity='foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
            catalog=blocks.new_project_catalog(identity)
            index=blocks.load_json(blocks.profile_registry()/'index.json')
            managed=root/'.program-kit/managed.json';managed.parent.mkdir()
            managed.write_text(json.dumps({'newProjectDependencyProfile':{'profile':identity,
                'catalogResolutionSha256':blocks.catalog_resolution_sha256(catalog),
                'entrySha256':blocks.canonical_sha256(index['profiles'][identity])}}),encoding='utf-8')
            before=snapshot(root)
            header,listing=self.publisher(root)
            self.assertEqual(identity,json.loads(listing)['profile'])
            self.assertIn('source: recorded-scaffold',header)
            self.assertIn('restoration and runtime compatibility not established',header)
            self.assertEqual(before,snapshot(root))
            record=json.loads(managed.read_text())
            record['newProjectDependencyProfile']['entrySha256']='0'*64
            managed.write_text(json.dumps(record),encoding='utf-8')
            failed=subprocess.run([sys.executable,str(BLOCKS/'publisher_knowledge.py'),'--target',str(root)],
                cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=30)
            self.assertNotEqual(0,failed.returncode)
            self.assertIn('scaffold authority changed',failed.stdout+failed.stderr)
            self.assertNotIn('source: qualified-default',failed.stdout)


if __name__=='__main__':unittest.main()

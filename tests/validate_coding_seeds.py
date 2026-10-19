"""F5 independent routing/exclusion, finite browser races and actual owned-source syntax checks."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-governance/scripts'),str(ROOT / 'tests')]
from phase_obligations import catalog
from coding_context import compose
from feature_context import context
from owned_fixture import FixtureDirectory

FAMILIES = {'seed-owned-slice','seed-thin-transport','seed-independent-events','seed-service-activation',
            'seed-browser-journey','seed-confirmation-options','seed-valid-construction','seed-relational-conformance',
            'seed-browser-selection','seed-private-diagnostics','seed-journey-context','seed-native-protocol',
            'seed-resource-recovery','seed-selected-inputs'}


class Seeds(unittest.TestCase):
    def test_complete_families_resolve_existing_canonical_owners_and_real_recipe(self):
        value = catalog()
        self.assertEqual(FAMILIES,{u['id'] for u in value['codingUnits'] if u['id'].startswith('seed-')})
        tags = {'all','dotnet','web','api','persistence','capabilities','domain-events','file-selection','resource-fencing','dotnet-io'}
        facts = {key:True for key in ('request','model-owner','contract-owner','effective-projects','verification-owner')}
        selected,_,blockers = compose(value,value['requirements'],tags,facts,ROOT/'extensions')
        self.assertFalse(blockers)
        seeds = [row for row in selected if row['id'] in FAMILIES]
        self.assertEqual(FAMILIES,{row['id'] for row in seeds})
        for row in seeds:
            self.assertTrue(row['rules'])
            self.assertTrue(row['recipes'])
            self.assertFalse(row['applicationObserved'])
        self.assertIn('tests/validate_local_fencing.py',value['rules']['principle.physical-effect-fencing']['bindings']['checks'])
        self.assertNotIn('tests/validate_persistence_runtime.py',value['rules']['principle.physical-effect-fencing']['bindings']['checks'])

    def test_actual_applicability_excludes_events_and_file_work_from_query(self):
        with FixtureDirectory() as temporary:
            root = Path(temporary); feature=root/'specs/query'; feature.mkdir(parents=True)
            (feature/'spec.md').write_text('Read-only .NET HTTP PostgreSQL query.\n')
            (feature/'plan.md').write_text('No independent domain-event reactions or FileReader work are required.\n')
            tags = context(root,feature,'implementation')
            self.assertNotIn('domain-events',tags)
            self.assertNotIn('file-selection',tags)
            facts = {key:True for key in ('request','model-owner','contract-owner','effective-projects','verification-owner')}
            selected,excluded,_=compose(catalog(),catalog()['requirements'],tags,facts,ROOT/'extensions')
            self.assertNotIn('seed-independent-events',{row['id'] for row in selected})
            self.assertIn('seed-independent-events',{row['id'] for row in excluded})
            (feature/'plan.md').write_text('Use independent domain-event reactions with IDomainEventHandler. Browser FileReader selection.\n')
            tags = context(root,feature,'implementation')
            self.assertTrue({'domain-events','file-selection','web'} <= tags)

    def test_real_browser_selection_algorithm_and_independent_stale_guard_mutation(self):
        example=ROOT/'extensions/program-kit-governance/references/file-selection-example.mjs'
        oracle=ROOT/'tests/fixtures/evidence-submission/selection-cases.mjs'
        with FixtureDirectory() as temporary:
            path=Path(temporary)/'invalid.mjs'
            path.write_bytes(example.read_bytes().replace(b'current !== generation',b'false'))
            for source,expected in [(example,0),(path,1)]:
                result=subprocess.run(['node',str(oracle),str(source)],cwd=ROOT,capture_output=True,text=True,timeout=20)
                self.assertEqual(expected,result.returncode,result.stdout+result.stderr)
            successful=subprocess.run(['node',str(oracle),str(example)],cwd=ROOT,capture_output=True,text=True,timeout=20,check=True)
            self.assertEqual(10,len(json.loads(successful.stdout)['cases']))

    def test_current_owned_csharp_and_fourteen_independent_readability_controls(self):
        from csharp_readability_check import check
        paths=[* (ROOT/'extensions/program-kit-dotnet/references/examples/evidence-submission').rglob('*.cs'),
               * (ROOT/'tests/fixtures/evidence-submission').glob('*.cs'),
               * (ROOT/'tests/fixtures/application-lifecycle/Core').glob('*.cs'),
               * (ROOT/'tests/fixtures/application-lifecycle/Runtime').glob('*.cs')]
        self.assertEqual(0,check(paths))


if __name__=='__main__': unittest.main()

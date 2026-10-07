"""Independent automatic updates, promotion and bounded publisher knowledge contracts."""
import importlib.util
import json
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'extensions/program-kit-building-blocks/scripts'))
import update_dependency_profiles as profiles
import publisher_knowledge as knowledge
import dependency_maintenance as maintenance


class WorkflowTests(unittest.TestCase):
    def test_added_knowledge_preserves_existing_authority_but_changed_proof_does_not(self):
        import building_blocks as blocks
        original={'path':'exact.json','sha256':'a'*64,'status':'qualified','evidence':{'path':'proof.json','sha256':'b'*64}}
        expected=blocks.canonical_sha256(original)
        augmented={**original,'knowledge':{'path':'knowledge/index.json','sha256':'c'*64}}
        self.assertTrue(blocks.profile_entry_matches_hash(augmented,expected))
        self.assertFalse(blocks.profile_entry_matches_hash({**augmented,'sha256':'d'*64},expected))
        self.assertFalse(blocks.profile_entry_matches_hash({**augmented,'unreviewedAuthority':True},expected))

    def test_profile_requires_successful_tagged_release_for_exact_package_commit(self):
        commit='a'*40
        spec=('<package><metadata><repository commit="'+commit+'"/></metadata></package>').encode()
        run={'head_branch':'v0.3.0','head_sha':commit,'status':'completed','conclusion':'success','html_url':'https://example.invalid/run'}
        with patch.object(profiles.urllib.request,'urlopen',return_value=io.BytesIO(spec)), patch.object(profiles.maintenance,'fetch',return_value={'workflow_runs':[run]}):
            self.assertEqual(commit,profiles.require_published_foundation('0.3.0')['commit'])
        for field,value in [('head_sha','b'*40),('conclusion','failure'),('head_branch','main')]:
            invalid={**run,field:value}
            with patch.object(profiles.urllib.request,'urlopen',return_value=io.BytesIO(spec)), patch.object(profiles.maintenance,'fetch',return_value={'workflow_runs':[invalid]}):
                with self.assertRaisesRegex(ValueError,'successful tagged Release'): profiles.require_published_foundation('0.3.0')

    def test_prerelease_numbers_sort_numerically_and_stable_is_newer(self):
        values=['1.0.0-preview.9','1.0.0-preview.10','1.0.0-preview.2','1.0.0']
        self.assertEqual(['1.0.0-preview.2','1.0.0-preview.9','1.0.0-preview.10','1.0.0'],
                         sorted(values,key=maintenance.nuget_version_key))

    def test_unqualified_candidate_cannot_change_default(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp); profiles.write(directory/'state.json',{'status':'prepared'})
            with self.assertRaisesRegex(ValueError,'cannot become the default'): profiles.promote(directory)

    def test_knowledge_pages_bound_long_lines_without_losing_unicode(self):
        text='😀'+('interface-schema '*2000)+'é'
        pages=knowledge.bounded_pages(text)
        self.assertEqual(text,''.join(pages))
        self.assertTrue(all(len(page.encode('utf-8'))<=12000 for page in pages))

    def test_indexed_source_reads_only_the_selected_document_and_rejects_invalid_ranges(self):
        import building_blocks as blocks
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'source.pack').write_bytes(b'first'+ 'second😀'.encode())
            document={'path':'source.pack','byteOffset':5,'byteLength':10}
            self.assertEqual('second😀',blocks.publisher_document_bytes(root,document).decode())
            for invalid in ({**document,'byteOffset':-1},{**document,'byteLength':100},{**document,'path':'../outside'}):
                with self.assertRaises(blocks.ResolverError): blocks.publisher_document_bytes(root,invalid)

    def test_indexed_package_facts_preserve_identity_and_utf8(self):
        import building_blocks as blocks
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); value={'id':'Orbyss.Foundation.Json','version':'0.3.1','facts':{'readme.md':'é😀'}}
            data=json.dumps(value,ensure_ascii=False).encode(); (root/'package.pack').write_bytes(b'prefix'+data+b'suffix')
            row={'path':'package.pack','byteOffset':6,'byteLength':len(data)}
            self.assertEqual(value,blocks.publisher_package_fact(root,row))

    def test_full_update_uses_complete_deterministic_inventory_without_release_receipt(self):
        text=(ROOT/'scripts/update_dependencies.py').read_text()
        self.assertIn("else 'PullRequest'",text)
        self.assertNotIn('--changed-from',text)
        self.assertNotIn('--receipt',text)
        self.assertNotIn('live-acceptance',text)
        workflow=(ROOT/'.github/workflows/update-dependencies.yml').read_text()
        ordered=['dependency_maintenance.py upgrade','update_dependency_profiles.py update',
                 'update_dependencies.py','dependency_maintenance.py scan','gh pr create']
        self.assertEqual(sorted(workflow.index(stage) for stage in ordered),[workflow.index(stage) for stage in ordered])
        self.assertIn('chromium,firefox,webkit',workflow)


if __name__=='__main__': unittest.main()

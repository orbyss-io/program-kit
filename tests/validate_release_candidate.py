"""Offline failure tests for package integrity and native publication boundaries."""
from __future__ import annotations

import copy
from datetime import timedelta
import hashlib
import io
from pathlib import Path
import sys
from types import SimpleNamespace
from owned_fixture import FixtureDirectory
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import release_candidate as rc
import publish_candidate as publication
from publish_candidate import publication_plan


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = FixtureDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.identity = {'commit': 'a' * 40, 'tree': 'b' * 40, 'version': '1.0.0', 'policySha256': 'c' * 64}
        self.rules = rc.policy()
        self.run = {'id': 12, 'run_attempt': 1, 'repository': {'full_name': self.rules['repository']},
                    'path': self.rules['workflow'], 'event': 'workflow_dispatch', 'head_branch': 'main',
                    'head_sha': self.identity['commit'], 'status': 'completed', 'conclusion': 'success'}
        self.jobs = [{'name': n, 'conclusion': 'success'} for n in self.rules['requiredJobs']]

    def payload(self):
        path = self.root / 'package.zip'
        path.write_bytes(b'qualified package')
        record = {'name': path.name, 'size': path.stat().st_size, 'sha256': rc.sha256(path)}
        return {'schemaVersion': 1, 'source': self.identity, 'assets': [record]}

    def verify(self, value):
        # Inventory derivation itself is exercised by release-guidance/package fixtures.
        expected = [{'path': 'artifacts/package.zip', **{k: v for k, v in self.payload()['assets'][0].items() if k != 'name'}}]
        with patch.object(rc, 'artifact_records', return_value=expected):
            rc.verify_payload(value, self.root, self.identity)

    def test_native_publication_boundaries(self):
        from release_workflow_contracts import validate_workflows
        validate_workflows()

    def test_payload_changes_and_missing_assets_block(self):
        value = self.payload()
        self.verify(value)
        for field, changed in [('sha256', 'd'*64), ('size', 0), ('name', 'missing.zip')]:
            bad = copy.deepcopy(value); bad['assets'][0][field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError): self.verify(bad)
        bad = copy.deepcopy(value); bad['source']['commit'] = 'd'*40
        with self.assertRaises(ValueError): self.verify(bad)

    def test_manifest_cannot_hide_or_add_files(self):
        value = self.payload()
        for records in ([], [*value['assets'], *value['assets']], [{**value['assets'][0], 'name': '../package.zip'}]):
            with self.subTest(records=records), self.assertRaises(ValueError): self.verify({**value, 'assets': records})
        with patch.object(rc, 'artifact_records', return_value=[]), self.assertRaises(ValueError):
            rc.verify_payload(value, self.root, self.identity)

    def test_exact_successful_main_run_and_every_required_job(self):
        rc.verify_run(self.run, self.jobs, self.identity, self.rules)
        mutations = {'head_sha': 'd'*40, 'head_branch': 'untrusted', 'path': '.github/workflows/ci.yml',
                     'event': 'pull_request', 'conclusion': 'failure', 'status': 'in_progress',
                     'repository': {'full_name': 'other/repository'}}
        for key, changed in mutations.items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                rc.verify_run({**self.run, key: changed}, self.jobs, self.identity, self.rules)
        for job in self.jobs:
            with self.subTest(job=job['name']), self.assertRaises(ValueError):
                rc.verify_run(self.run, [j for j in self.jobs if j != job], self.identity, self.rules)
            with self.assertRaises(ValueError):
                rc.verify_run(self.run, [{**j, 'conclusion':'skipped'} if j == job else j for j in self.jobs], self.identity, self.rules)

    def archive(self, name='package.zip', content=b'payload'):
        stream = io.BytesIO()
        info = zipfile.ZipInfo('entry')
        info.filename = name
        with zipfile.ZipFile(stream, 'w') as archive: archive.writestr(info, content)
        data = stream.getvalue()
        return data, {'id': 1, 'digest': 'sha256:' + hashlib.sha256(data).hexdigest()}

    def test_download_rejects_digest_changes_and_unsafe_paths(self):
        data, record = self.archive()
        with patch.object(rc, 'gh', return_value=data+b'changed'), self.assertRaisesRegex(ValueError, 'digest'):
            rc.download(record, self.root / 'bad')
        for name in ('../escape', '/absolute', 'C:/drive', 'folder\\escape'):
            data, record = self.archive(name)
            with self.subTest(name=name), patch.object(rc, 'gh', return_value=data), self.assertRaises(ValueError):
                rc.download(record, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_download_preserves_differing_existing_data(self):
        data, record = self.archive()
        destination = self.root / 'download'
        with patch.object(rc, 'gh', return_value=data):
            rc.download(record, destination)
            rc.download(record, destination)
            (destination / 'package.zip').write_bytes(b'valuable earlier evidence')
            with self.assertRaisesRegex(ValueError, 'Preserve'): rc.download(record, destination)
        self.assertEqual(b'valuable earlier evidence', (destination / 'package.zip').read_bytes())

    def test_publication_is_idempotent_but_never_clobbers_public_bytes(self):
        content = b'qualified package'
        records = [{'name':'package.zip', 'size': len(content), 'sha256':hashlib.sha256(content).hexdigest()}]
        self.assertEqual(['package.zip'], publication_plan(records, [], lambda _: content))
        self.assertEqual([], publication_plan(records, [{'name':'package.zip'}], lambda _: content))
        with self.assertRaisesRegex(ValueError, 'Differing'):
            publication_plan(records, [{'name':'package.zip'}], lambda _: b'incorrect')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            publication_plan(records, [{'name':'unexpected.zip'}], lambda _: b'')

    def test_unconfigured_environment_cannot_silently_publish(self):
        for rules in ([], [{'type':'wait_timer'}], [{'type':'required_reviewers','reviewers': []}], [{'type':'required_reviewers','reviewers':[{'id':1}],'prevent_self_review':True}]):
            with self.subTest(rules=rules), patch.object(rc, 'api', return_value={'protection_rules':rules}), self.assertRaises(ValueError):
                rc.assert_environment()
        with patch.object(rc, 'api', return_value={'protection_rules':[{'type':'required_reviewers','reviewers':[{'id':1}]}]}):
            rc.assert_environment()

    def test_approval_cannot_outlive_scan_or_switch_artifacts(self):
        payload = self.payload()
        with patch.object(rc, 'fetch_candidate', return_value=(payload, 'd'*64)):
            with self.assertRaisesRegex(ValueError, 'changed since approval'):
                rc.verify_promotion(1, self.root, expected_payload='e'*64)
            for observed in (rc.now()-timedelta(hours=25), rc.now()+timedelta(hours=1)):
                with self.assertRaisesRegex(ValueError, 'Security expired'):
                    rc.verify_promotion(1, self.root, security_observed_at=observed.isoformat())
            rc.verify_promotion(1, self.root, expected_payload='d'*64, security_observed_at=rc.now().isoformat())

    def test_security_reuses_current_scan_and_refreshes_only_expired_scan(self):
        manifest = self.payload()
        rc.write(self.root / 'payload/candidate-payload.json', manifest)
        record = {'status':'passed','source':self.identity,'payloadSha256':rc.sha256(self.root / 'payload/candidate-payload.json'),
                  'target':'registry.example/host@sha256:'+'a'*64,'observedAt':rc.now().isoformat()}
        rc.write(self.root / 'security/security.json', record)
        module = SimpleNamespace(default_host=lambda *args: record['target'])
        with patch.dict(sys.modules, {'dependency_maintenance':module}), patch.object(rc,'source',return_value=self.identity), patch.object(rc,'scan_security') as scan:
            rc.ensure_security(self.root, self.root / 'reused')
            scan.assert_not_called()
            self.assertEqual(record, rc.read(self.root / 'reused/security.json'))
            rc.write(self.root / 'security/security.json', {**record,'observedAt':(rc.now()-timedelta(hours=25)).isoformat()})
            rc.ensure_security(self.root, self.root / 'refreshed')
            scan.assert_called_once_with(self.root / 'payload/candidate-payload.json', self.root / 'refreshed')
            rc.write(self.root / 'security/security.json', {**record,'source':{**self.identity,'commit':'d'*40}})
            with self.assertRaisesRegex(ValueError,'binding/result'): rc.ensure_security(self.root, self.root / 'bad')

    def test_same_source_tag_retry_is_safe_and_lookup_errors_never_create(self):
        rc.write(self.root / 'promotion.json', {'source':self.identity})
        result = SimpleNamespace(returncode=0, stdout=__import__('json').dumps({'object':{'type':'commit','sha':self.identity['commit']}}).encode(), stderr=b'')
        with patch.object(publication,'source',return_value=self.identity), patch.object(publication.subprocess,'run',return_value=result), patch.object(publication,'gh') as gh, patch.object(publication,'git') as git:
            publication.create_tag('v1.0.0',self.root)
            gh.assert_not_called()
            git.assert_called_once()
            result.stdout=__import__('json').dumps({'object':{'type':'commit','sha':'d'*40}}).encode()
            with self.assertRaisesRegex(ValueError,'another source'): publication.create_tag('v1.0.0',self.root)
            result.returncode=1; result.stderr=b'HTTP 403 Forbidden'
            with self.assertRaisesRegex(ValueError,'lookup failed'): publication.create_tag('v1.0.0',self.root)
            gh.assert_not_called()
            result.stderr=b'HTTP 404 Not Found'
            publication.create_tag('v1.0.0',self.root)
            self.assertIn('POST',gh.call_args.args)

    def test_runtime_overrun_remains_nonpassing_and_retains_summary(self):
        current = rc.now()
        environment = {'GITHUB_RUN_ID':'12','CI_BUDGET_SECONDS':'600',
                       'GITHUB_STEP_SUMMARY':str(self.root / 'summary.md')}
        with patch.dict(rc.os.environ,environment), patch.object(rc,'source',return_value=self.identity), patch.object(rc,'now',return_value=current):
            for seconds in (60,601):
                run = {**self.run,'created_at':(current-timedelta(seconds=seconds)).isoformat()}
                with patch.object(rc,'run_metadata',return_value=(run,self.jobs)):
                    if seconds > 600:
                        with self.assertRaisesRegex(ValueError,'exceeded its budget'): rc.timing_summary()
                    else: rc.timing_summary()
            self.assertIn('601.0s', (self.root / 'summary.md').read_text())

    def test_newer_failed_or_pending_candidate_cannot_hide_behind_older_success(self):
        older = {**self.run,'created_at':(rc.now()-timedelta(hours=1)).isoformat()}
        latest = {**self.run,'id':13,'created_at':rc.now().isoformat()}
        with patch.object(rc,'source',return_value=self.identity), patch.object(rc,'artifact_metadata'):
            for changes in ({'conclusion':'failure'}, {'status':'in_progress','conclusion':None}):
                failed = {**latest,**changes}
                with patch.object(rc,'pages',return_value=[older,failed]), patch.object(rc,'run_metadata',return_value=(failed,self.jobs)):
                    with self.assertRaisesRegex(ValueError,'successful exact-source'): rc.find_candidate()
                with patch.object(rc,'latest_candidate_run',return_value=failed), patch.object(rc,'run_metadata',return_value=(older,self.jobs)):
                    with self.assertRaisesRegex(ValueError,'newer exact-source'): rc.fetch_candidate(older['id'],self.root/'candidate')
            with patch.object(rc,'pages',return_value=[older,latest]), patch.object(rc,'run_metadata',return_value=(latest,self.jobs)):
                self.assertEqual(13,rc.find_candidate())


if __name__ == '__main__': unittest.main()

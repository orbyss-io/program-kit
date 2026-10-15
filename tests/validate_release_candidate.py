"""Adversarial candidate handoff fixtures; no publication, builders or agents."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import release_candidate as rc
import run_validation as runner
from publish_candidate import publication_plan

# Activate the existing pinned runtime once; fixture roots hold data, not tools.
rc.schema(rc.read(ROOT / 'release-policy.json'), 'release-policy')
from jsonschema import Draft202012Validator, ValidationError


def validate_fixture(value, name):
    Draft202012Validator(rc.read(ROOT / 'tests/schemas' / (name + '.schema.json'))).validate(value)


class CandidateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.rules = rc.read(ROOT / 'release-policy.json')
        self.identity = {'commit': 'a' * 40, 'tree': 'b' * 40, 'version': '0.0.1',
                         'policySha256': 'c' * 64, 'inventorySha256': 'd' * 64}
        self.digest = 'e' * 64
        checks = [{'id': 'build-release', 'command': ['{python}', 'scripts/build_release.py'],
                   'qualification': {'build': True, 'linux': False, 'windows': False}},
                  {'id': 'dev', 'command': ['{python}', 'tests/dev.py'],
                   'qualification': {'build': False, 'linux': True, 'windows': True}}]
        rc.write(self.root / 'tests/validation-inventory.json', {'checks': checks})
        for mocked in (patch.object(rc, 'ROOT', self.root), patch.object(rc, 'schema', side_effect=validate_fixture),
                       patch.object(rc, 'policy', return_value=self.rules)):
            mocked.start(); self.addCleanup(mocked.stop)
        self.run = {'id': 5, 'run_attempt': 1, 'repository': {'full_name': self.rules['repository']},
                    'head_repository': {'full_name': self.rules['repository']},
                    'path': self.rules['workflows']['qualification'], 'event': 'workflow_dispatch',
                    'head_branch': 'main', 'head_sha': self.identity['commit'], 'status': 'completed', 'conclusion': 'success'}
        self.jobs = [{'name': name, 'conclusion': 'success', 'head_sha': self.identity['commit']}
                     for name in self.rules['requiredJobs']]

    def security(self, **changes):
        value = {'schemaVersion': 1, 'candidate': self.digest, 'source': self.identity, 'payloadSha256': 'f'*64, 'targets': ['image@sha256:' + '1' * 64],
                 'status': 'passed', 'observedAt': rc.now().isoformat(), 'runId': 5, 'attempt': 1,
                 'identity': '5/1', 'scanner': 'fixture scanner', 'report': {'scans': [dict(platform=p, exitCode=0, validationErrors=[], image='image@sha256:'+'1'*64, reportedPlatform=p, imageID='sha256:'+'2'*64, configDigest='sha256:'+'2'*64, manifestDigest='sha256:'+'3'*64, sha256='4'*64) for p in ('linux/amd64','linux/arm64')]}, 'supersedes': []}
        return dict(value, **changes)

    def assessment(self, **changes):
        value = {'schemaVersion': 1, 'candidate': self.digest, 'source': self.identity, 'payloadSha256': 'f'*64, 'recordedAt': rc.now().isoformat(),
                 'runId': 10, 'attempt': 1, 'ready': True, 'review': {'actor': 'human', 'reference': 'review/10'},
                 'summary': 'No AI trial run; no AI acceptance claim.', 'recommendations': [],
                 'selectedTrials': [], 'trials': [], 'findings': [], 'supersedes': []}
        return dict(value, **changes)

    def qualification(self):
        return {'schemaVersion': 1, 'source': self.identity,
                'producer': {'repository': self.rules['repository'], 'workflow': self.rules['workflows']['qualification'],
                             'workflowRevision': self.identity['commit'], 'runId': 5, 'attempt': 1},
                'payloadSha256': 'f' * 64, 'lanes': ['build', 'linux', 'windows'],
                'coverage': {'build': ['build-release'], 'linux': ['dev', 'prepare-qualified-packages'],
                             'windows': ['dev', 'prepare-qualified-packages']}, 'browsers': self.rules['browsers'],
                'artifacts': {name: {'id': i, 'name': name + '-1', 'digest': 'sha256:' + str(i) * 64}
                              for i, name in enumerate(('payload', 'build', 'linux', 'windows', 'security'), 1)},
                'security': self.security(candidate='f' * 64), 'finishedAt': rc.now().isoformat()}

    def test_complete_source_producer_attempt_and_job_variants(self):
        q = self.qualification()
        rc.verify_qualification(q, self.identity, self.run, self.jobs, self.rules)
        for key, bad in [('head_sha', '9' * 40), ('path', '.github/workflows/ci.yml'), ('event', 'pull_request'),
                         ('head_branch', 'topic'), ('run_attempt', 2), ('conclusion', 'failure')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                rc.verify_qualification(q, self.identity, dict(self.run, **{key: bad}), self.jobs, self.rules)
        for key in ('repository', 'head_repository'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                rc.verify_qualification(q, self.identity, dict(self.run, **{key: {'full_name': 'fork/kit'}}), self.jobs, self.rules)
        for name in self.rules['requiredJobs']:
            with self.subTest(job=name), self.assertRaises(ValueError):
                rc.verify_qualification(q, self.identity, self.run, [j for j in self.jobs if j['name'] != name], self.rules)
        for mutation in ('source', 'coverage', 'browser', 'artifact', 'cycle'):
            bad = copy.deepcopy(q)
            if mutation == 'source': bad['source']['tree'] = '0' * 40
            if mutation == 'coverage': bad['coverage']['windows'].remove('dev')
            if mutation == 'browser': bad['browsers'] = ['chromium', 'webkit']
            if mutation == 'artifact': del bad['artifacts']['windows']
            if mutation == 'cycle': bad['artifacts']['qualification'] = bad['artifacts']['payload']
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, ValidationError)):
                rc.verify_qualification(bad, self.identity, self.run, self.jobs, self.rules)

    def test_wrong_planned_tag_rejects_before_any_publication(self):
        with patch.object(rc, 'fetch_candidate', return_value=(self.qualification(), self.digest)):
            with self.assertRaisesRegex(ValueError, 'Tag/VERSION'):
                rc.verify_promotion(5, self.root / 'promotion', tag='v9.9.9')

    def payload(self):
        directory = self.root / 'payload'; directory.mkdir()
        version = self.identity['version']
        names = [f'{name}-{version}.zip' for name in ('program-kit-governance', 'program-kit-building-blocks',
                 'program-kit-dotnet', 'program-kit-governance-preset', 'program-kit-bootstrap', 'program-kit')]
        names += [f'Initialize-ProgramKit-{version}.cmd', f'Initialize-ProgramKit-{version}.sh',
                  f'RELEASE-NOTES-{version}.md', f'MIGRATIONS-{version}.md']
        for name in names: (directory / name).write_bytes(('fixture: ' + name).encode())
        rc.write(directory / f'migration-index-{version}.json', {'entries': [{'guide': 'migration-extra.md'}]})
        (directory / 'migration-extra.md').write_text('actual indexed guide')
        profile = directory / 'dependency-profile-exact.json'; profile.write_text('{}')
        evidence = directory / 'dependency-qualification-exact.json'; evidence.write_text('{}')
        rc.write(directory / f'dependency-profile-index-{version}.json', {'schemaVersion': 1, 'profiles': [{
            'profile': {'file': profile.name, 'sha256': rc.sha256(profile)},
            'evidence': {'file': evidence.name, 'sha256': rc.sha256(evidence)}}]})
        (directory / 'SHA256SUMS').write_text(''.join(rc.sha256(p) + '  ' + p.name + '\n' for p in sorted(directory.iterdir())))
        records = rc.artifact_records(directory, version)
        manifest = {'schemaVersion': 1, 'source': self.identity, 'assets': [
            {'name': Path(r['path']).name, 'size': r['size'], 'sha256': r['sha256']} for r in records]}
        return directory, manifest

    def test_payload_transitive_assets_and_replaced_checksum_cannot_replace_authenticated_manifest(self):
        directory, manifest = self.payload()
        rc.verify_payload(manifest, directory, self.identity)
        for name in ('migration-extra.md', 'dependency-qualification-exact.json', 'RELEASE-NOTES-0.0.1.md'):
            path = directory / name; original = path.read_bytes(); path.unlink()
            with self.subTest(name=name), self.assertRaises(ValueError): rc.verify_payload(manifest, directory, self.identity)
            path.write_bytes(original)
        archive = directory / 'program-kit-0.0.1.zip'; archive.write_bytes(b'replaced package')
        sums = directory / 'SHA256SUMS'
        sums.write_text(''.join(rc.sha256(p) + '  ' + p.name + '\n' for p in sorted(directory.iterdir()) if p != sums))
        with self.assertRaises(ValueError): rc.verify_payload(manifest, directory, self.identity)

    def test_archive_download_checks_actual_bytes_before_extraction(self):
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w') as z: z.writestr('file.txt', b'original')
        data = content.getvalue(); record = {'id': 4, 'expired': False, 'digest': 'sha256:' + hashlib.sha256(data).hexdigest()}
        with patch.object(rc, 'gh', return_value=data):
            rc.download(record, self.root / 'ok')
        with patch.object(rc, 'gh', return_value=data + b'tampered'), self.assertRaisesRegex(ValueError, 'digest mismatch'):
            rc.download(record, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())
        with patch.object(rc, 'gh', return_value=data), self.assertRaisesRegex(ValueError, 'expired'):
            rc.download(dict(record, expired=True), self.root / 'expired')

    def test_artifact_expiry_and_missing_api_object(self):
        at = rc.now()
        record = {'id': 1, 'name': 'payload-1', 'expired': False, 'expires_at': (at + timedelta(days=1)).isoformat(), 'digest': 'sha256:' + '1' * 64}
        with patch.object(rc, 'pages', return_value=[record]): self.assertEqual(record, rc.artifact_metadata(5, 'payload-1'))
        for records in ([], [dict(record, expired=True)], [dict(record, expires_at=(at-timedelta(seconds=1)).isoformat())]):
            with patch.object(rc, 'pages', return_value=records), self.assertRaises(ValueError): rc.artifact_metadata(5, 'payload-1')

    def test_original_journal_log_command_and_tested_byte_stability(self):
        lane = self.root / 'lane'; lane.mkdir()
        journal = {'source': {k: self.identity[k] for k in ('commit', 'tree')}, 'inventorySha256': self.identity['inventorySha256'],
                   'packageInput': {'manifestSha256': self.digest, 'assetsBefore': [{'name': 'fixture'}]},
                   'platform': 'Linux', 'status': 'passed', 'browserEngines': 'chromium,firefox,webkit',
                   'executables': {'python': '/actual/python', 'powershell': '/actual/pwsh', 'mixedPython': None}, 'steps': []}
        for identity, cmd in [('dev', ['/actual/python', 'tests/dev.py']), ('prepare-qualified-packages',
                              ['/actual/python', 'scripts/release_candidate.py', 'verify-payload', '--manifest', 'artifacts/candidate-payload.json'])]:
            log = lane / (identity + '.log'); log.write_text('actual fixture output')
            journal['steps'].append({'id': identity, 'command': cmd, 'exitCode': 0, 'log': log.name, 'logSha256': rc.sha256(log)})
        rc.write(lane / 'journal.json', journal)
        value = {'lane': 'linux', 'source': self.identity, 'payloadSha256': self.digest, 'platform': {'system': 'Linux'},
                 'journals': [journal], 'journalRecords': [{'path': 'journal.json', 'sha256': rc.sha256(lane / 'journal.json')}],
                 'beforeAssets': [{'name': 'fixture'}], 'afterAssets': [{'name': 'fixture'}]}
        rc.verify_lane(value, 'linux', self.identity, self.digest, lane, [{'name': 'fixture'}])
        bad = copy.deepcopy(value); bad['afterAssets'] = []
        with self.assertRaisesRegex(ValueError, 'bytes changed'): rc.verify_lane(bad, 'linux', self.identity, self.digest, lane)
        (lane / 'dev.log').write_text('different original log')
        with self.assertRaisesRegex(ValueError, 'log missing/changed'): rc.verify_lane(value, 'linux', self.identity, self.digest, lane)

    def test_security_boundary_future_wrong_target_and_later_failure_supersession(self):
        at = rc.now(); passing = self.security(observedAt=(at-timedelta(hours=24)).isoformat())
        rc.select_security([passing], self.digest, passing['targets'], self.rules, at)
        for change in ({'observedAt': (at-timedelta(hours=24, microseconds=1)).isoformat()},
                       {'observedAt': (at+timedelta(seconds=1)).isoformat()}, {'candidate': '9'*64}, {'targets': ['wrong']}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                rc.select_security([dict(passing, **change)], self.digest, passing['targets'], self.rules, at)
        failed = self.security(status='failed', identity='6/1', runId=6, observedAt=(at-timedelta(minutes=2)).isoformat())
        with self.assertRaises(ValueError): rc.select_security([passing, failed], self.digest, passing['targets'], self.rules, at)
        repair = self.security(identity='7/1', runId=7, observedAt=(at-timedelta(minutes=1)).isoformat(), supersedes=['6/1'])
        self.assertEqual(repair, rc.select_security([passing, failed, repair], self.digest, passing['targets'], self.rules, at))
        with self.assertRaises(ValueError): rc.select_security([passing, failed, dict(repair, supersedes=[])], self.digest, passing['targets'], self.rules, at)

    def test_newer_defect_blocks_old_readiness_until_explicit_resolution(self):
        at = rc.now()
        passing = self.assessment(recordedAt=(at-timedelta(minutes=3)).isoformat())
        self.assertEqual(passing, rc.select_assessment([passing], self.digest))
        finding = {'id': 'bug-1', 'kind': 'product-defect', 'status': 'open', 'description': 'Confirmed fixture defect', 'resolution': ''}
        failing = self.assessment(runId=11, ready=False, recordedAt=(at-timedelta(minutes=2)).isoformat(), findings=[finding])
        newer = self.assessment(runId=12, recordedAt=(at-timedelta(minutes=1)).isoformat())
        with self.assertRaises(ValueError): rc.select_assessment([passing, failing, newer], self.digest)
        resolved = dict(newer, findings=[dict(finding, status='resolved', resolution='Repair evidence ref/digest')])
        self.assertEqual(resolved, rc.select_assessment([passing, failing, resolved], self.digest))
        claimed = dict(newer, trials=[{'phase': 'bootstrap-checkpoint', 'scope': 'fixture', 'outcome': 'inconclusive',
            'provenance': 'human-attested', 'manifest': {'reference': 'internal/run.json', 'sha256': '1'*64}, 'disposition': ''}])
        with self.assertRaises(ValueError): rc.select_assessment([claimed], self.digest)

    def test_requalification_cannot_erase_same_source_payload_failures_or_findings(self):
        old = self.assessment(candidate='9'*64, ready=False, findings=[{'id': 'bug-1', 'kind': 'product-defect',
            'status': 'open', 'description': 'Confirmed on identical bytes under another qualification', 'resolution': ''}])
        new = self.assessment(runId=12)
        binding = {'identity': self.identity, 'payload_sha': 'f'*64}
        with self.assertRaisesRegex(ValueError, 'Unresolved confirmed'):
            rc.select_assessment([old, new], self.digest, **binding)
        resolved = dict(new, findings=[dict(old['findings'][0], status='resolved', resolution='Exact repair/disposition reference')])
        self.assertEqual(resolved, rc.select_assessment([old, resolved], self.digest, **binding))
        failed = self.security(candidate='9'*64, status='failed', identity='6/1')
        passed = self.security(runId=7, identity='7/1')
        with self.assertRaisesRegex(ValueError, 'failed security'):
            rc.select_security([failed, passed], self.digest, failed['targets'], self.rules, **binding)
        self.assertEqual('7/1', rc.select_security([failed, dict(passed, supersedes=['6/1'])], self.digest,
                                                 failed['targets'], self.rules, **binding)['identity'])
        with self.assertRaisesRegex(ValueError, 'source/payload'):
            rc.select_assessment([dict(new, payloadSha256='0'*64)], self.digest, **binding)

    def test_publication_retries_identical_assets_and_refuses_clobber(self):
        record = {'name': 'archive.zip', 'size': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()}
        self.assertEqual(['archive.zip'], publication_plan([record], [], lambda _: b'abc'))
        self.assertEqual([], publication_plan([record], [{'name': 'archive.zip'}], lambda _: b'abc'))
        with self.assertRaises(ValueError): publication_plan([record], [{'name': 'archive.zip'}], lambda _: b'def')
        with self.assertRaises(ValueError): publication_plan([record], [{'name': 'unexpected'}], lambda _: b'abc')

    def test_recorder_signature_binds_run_and_attempt(self):
        good = [{'verificationResult': {'signature': {'certificate': {'runInvocationURI':
                 'https://github.com/orbyss-io/program-kit/actions/runs/5/attempts/1'}}}}]
        with patch.object(rc, 'gh', return_value=json.dumps(good)) as call:
            rc.attest_verify(self.root / 'qualification.json', 'qualification', self.identity['commit'], 5, 1)
            self.assertIn('--source-digest', call.call_args.args)
            self.assertIn('--signer-digest', call.call_args.args)
            self.assertIn('--deny-self-hosted-runners', call.call_args.args)
            with self.assertRaises(ValueError): rc.attest_verify(self.root / 'qualification.json', 'qualification', self.identity['commit'], 5, 2)

    def test_local_preparation_retains_host_source_packages_and_internal_logs(self):
        import release_trial as trial
        directory, payload = self.payload()
        import shutil
        shutil.copytree(directory, self.root / 'artifacts')
        payload_path = self.root / 'artifacts/ci/candidate-payload.json'
        rc.write(payload_path, payload)
        qualification = self.qualification()
        qualification['payloadSha256'] = rc.sha256(payload_path)
        qualification['security'].update(candidate=rc.sha256(payload_path), payloadSha256=rc.sha256(payload_path))
        final = self.root / 'artifacts/ci/qualification.json'
        rc.write(final, qualification)
        log = self.root / 'artifacts/preparation.log'; log.write_text('actual installation preparation')
        receipt = {'schemaVersion': '2.0', 'status': 'ci-trial-prepared', 'acceptanceScope': 'local-preparation-from-ci',
                   'releaseValidationPassed': False, 'version': '0.0.1',
                   'source': {'commit': self.identity['commit'], 'tree': self.identity['tree'], 'clean': True},
                   'platform': {'system': 'Windows', 'release': 'fixture', 'machine': 'fixture'},
                   'toolchains': dict.fromkeys(('python', 'node', 'npm', 'dotnet', 'specify', 'git', 'codex'), 'fixture'),
                   'steps': [{'id': 'install-disposable-consumer', 'command': ['fixture'], 'exitCode': 0, 'startedAt': 'start', 'finishedAt': 'end'}],
                   'catalog': {'sha256': '1' * 64}, 'startedAt': 'start', 'finishedAt': 'end',
                   'artifacts': [{'path': 'artifacts/' + r['name'], 'size': r['size'], 'sha256': r['sha256']} for r in payload['assets']],
                   'preparationLogs': [{'path': 'artifacts/preparation.log', 'size': log.stat().st_size, 'sha256': rc.sha256(log)}],
                   'ci': {'runId': 5, 'qualificationSha256': rc.sha256(final), 'qualificationPath': 'artifacts/ci/qualification.json',
                          'payloadPath': 'artifacts/ci/candidate-payload.json'}}
        path = self.root / 'artifacts/preparation.json'
        with patch.object(trial, 'ROOT', self.root), patch.object(trial, 'source', return_value=self.identity), \
                patch.object(trial, 'run_metadata', return_value=(self.run, self.jobs)), patch.object(trial, 'attest_verify') as attestation:
            receipt['host'] = trial.host()
            rc.write(path, receipt)
            result, digest = trial.validate_preparation(self.root, path, ROOT / 'tests/live/schemas/v2')
            self.assertEqual(rc.sha256(path), digest)
            self.assertEqual('ci-trial-prepared', result['status'])
            attestation.assert_called_once()
            receipt['host']['node'] = 'another-device'
            rc.write(path, receipt)
            with self.assertRaisesRegex(ValueError, 'another local host'):
                trial.validate_preparation(self.root, path, ROOT / 'tests/live/schemas/v2')
            receipt['host'] = trial.host(); rc.write(path, receipt)
            log.write_text('replaced preparation')
            with self.assertRaisesRegex(ValueError, 'artifact/log changed'):
                trial.validate_preparation(self.root, path, ROOT / 'tests/live/schemas/v2')

    def test_preparation_resolves_relative_output_and_installs_only_imported_bytes(self):
        import contextlib
        import shutil
        import release_trial as trial
        from live.v2 import cli
        directory, payload = self.payload()
        def fetch(run_id, destination):
            shutil.copytree(directory, destination / 'payload')
            rc.write(destination / 'payload/candidate-payload.json', payload)
            return self.qualification(), self.digest
        def install(root, consumer, packages, receipt, evidence):
            self.assertTrue(consumer.is_absolute() and consumer.is_dir())
            self.assertEqual(payload['assets'][0]['sha256'], rc.sha256(root / receipt['artifacts'][0]['path']))
            evidence.mkdir(); (evidence / 'setup.log').write_text('fixture consumer preparation')
            return []
        with patch.object(trial, 'ROOT', self.root), patch.object(trial, 'git', return_value=''), \
                patch.object(trial, 'source', return_value=self.identity), patch.object(trial, 'fetch_candidate', side_effect=fetch), \
                patch.object(trial, 'validate_preparation'), patch.object(cli, 'preflight'), patch.object(cli, 'tool_version', return_value='fixture'), \
                patch.object(trial.subprocess, 'check_output', return_value='1'*64), patch.object(runner, 'require_device_toolchain'), \
                patch('live.v2.candidate.install_candidate_from_receipt', side_effect=install) as installer, \
                patch.object(cli, 'run_supervised') as worker, contextlib.chdir(self.root):
            path = trial.prepare(5, Path('artifacts/trial'))
        self.assertTrue(path.is_absolute() and path.is_file())
        self.assertEqual('ci-trial-prepared', rc.read(path)['status'])
        installer.assert_called_once()
        worker.assert_not_called()

    def test_later_failed_history_cannot_be_hidden_by_selecting_older_run(self):
        run = dict(self.run, path=self.rules['workflows']['security'], display_title='Refresh candidate security ' + self.identity['commit'] + ' ' + self.digest,
                   conclusion='failure')
        with patch.object(rc, 'matching_runs', return_value=[run]), self.assertRaisesRegex(ValueError, 'supersession'):
            rc.history_for('security', self.digest, self.identity['commit'], self.root / 'history')

    def test_failed_qualification_attempt_survives_a_successful_rerun(self):
        q = self.qualification()
        latest = dict(self.run, run_attempt=2)
        failed_job = {'name': 'security', 'status': 'completed', 'conclusion': 'failure', 'completed_at': rc.now().isoformat()}
        with patch.object(rc, 'matching_runs', return_value=[latest]), patch.object(rc, 'run_metadata', side_effect=[
                (dict(self.run, id=6), [failed_job]), (dict(latest, id=6), [dict(failed_job, conclusion='success')])]):
            failures = rc.qualification_security_failures(q, self.digest)
        self.assertEqual(['6/1'], [f['identity'] for f in failures])
        with self.assertRaises(ValueError):
            rc.select_security([self.security(), *failures], self.digest, self.security()['targets'], self.rules)

    def test_submitted_assessment_cannot_claim_independent_execution_verification(self):
        value = self.assessment(trials=[{'phase': 'bootstrap-checkpoint', 'scope': 'fictional', 'outcome': 'passed',
                    'provenance': 'verified-internal', 'manifest': {'reference': 'internal/run.json', 'sha256': '1'*64}, 'disposition': ''}])
        path = self.root / 'submitted.json'; rc.write(path, value)
        qualification = self.root / 'qualification.json'; rc.write(qualification, self.qualification())
        args = ['release_candidate.py', 'record-assessment', '--qualification', str(qualification), '--candidate', rc.sha256(qualification), '--input', str(path), '--output', str(self.root/'record.json')]
        with patch.object(rc, 'source', return_value=self.identity), patch.object(sys, 'argv', args), patch.dict(os.environ, {'GITHUB_RUN_ID': '10', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_ACTOR': 'human'}):
            self.assertEqual(2, rc.main())
        self.assertFalse((self.root/'record.json').exists())


class RoutingTests(unittest.TestCase):
    def test_trial_recommendations_follow_actual_runtime_and_migration_changes(self):
        ci = rc.recommendation(['.github/workflows/ci.yml'])
        self.assertFalse([trial for row in ci for trial in row['trials']])
        runtime = rc.recommendation(['extensions/program-kit-governance/scripts/workflow_lifecycle.py'])
        self.assertTrue({'bootstrap-checkpoint', 'workflow-failure', 'workflow-resume'} <=
                        {trial for row in runtime for trial in row['trials']})
        upgrade = rc.recommendation(['scripts/upgrade_program_kit.py'])
        self.assertTrue({'upgrade-consumer', 'upgrade-continuation'} <= {trial for row in upgrade for trial in row['trials']})

    def test_push_whole_range_and_conservative_missing_history(self):
        checks = [dict(id='dev', group='development', needs=[], inputs=['docs/**']),
                  dict(id='build', group='package', needs=[], inputs=['bundle.yml']),
                  dict(id='install', group='package', needs=['build'], inputs=['tests/install.py'])]
        calls = []
        def git(root, *args):
            calls.append(args)
            return 'tests/install.py' if args[0] == 'diff' else 'commit'
        with patch('write_release_receipt.git', side_effect=git):
            self.assertEqual(checks, runner.changed_checks(checks, 'before', 'after', push=True))
        self.assertIn(('diff', '--no-renames', '--name-only', 'before..after'), calls)
        with patch('write_release_receipt.git', side_effect=RuntimeError('missing')):
            self.assertEqual(checks, runner.changed_checks(checks, 'missing'))
        self.assertEqual(checks, runner.changed_checks(checks, '0' * 40))
        self.assertEqual(checks, runner.affected_checks(checks, ['unknown']))

    def test_local_release_and_targeted_qualification_cannot_claim_acceptance(self):
        for approved, optin in ((False, False), (True, False), (True, True)):
            with self.assertRaisesRegex(ValueError, 'retired'): runner.require_release_authority('Release', approved, optin, {}, 'nt')
        with self.assertRaises(ValueError): runner.require_release_authority('Qualification', False, False, {}, 'posix')
        for system, lane in (('Linux', 'linux'), ('Windows', 'windows')):
            with patch.object(runner.platform, 'system', return_value=system):
                checks = runner.qualification_checks(lane)
            self.assertNotIn('build-release', {c['id'] for c in checks})
            self.assertIn('prepare-qualified-packages', {c['id'] for c in checks})
            self.assertTrue({d for c in checks for d in c['needs']} <= {c['id'] for c in checks})


if __name__ == '__main__':
    unittest.main()

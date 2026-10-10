"""Automatic dependency update and rollback contracts; no network or agents."""
import importlib.util
import json
import hashlib
import io
import subprocess
import tarfile
from pathlib import Path
import tempfile
import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('maintenance', ROOT / 'scripts/dependency_maintenance.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class UpdateTests(unittest.TestCase):
    def test_lock_refresh_uses_active_shared_npm_without_shortening_inherited_path(self):
        spec = importlib.util.spec_from_file_location('update_dependencies', ROOT / 'scripts/update_dependencies.py')
        update = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(update)
        npm = self.root / 'shared tools/npm.cmd'
        npm.parent.mkdir()
        npm.write_text('fixture launcher')
        ready, commands = [], []
        policy = SimpleNamespace(contributor=lambda root: ready.append(root),
                                 executable=lambda name, root: npm)
        fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))
        inherited = os.environ.get('PATH', '') + os.pathsep + 'X' * 8500
        with patch.dict(os.environ, {'PATH': inherited}), patch.object(sys, 'argv', ['update_dependencies', '--development']), \
                patch.object(importlib.util, 'spec_from_file_location', return_value=fake_spec), \
                patch.object(importlib.util, 'module_from_spec', return_value=policy), \
                patch.object(update, 'run', side_effect=lambda name, args: commands.append((name, args))):
            update.main()
            self.assertEqual(inherited, os.environ['PATH'])
        self.assertEqual([ROOT], ready)
        locks = [args for name, args in commands if name.startswith('lock-')]
        self.assertEqual(2, len(locks))
        self.assertTrue(all(args[0] == str(npm) and '--package-lock-only' in args for args in locks))
        self.assertTrue(all('--global' not in args for args in locks))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = {'inputs': ['package.json', 'global.json'], 'additionalPins': []}
        m.write_json(self.root / 'maintenance-policy.json', self.policy)
        m.write_json(self.root / 'package.json', {'devDependencies': {'typescript': '7.0.2'}, 'engines': {'node':'24.20.0'}})
        m.write_json(self.root / 'global.json', {'sdk':{'version':'10.0.202'}})

    def observations(self):
        latest = {'typescript':'7.0.3', 'node':'26.0.0', 'dotnet-sdk':'10.0.401'}
        return m.collect(self.root, self.policy, lambda p, o: {'latest':latest.get(p['name'],p['current']), 'source':'fixture'})

    def test_actual_package_engine_and_sdk_pins_upgrade_together(self):
        changes = m.upgrade(self.root, self.policy, self.observations())
        self.assertEqual(3, len(changes))
        self.assertEqual('7.0.3', m.read_json(self.root / 'package.json')['devDependencies']['typescript'])
        self.assertEqual('26.0.0', m.read_json(self.root / 'package.json')['engines']['node'])
        self.assertEqual('10.0.401', m.read_json(self.root / 'global.json')['sdk']['version'])

    def additional_nuget(self, document=None, pointer='/xunit.v3.mtp-v2', path='eng/packages.json'):
        m.write_json(self.root / path, document or {'xunit.v3.mtp-v2': '4.0.1', 'consumerField': 'preserve'})
        self.policy['inputs'].append(path)
        self.policy['additionalPins'].append({'kind': 'nuget', 'name': 'xunit.v3.mtp-v2',
                                             'path': path, 'pointer': pointer})
        observations = self.observations()
        pin = next(pin for pin in observations['pins'] if pin['name'] == 'xunit.v3.mtp-v2')
        pin['latest'] = '4.0.2'
        return observations, pin

    def test_declared_nuget_json_pointer_is_discovered_and_actually_upgraded(self):
        observations, pin = self.additional_nuget()
        self.assertEqual(['eng/packages.json'], pin['paths'])
        self.assertEqual(m.digest(self.root / 'eng/packages.json'), observations['inputs']['eng/packages.json'])
        changes = m.upgrade(self.root, self.policy, observations)
        self.assertIn({'path': 'eng/packages.json', 'dependency': pin['id'], 'to': '4.0.2'}, changes)
        self.assertEqual({'xunit.v3.mtp-v2': '4.0.2', 'consumerField': 'preserve'},
                         m.read_json(self.root / 'eng/packages.json'))
        self.assertTrue(any(p['current'] == '4.0.2' for p in m.inventory(self.root, self.policy)['pins']
                            if p['name'] == 'xunit.v3.mtp-v2'))

    def test_declared_nuget_pointer_handles_nested_arrays_and_escaped_keys(self):
        observations, _ = self.additional_nuget({'packages': [{'test/runner~name': '4.0.1'}], 'unrelated': ['keep']},
                                               '/packages/0/test~1runner~0name', 'package.json')
        m.upgrade(self.root, self.policy, observations)
        self.assertEqual({'packages': [{'test/runner~name': '4.0.2'}], 'unrelated': ['keep']},
                         m.read_json(self.root / 'package.json'))

    def test_declared_pointer_old_value_mismatch_rolls_back_preceding_upgrades(self):
        observations, pin = self.additional_nuget()
        before = {path: m.safe_path(self.root, path).read_bytes() for path in observations['inputs']}
        pin['current'] = '4.0.0'
        with self.assertRaisesRegex(ValueError, 'observed current version'):
            m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, {path: m.safe_path(self.root, path).read_bytes() for path in before})

    def test_stale_additional_input_is_rejected_without_overwriting_local_changes(self):
        observations, _ = self.additional_nuget()
        m.write_json(self.root / 'eng/packages.json', {'xunit.v3.mtp-v2': '4.0.0'})
        before = {path: m.safe_path(self.root, path).read_bytes() for path in observations['inputs']}
        with self.assertRaisesRegex(ValueError, 'collect again'):
            m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, {path: m.safe_path(self.root, path).read_bytes() for path in before})

    def test_undeclared_nuget_json_pin_blocks_and_rolls_back(self):
        observations, _ = self.additional_nuget()
        self.policy['additionalPins'] = []
        before = {path: m.safe_path(self.root, path).read_bytes() for path in observations['inputs']}
        with self.assertRaisesRegex(ValueError, 'no declared additional pin'):
            m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, {path: m.safe_path(self.root, path).read_bytes() for path in before})

    def test_pointer_errors_and_path_escape_roll_back_without_creating_fields(self):
        for pointer in ('/missing', '/xunit~2v3', ''):
            with self.subTest(pointer=pointer):
                self.policy['additionalPins'] = []
                observations, _ = self.additional_nuget()
                self.policy['additionalPins'][-1]['pointer'] = pointer
                # Keep one declaration so duplicate fixtures cannot obscure the selected failure.
                self.policy['additionalPins'] = self.policy['additionalPins'][-1:]
                before = {path: m.safe_path(self.root, path).read_bytes() for path in observations['inputs']}
                with self.assertRaisesRegex(ValueError, 'JSON pointer'):
                    m.upgrade(self.root, self.policy, observations)
                self.assertEqual(before, {path: m.safe_path(self.root, path).read_bytes() for path in before})
        self.policy['additionalPins'] = []
        observations, _ = self.additional_nuget()
        self.policy['additionalPins'][0]['path'] = '../outside.json'
        before = {path: m.safe_path(self.root, path).read_bytes() for path in observations['inputs']}
        with self.assertRaisesRegex(ValueError, 'escapes repository'):
            m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, {path: m.safe_path(self.root, path).read_bytes() for path in before})

    def test_unhashed_observed_path_cannot_be_written(self):
        observations, pin = self.additional_nuget()
        del observations['inputs']['eng/packages.json']
        before = (self.root / 'eng/packages.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'not a hashed input'):
            m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, (self.root / 'eng/packages.json').read_bytes())

    def test_declared_immutable_nuget_input_is_preserved(self):
        observations, _ = self.additional_nuget()
        self.policy['immutableInputs'] = ['eng/packages.json']
        before = (self.root / 'eng/packages.json').read_bytes()
        changes = m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, (self.root / 'eng/packages.json').read_bytes())
        self.assertFalse(any(change['path'] == 'eng/packages.json' for change in changes))

    def test_structurizr_keeps_specialized_semantic_and_image_update(self):
        path = self.root / 'c4-viewer-tool.json'
        m.write_json(path, {'selected': {'version': '2026.01.01', 'docker_image': 'structurizr/structurizr:2026.01.01',
                                       'docker_digest': 'sha256:' + 'a' * 64,
                                       'java_war': 'structurizr-2026.01.01.war',
                                       'java_war_url': 'https://publisher/2026.01.01/structurizr.war'},
                            'sources': [{'url': 'https://github.com/structurizr/structurizr/releases/tag/v2026.01.01'}],
                            'tested': {'status': 'passed'}})
        self.policy['inputs'].append(path.name)
        self.policy['additionalPins'].append({'kind': 'github', 'name': 'structurizr/structurizr',
                                             'path': path.name, 'pointer': '/selected/version'})
        observations = self.observations()
        next(p for p in observations['pins'] if p['name'] == 'structurizr/structurizr')['latest'] = '2026.02.01'
        with patch.object(m, 'observe', return_value={'latest': 'sha256:' + 'b' * 64}) as observe:
            m.upgrade(self.root, self.policy, observations)
        updated = m.read_json(path)
        self.assertEqual('2026.02.01', updated['selected']['version'])
        self.assertEqual('structurizr/structurizr:2026.02.01', updated['selected']['docker_image'])
        self.assertEqual('sha256:' + 'b' * 64, updated['selected']['docker_digest'])
        self.assertEqual('structurizr-2026.02.01.war', updated['selected']['java_war'])
        self.assertEqual('pending-update-validation', updated['tested']['status'])
        observe.assert_called_once_with({'kind': 'image', 'name': 'structurizr/structurizr:2026.02.01'}, {})

    def test_failed_upstream_lookup_does_not_partially_upgrade(self):
        before = (self.root / 'package.json').read_bytes()
        observations = self.observations()
        observations['pins'][-1]['latest'] = None
        with self.assertRaisesRegex(ValueError, 'lookup failed'):
            m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, (self.root / 'package.json').read_bytes())

    def test_failed_image_resolution_rolls_back_other_upgrades(self):
        path = self.root / 'Dockerfile'
        path.write_text('FROM mcr.microsoft.com/dotnet/sdk:10.0.202@sha256:' + 'a'*64)
        self.policy['inputs'].append('Dockerfile')
        before = {p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        observations = self.observations()
        for row in observations['pins']:
            if row['kind'] == 'image': row['latest'] = 'sha256:' + 'b'*64
        with patch.object(m, 'observe', side_effect=OSError('registry unavailable')):
            with self.assertRaises(OSError): m.upgrade(self.root, self.policy, observations)
        self.assertEqual(before, {p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()})

    def test_new_dependency_is_discovered_and_historical_profile_is_preserved(self):
        m.write_json(self.root / 'package.json', {'devDependencies': {'typescript':'7.0.2','vite':'8.0.0'}})
        pins = m.inventory(self.root, self.policy)['pins']
        self.assertTrue(any(p['name']=='vite' for p in pins))
        path = self.root / 'references/dependency-profiles/old.json'
        m.write_json(path, {'immutable':'old'})
        self.policy['inputs'].append('references/dependency-profiles/old.json')
        observations = self.observations()
        observations['pins'].append({'kind':'nuget','name':'Orbyss.Foundation.WebDefaults','current':'0.2.4',
            'latest':'0.3.0','id':'historical','paths':['references/dependency-profiles/old.json']})
        m.upgrade(self.root, self.policy, observations)
        self.assertEqual({'immutable':'old'}, m.read_json(path))

    def test_unavailable_lookup_is_an_explicit_failure_not_a_current_version(self):
        def failure(*args): raise OSError('credential diagnostic must not be recorded')
        observations = m.collect(self.root, self.policy, failure)
        self.assertTrue(all(p['latest'] is None and p['error']=='OSError' for p in observations['pins']))
        self.assertNotIn('credential diagnostic', json.dumps(observations))

    def test_explicit_public_metadata_policy_resolves_the_exact_action_commit(self):
        calls = []
        def metadata(url, **kwargs):
            calls.append((url, kwargs))
            if url.endswith('/releases/latest'):
                return {'tag_name': 'v0.3.1'}
            if '/git/ref/tags/' in url:
                return {'object': {'type': 'tag', 'url': 'https://api.github.com/repos/aquasecurity/setup-trivy/git/tags/exact'}}
            return {'object': {'type': 'commit', 'sha': 'a' * 40}}
        pin = {'kind': 'github-action', 'name': 'aquasecurity/setup-trivy'}
        with patch.object(m, 'fetch', side_effect=metadata):
            result = m.observe(pin, {'anonymousGithubMetadata': [pin['name']]})
        self.assertEqual('a' * 40, result['latest'])
        self.assertEqual('v0.3.1', result['release'])
        self.assertEqual(3, len(calls))
        self.assertTrue(all(kwargs == {'use_github_token': False} for _, kwargs in calls))
        calls.clear()
        with patch.object(m, 'fetch', side_effect=metadata):
            m.observe(pin, {})
        self.assertTrue(all(not kwargs for _, kwargs in calls))
        with patch.object(m, 'fetch', side_effect=OSError('publisher unavailable')):
            with self.assertRaises(OSError):
                m.observe(pin, {'anonymousGithubMetadata': [pin['name']]})

    def test_http_lookup_status_is_retained_without_sensitive_response_text(self):
        def failure(*args):
            raise m.urllib.error.HTTPError('https://api.github.com/repos/example/publisher', 403,
                                          'credential diagnostic must not be recorded', None, None)
        observations = m.collect(self.root, self.policy, failure)
        self.assertTrue(all(p['latest'] is None and p['httpStatus'] == 403 for p in observations['pins']))
        self.assertNotIn('credential diagnostic', json.dumps(observations))
        with self.assertRaisesRegex(ValueError, 'lookup failed'):
            m.upgrade(self.root, self.policy, observations)

    def test_oci_scan_selects_both_real_platforms_from_nested_index(self):
        payloads={}
        def blob(value):
            data=json.dumps(value).encode(); digest=hashlib.sha256(data).hexdigest()
            payloads['blobs/sha256/'+digest]=data
            return {'digest':'sha256:'+digest,'size':len(data)}
        images=[]
        for architecture in ('amd64','arm64'):
            configuration=blob({'architecture':architecture,'os':'linux'})
            descriptor=blob({'config':configuration,'layers':[]})
            descriptor['platform']={'os':'linux','architecture':architecture}
            images.append(descriptor)
        nested=blob({'schemaVersion':2,'manifests':images})
        payloads['index.json']=json.dumps({'schemaVersion':2,'manifests':[nested]}).encode()
        archive=self.root/'candidate.tar'
        with tarfile.open(archive,'w') as stream:
            for name,data in payloads.items():
                info=tarfile.TarInfo(name); info.size=len(data); stream.addfile(info,io.BytesIO(data))
        observed=[]
        def scanner(command,**kwargs):
            platform=command[command.index('--platform')+1]
            layout=Path(kwargs['cwd'])/command[command.index('--input')+1]
            selected=m.read_json(layout/'index.json')['manifests']
            self.assertEqual(1,len(selected))
            self.assertEqual(platform.split('/')[1],selected[0]['platform']['architecture'])
            observed.append(platform)
            configuration=m.read_json(layout/'blobs'/selected[0]['digest'].replace(':','/'))['config']['digest']
            m.write_json(Path(command[command.index('--output')+1]),{
                'ArtifactType':'container_image', 'Metadata':{'ImageID':configuration,
                'ImageConfig':{'os':'linux','architecture':platform.split('/')[1]}}, 'Results':[]})
            return subprocess.CompletedProcess(command,0)
        with patch.object(m.subprocess,'run',side_effect=scanner): m.scan(self.root,str(archive))
        self.assertEqual(['linux/amd64','linux/arm64'],observed)
        result=m.read_json(self.root/'artifacts/dependency-security/result.json')
        self.assertEqual(2,len({row['manifestDigest'] for row in result['scans']}))

    def registry_fixture(self):
        repository = 'ghcr.io/example/host'
        registry, images, configurations, children = {}, [], {}, {}
        for architecture in ('amd64', 'arm64'):
            configuration = json.dumps({'os': 'linux', 'architecture': architecture}).encode()
            config_digest = 'sha256:' + hashlib.sha256(configuration).hexdigest()
            manifest = json.dumps({'schemaVersion': 2, 'config': {'digest': config_digest}, 'layers': []}).encode()
            manifest_digest = 'sha256:' + hashlib.sha256(manifest).hexdigest()
            reference = repository + '@' + manifest_digest
            registry[reference] = manifest
            configurations[architecture] = config_digest
            children[architecture] = reference
            images.append({'digest': manifest_digest, 'platform': {'os': 'linux', 'architecture': architecture}})
        index = json.dumps({'schemaVersion': 2, 'manifests': images}).encode()
        image = repository + '@sha256:' + hashlib.sha256(index).hexdigest()
        registry[image] = index
        return image, registry, configurations, children

    def registry_scanner(self, registry, configurations, children, defect=None):
        observed = []
        def command_runner(command, **kwargs):
            if command[:2] == ['docker', 'buildx']:
                self.assertEqual(['docker', 'buildx', 'imagetools', 'inspect', '--raw'], command[:-1])
                self.assertEqual(90, kwargs['timeout'])
                return subprocess.CompletedProcess(command, 0, stdout=registry[command[-1]])
            self.assertEqual(['trivy', 'image'], command[:2])
            self.assertEqual('remote', command[command.index('--image-src') + 1])
            self.assertNotIn('--input', command)
            platform = command[command.index('--platform') + 1]
            architecture = platform.split('/')[1]
            self.assertEqual(children[architecture], command[-1])
            self.assertEqual(960, kwargs['timeout'])
            self.assertEqual('1', command[command.index('--exit-code') + 1])
            self.assertEqual('HIGH,CRITICAL', command[command.index('--severity') + 1])
            observed.append(platform)
            report = {'ArtifactType': 'container_image', 'ArtifactName': command[-1],
                      'Metadata': {'ImageID': configurations[architecture],
                                   'ImageConfig': {'os': 'linux', 'architecture': architecture},
                                   'RepoDigests': [command[-1]]}, 'Results': []}
            if defect == 'cached-amd64' and architecture == 'arm64':
                report['Metadata']['ImageConfig']['architecture'] = 'amd64'
                report['Metadata']['ImageID'] = configurations['amd64']
            elif defect == 'repeated-id' and architecture == 'arm64':
                report['Metadata']['ImageID'] = configurations['amd64']
            elif defect == 'wrong-os':
                report['Metadata']['ImageConfig']['os'] = 'windows'
            elif defect == 'wrong-config':
                report['Metadata']['ImageID'] = 'sha256:' + 'f' * 64
            elif defect == 'wrong-manifest':
                report['Metadata']['RepoDigests'] = ['ghcr.io/example/host@sha256:' + 'f' * 64]
            elif defect == 'invalid-repo-digests':
                report['Metadata']['RepoDigests'] = command[-1]
            elif defect == 'wrong-artifact':
                report['ArtifactName'] = 'ghcr.io/example/host:latest'
            elif defect == 'high-critical':
                report['Results'] = [{'Vulnerabilities': [{'Severity': 'HIGH'}]}]
            elif defect == 'invalid-results':
                report['Results'] = {}
            elif defect == 'missing-metadata':
                del report['Metadata']['ImageConfig']
            elif defect == 'invalid-json':
                Path(command[command.index('--output') + 1]).write_text('{')
                return subprocess.CompletedProcess(command, 0)
            if defect != 'missing-report':
                m.write_json(Path(command[command.index('--output') + 1]), report)
            return subprocess.CompletedProcess(command, 1 if defect == 'scanner-failure' else 0)
        return command_runner, observed

    def test_registry_scan_binds_actual_distinct_child_manifests_and_configurations(self):
        image, registry, configurations, children = self.registry_fixture()
        scanner, observed = self.registry_scanner(registry, configurations, children)
        with patch.object(m.subprocess, 'run', side_effect=scanner):
            m.scan(self.root, image)
        self.assertEqual(['linux/amd64', 'linux/arm64'], observed)
        results = m.read_json(self.root / 'artifacts/dependency-security/result.json')['scans']
        self.assertEqual(set(children.values()), {row['scannedImage'] for row in results})
        self.assertEqual(set(configurations.values()), {row['imageID'] for row in results})
        self.assertEqual(2, len({row['manifestDigest'] for row in results}))
        self.assertTrue(all(row['validationErrors'] == [] and row['sha256'] for row in results))
        self.assertEqual(registry[image], (self.root / 'artifacts/dependency-security/registry-index.json').read_bytes())

    def test_wrong_cache_platform_and_repeated_image_id_fail_despite_success_exit(self):
        for defect in ('cached-amd64', 'repeated-id'):
            with self.subTest(defect=defect):
                image, registry, configurations, children = self.registry_fixture()
                scanner, observed = self.registry_scanner(registry, configurations, children, defect)
                root = self.root / defect
                with patch.object(m.subprocess, 'run', side_effect=scanner), self.assertRaisesRegex(ValueError, 'security gate failed'):
                    m.scan(root, image)
                results = m.read_json(root / 'artifacts/dependency-security/result.json')['scans']
                self.assertEqual(['linux/amd64', 'linux/arm64'], observed)
                self.assertTrue(all(row['exitCode'] == 0 for row in results))
                self.assertIn('repeated-image-config', results[1]['validationErrors'])
                self.assertIn('wrong-image-config', results[1]['validationErrors'])
                if defect == 'cached-amd64':
                    self.assertIn('wrong-platform', results[1]['validationErrors'])

    def test_unbound_invalid_missing_or_vulnerable_reports_fail_closed(self):
        for defect, expected in [('wrong-os', 'wrong-platform'), ('wrong-config', 'wrong-image-config'),
                                 ('wrong-manifest', 'wrong-registry-manifest'), ('wrong-artifact', 'wrong-registry-manifest'),
                                 ('high-critical', 'high-critical-findings'), ('invalid-results', 'invalid-report'),
                                 ('invalid-repo-digests', 'invalid-report'),
                                 ('missing-metadata', 'invalid-report'), ('invalid-json', 'invalid-report'),
                                 ('missing-report', 'missing-report')]:
            with self.subTest(defect=defect):
                image, registry, configurations, children = self.registry_fixture()
                scanner, _ = self.registry_scanner(registry, configurations, children, defect)
                root = self.root / defect
                with patch.object(m.subprocess, 'run', side_effect=scanner), self.assertRaisesRegex(ValueError, 'security gate failed'):
                    m.scan(root, image)
                results = m.read_json(root / 'artifacts/dependency-security/result.json')['scans']
                self.assertEqual(2, len(results))
                self.assertTrue(all(expected in row['validationErrors'] and row['exitCode'] == 0 for row in results))
                if defect == 'missing-report':
                    self.assertTrue(all(row['sha256'] is None for row in results))

    def test_scanner_error_remains_failure_with_valid_metadata(self):
        image, registry, configurations, children = self.registry_fixture()
        scanner, _ = self.registry_scanner(registry, configurations, children, 'scanner-failure')
        with patch.object(m.subprocess, 'run', side_effect=scanner), self.assertRaisesRegex(ValueError, 'security gate failed'):
            m.scan(self.root, image)
        results = m.read_json(self.root / 'artifacts/dependency-security/result.json')['scans']
        self.assertTrue(all(row['exitCode'] == 1 and row['sha256'] for row in results))

    def test_second_platform_scanner_timeout_retains_first_report_and_finite_error(self):
        image, registry, configurations, children = self.registry_fixture()
        scanner, observed = self.registry_scanner(registry, configurations, children)
        def timeout(command, **kwargs):
            if command[:2] == ['trivy', 'image'] and command[command.index('--platform') + 1] == 'linux/arm64':
                self.assertEqual(960, kwargs['timeout'])
                raise subprocess.TimeoutExpired(command, 960)
            return scanner(command, **kwargs)
        with patch.object(m.subprocess, 'run', side_effect=timeout), self.assertRaises(subprocess.TimeoutExpired):
            m.scan(self.root, image)
        evidence = m.read_json(self.root / 'artifacts/dependency-security/result.json')
        self.assertEqual(['linux/amd64'], observed)
        self.assertEqual('TimeoutExpired', evidence['error'])
        self.assertEqual(1, len(evidence['scans']))
        first = evidence['scans'][0]
        self.assertEqual('linux/amd64', first['platform'])
        self.assertEqual(0, first['exitCode'])
        self.assertEqual([], first['validationErrors'])
        self.assertEqual(first['sha256'], m.digest(self.root / first['report']))
        self.assertFalse((self.root / 'artifacts/dependency-security/linux-arm64.json').exists())

    def test_registry_digest_lookup_and_timeout_failures_preserve_finite_error_evidence(self):
        image, registry, _, _ = self.registry_fixture()
        for mode in ('digest-mismatch', 'lookup-failure', 'timeout', 'mutable-tag'):
            with self.subTest(mode=mode):
                root = self.root / mode
                selected = 'ghcr.io/example/host:latest' if mode == 'mutable-tag' else image
                def failure(command, **kwargs):
                    if mode == 'timeout':
                        raise subprocess.TimeoutExpired(command, 90)
                    return subprocess.CompletedProcess(command, 1 if mode == 'lookup-failure' else 0,
                        stdout=b'{}' if mode == 'digest-mismatch' else registry[image])
                with patch.object(m.subprocess, 'run', side_effect=failure), self.assertRaises((ValueError, subprocess.TimeoutExpired)):
                    m.scan(root, selected)
                evidence = m.read_json(root / 'artifacts/dependency-security/result.json')
                self.assertEqual([], evidence['scans'])
                self.assertIn(evidence['error'], ('ValueError', 'TimeoutExpired'))
                if mode in ('digest-mismatch', 'lookup-failure'):
                    self.assertTrue((root / 'artifacts/dependency-security/registry-index.json').is_file())

    def test_repeated_nested_descriptors_are_cached_and_bounded_before_lookup(self):
        image, registry, _, children = self.registry_fixture()
        leaf = {'digest': children['amd64'].rsplit('@', 1)[1],
                'platform': {'os': 'linux', 'architecture': 'amd64'}}
        nested = json.dumps({'schemaVersion': 2, 'manifests': [leaf] * 64}).encode()
        nested_digest = 'sha256:' + hashlib.sha256(nested).hexdigest()
        index = json.dumps({'schemaVersion': 2, 'manifests': [{'digest': nested_digest}] * 64}).encode()
        repository = image.rsplit('@', 1)[0]
        selected = repository + '@sha256:' + hashlib.sha256(index).hexdigest()
        registry[selected] = index
        registry[repository + '@' + nested_digest] = nested
        calls = []
        def reader(command, **kwargs):
            self.assertEqual(['docker', 'buildx', 'imagetools', 'inspect', '--raw'], command[:-1])
            calls.append(command[-1])
            return subprocess.CompletedProcess(command, 0, stdout=registry[command[-1]])
        with patch.object(m.subprocess, 'run', side_effect=reader), self.assertRaisesRegex(ValueError, 'bounded descriptor count'):
            m.scan(self.root, selected)
        # The former recursion-entry-only limit allowed thousands of lookups.
        # One root, one nested index, one verified leaf; repeated leaves reuse bytes.
        self.assertEqual([selected, repository + '@' + nested_digest, children['amd64']], calls)
        evidence = m.read_json(self.root / 'artifacts/dependency-security/result.json')
        self.assertEqual({'scans': [], 'error': 'ValueError'}, {key: evidence[key] for key in ('scans', 'error')})
        self.assertEqual(3, len(list((self.root / 'artifacts/dependency-security').glob('*manifest*.json')))
                         + len(list((self.root / 'artifacts/dependency-security').glob('registry-index.json'))))

    def test_excessive_manifest_depth_fails_before_further_lookup(self):
        image, registry, _, children = self.registry_fixture()
        repository = image.rsplit('@', 1)[0]
        descriptor = {'digest': children['amd64'].rsplit('@', 1)[1],
                      'platform': {'os': 'linux', 'architecture': 'amd64'}}
        for _ in range(7):
            document = json.dumps({'schemaVersion': 2, 'manifests': [descriptor]}).encode()
            reference = repository + '@sha256:' + hashlib.sha256(document).hexdigest()
            registry[reference] = document
            descriptor = {'digest': reference.rsplit('@', 1)[1]}
        calls = []
        def reader(command, **kwargs):
            calls.append(command[-1])
            return subprocess.CompletedProcess(command, 0, stdout=registry[command[-1]])
        with patch.object(m.subprocess, 'run', side_effect=reader), self.assertRaisesRegex(ValueError, 'bounded nesting'):
            m.scan(self.root, reference)
        self.assertEqual(6, len(calls))
        self.assertNotIn(children['amd64'], calls)
        evidence = m.read_json(self.root / 'artifacts/dependency-security/result.json')
        self.assertEqual([], evidence['scans'])
        self.assertEqual('ValueError', evidence['error'])

    def test_stale_security_reports_are_preserved_and_cannot_supply_scanner_output(self):
        image, _, _, _ = self.registry_fixture()
        path = self.root / 'artifacts/dependency-security/linux-amd64.json'
        m.write_json(path, {'previous': 'evidence'})
        original = path.read_bytes()
        with patch.object(m.subprocess, 'run') as command, self.assertRaisesRegex(ValueError, 'Preserve prior security evidence'):
            m.scan(self.root, image)
        command.assert_not_called()
        self.assertEqual(original, path.read_bytes())


if __name__ == '__main__': unittest.main()

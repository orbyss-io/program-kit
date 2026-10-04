"""Qualified dependency profiles retain choices and require exact review before promotion."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import building_blocks as blocks
import dependency_profiles as profiles
import validate_building_blocks as fixtures

HISTORICAL = 'foundation-0.2.2-exporter-0.2.2-forms-0.2.0-localization-0.1.1'
CURRENT = 'foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'


class ProfileTests(unittest.TestCase):
    def test_portable_receipt_builder_rejects_changed_or_failed_evidence(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from build_dependency_qualification import build
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native, browser = root / 'native', root / 'browser'
            index = blocks.load_json(blocks.profile_registry() / 'index.json')
            entry = index['profiles'][CURRENT]
            profile = blocks.profile_registry() / entry['path']
            receipt = blocks.load_json(blocks.profile_registry() / entry['evidence']['path'])
            browser_summary = receipt.pop('browserIntegration')
            available = receipt.pop('availableArtifacts')
            host_summary = receipt.pop('hostRuntime')
            host = root / 'host'
            host.mkdir()
            from xml.etree import ElementTree as ET
            cases = ET.Element('testsuite')
            for identity in host_summary['cases']:
                owner, name = identity.rsplit('.', 1)
                ET.SubElement(cases, 'testcase', classname=owner, name=name)
            ET.ElementTree(cases).write(host / 'compatibility-results.xml', encoding='utf-8')
            host_summary['resultsSha256'] = blocks.raw_sha256(host / 'compatibility-results.xml')
            fixtures.write_json(host / 'qualification-result.json', host_summary)
            def build_receipt():
                return build(profile, native, browser, root / 'availability.json', host)
            receipt['status'] = 'generic-integration-passed'
            receipt['steps'] = [s for s in receipt['steps'] if s['id'] not in {'published-forms-browser', 'public-artifact-availability', 'published-host-runtime'}]
            for step in receipt['steps']:
                name = {'publisher-descriptors': 'publisher-metadata.json', 'activation-export-matrix': 'activation-matrix.json'}.get(step['id'], step['id'] + '.log')
                path = native / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('isolated unit-test evidence')
                step['evidenceSha256'] = blocks.raw_sha256(path)
            fixtures.write_json(native / 'qualification.json', receipt)
            fixtures.write_json(root / 'availability.json', {'artifacts': available})
            fixtures.write_json(browser / 'qualification-profile.json', browser_summary['profile'])
            fixtures.write_json(browser / 'qualification-result.json', {'satisfied': True, 'engines': ['chromium', 'webkit']})
            processes = []
            for stage in browser_summary['stages']:
                path = browser / 'evidence' / stage / 'process.json'
                stream = path.with_name('output.log')
                stream.parent.mkdir(parents=True, exist_ok=True)
                stream.write_text('isolated unit-test stream')
                record = {'exitCode': 0, 'timedOut': False, 'cleanupComplete': True, 'logsDrained': True,
                          'stdout': {'path': stream.name, 'sha256': blocks.raw_sha256(stream)},
                          'stderr': {'path': stream.name, 'sha256': blocks.raw_sha256(stream)}}
                fixtures.write_json(path, record)
                processes.append((path, record, stream))
            self.assertEqual(9, len(build_receipt()['steps']))
            path, record, stream = processes[0]
            stream.write_text('changed execution output')
            with self.assertRaisesRegex(ValueError, 'stream changed'):
                build_receipt()
            stream.write_text('isolated unit-test stream')
            for mutate in (lambda value: value.update(cleanupComplete=False),
                           lambda value: value.update(exitCode=1),
                           lambda value: value['stdout'].update(path='../outside.log')):
                changed = copy.deepcopy(record)
                mutate(changed)
                fixtures.write_json(path, changed)
                with self.assertRaises(ValueError):
                    build_receipt()
            fixtures.write_json(path, record)
            receipt['consumerContract'] = 'private-contract-must-not-ship'
            fixtures.write_json(native / 'qualification.json', receipt)
            with self.assertRaisesRegex(ValueError, 'unexpected generic report fields'):
                build_receipt()

    def test_generic_default_receipt_rejects_incomplete_or_changed_qualification(self):
        catalog = blocks.load_json(fixtures.CATALOG)
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / 'registry'
            shutil.copytree(blocks.profile_registry(), registry)
            index = blocks.load_json(registry / 'index.json')
            self.assertEqual(CURRENT, index['default'])
            entry = index['profiles'][CURRENT]
            receipt = blocks.load_json(registry / entry['evidence']['path'])
            blocks.qualified_dependency_profile(registry, None, catalog)
            mutations = [lambda value: value['steps'].pop(),
                lambda value: value['steps'][0].update(exitCode=1),
                lambda value: value['activationMatrix'].pop(),
                lambda value: value['activationMatrix'].append(value['activationMatrix'][0]),
                lambda value: value['activationMatrix'][0].update(closure=[]),
                lambda value: value['compositionMatrix'].pop(),
                lambda value: value['compositionMatrix'][0].update(closure=['ProgramKitQualificationProbe']),
                lambda value: value['scope']['allowedActivations'].pop(),
                lambda value: value['source'].update(recipeSha256='a' * 64),
                lambda value: value['artifacts']['Orbyss.Forms.Management'].update(version='0.2.0'),
                lambda value: value['browserIntegration']['profile']['packages'].update({'@orbyss-io/forms-react': '0.2.0'}),
                lambda value: value['browserIntegration']['stages'].pop('locked'),
                lambda value: value['availableArtifacts'].pop(),
                lambda value: value['hostRuntime']['inputs'].update(foundationRelease='0.2.2'),
                lambda value: value['hostRuntime']['inputs'].update(hostImage=None),
                lambda value: value['hostRuntime']['cases'].pop()]
            for mutate in mutations:
                changed = copy.deepcopy(receipt)
                mutate(changed)
                fixtures.write_json(registry / entry['evidence']['path'], changed)
                entry['evidence']['sha256'] = blocks.raw_sha256(registry / entry['evidence']['path'])
                fixtures.write_json(registry / 'index.json', index)
                with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                    blocks.qualified_dependency_profile(registry, None, catalog)

    def test_six_scaffold_choices_use_new_default_and_retain_historical_profile(self):
        import subprocess
        registry = blocks.profile_registry()
        index = blocks.load_json(registry / 'index.json')
        historical, _ = blocks.qualified_dependency_profile(registry, HISTORICAL, blocks.load_json(fixtures.CATALOG))
        captured = {'profile': HISTORICAL, 'catalogResolutionSha256': blocks.catalog_resolution_sha256(historical),
                    'entrySha256': blocks.canonical_sha256(index['profiles'][HISTORICAL])}
        for web in ('none', 'spa-pkce', 'bff-cookie'):
            for persistence in ('none', 'ef-postgresql'):
                with self.subTest(web=web, persistence=persistence), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                        '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                        '--building-block-sources-approved', '--persistence-profile', persistence, '--web-profile', web]
                    if persistence != 'none':
                        from validate_persistence_selection import PersistenceTests
                        fixture = PersistenceTests()
                        fixture.root = root
                        fixture.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet']})
                        fixture.select(fixture.owner(profile=persistence))
                    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    managed_path = root / '.program-kit/managed.json'
                    managed = blocks.load_json(managed_path)
                    self.assertEqual(CURRENT, managed['newProjectDependencyProfile']['profile'])
                    manifest = root / '.program-kit/eng/.config/dotnet-tools.json'
                    self.assertEqual('0.2.4', blocks.load_json(manifest)['tools']['orbyss.foundation.openapi.exporter']['version'])
                    # Model the same scaffold captured by 0.12.6. Sync must use its
                    # original exact qualification, rather than the changed default.
                    managed['newProjectDependencyProfile'] = captured
                    fixtures.write_json(managed_path, managed)
                    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assertEqual(captured, blocks.load_json(managed_path)['newProjectDependencyProfile'])
                    self.assertEqual('0.2.2', blocks.load_json(manifest)['tools']['orbyss.foundation.openapi.exporter']['version'])
                    result = subprocess.run(command + ['--check'], capture_output=True, text=True, encoding='utf-8')
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_public_native_profile_preserves_runtime_and_restricts_scope(self):
        identity = 'foundation-0.2.2-exporter-0.2.4-forms-0.2.0-localization-0.1.1'
        registry = blocks.profile_registry()
        catalog, selected = blocks.qualified_dependency_profile(registry, identity, blocks.load_json(fixtures.CATALOG))
        historical = blocks.new_project_catalog(HISTORICAL)
        changed = [key for key in catalog['packages'] if catalog['packages'][key]['version'] != historical['packages'][key]['version']]
        self.assertEqual([profiles.producers.EXPORTER_KEY], changed)
        self.assertEqual('0.2.4', catalog['packages'][profiles.producers.EXPORTER_KEY]['version'])
        self.assertEqual('0.2.2', selected['families']['foundation']['releaseVersion'])
        entry = blocks.load_json(registry / 'index.json')['profiles'][identity]
        self.assertIn('Orbyss.Foundation.Authentication.Assurance', entry['allowedActivations'])
        blocks.verify_qualification_scope(entry, [{'featureIdentity': value} for value in entry['allowedActivations']])
        with self.assertRaisesRegex(ValueError, 'qualification scope'):
            blocks.verify_qualification_scope(entry, [{'featureIdentity': 'Orbyss.Forms.Management'}])

    def native_registry(self, directory):
        registry = Path(directory) / 'profiles'
        shutil.copytree(blocks.profile_registry(), registry)
        index = blocks.load_json(registry / 'index.json')
        index['default'] = HISTORICAL
        entry = index['profiles'][index['default']]
        selected = blocks.load_json(registry / entry['path'])
        stages = ['locked-restore', 'consumer-build-pack-stage', 'canonical-consumer-descriptors',
            'native-openapi-export', 'normalize-oasdiff-existing-baseline',
            'typescript-generation-and-application-compilation', 'native-compatibility-renewal',
            'native-engine-completion', 'affected-feature-readiness']
        allowed = ['Orbyss.Foundation.Authentication.Assurance']
        entry['allowedActivations'] = allowed
        entry['excludedActivations'] = []
        receipt = {'schemaVersion': 1, 'status': 'dependency-profile-qualified',
            'catalog': {'sha256': selected['catalogResolutionSha256']},
            'source': {'kind': 'verified-program-kit-bundle', 'commit': 'b' * 40,
                'bundleSha256': 'c' * 64, 'releaseInputsSha256': 'd' * 64},
            'scope': {'claim': 'native-export-and-runtime-compatibility', 'allowedActivations': allowed},
            'steps': [{'id': stage, 'exitCode': 0, 'evidenceSha256': 'e' * 64} for stage in stages]}
        fixtures.write_json(registry / entry['evidence']['path'], receipt)
        entry['evidence']['sha256'] = blocks.raw_sha256(registry / entry['evidence']['path'])
        fixtures.write_json(registry / 'index.json', index)
        return registry, index, receipt

    def test_native_qualification_binds_complete_stages_and_exact_activation_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            registry, index, receipt = self.native_registry(directory)
            catalog = blocks.load_json(fixtures.CATALOG)
            blocks.qualified_dependency_profile(registry, None, catalog)
            entry = index['profiles'][index['default']]
            blocks.verify_qualification_scope(entry, [{'featureIdentity': 'Orbyss.Foundation.Authentication.Assurance'}])
            with self.assertRaisesRegex(ValueError, 'qualification scope'):
                blocks.verify_qualification_scope(entry, [{'featureIdentity': 'Orbyss.Forms.Management'}])
            mutations = [lambda value: value['steps'].pop(),
                lambda value: value['steps'].append(value['steps'][0]),
                lambda value: value['steps'][0].update(exitCode=1),
                lambda value: value['steps'][0].update(evidenceSha256='missing'),
                lambda value: value['scope'].update(allowedActivations=['Unqualified.Feature']),
                lambda value: value['source'].update(bundleSha256='missing'),
                lambda value: value['scope'].update(allowedActivations=[{}]),
                lambda value: value.update(steps=[False]),
                lambda value: value['steps'][0].update(id=[]),
                lambda value: value.update(status='release-validation-passed')]
            for mutate in mutations:
                altered = copy.deepcopy(receipt)
                mutate(altered)
                fixtures.write_json(registry / entry['evidence']['path'], altered)
                entry['evidence']['sha256'] = blocks.raw_sha256(registry / entry['evidence']['path'])
                fixtures.write_json(registry / 'index.json', index)
                with self.subTest(receipt=altered), self.assertRaises(ValueError):
                    blocks.qualified_dependency_profile(registry, None, catalog)

    def test_installed_qualified_profile_binds_portable_checkout_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / 'profiles'
            shutil.copytree(blocks.profile_registry(), registry)
            index = blocks.load_json(registry / 'index.json')
            entry = index['profiles'][index['default']]
            profile = registry / entry['path']
            # Git ships LF text on Linux and Windows. Qualification must bind
            # these exact installed bytes, not a Windows writer's CRLF copy.
            profile.write_bytes(profile.read_bytes().replace(b'\r\n', b'\n'))
            catalog, selected = blocks.qualified_dependency_profile(
                registry, None, blocks.load_json(fixtures.CATALOG))
            self.assertEqual(index['default'], selected['id'])
            self.assertEqual('0.2.4', catalog['packages'][profiles.producers.EXPORTER_KEY]['version'])
            original = profile.read_bytes()
            profile.write_bytes(original + b'\n')
            with self.assertRaisesRegex(ValueError, 'qualified profile changed'):
                blocks.qualified_dependency_profile(registry, None, blocks.load_json(fixtures.CATALOG))
            profile.write_bytes(original)
            proof = registry / entry['evidence']['path']
            proof.write_bytes(proof.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'qualification evidence changed'):
                blocks.qualified_dependency_profile(registry, None, blocks.load_json(fixtures.CATALOG))

    def test_scaffold_default_survives_check_and_later_registry_default_change(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                '--building-block-sources-approved', '--persistence-profile', 'none', '--web-profile', 'none']
            for check in (False, True):
                result = subprocess.run(command + (['--check'] if check else []), capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            managed = blocks.load_json(root / '.program-kit/managed.json')
            captured = managed['newProjectDependencyProfile']
            registry = root / 'registry'
            shutil.copytree(ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles', registry)
            index = blocks.load_json(registry / 'index.json')
            index['default'] = 'an-unqualified-later-default'
            fixtures.write_json(registry / 'index.json', index)
            selection = root / 'docs/architecture/building-block-selection.json'
            with patch.object(blocks, 'profile_registry', return_value=registry):
                blocks.draft_qualified_selection(root, selection, blocks.load_json(fixtures.CATALOG), [])
            self.assertEqual(captured['catalogResolutionSha256'], blocks.load_json(selection)['catalog']['resolutionSha256'])
            self.assertEqual(captured['profile'], blocks.load_json(root / '.program-kit/dependency-profile.json')['newProjectQualification']['profile'])

    def producer_fixture(self, root, catalog):
        relative = 'contracts/openapi/catalog.contract.json'
        fixtures.write_json(root / '.program-kit/openapi-contracts.json', {'schemaVersion': 1, 'contracts': [relative]})
        fixtures.write_json(root / relative, {'producer': {'kind': profiles.producers.PRODUCER_KIND,
            'version': catalog['packages'][profiles.producers.EXPORTER_KEY]['version']}})
        fixtures.write_json(root / 'specs/SPC-001/artifact-ownership.json', {'artifacts': [{'path': relative}]})
        (root / 'specs/SPC-001/plan.md').write_text('Foundation runtime 0.2.2; exporter 0.2.4; analyzer 0.2.2.\n', encoding='utf-8')
        fixtures.write_json(root / '.program-kit/lifecycle/SPC-001.json',
            {'phases': {'afterTasksAnalysis': {'report': 'specs/SPC-001/analysis.md', 'reportSha256': 'a' * 64}}})
        (root / 'specs/SPC-001/analysis.md').write_text('Preserved historical analysis', encoding='utf-8')
        return relative

    def test_profile_review_reconciles_producers_with_recoverable_sealed_files(self):
        class Interrupted(BaseException): pass
        for stop in ('catalog.contract.json', 'plan.md', 'SPC-001.json', 'accepted.json'):
            with self.subTest(stop=stop), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                catalog = blocks.load_json(fixtures.CATALOG)
                installed = root / 'installed-catalog.json'
                fixtures.write_json(installed, catalog)
                selection, architecture = fixtures.accepted_fixture(blocks, root, catalog)
                version = root / '.specify/extensions/program-kit-governance/extension.yml'
                version.parent.mkdir(parents=True, exist_ok=True)
                version.write_text('extension:\n  version: "0.12.6"\n')
                relative = self.producer_fixture(root, catalog)
                registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
                identity = HISTORICAL
                destination, packet = profiles.draft(root, installed, identity, registry)
                self.assertIn(relative, packet['producerChanges'])
                self.assertEqual((destination, packet), profiles.draft(root, installed, identity, registry))
                decision = root / 'docs/architecture/decisions/profile-review.md'
                decision.parent.mkdir(parents=True, exist_ok=True)
                decision.write_text('Accepted exact profile: ' + packet['profileSha256'] + '\nReview: ' + packet['reviewSha256'])
                model = blocks.load_json(architecture)
                model['decisions'].append({'id': 'profile-review', 'status': 'Accepted',
                    'path': decision.relative_to(root).as_posix(), 'sha256': blocks.raw_sha256(decision)})
                fixtures.write_json(architecture, model)
                original_write = blocks.atomic_write_bytes
                hit = []
                def interrupt(path, content, suffix):
                    original_write(path, content, suffix)
                    if path.name == stop and not hit:
                        hit.append(True)
                        raise Interrupted()
                # Exercise a hard process-style interruption after the actual file write.
                if stop == 'accepted.json':
                    original_text = blocks.atomic_write
                    def interrupt_text(path, content):
                        original_text(path, content)
                        if path.name == stop and not hit:
                            hit.append(True)
                            raise Interrupted()
                    context = patch.object(blocks, 'atomic_write', side_effect=interrupt_text)
                else:
                    context = patch.object(blocks, 'atomic_write_bytes', side_effect=interrupt)
                with context, self.assertRaises(Interrupted):
                    profiles.accept(root, destination, registry, 'profile-review', 'Reviewed qualified profile')
                result = profiles.accept(root, destination, registry, 'profile-review', 'Reviewed qualified profile')
                self.assertEqual('0.2.2', blocks.load_json(root / relative)['producer']['version'])
                self.assertEqual('Foundation runtime 0.2.2; exporter 0.2.2; analyzer 0.2.2.\n',
                                 (root / 'specs/SPC-001/plan.md').read_text(encoding='utf-8'))
                state = blocks.load_json(root / '.program-kit/lifecycle/SPC-001.json')
                self.assertNotIn('afterTasksAnalysis', state['phases'])
                self.assertEqual(1, len(state['invalidations']))
                self.assertFalse(result['migrationCompletionEstablished'])
                self.assertEqual('Preserved historical analysis', (root / 'specs/SPC-001/analysis.md').read_text(encoding='utf-8'))
                # Later analysis and producer edits are later consumer history. Repeat
                # acceptance must preserve them rather than replay the original proposal.
                state['phases']['afterTasksAnalysis'] = {'report': 'renewed-analysis.md'}
                fixtures.write_json(root / '.program-kit/lifecycle/SPC-001.json', state)
                (root / 'specs/SPC-001/plan.md').write_text('Later legitimate feature planning', encoding='utf-8')
                self.assertEqual(result, profiles.accept(root, destination, registry, 'profile-review', 'Reviewed qualified profile'))
                self.assertEqual(state, blocks.load_json(root / '.program-kit/lifecycle/SPC-001.json'))

    def test_profile_review_rejects_changed_producer_proposals_and_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = blocks.load_json(fixtures.CATALOG)
            installed = root / 'installed-catalog.json'
            fixtures.write_json(installed, catalog)
            selection, architecture = fixtures.accepted_fixture(blocks, root, catalog)
            version = root / '.specify/extensions/program-kit-governance/extension.yml'
            version.parent.mkdir(parents=True, exist_ok=True)
            version.write_text('extension:\n  version: "0.12.6"\n')
            relative = self.producer_fixture(root, catalog)
            registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
            identity = HISTORICAL
            original = (root / relative).read_bytes()
            fixtures.write_json(root / relative, {'producer': {'kind': profiles.producers.PRODUCER_KIND, 'version': '0.2.3'}})
            with self.assertRaisesRegex(ValueError, 'original reviewed dependency profile'):
                profiles.draft(root, installed, identity, registry)
            self.assertFalse((root / 'docs/architecture/dependency-transitions').exists())
            (root / relative).write_bytes(original)
            destination, packet = profiles.draft(root, installed, identity, registry)
            decision = root / 'docs/architecture/decisions/profile-review.md'
            decision.parent.mkdir(parents=True, exist_ok=True)
            decision.write_text('Accepted exact profile: ' + packet['profileSha256'] + '\nReview: ' + packet['reviewSha256'])
            model = blocks.load_json(architecture)
            model['decisions'].append({'id': 'profile-review', 'status': 'Accepted',
                'path': decision.relative_to(root).as_posix(), 'sha256': blocks.raw_sha256(decision)})
            fixtures.write_json(architecture, model)
            before = {p: p.read_bytes() for p in (selection, architecture)}
            for path in (destination / 'producer-proposed' / relative,
                         destination / 'producer-originals' / relative, root / relative):
                preserved = path.read_bytes()
                path.write_text('{}')
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'producer .*changed|producer transition evidence changed'):
                    profiles.accept(root, destination, registry, 'profile-review', 'Reviewed qualified profile')
                for target, data in before.items(): self.assertEqual(data, target.read_bytes())
                self.assertFalse((destination / 'promotion.json').exists())
                if path.is_relative_to(destination):
                    with self.assertRaisesRegex(ValueError, 'preserved producer transition differs'):
                        profiles.draft(root, installed, identity, registry)
                path.write_bytes(preserved)
            # Ordinary write errors roll back producer, architecture and dependency state.
            original_write = blocks.atomic_write_bytes
            hit = []
            def fail_write(path, content, suffix):
                original_write(path, content, suffix)
                if path == root / relative and not hit:
                    hit.append(True)
                    raise OSError('injected producer write failure')
            with patch.object(blocks, 'atomic_write_bytes', side_effect=fail_write), self.assertRaisesRegex(OSError, 'injected'):
                profiles.accept(root, destination, registry, 'profile-review', 'Reviewed qualified profile')
            for target, data in before.items(): self.assertEqual(data, target.read_bytes())
            self.assertEqual(original, (root / relative).read_bytes())
            self.assertFalse((root / '.program-kit/dependency-profile.json').exists())
            profiles.accept(root, destination, registry, 'profile-review', 'Reviewed qualified profile')

    def test_new_project_scaffolding_and_draft_share_qualified_default(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = blocks.load_json(fixtures.CATALOG)
            registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
            expected, exact = profiles.supported(registry, blocks.load_json(registry / 'index.json')['default'], catalog)
            selection = root / 'docs/architecture/building-block-selection.json'
            command = [sys.executable, str(fixtures.RESOLVER), 'draft', '--target', str(root)]
            renderer = ROOT / 'extensions/program-kit-dotnet/scripts/dependency_profile.py'
            # The standalone .NET adapter must work without sibling extensions on sys.path.
            code = ('import importlib.util,json,pathlib,sys; '
                    's=importlib.util.spec_from_file_location("renderer",sys.argv[1]); '
                    'm=importlib.util.module_from_spec(s);s.loader.exec_module(m); '
                    'print(m.render(pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4].encode()).decode())')
            manifest = json.dumps({'tools': {'orbyss.foundation.openapi.exporter': {'version': '0.2.4'}}})
            relative = '.program-kit/eng/.config/dotnet-tools.json'
            for drafted in (False, True):
                if drafted:
                    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
                result = subprocess.run([sys.executable, '-I', '-c', code, str(renderer), str(root), relative, manifest],
                                        capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(exact['artifacts']['nuget:Orbyss.Foundation.OpenApi.Exporter'],
                                 json.loads(result.stdout)['tools']['orbyss.foundation.openapi.exporter']['version'])
                self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})
            draft = blocks.load_json(selection)
            self.assertEqual('Draft', draft['status'])
            self.assertEqual(blocks.catalog_binding(expected), draft['catalog'])
            self.assertFalse((root / '.program-kit/building-blocks.lock.json').exists())
            binding = blocks.load_json(root / '.program-kit/dependency-profile.json')
            self.assertIn('no acceptance', binding['authority'])
            # Complete real assignments using the existing architecture fixture; promote
            # against the newer bundled catalog without changing reviewed Draft pins.
            selection, architecture = fixtures.accepted_fixture(blocks, root, expected)
            draft = blocks.load_json(selection)
            draft['status'] = 'Draft'
            fixtures.write_json(selection, draft)
            lock = blocks.accept_selection(root, selection, fixtures.CATALOG,
                'docs/architecture/architecture-map.json', draft['authority']['decisionIds'],
                draft['authority']['rationale'], '0.12.6')
            self.assertEqual(exact['catalogResolutionSha256'], lock['inputs']['catalog']['resolutionSha256'])
            self.assertEqual(expected, blocks.load_json(blocks.consumer_catalog(root, blocks.load_json(selection), fixtures.CATALOG)))
            self.assertIn('newProjectQualification', blocks.load_json(root / '.program-kit/dependency-profile.json'))

    def test_new_default_requires_qualification_and_rejects_excluded_activations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / 'registry'
            shutil.copytree(ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles', registry)
            index = blocks.load_json(registry / 'index.json')
            identity = index['default']
            index['profiles'][identity]['excludedActivations'] = ['Orbyss.Foundation.DomainEvents']
            fixtures.write_json(registry / 'index.json', index)
            catalog = blocks.load_json(fixtures.CATALOG)
            qualified, _ = profiles.supported(registry, identity, catalog)
            selection = root / 'docs/architecture/building-block-selection.json'
            with patch.object(blocks, 'profile_registry', return_value=registry):
                blocks.draft_qualified_selection(root, selection, catalog, [])
                selection, architecture = fixtures.accepted_fixture(blocks, root, qualified)
                draft = blocks.load_json(selection)
                draft['status'] = 'Draft'
                fixtures.write_json(selection, draft)
                preserved = {p: p.read_bytes() for p in (selection, architecture, root / '.program-kit/dependency-profile.json')}
                with self.assertRaisesRegex(ValueError, 'qualification scope'):
                    blocks.accept_selection(root, selection, fixtures.CATALOG,
                        'docs/architecture/architecture-map.json', draft['authority']['decisionIds'],
                        draft['authority']['rationale'], '0.12.6')
                for path, content in preserved.items(): self.assertEqual(content, path.read_bytes())
                index['default'] = 'private-exporter-0.2.4'
                fixtures.write_json(registry / 'index.json', index)
                other = root / 'other'
                with self.assertRaisesRegex(ValueError, 'unlisted or unqualified'):
                    blocks.draft_qualified_selection(other, other / 'selection.json', catalog, [])
                self.assertFalse(other.exists())

    def test_transition_registers_review_and_preserves_unaffected_scoped_proof(self):
        from validate_bootstrap_proof_plan import ProofPlanTests
        from bootstrap_lifecycle import LEDGER, run_proof, load, write, source_digest
        from bootstrap_proof_plan import execute, require_proven_closure
        fixture = ProofPlanTests()
        fixture.setUp()
        try:
            root = fixture.root
            catalog = blocks.load_json(fixtures.CATALOG)
            installed = root / 'installed-catalog.json'
            fixtures.write_json(installed, catalog)
            selection, architecture = fixtures.accepted_fixture(blocks, root, catalog)
            old_review = root / 'docs/architecture/selected.md'
            old_review.write_text('Status: Accepted\nUse the fixture building blocks.\n')
            model = load(architecture)
            model['decisions'][0]['path'] = old_review.relative_to(root).as_posix()
            write(architecture, model)
            ledger = load(root / LEDGER)
            ledger['sources'].append({'path': old_review.relative_to(root).as_posix(), 'sha256': source_digest(old_review), 'prerequisites': []})
            write(root / LEDGER, ledger)
            contract = fixture.recipe.with_suffix('.contract.json')
            value = load(contract)
            value['dependencyScope'] = {'schemaVersion': 1, 'artifactKeys': ['nuget:Orbyss.Foundation.DomainEvents']}
            write(contract, value)
            proof = run_proof(root, 'runtime', 'docs/architecture/probe.py', 10)
            execute(root)
            original_proof = (root / proof['path']).read_bytes()
            version = root / '.specify/extensions/program-kit-governance/extension.yml'
            version.parent.mkdir(parents=True, exist_ok=True)
            version.write_text('extension:\n  version: "0.12.5"\n')
            registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
            identity = HISTORICAL
            destination, packet = profiles.draft(root, installed, identity, registry)
            decision = root / 'docs/architecture/dependency-review.md'
            decision.write_text('Status: Accepted\nReviewed ' + packet['profileSha256'] + ' ' + packet['reviewSha256'])
            model = load(architecture)
            model['decisions'].append({'id': 'profile-review', 'status': 'Accepted', 'path': decision.relative_to(root).as_posix(), 'sha256': blocks.raw_sha256(decision)})
            write(architecture, model)
            result = profiles.accept(root, destination, registry, 'profile-review', 'Reviewed independent exporter change')
            self.assertEqual(result, profiles.accept(root, destination, registry, 'profile-review', 'Reviewed independent exporter change'))
            self.assertEqual(['runtime'], require_proven_closure(root))
            self.assertEqual(original_proof, (root / proof['path']).read_bytes())
            self.assertEqual('closed', load(root / LEDGER)['prerequisites'][0]['status'])
            self.assertEqual(3, len(load(root / LEDGER)['sources']))
            # A completed retry does not restore later native lifecycle history.
            changed = load(root / LEDGER)
            changed['prerequisites'][0]['status'] = 'open'
            write(root / LEDGER, changed)
            changed_bytes = (root / LEDGER).read_bytes()
            self.assertEqual(result, profiles.accept(root, destination, registry, 'profile-review', 'Reviewed independent exporter change'))
            self.assertEqual(changed_bytes, (root / LEDGER).read_bytes())
            (destination / 'accepted.json').unlink()
            with self.assertRaisesRegex(ValueError, 'ledger differs'):
                profiles.accept(root, destination, registry, 'profile-review', 'Reviewed independent exporter change')
        finally:
            fixture.doCleanups()

    def test_publisher_qualification_scope_cannot_be_bypassed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = blocks.load_json(fixtures.CATALOG)
            installed = root / 'installed-catalog.json'
            fixtures.write_json(installed, catalog)
            selection, _ = fixtures.accepted_fixture(blocks, root, catalog)
            registry = root / 'registry'
            shutil.copytree(ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles', registry)
            index = blocks.load_json(registry / 'index.json')
            identity = index['default']
            index['profiles'][identity]['excludedActivations'] = ['Orbyss.Foundation.DomainEvents']
            fixtures.write_json(registry / 'index.json', index)
            before = selection.read_bytes()
            with self.assertRaisesRegex(ValueError, 'qualification scope'):
                profiles.draft(root, installed, identity, registry)
            self.assertEqual(before, selection.read_bytes())
            self.assertFalse((root / 'docs/architecture/dependency-transitions').exists())

    def test_exact_profiles_are_separate_from_composition(self):
        catalog = blocks.load_json(fixtures.CATALOG)
        selected = profiles.profile(catalog, 'test-profile')
        changed = copy.deepcopy(catalog)
        changed['packages']['nuget:Orbyss.Foundation.Analyzers']['version'] = '0.2.3'
        changed['families']['foundation']['toolVersions']['Orbyss.Foundation.Analyzers'] = '0.2.3'
        self.assertEqual(profiles.composition(catalog), profiles.composition(changed))
        self.assertEqual(catalog, profiles.materialize(changed, selected))
        changed['compositions'].pop(next(iter(changed['compositions'])))
        with self.assertRaisesRegex(ValueError, 'composition rules'): profiles.materialize(changed, selected)

    def test_draft_review_recovery_and_unqualified_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = blocks.load_json(fixtures.CATALOG)
            installed = root / '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
            fixtures.write_json(installed, catalog)
            selection, architecture = fixtures.accepted_fixture(blocks, root, catalog)
            version = root / '.specify/extensions/program-kit-governance/extension.yml'
            version.parent.mkdir(parents=True, exist_ok=True)
            version.write_text('extension:\n  version: "0.12.5"\n')
            registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
            identity = HISTORICAL
            original = selection.read_bytes()
            destination, packet = profiles.draft(root, installed, identity, registry)
            self.assertEqual(original, selection.read_bytes())
            self.assertFalse(packet['approvalPerformed'])
            with self.assertRaisesRegex(ValueError, 'Accepted architecture decision'):
                profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile change')
            decision = root / 'docs/architecture/decisions/dependency-change.md'
            decision.parent.mkdir(parents=True, exist_ok=True)
            decision.write_text('Accepted dependency profile SHA-256: ' + packet['profileSha256'] + '\nAccepted transition: ' + packet['reviewSha256'])
            model = blocks.load_json(architecture)
            model['decisions'].append({'id': 'dependency-change', 'status': 'Accepted', 'path': decision.relative_to(root).as_posix(), 'sha256': blocks.raw_sha256(decision)})
            fixtures.write_json(architecture, model)
            result = profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile change')
            accepted = blocks.load_json(selection)
            old = json.loads(original)
            for field in ('scopes', 'targets', 'instances'): self.assertEqual(old[field], accepted[field])
            self.assertEqual('Accepted', accepted['status'])
            self.assertFalse(result['materializationPerformed'])
            self.assertEqual(result, profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile change'))
            self.assertEqual(original, (destination / 'originals/selection.json').read_bytes())
            with self.assertRaisesRegex(ValueError, 'unlisted or unqualified'):
                profiles.supported(registry, 'unknown-profile', catalog)
            (destination / 'originals/catalog.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'evidence changed'):
                profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile change')

    def test_interrupted_promotion_resumes_sealed_review_and_invalidates_only_affected_readiness(self):
        class Interrupted(BaseException): pass
        for stop in ('architecture-map.json', 'building-block-selection.json', 'dependency-profile.json', 'accepted.json'):
            with self.subTest(stop=stop), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                catalog = blocks.load_json(fixtures.CATALOG)
                catalog['families']['foundation']['releaseVersion'] = '0.2.3'
                for package in catalog['packages'].values():
                    if package['family'] == 'foundation' and package['packageId'] not in catalog['families']['foundation'].get('toolVersions', {}):
                        package['version'] = '0.2.3'
                installed = root / 'installed-catalog.json'
                fixtures.write_json(installed, catalog)
                selection, architecture = fixtures.accepted_fixture(blocks, root, catalog)
                original = selection.read_bytes()
                blocks.preserve_dependency_profile(root, blocks.load_json(selection), installed)
                version = root / '.specify/extensions/program-kit-governance/extension.yml'
                version.parent.mkdir(parents=True, exist_ok=True)
                version.write_text('extension:\n  version: "0.12.5"\n')
                target = blocks.load_json(selection)['targets'][0]['path']
                fixtures.write_json(root / '.program-kit/building-blocks.lock.json', {'targets': [{'path': target, 'packages': [{'packageId': 'Orbyss.Foundation.DomainEvents'}]}]})
                for feature, project in [('SPC-001', target), ('SPC-002', 'src/Unrelated.csproj')]:
                    fixtures.write_json(root / 'specs' / feature / 'artifact-ownership.json', {'runtimeComposition': {'projects': [{'path': project}]}})
                    fixtures.write_json(root / '.program-kit/lifecycle' / (feature + '.json'), {'phases': {'afterTasksAnalysis': {'report': 'historical-report'}}})
                registry = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profiles'
                identity = blocks.load_json(registry / 'index.json')['default']
                destination, packet = profiles.draft(root, installed, identity, registry)
                decision = root / 'docs/architecture/decisions/dependency-change.md'
                decision.parent.mkdir(parents=True, exist_ok=True)
                decision.write_text('Accepted ' + packet['profileSha256'] + ' ' + packet['reviewSha256'])
                model = blocks.load_json(architecture)
                model['decisions'].append({'id': 'dependency-change', 'status': 'Accepted', 'path': decision.relative_to(root).as_posix(), 'sha256': blocks.raw_sha256(decision)})
                fixtures.write_json(architecture, model)
                writer = blocks.atomic_write
                def interrupt(path, content):
                    writer(path, content)
                    if path.name == stop: raise Interrupted()
                with patch.object(blocks, 'atomic_write', side_effect=interrupt), self.assertRaises(Interrupted):
                    profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile')
                result = profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile')
                self.assertEqual(result, profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile'))
                self.assertEqual(original, (destination / 'originals/selection.json').read_bytes())
                changed = blocks.load_json(root / '.program-kit/lifecycle/SPC-001.json')
                self.assertNotIn('afterTasksAnalysis', changed['phases'])
                self.assertEqual(1, len(changed['invalidations']))
                self.assertIn('afterTasksAnalysis', blocks.load_json(root / '.program-kit/lifecycle/SPC-002.json')['phases'])
                blocks.verify_architecture_authority(root, selection, blocks.load_json(selection))
                blocks.consumer_catalog(root, blocks.load_json(selection), installed)
                with self.assertRaisesRegex(ValueError, 'selection changed|contradictory review'):
                    profiles.accept(root, destination, registry, 'dependency-change', 'Changed rationale')
                promotion = destination / 'promotion.json'
                promotion.unlink()
                with self.assertRaisesRegex(ValueError, 'no sealed Accepted review|contradictory evidence'):
                    profiles.accept(root, destination, registry, 'dependency-change', 'Reviewed profile')


if __name__ == '__main__': unittest.main()

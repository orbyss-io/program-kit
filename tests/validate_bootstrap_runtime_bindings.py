"""Synthetic public Host binding/capture guards. No Docker, registry, build or qualification claims."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import zipfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_dependency_qualification as sealer
spec = importlib.util.spec_from_file_location('bootstrap_runtime_coordinator', ROOT / 'tests/validate_bootstrap_runtime.py')
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)
probe = wrapper.runtime_contract_module()
IMAGE = 'ghcr.io/orbyss-io/foundation-host@sha256:' + 'a' * 64
IMAGE_ID = 'sha256:' + 'b' * 64
EXPECTED_HOST_SHARED = {
    'CShells.Abstractions': '0.0.29-preview.147',
    'CShells.AspNetCore.Abstractions': '0.0.29-preview.147',
}
RUNTIME_FOUNDATION = {
    'Orbyss.Foundation.Web.ProblemDetails': '0.3.0',
    'Orbyss.Foundation.Web.ProblemDetails.Core': '0.3.0',
    'Orbyss.Foundation.Json': '0.3.0',
    'Orbyss.Foundation.Collections.Core': '0.3.0',
}


def maintained_cshells_source():
    # This is the mapping copied by the real coordinator, not a fabricated
    # restore-source value chosen to satisfy the runtime admission predicate.
    configuration = ET.parse(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/NuGet.config')
    sources = {entry.get('key'): entry.get('value') for entry in configuration.findall('./packageSources/add')}
    mappings = [entry for entry in configuration.findall('./packageSourceMapping/packageSource')
                if {'CShells', 'CShells.*'} <= {package.get('pattern') for package in entry.findall('package')}]
    assert len(mappings) == 1, 'Maintained CShells restore mapping is missing or ambiguous'
    return sources[mappings[0].get('key')]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def fixture(root):
    payload = root / 'public-host-payload'
    payload.mkdir(parents=True)
    assemblies = {name: ('native-public-' + name).encode() for name in EXPECTED_HOST_SHARED}
    for name, value in assemblies.items():
        (payload / (name + '.dll')).write_bytes(value)
    (payload / 'Orbyss.Foundation.Host.dll').write_bytes(b'public-host')
    write_json(payload / 'Orbyss.Foundation.Host.runtimeconfig.json', {'runtimeOptions': {}})
    write_json(payload / 'Orbyss.Foundation.Host.deps.json', {'libraries': {
        'Orbyss.Foundation.Host/0.3.0': {'type': 'project'},
        **{name + '/' + version: {'type': 'package'} for name, version in EXPECTED_HOST_SHARED.items()}}})
    shared = [{'Name': name, 'PublicKeyToken': None, 'MajorVersion': 0} for name in EXPECTED_HOST_SHARED]
    write_json(payload / 'appsettings.json', {'Nuplane': {'Loading': {'SharedAssemblies': shared}}})
    write_json(payload / 'shells.json', {'CShells': {'Shells': {}}})
    write_json(payload / 'extra.json', {'effective': True})
    source = payload / '.orbyss-foundation/settings-sources/host/Transport/Options.cs.txt'
    source.parent.mkdir(parents=True)
    source.write_text('public int MaxRequestHeadersBytes { get; set; } = 32768;\n', encoding='utf-8')
    (payload / 'runtimes/linux-x64/native').mkdir(parents=True)
    (payload / 'runtimes/linux-x64/native/provider.so').write_bytes(b'native')
    cache = root / 'native-cache'
    assets = {'packageFolders': {str(cache): {}}, 'libraries': {}}
    for identity, version in {**EXPECTED_HOST_SHARED, **RUNTIME_FOUNDATION,
                              'CShells.Additional': '1.0.0', 'Nuplane.Additional': '1.0.0'}.items():
        path = cache / identity.lower() / version
        path.mkdir(parents=True)
        archive = path / f'{identity.lower()}.{version}.nupkg'
        with zipfile.ZipFile(archive, 'w') as package:
            package.writestr(identity + '.nuspec', f'<package><metadata><id>{identity}</id><version>{version}</version></metadata></package>')
            package.writestr('lib/net10.0/' + identity + '.dll', assemblies.get(identity, b'additional'))
        source = maintained_cshells_source() if identity.startswith('CShells.') else 'https://api.nuget.org/v3/index.json'
        write_json(path / '.nupkg.metadata', {'source': source})
        assets['libraries'][identity + '/' + version] = {'type': 'package', 'path': identity.lower() + '/' + version}
    pins = {'foundationRelease': '0.3.0', 'dependencyProfile': probe.CONTRACTS_PROFILE, 'hostImage': IMAGE}
    reseal(root, pins)
    packages = root / 'runtime-packages'
    packages.mkdir()
    return pins, assets, packages


def reseal(root, pins):
    write_json(root / 'public-host-inputs.json', probe.public_host_contract(root / 'public-host-payload', IMAGE, IMAGE_ID))
    pins['hostPayload'] = {'path': 'public-host-payload', 'inputs': 'public-host-inputs.json',
                           'inputsSha256': probe.file_sha256(root / 'public-host-inputs.json')}


def package_path(root, identity):
    version = {**EXPECTED_HOST_SHARED, **RUNTIME_FOUNDATION}[identity]
    return root / 'native-cache' / identity.lower() / version / f'{identity.lower()}.{version}.nupkg'


def rewrite_archive(path, mutation):
    with zipfile.ZipFile(path) as archive:
        entries = [(name, archive.read(name)) for name in archive.namelist()]
    with zipfile.ZipFile(path, 'w') as archive:
        for name, content in mutation(entries):
            archive.writestr(name, content)


def main():
    results = []
    assert maintained_cshells_source() == probe.CSHELLS_PREVIEW_SOURCE
    results.append('canonical-cshells-source-matches-maintained-native-restore-mapping')
    parent = ROOT / 'artifacts/bootstrap-runtime-binding-guards'
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as temporary:
        base = Path(temporary)
        pins, assets, packages = fixture(base / 'positive')
        shared = probe.prepare_shared_runtime(base / 'positive', pins, assets, packages)
        assert '.orbyss-foundation/settings-sources/host/Transport/Options.cs.txt' in probe.host_runtime_inventory(
            base / 'positive/public-host-payload'), 'Host metadata source snapshots must be bound runtime inputs'
        assert {item['Name'] for item in shared} == set(EXPECTED_HOST_SHARED)
        assert {p.name for p in packages.glob('*.nupkg')} == {
            'cshells.additional.1.0.0.nupkg', 'nuplane.additional.1.0.0.nupkg',
            *{identity.lower() + '.' + version + '.nupkg' for identity, version in RUNTIME_FOUNDATION.items()}}
        assert len(list((base / 'positive/runtime-archive-inputs').glob('*.nupkg'))) == 8
        assert len(json.loads((base / 'positive/runtime-shared-bindings.json').read_text())) == 2
        probe.verify_retained_runtime_inputs(base / 'positive', pins)
        results.append('neutral-host-full-archive-retention-and-only-two-proven-exclusions')

        retained = base / 'positive/runtime-archive-inputs'
        original = (retained / 'orbyss.foundation.json.0.3.0.nupkg').read_bytes()
        (retained / 'orbyss.foundation.json.0.3.0.nupkg').write_bytes(b'tampered')
        try:
            probe.verify_retained_runtime_inputs(base / 'positive', pins)
        except ValueError as error:
            assert 'archive bytes changed' in str(error)
        else:
            raise AssertionError('Post-runtime archive change was admitted')
        (retained / 'orbyss.foundation.json.0.3.0.nupkg').write_bytes(original)
        results.append('post-runtime-full-archive-rehash')

        # A synthetic retained receipt exercises the same independent recheck
        # that the real sealer will apply. It is never written as qualification.
        evidence_root = base / 'positive'
        pins['runtimeContainer'] = 'pk-compat-' + 'c' * 32
        write_json(evidence_root / 'runtime-inputs.json', pins)
        write_json(evidence_root / 'runtime-cleanup.json', {'container': pins['runtimeContainer'], 'absent': True, 'removed': False})
        write_json(evidence_root / 'runtime-process-result.json', {'exitCode': 0, 'boundedTimeoutExitCode': 124})
        write_json(evidence_root / 'image-capture-operations.json', [
            {'args': ['docker', action], 'exitCode': 0} for action in ('pull', 'create', 'inspect', 'cp', 'rm')])
        write_json(evidence_root / 'Feature/obj/project.assets.json', assets)
        write_json(evidence_root / 'Feature/packages.lock.json', {'syntheticNativeLock': True})
        write_json(evidence_root / 'artifacts/program-kit/building-block-restore.json', {'mode': 'locked', 'satisfied': True})
        for name in ('runtime.log', 'runtime.stderr'):
            (evidence_root / name).write_text('synthetic lifecycle guard, not an actual runtime proof')
        (evidence_root / 'bundle').mkdir()
        write_json(evidence_root / 'bundle/hostsettings.json', {'Nuplane': {'Loading': {'SharedAssemblies': shared}}})
        proof = {'inputs': pins, 'publicHostEvidence': probe.published_host_evidence(evidence_root, pins),
                 'runtimePackageInputsSha256': probe.file_sha256(evidence_root / 'runtime-package-inputs.json'),
                 'runtimeSharedBindingsSha256': probe.file_sha256(evidence_root / 'runtime-shared-bindings.json')}
        sealer.verify_named_host_evidence(evidence_root, proof)
        forged = copy.deepcopy(proof)
        forged['inputs']['catalogResolutionSha256'] = 'f' * 64
        try:
            sealer.verify_named_host_evidence(evidence_root, forged)
        except ValueError as error:
            assert 'retained inputs differ' in str(error)
        else:
            raise AssertionError('Sealer recheck admitted a claimed catalog differing from the retained runtime')
        results.append('seal-rejects-forged-catalog-versus-retained-inputs')
        for name, target in [('seal-rejects-changed-runtime-log', evidence_root / 'runtime.log'),
                             ('seal-rejects-changed-effective-bundle', evidence_root / 'bundle/hostsettings.json'),
                             ('seal-rejects-changed-native-lock', evidence_root / 'Feature/packages.lock.json'),
                             ('seal-rejects-changed-restore-provenance', retained / 'cshells.abstractions.0.0.29-preview.147.nupkg.metadata.json')]:
            original = target.read_bytes()
            target.write_bytes(b'changed')
            try:
                sealer.verify_named_host_evidence(evidence_root, proof)
            except (ValueError, json.JSONDecodeError):
                pass
            else:
                raise AssertionError('Sealer recheck admitted changed evidence: ' + name)
            target.write_bytes(original)
            results.append(name)
        write_json(evidence_root / 'bundle/extra.json', {})
        try:
            sealer.verify_named_host_evidence(evidence_root, proof)
        except ValueError as error:
            assert 'evidence changed' in str(error)
        else:
            raise AssertionError('Sealer recheck admitted an extra effective runtime file')
        (evidence_root / 'bundle/extra.json').unlink()
        results.append('seal-rejects-added-effective-bundle-input')
        for field in ('runtimePackageInputsSha256', 'runtimeSharedBindingsSha256'):
            forged = {**proof, field: 'f' * 64}
            try:
                sealer.verify_named_host_evidence(evidence_root, forged)
            except ValueError as error:
                assert 'manifest alias changed' in str(error)
            else:
                raise AssertionError('Sealer recheck admitted a forged manifest alias: ' + field)
            results.append('seal-rejects-' + field)

        def rejected(name, mutate, expected):
            root = base / name
            pins, assets, packages = fixture(root)
            try:
                mutate(root, pins, assets)
                probe.prepare_shared_runtime(root, pins, assets, packages)
            except (ValueError, OSError) as error:
                assert expected in str(error), (name, str(error))
            else:
                raise AssertionError('Invalid public binding admitted: ' + name)
            assert not list(packages.iterdir()), name
            assert not (root / 'runtime-archive-inputs').exists(), name
            results.append(name)

        rejected('wrong-profile', lambda root, pins, assets: pins.update(dependencyProfile='another-0.3-profile'), 'exact reviewed')
        rejected('mutable-image-tag', lambda root, pins, assets: pins.update(hostImage='ghcr.io/orbyss-io/foundation-host:0.3.0'), 'immutable public')
        rejected('changed-proof', lambda root, pins, assets: (root / 'public-host-inputs.json').write_text('{}'), 'capture inputs changed')
        rejected('external-proof-path', lambda root, pins, assets: pins['hostPayload'].update(inputs='../inputs.json'), 'fixture-owned')
        rejected('changed-host-dll', lambda root, pins, assets: (root / 'public-host-payload/CShells.Abstractions.dll').write_bytes(b'changed'), 'differs from its recorded')
        rejected('changed-effective-config', lambda root, pins, assets: write_json(root / 'public-host-payload/extra.json', {'changed': True}), 'differs from its recorded')
        rejected('added-effective-config', lambda root, pins, assets: write_json(root / 'public-host-payload/additional.json', {}), 'differs from its recorded')
        rejected('changed-native-runtime', lambda root, pins, assets: (root / 'public-host-payload/runtimes/linux-x64/native/provider.so').write_bytes(b'changed'), 'differs from its recorded')
        source_relative = '.orbyss-foundation/settings-sources/host/Transport/Options.cs.txt'
        rejected('changed-host-metadata-source', lambda root, pins, assets: (
            root / 'public-host-payload' / source_relative).write_bytes(b'changed'), 'differs from its recorded')
        rejected('missing-host-metadata-source', lambda root, pins, assets: (
            root / 'public-host-payload' / source_relative).unlink(), 'differs from its recorded')
        rejected('added-host-metadata-source', lambda root, pins, assets: (
            root / 'public-host-payload/.orbyss-foundation/settings-sources/host/Transport/Extra.cs.txt').write_bytes(
                b'additional source'), 'differs from its recorded')
        rejected('missing-required-shells-even-resealed', lambda root, pins, assets: ((root / 'public-host-payload/shells.json').unlink(), reseal(root, pins)), 'required runtime configuration')

        def config_mutation(root, mutate):
            path = root / 'public-host-payload/appsettings.json'
            value = json.loads(path.read_text())
            mutate(value['Nuplane']['Loading']['SharedAssemblies'])
            write_json(path, value)
        rejected('missing-cshell-shared-identity', lambda root, pins, assets: config_mutation(root, lambda shared: shared.pop()), 'exactly two')
        rejected('duplicate-shared-identity', lambda root, pins, assets: config_mutation(root, lambda shared: shared.__setitem__(1, shared[0])), 'duplicated or incomplete')
        rejected('broad-shared-major', lambda root, pins, assets: config_mutation(root, lambda shared: shared[0].update(MajorVersion=None)), 'policy differs')
        rejected('bool-shared-major', lambda root, pins, assets: config_mutation(root, lambda shared: shared[0].update(MajorVersion=False)), 'policy differs')
        rejected('unknown-shared-identity', lambda root, pins, assets: config_mutation(root, lambda shared: shared[0].update(Name='Orbyss.Foundation.*')), 'policy differs')
        rejected('optional-config-overrides-shared', lambda root, pins, assets: write_json(root / 'public-host-payload/hostsettings.json', {'Nuplane': {'Loading': {'SharedAssemblies': []}}}), 'overrides shared')
        rejected('foundation-shared-identity', lambda root, pins, assets: config_mutation(root, lambda shared: shared.__setitem__(1, {
            'Name': 'Orbyss.Foundation.Web.ProblemDetails', 'PublicKeyToken': None, 'MajorVersion': 0})), 'policy differs')
        rejected('extra-foundation-shared-identity', lambda root, pins, assets: config_mutation(root, lambda shared: shared.append({
            'Name': 'Orbyss.Foundation.Json', 'PublicKeyToken': None, 'MajorVersion': 0})), 'exactly two')
        rejected('foundation-root-dll-even-resealed', lambda root, pins, assets: (
            (root / 'public-host-payload/Orbyss.Foundation.Json.dll').write_bytes(b'coupled'), reseal(root, pins)), 'cannot carry Foundation runtime DLLs')
        rejected('foundation-native-dll-even-resealed', lambda root, pins, assets: (
            (root / 'public-host-payload/runtimes/linux-x64/native/orbyss.foundation.Json.DLL').write_bytes(b'coupled'), reseal(root, pins)), 'cannot carry Foundation runtime DLLs')

        def coupled_dependencies(root, pins, assets):
            path = root / 'public-host-payload/Orbyss.Foundation.Host.deps.json'
            value = json.loads(path.read_text())
            value['libraries']['Orbyss.Foundation.Web.ProblemDetails/0.3.0'] = {'type': 'package'}
            write_json(path, value)
            reseal(root, pins)
        rejected('foundation-native-library-even-without-dll', coupled_dependencies, 'cannot reference a Foundation runtime package')

        def wrong_native_version(root, pins, assets):
            path = root / 'public-host-payload/Orbyss.Foundation.Host.deps.json'
            value = json.loads(path.read_text())
            value['libraries']['CShells.Abstractions/0.0.29-preview.146'] = value['libraries'].pop('CShells.Abstractions/0.0.29-preview.147')
            write_json(path, value)
            reseal(root, pins)
        rejected('native-version-even-resealed', wrong_native_version, 'shared package version')
        def wrong_host_version(root, pins, assets):
            path = root / 'public-host-payload/Orbyss.Foundation.Host.deps.json'
            value = json.loads(path.read_text())
            value['libraries']['Orbyss.Foundation.Host/0.2.4'] = value['libraries'].pop('Orbyss.Foundation.Host/0.3.0')
            write_json(path, value)
            reseal(root, pins)
        rejected('wrong-native-host-version-even-resealed', wrong_host_version, 'native version differs')
        rejected('missing-shared-archive', lambda root, pins, assets: package_path(root, 'CShells.Abstractions').unlink(), 'archive missing or ambiguous')
        rejected('missing-shared-assets', lambda root, pins, assets: assets['libraries'].pop('CShells.Abstractions/0.0.29-preview.147'), 'closure omits')
        rejected('private-cshell-archive', lambda root, pins, assets: write_json(package_path(root, 'CShells.Abstractions').parent / '.nupkg.metadata', {'source': 'C:/private/feed'}), 'public CShells preview source')
        rejected('missing-cshell-native-source', lambda root, pins, assets: write_json(package_path(root, 'CShells.Abstractions').parent / '.nupkg.metadata', {}), 'public CShells preview source')
        for name, source in [('nuget-org-cshell-archive', 'https://api.nuget.org/v3/index.json'),
                             ('external-cshell-archive', 'https://packages.example.invalid/v3/index.json')]:
            rejected(name, lambda root, pins, assets, source=source: write_json(
                package_path(root, 'CShells.Abstractions').parent / '.nupkg.metadata', {'source': source}),
                'public CShells preview source')

        def retained_source_rejected(name, source, *, change_metadata=True, change_binding=True):
            root = base / name
            pins, assets, packages = fixture(root)
            probe.prepare_shared_runtime(root, pins, assets, packages)
            probe.verify_retained_runtime_inputs(root, pins)
            records = json.loads((root / 'runtime-package-inputs.json').read_text())
            bindings = json.loads((root / 'runtime-shared-bindings.json').read_text())
            record = next(item for item in records if item['id'].startswith('CShells.Abstractions/'))
            metadata_path = root / 'runtime-archive-inputs' / record['nativeProvenance']
            if change_metadata:
                write_json(metadata_path, {} if source is None else {'source': source})
                record['nativeProvenanceSha256'] = probe.file_sha256(metadata_path)
            if change_binding:
                if source is None:
                    record.pop('nativeSource')
                else:
                    record['nativeSource'] = source
            # Keep archive/provenance hashes and both manifests self-consistent.
            # Rejection must come from source admission, not a stale hash alias.
            binding = next(item for item in bindings if item['id'] == record['id'])
            for field in ('nativeSource', 'nativeProvenanceSha256'):
                if field in record:
                    binding[field] = record[field]
                else:
                    binding.pop(field, None)
            write_json(root / 'runtime-package-inputs.json', records)
            write_json(root / 'runtime-shared-bindings.json', bindings)
            try:
                probe.verify_retained_runtime_inputs(root, pins)
            except ValueError as error:
                assert 'Retained CShells public preview restore source differs' in str(error)
            else:
                raise AssertionError('Retained unreviewed CShells source admitted: ' + name)
            results.append(name)

        for name, source in [('retained-nuget-org-source', 'https://api.nuget.org/v3/index.json'),
                             ('retained-external-source', 'https://packages.example.invalid/v3/index.json'),
                             ('retained-private-source', 'C:/private/feed'),
                             ('retained-missing-source', None)]:
            retained_source_rejected(name, source)
        retained_source_rejected('retained-binding-source-drift', 'https://api.nuget.org/v3/index.json', change_metadata=False)
        retained_source_rejected('retained-native-source-disagrees-with-binding', 'C:/private/feed', change_binding=False)
        rejected('wrong-archive-dll', lambda root, pins, assets: rewrite_archive(package_path(root, 'CShells.Abstractions'), lambda entries: [(name, b'changed' if name.endswith('.dll') else value) for name, value in entries]), 'DLL differs')
        rejected('wrong-archive-framework', lambda root, pins, assets: rewrite_archive(package_path(root, 'CShells.Abstractions'), lambda entries: [(name.replace('lib/net10.0/', 'lib/net8.0/'), value) for name, value in entries]), 'exact net10 DLL')
        rejected('wrong-nuspec-version', lambda root, pins, assets: rewrite_archive(package_path(root, 'CShells.Abstractions'), lambda entries: [(name, value.replace(b'<version>0.0.29-preview.147</version>', b'<version>0.0.29-preview.146</version>') if name.endswith('.nuspec') else value) for name, value in entries]), 'metadata differs')
        rejected('unsafe-native-path', lambda root, pins, assets: assets['libraries']['CShells.Abstractions/0.0.29-preview.147'].update(path='../outside'), 'path is unsafe')

        def duplicate_root(root, pins, assets):
            source = root / 'native-cache'
            target = root / 'duplicate-cache'
            shutil.copytree(source, target)
            assets['packageFolders'][str(target)] = {}
        rejected('ambiguous-cache-roots', duplicate_root, 'archive missing or ambiguous')

        # Existing fixtures and restored inputs never acquire the new restore policy.
        old = {'foundationRelease': '0.2.2', 'hostImage': 'historical'}
        assert probe.contracts_profile(old) is False
        try:
            probe.contracts_profile({**old, 'hostPayload': {}})
        except ValueError:
            pass
        else:
            raise AssertionError('Historical inputs admitted a new binding contract')
        for name, use_contracts in [('old-fixture', False), ('new-fixture', True)]:
            target = base / name
            target.mkdir()
            (target / 'Feature.csproj').write_text('<Project><ItemGroup><PackageReference Include="Orbyss.Foundation.Json" Version="0.2.2"/></ItemGroup></Project>')
            wrapper.retarget_fixture(target, {'packages': {'nuget:Orbyss.Foundation.Json': {'version': '0.3.0' if use_contracts else '0.2.2'}}}, use_contracts)
            project = ET.parse(target / 'Feature.csproj')
            settings = list(project.iter('RestoreEnablePackagePruning'))
            assert ([setting.text for setting in settings] == ['false']) if use_contracts else not settings
        results.append('historical-selection-and-disposable-only-pruning')

        # Fake Docker executes the same owned capture lifecycle. It never invokes
        # Docker or network; the positive is not image qualification evidence.
        source_payload = base / 'positive/public-host-payload'
        for name, failure in [('capture-positive', None), ('capture-copy-failure', 'cp'), ('capture-inspection-mismatch', 'inspect'), ('capture-cleanup-failure', 'rm'), ('capture-create-failure', 'create'),
                              ('capture-timeout-cleanup', 'timeout'), ('capture-image-env-override', 'env'), ('capture-image-command-override', 'cmd')]:
            target = base / name
            target.mkdir()
            calls = []
            def fake(arguments, **options):
                calls.append(arguments)
                assert options['env'] == wrapper.runtime_environment()
                assert arguments[:2] != ['docker', 'build']
                action = arguments[1]
                if action == 'cp' and failure == 'timeout':
                    raise subprocess.TimeoutExpired(arguments, 300, output=b'partial native output', stderr=b'timeout')
                if action == failure and action != 'inspect':
                    return SimpleNamespace(returncode=1, stdout='', stderr='synthetic failure')
                if action == 'inspect':
                    selected_image = 'changed' if failure == 'inspect' else IMAGE
                    config = {'Image': selected_image}
                    if failure == 'env':
                        config['Env'] = ['NUPLANE__Loading__SharedAssemblies__0__Name=changed']
                    if failure == 'cmd':
                        config['Cmd'] = ['dotnet', 'Orbyss.Foundation.Host.dll', '--Nuplane:Loading:SharedAssemblies:0:Name=changed']
                    return SimpleNamespace(returncode=0, stdout=json.dumps([{'Config': config, 'Image': IMAGE_ID}]), stderr='')
                if action == 'cp':
                    shutil.copytree(source_payload, Path(arguments[-1]), dirs_exist_ok=True)
                return SimpleNamespace(returncode=0, stdout='owned', stderr='')
            try:
                result = wrapper.capture_public_host(target, IMAGE, runner=fake)
                assert failure is None and result['inputsSha256'] == probe.file_sha256(target / 'public-host-inputs.json')
            except (ValueError, RuntimeError, subprocess.TimeoutExpired):
                assert failure is not None
                assert not (target / 'public-host-inputs.json').exists()
            assert calls[-1][1:3] == ['rm', '-v']
            assert [call[1] for call in calls][:2] == ['pull', 'create']
            assert '--pull=never' in calls[1]
            assert json.loads((target / 'image-capture-operations.json').read_text())[-1]['args'][1] == 'rm'
            results.append(name)

        before = os.environ.copy()
        try:
            os.environ.update({'NUGET_CREDENTIALPROVIDERS_PATH': 'credential', 'GITHUB_TOKEN': 'secret',
                               'NUPLANE__Loading__SharedAssemblies__0__Name': 'override', 'SAFE_TEST_VALUE': 'safe'})
            environment = wrapper.runtime_environment()
            assert 'GITHUB_TOKEN' not in environment and 'NUGET_CREDENTIALPROVIDERS_PATH' not in environment
            assert 'NUPLANE__Loading__SharedAssemblies__0__Name' not in environment
            assert environment['SAFE_TEST_VALUE'] == 'safe'
            os.environ['CUSTOM_REGISTRY_KEY'] = 'registry-value'
            assert 'CUSTOM_REGISTRY_KEY' not in wrapper.runtime_environment(['CUSTOM_REGISTRY_KEY'])
        finally:
            os.environ.clear()
            os.environ.update(before)
        results.append('runtime-child-credentials-and-framework-overrides-removed')

        for name, child_code, present, wrong_owner, cleanup_failure in [
            ('outer-timeout-removes-owned-runtime', 124, True, False, False),
            ('outer-success-confirms-child-cleanup', 0, False, False, False),
            ('outer-wrong-owner-refuses-delete', 124, True, True, False),
            ('outer-cleanup-failure-forbids-success', 0, True, False, True)]:
            target = base / name
            target.mkdir()
            pins = {'runtimeContainer': 'pk-compat-' + 'c' * 32, 'hostImage': IMAGE,
                    'credentialEnvironmentNames': ['CUSTOM_REGISTRY_KEY']}
            commands = []
            state = {'present': present}
            def child(arguments, cwd, stdout, stderr, timeout):
                assert timeout == 600 and arguments == [wrapper.sys.executable, 'runtime_probe.py']
                assert not any(key == 'GITHUB_TOKEN' for key in os.environ)
                assert 'CUSTOM_REGISTRY_KEY' not in os.environ
                stdout.write(b'synthetic native child completion')
                stderr.write(b'synthetic timeout' if child_code == 124 else b'')
                return child_code
            def cleanup(arguments, **options):
                commands.append(arguments)
                action = arguments[1]
                if action == 'ps':
                    output = 'owned-native-id' if state['present'] else ''
                elif action == 'inspect':
                    output = json.dumps([{'Name': '/' + pins['runtimeContainer'], 'Config': {'Image': IMAGE,
                        'Labels': {'program-kit.owner': 'other' if wrong_owner else pins['runtimeContainer']}}}])
                elif action == 'rm':
                    if cleanup_failure:
                        return SimpleNamespace(returncode=1, stdout='', stderr='synthetic cleanup failure')
                    state['present'] = False
                    output = 'removed'
                else:
                    raise AssertionError(arguments)
                return SimpleNamespace(returncode=0, stdout=output, stderr='')
            os.environ['GITHUB_TOKEN'] = 'synthetic-secret'
            os.environ['CUSTOM_REGISTRY_KEY'] = 'synthetic-registry-secret'
            try:
                code = wrapper.run_prepared_runtime(target, pins, runner=child, cleanup_runner=cleanup)
                assert not wrong_owner and not cleanup_failure and code == child_code
            except (ValueError, RuntimeError):
                assert wrong_owner or cleanup_failure
            finally:
                os.environ.pop('GITHUB_TOKEN')
                os.environ.pop('CUSTOM_REGISTRY_KEY')
            receipt = json.loads((target / 'runtime-cleanup.json').read_text())
            assert receipt['absent'] is (not wrong_owner and not cleanup_failure)
            assert receipt['removed'] is (present and not wrong_owner and not cleanup_failure)
            if wrong_owner:
                assert not any(command[1] == 'rm' for command in commands)
            if child_code == 124:
                assert json.loads((target / 'runtime-process-result.json').read_text())['exitCode'] == 124
            assert not (target / 'qualification-result.json').exists()
            results.append(name)

    write_json(parent / 'results.json', {'satisfied': True, 'qualificationClaimed': False,
                                       'groups': results, 'count': len(results)})
    print(f'Published Host fixture binding guards passed ({len(results)} groups). No public image or runtime qualification was invoked.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

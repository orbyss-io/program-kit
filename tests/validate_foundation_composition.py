"""Bounded typed composition reconciliation and preserved source/security conflicts."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import shutil

ARTIFACT = None
COMMAND_NUMBER = 0

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-dotnet/scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
import foundation_composition as composition


def run(command, cwd, expected=0, timeout=240):
    global COMMAND_NUMBER
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if ARTIFACT:
        COMMAND_NUMBER += 1
        stem = ARTIFACT / ('command-'+str(COMMAND_NUMBER))
        stem.with_suffix('.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        stem.with_suffix('.json').write_text(json.dumps({'command':command, 'exitCode':result.returncode, 'expected':expected}), encoding='utf-8')
    if result.returncode != expected:
        if ARTIFACT and Path(cwd) != ROOT:
            retained = ARTIFACT / ('failed-command-'+str(COMMAND_NUMBER))
            shutil.copytree(cwd,retained,ignore=shutil.ignore_patterns('bin','obj','__pycache__','artifacts'))
            normal_evidence = Path(cwd)/'artifacts/program-kit'
            if normal_evidence.is_dir(): shutil.copytree(normal_evidence,retained/'artifacts/program-kit')
            packages = Path(cwd)/'artifacts/packages'
            if packages.is_dir(): shutil.copytree(packages,retained/'artifacts/packages')
        raise AssertionError(str(command) + '\n' + result.stdout + result.stderr)
    return result


def sync(root, check=False, expected=0):
    import composition_model
    input_path = root / composition.INPUT
    value = composition.read(input_path)
    if value.get('schemaVersion') == 1:
        input_path.write_bytes(composition.encoded(composition_model.from_legacy(value, root)))
    args = [sys.executable, str(SCRIPTS/'dotnet_sync.py'), '--target', str(root), '--profile-selected',
            '--foundation-host-accepted', '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
    if check: args.append('--check')
    result = run(args, ROOT, expected)
    if not result.stdout.lstrip().startswith('{'):
        raise AssertionError('Sync did not emit a reconciliation plan: '+result.stderr)
    return json.loads(result.stdout.split('committed reconciliation transaction:')[0])


def rejected(value, mutate):
    altered = copy.deepcopy(value); mutate(altered)
    try: composition.validate_configuration(altered)
    except ValueError: return
    raise AssertionError('Invalid composition was accepted')


def retirement_checks(root, value):
    # Leave the independent optional package-build fixture untouched.
    with tempfile.TemporaryDirectory(prefix='program-kit-retirement-') as temporary:
        isolated = Path(temporary)
        shutil.copytree(root, isolated, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('artifacts','bin','obj','__pycache__'))
        _retirement_checks(isolated, value)


def _retirement_checks(root, value):
    """Exercise source ownership through actual feature selection and reconciliation."""
    selected = copy.deepcopy(value)
    extras = [{'path':f'src/Retirement.{kind}/Retirement.{kind}.csproj',
               'packageId':f'Retirement.{kind}', 'featureIdentity':f'Retirement.{kind}',
               'role':'implementation'} for kind in ('Both','SourceOnly','ProjectOnly','AddedSource','Untouched')]
    selected['projects'].extend(extras)
    selected['runtime']['rootPackages'].extend(p['packageId'] for p in extras)
    (root/composition.INPUT).write_bytes(composition.encoded(selected)); sync(root)
    custom = [root/extras[0]['path'], root/'src/Retirement.Both/ApiFeature.cs',
              root/'src/Retirement.SourceOnly/ApiFeature.cs', root/extras[2]['path']]
    retained = {path for project in extras[:4]
                for path in (project['path'], str(Path(project['path']).parent/'ApiFeature.cs').replace('\\','/'))}
    original_state = composition.read(root/'config/program-kit/managed.json')
    for path in custom:
        path.write_bytes(path.read_bytes()+b'\n<!-- consumer edit -->\n' if path.suffix=='.csproj'
                         else path.read_bytes()+b'\n// consumer edit\n')
    added_source = 'src/Retirement.AddedSource/OwnedCode.cs'
    (root/added_source).write_bytes(b'namespace Retirement.AddedSource; public sealed class OwnedCode {}\n')
    custom_bytes = {p.relative_to(root).as_posix():p.read_bytes() for p in custom}
    retained_bytes = {path:(root/path).read_bytes() for path in retained | {added_source}}
    sync(root)
    customized_state = composition.read(root/'config/program-kit/managed.json')
    for path in custom_bytes:
        # Preserving source does not authenticate a consumer's new bytes.
        assert customized_state['files'][path] == original_state['files'][path]
    assert added_source not in original_state['files'] and added_source not in customized_state['files']
    (root/composition.INPUT).write_bytes(composition.encoded(value))
    preview = sync(root, True, 1)
    assert retained <= set(preview['preserved'])
    assert not preview['conflicts']
    assert not any(a['path'] in retained for a in preview['actions'])
    assert all((root/path).read_bytes()==content for path,content in custom_bytes.items())
    sync(root)
    released = composition.read(root/'config/program-kit/managed.json')
    assert all(path not in released['files'] for path in retained)
    assert all((root/path).read_bytes()==content for path,content in retained_bytes.items())
    assert added_source not in released['files']
    assert not (root/extras[4]['path']).exists()
    assert not (root/'src/Retirement.Untouched/ApiFeature.cs').exists()
    resolved = next(iter(composition.read(root/composition.RESOLVED)['hosts'].values()))
    graph = composition.read(root/'config/program-kit/architecture.json')['runtimeComposition']
    features = composition.read(root/'config/program-kit/web-profile.shells.json')['CShells']['Shells']['default']['Features']
    for project in extras:
        assert project['packageId'] not in resolved['rootPackages']
        assert (project['path'] in {p['path'] for p in graph['projects']}) == (project in extras[:4])
        assert project['featureIdentity'] not in features
    sync(root, True)
    import importlib.util
    sys.path.insert(0, str(root/'scripts'))
    try:
        spec = importlib.util.spec_from_file_location('retirement_architecture', root/'scripts/repository_architecture.py')
        architecture_checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(architecture_checker)
        architecture_checker.validate_planned(root, composition.read(root/'config/program-kit/architecture.json'))
    finally:
        sys.path.remove(str(root/'scripts'))
    physical = {p.relative_to(root).as_posix() for p in (root/'src').rglob('*.csproj')}
    assert physical <= {p['path'] for p in graph['projects']}
    # A second apply cannot silently forget the released source classification.
    sync(root); sync(root, True)
    assert composition.read(root/'config/program-kit/architecture.json')['runtimeComposition']['projects'] == graph['projects']
    assert all((root/path).read_bytes()==content for path,content in retained_bytes.items())
    if ARTIFACT:
        (ARTIFACT/(value['compositionId']+'-retirement.json')).write_bytes(composition.encoded({
            'preservedSourceHashes':{path:composition.digest(content) for path,content in retained_bytes.items()},
            'sourceRoles':graph['projects'], 'selectedRoots':resolved['rootPackages'],
            'releasedStateEntries':sorted(retained), 'untouchedProjectRemoved':True,
            'addedConsumerSourceNeverGoverned':added_source,
            'plannedArchitectureValidated':True,'physicalProjectsClassified':True}))

    # Counterexamples enter the same real retirement loop: neither a managed or
    # configuration source nor unrelated/engineering scaffolds get this exception.
    state_path = root/'config/program-kit/managed.json'; original = state_path.read_bytes()
    producer = '../../scripts/foundation_composition.py'
    controls = [('eng/retired-managed.cs','managed','foundation',producer),
                ('eng/retired-configuration.cs','configuration','foundation',producer),
                ('eng/retired-architecture.json','scaffold','foundation',producer),
                ('src/OtherContribution.cs','scaffold','base',producer),
                ('src/OtherProducer.csproj','scaffold','foundation','files/other.csproj'),
                ('src/UnknownProducer.cs','scaffold','foundation',None)]
    state = composition.read(state_path)
    for path,ownership,contribution,source_identity in controls:
        state['files'][path] = {'ownership':ownership,'contribution':contribution,
            'baselineHash':composition.digest(b'authenticated'),
            'lastWrittenHash':composition.digest(b'authenticated'),
            'installedHash':composition.digest(b'authenticated')}
        if source_identity is not None: state['files'][path]['sourceIdentity'] = source_identity
        destination=root/path; destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(b'customized consumer bytes')
    state_path.write_bytes(composition.encoded(state))
    before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    conflicts = sync(root, True, 2)
    assert {path for path,_,_,_ in controls} <= {c['path'] for c in conflicts['conflicts']}
    assert not {path for path,_,_,_ in controls} & set(conflicts['preserved'])
    assert before == {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    state_path.write_bytes(original)
    for path,_,_,_ in controls: (root/path).unlink()
    sync(root, True)


def main():
    """Bounded current reconciliation coverage; historical layouts are not acceptance."""
    global ARTIFACT
    import uuid
    import composition_model as model
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=sorted(composition.VARIANTS))
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--identity-services', action='store_true')
    parser.add_argument('--candidate-feed')
    args = parser.parse_args()
    if args.candidate_feed:
        raise ValueError('Use the explicit retained development-candidate qualifier; this validator uses public captured packages')
    ARTIFACT = ROOT / 'artifacts/foundation-composition' / uuid.uuid4().hex
    ARTIFACT.mkdir(parents=True)
    # A former standalone generator must hand native pins back without deleting
    # them, and add its new import without replacing the consumer's central file.
    from composition_fixture import two_apps, accept_fixture
    accepted_root = ARTIFACT / 'accepted-ownership/consumer'
    (accepted_root / 'scripts').mkdir(parents=True)
    accepted_graph = two_apps(ROOT)
    accept_fixture(accepted_root, accepted_graph, ROOT)
    (accepted_root / composition.INPUT).write_bytes(composition.encoded(accepted_graph))
    activation = accepted_root / 'tests/Activation/Activation.csproj'
    activation.parent.mkdir(parents=True)
    activation_bytes = (ROOT / 'tests/fixtures/composition-activation/Activation.Tests.csproj').read_bytes()
    activation.write_bytes(activation_bytes)
    sync(accepted_root)
    assert activation.read_bytes() == activation_bytes
    native_path = 'config/program-kit/build/ProgramKit.BuildingBlocks.props'
    native_bytes = b'<Project><!-- existing native selection contribution --></Project>\n'
    (accepted_root / native_path).write_bytes(native_bytes)
    state_path = accepted_root / 'config/program-kit/managed.json'
    state = composition.read(state_path)
    state['files'][native_path] = copy.deepcopy(state['files']['config/program-kit/build/ProgramKit.Foundation.props'])
    state_path.write_bytes(composition.encoded(state))
    central_path = accepted_root / 'Directory.Packages.props'
    central = central_path.read_text()
    central = '\n'.join(line for line in central.split('\n') if 'ProgramKit.Foundation.props' not in line)
    central = central.replace('</Project>', '  <!-- consumer-owned central configuration -->\n</Project>')
    central_path.write_text(central, encoding='utf-8')
    sync(accepted_root)
    assert (accepted_root / native_path).read_bytes() == native_bytes
    assert native_path not in composition.read(state_path)['files']
    migrated_central = central_path.read_text()
    assert 'consumer-owned central configuration' in migrated_central
    assert migrated_central.count('<Import Project="config/program-kit/build/ProgramKit.Foundation.props"') == 1
    sync(accepted_root, True)
    assert activation.read_bytes() == activation_bytes
    observations = []
    for variant in [args.variant] if args.variant else sorted(composition.VARIANTS):
        legacy = composition.read(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions' / (variant + '.json'))
        legacy['theme']['branding'] = {'displayName': 'Qualified Example', 'accentColor': '#0088aa'}
        root = ARTIFACT / variant / 'consumer'; (root / 'scripts').mkdir(parents=True)
        input_path = root / composition.INPUT
        input_path.write_bytes(composition.encoded(legacy))
        rejected_before = input_path.read_bytes()
        denied = run([sys.executable, str(SCRIPTS / 'dotnet_sync.py'), '--target', str(root), '--check',
                      '--profile-selected', '--web-profile', 'bff-cookie'], ROOT, 1)
        assert 'PKM001' in denied.stderr and input_path.read_bytes() == rejected_before
        graph = model.from_legacy(legacy, root)
        input_path.write_bytes(composition.encoded(graph))
        began = time.monotonic(); preview = sync(root, True, 1)
        assert not (root / 'src').exists() and not (root / 'deploy').exists()
        sync(root); sync(root, True); composition.verify_outputs(root)
        resolved = composition.read(root / composition.RESOLVED)
        assert resolved['schemaVersion'] == 2 and len(resolved['hosts']) == 1
        assert not (root / 'eng/Dev.ps1').exists() and not (root / 'deploy/compose.identity.yml').exists()
        assert not list((root / 'src').glob('**/*Composition*.csproj'))
        authority = model.environment(graph)['product-identity']
        realm = root / ('deploy/keycloak/product-identity/' + authority['realm'] + '-realm.json')
        assert composition.read(realm)['displayName'] == 'Qualified Example'
        theme = root / 'deploy/keycloak/product-identity/themes/program-kit/login/resources/css/program-kit.css'
        assert '--program-kit-brand-accent: #0088aa' in theme.read_text()
        feature = root / Path(legacy['projects'][0]['path']).parent / 'ApiFeature.cs'
        feature.write_text(feature.read_text() + '\n// Consumer-owned customization.\n')
        sync(root); assert 'Consumer-owned customization' in feature.read_text()
        shell = root / graph['resources']['application-shell']['source']
        original_shell = shell.read_bytes()
        product_policy = composition.read(shell)
        product_policy['CShells']['Shells']['default']['Configuration'] = {'Foundation': {'Web': {'RolePermissions': {'user': ['product.read']}}}}
        shell.write_bytes(composition.encoded(product_policy)); sync(root); composition.verify_outputs(root)
        for key, value in [('CallbackPath', '/unreviewed'), ('BackchannelAuthority', 'https://other.example/realms/wrong'),
                           ('DiscoveryTimeoutSeconds', 31)]:
            wrong = copy.deepcopy(product_policy)
            wrong['CShells']['Shells']['default']['Configuration']['Foundation']['Web'][key] = value
            shell.write_bytes(composition.encoded(wrong))
            before = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            run([sys.executable, str(SCRIPTS / 'dotnet_sync.py'), '--target', str(root), '--profile-selected',
                 '--foundation-host-accepted', '--building-block-sources-approved', '--web-profile', 'bff-cookie'], ROOT, 1)
            assert before == {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob('*') if path.is_file()}
        shell.write_bytes(original_shell)
        graph['resources']['application-client']['callbackPath'] = '/callback/custom'
        input_path.write_bytes(composition.encoded(graph)); sync(root); composition.verify_outputs(root)
        assert any('/callback/custom' in item.get('redirectUris', []) [0] for item in composition.read(realm)['clients'] if item.get('redirectUris'))
        for protected in (root / 'config/program-kit/web-profile.shells.json', realm, theme):
            original = protected.read_bytes(); protected.write_bytes(original + b'\n')
            try:
                if protected.name == 'web-profile.shells.json':
                    conflicts = sync(root, True, 2)
                    assert protected.relative_to(root).as_posix() in {row['path'] for row in conflicts['conflicts']}
                else:
                    try: composition.verify_outputs(root)
                    except ValueError: pass
                    else: raise AssertionError('changed managed authority/theme retained inherited assurance')
            finally: protected.write_bytes(original)
        # Preserve all source/project customization and retirement counterexamples.
        retirement_checks(root, legacy)
        observations.append({'variant': variant, 'reconciliationSeconds': round(time.monotonic() - began, 3),
                             'typedModel': True, 'realRuntimeTested': False})
    if args.build or args.identity_services:
        run([sys.executable, 'tests/validate_composition_start.py', '--execute'], ROOT, timeout=1800)
    (ARTIFACT / 'status.json').write_text(json.dumps({'status': 'passed', 'observations': observations}, indent=2))
    print('Typed composition reconciliation passed: ' + str(ARTIFACT))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        if ARTIFACT:
            (ARTIFACT/'status.json').write_text(json.dumps({'status':'failed','failure':str(error)}),encoding='utf-8')
        raise

"""F8 actual packaged coding journeys through maintained native owners.

All consumer authorship is fictional. These deterministic commands never start
an agent, bootstrap workflow, provider operation or an existing real consumer.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
F7 = '4b90dc7ea6458fc2fbd6a5ae7e35c552426ad9e8'
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'scripts'),
               str(ROOT / 'extensions/program-kit-governance/scripts')]
from coding_review_fixture import write
from local_bundle_fixture import install_local_bundle, verify_release_copies
from owned_fixture import filesystem_path, native_path
from validate_package_smoke import extract
from run_validation import input_snapshot
from live.v2.supervisor import run_supervised


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_baseline_source():
    return '''import json,sys
from pathlib import Path
root=Path(sys.argv[1]);installed=root/'.specify/extensions'
sys.path.insert(0,str(installed/'program-kit-building-blocks/scripts'))
import building_blocks as blocks
catalog_path=installed/'program-kit-building-blocks/references/orbyss-building-blocks.json'
catalog=blocks.load_json(catalog_path)
path=root/'docs/architecture/building-block-selection.json';old=blocks.load_json(path)
graph=blocks.load_json(root/'eng/architecture.json')['runtimeComposition']['projects']
roles={p['path']:p['role'] for p in graph}
targets=[]
for target in old['targets']:
 targets.append({'id':target['id'],'kind':'dotnet-project','path':target['path'],
  'role':roles[target['path']],'scope':'application','placement':{'owner':'lookup',
   'state':'observed','rationale':'Existing fictional immutable snapshot owner; no package activation.',
   'decisionIds':['snapshot-owner']}})
selection={'$schema':'.specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json',
 'schemaVersion':'1.0','selectionId':'fictional-snapshot-baseline','revision':1,'status':'Accepted',
 'catalog':blocks.catalog_binding(catalog),
 'authority':{'architectureMap':'docs/architecture/architecture-map.json','decisionIds':['snapshot-owner'],
  'rationale':'Fictional existing SDK/BCL source. Empty component selection claims no host/provider activation.'},
 'scopes':[{'id':'application','kind':'application','environment':'development'}], 'targets':targets,'instances':[]}
blocks.atomic_write(path,blocks.pretty_json(selection))
decision=root/'docs/architecture/decisions/snapshot-owner.md';decision.parent.mkdir(parents=True,exist_ok=True)
decision.write_text('# Fictional existing snapshot owner\\nStatus: Accepted\\nOwn exact immutable row/report semantics in the existing pure source owners. No host, provider, durable store or real product acceptance.\\n')
model_path=root/'docs/architecture/architecture-map.json';model=blocks.load_json(model_path)
for owner in model['elements']:
 if owner['id']=='lookup':owner['ownership']='Fictional immutable snapshot report and row semantics'
for item in model['decisions']:
 if item['id']=='snapshot-owner':item.update(path=decision.relative_to(root).as_posix(),sha256=blocks.raw_sha256(decision))
model['documentation']=[{'id':'building-block-selection','path':path.relative_to(root).as_posix(),
 'sha256':blocks.raw_sha256(path),'scope':'Fictional existing SDK/BCL source only'}]
blocks.atomic_write(model_path,blocks.pretty_json(model))
blocks.preserve_dependency_profile(root,selection,catalog_path)
print('Fictional accepted source/catalog baseline; no feature, bootstrap approval or product acceptance created.')
'''


def scenario(mode):
    token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6]
    review = Path(filesystem_path(ROOT / 'artifacts/f8-review' / token))
    review.mkdir(parents=True)
    consumer = Path(filesystem_path(ROOT / 'artifacts/t' / ('f8-' + uuid.uuid4().hex[:8])))
    consumer.mkdir(parents=True)
    release = Path(filesystem_path(ROOT / 'artifacts/t' / ('r8-' + uuid.uuid4().hex[:8])))
    release.mkdir(parents=True)
    scratch = review / 'tmp'; scratch.mkdir()
    before = input_snapshot()
    started = time.monotonic()
    result = {'status': 'running', 'mode': mode, 'sourceCommit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'workingInputs': before,
        'fixtureSha256': sha(Path(__file__)), 'consumer': native_path(consumer),
        'release': native_path(release), 'fictionalAuthorship': True, 'commands': []}
    environment = dict(os.environ, PYTHONUTF8='1', TEMP=native_path(scratch),
                       TMP=native_path(scratch), TMPDIR=native_path(scratch))
    write(review / 'index.md', '# Incomplete F8 ' + mode + '\n\nInspect results.json and both streams. No success inferred.\n')

    def run(label, command, expected=0, marker=None, cwd=None):
        arguments = [native_path(v) if isinstance(v, Path) else str(v) for v in command]
        step_start = time.monotonic()
        directory = review / 'output' / label
        observed = run_supervised(arguments, cwd=native_path(cwd or consumer), environment=environment,
                                  evidence_directory=directory, timeout_seconds=240)
        row = {'id': label, 'command': arguments, 'cwd': native_path(cwd or consumer),
               'expectedExit': expected, 'actualExit': observed.exitCode,
               'timedOut': observed.timedOut, 'cleanupComplete': observed.cleanupComplete,
               'logsDrained': observed.logsDrained, 'elapsedSeconds': round(time.monotonic() - step_start, 3),
               'stdoutSha256': sha(directory / 'workflow.stdout.log'),
               'stderrSha256': sha(directory / 'workflow.stderr.log')}
        result['commands'].append(row); write(review / 'results.json', result)
        output = (directory / 'workflow.stdout.log').read_text(encoding='utf-8')
        errors = (directory / 'workflow.stderr.log').read_text(encoding='utf-8')
        assert not observed.timedOut and observed.cleanupComplete and observed.logsDrained, label + ': incomplete execution'
        assert observed.exitCode == expected, label + ': inspect both retained streams in ' + native_path(directory)
        assert not marker or marker in output + errors, label + ': intended independent marker absent'
        try: return json.loads(output)
        except ValueError: return output

    def packages():
        destination = review / 'packages'
        run('build-actual-archives', [sys.executable, ROOT / 'scripts/build_release.py', '--output',
                                   destination.relative_to(Path(filesystem_path(ROOT))).as_posix()], cwd=ROOT)
        version = (ROOT / 'VERSION').read_text().strip()
        archives = {p.name: sha(p) for p in destination.glob('*.zip')}
        result['archives'] = archives
        extract(destination / ('program-kit-' + version + '.zip'), release)
        from zipfile import ZipFile
        with ZipFile(destination / ('program-kit-' + version + '.zip')) as archive:
            result['bundleEntries'] = len(archive.namelist())
            assert result['bundleEntries'] <= 512
        return version

    def install():
        import specify_cli
        site = Path(specify_cli.__file__).parent.parent
        bridge = [sys.executable, release / 'scripts/invoke_specify.py', '--site-packages', site, '--']
        environment.update(SPECIFY_INIT_DIR=native_path(consumer), PROGRAM_KIT_SPECIFY_SITE_PACKAGES=str(site))
        run('native-init', [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                            '--script', 'py', '--ignore-agent-tools'])
        install_local_bundle(consumer, release, bridge, run)
        import schema_runtime
        original = schema_runtime.runtime_path(ROOT)
        target = schema_runtime.runtime_path(consumer)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(filesystem_path(original), filesystem_path(target))
        schema_runtime.record_copy(consumer)
        run('installed-coherence', [sys.executable, consumer / '.specify/extensions/program-kit-governance/scripts/governance_state.py',
                                    'validate-installation'])
        from validate_task_generation import validate_installed_workflow
        validate_installed_workflow(consumer, execute=False)
        verify_release_copies(consumer, release)
        result['installedHookAndCommandMechanics'] = True
        return bridge

    def baseline(label):
        helper = review / (label + '-native-baseline.py')
        write(helper, native_baseline_source())
        run(label + '-authored-native-baseline', [sys.executable, helper, consumer])
        blocks = consumer / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py'
        run(label + '-native-selection-validation', [sys.executable, blocks, 'validate-accepted', '--target', consumer])
        plan = run(label + '-native-materialization-plan', [sys.executable, blocks, 'plan', '--target', consumer])
        run(label + '-native-materialization', [sys.executable, blocks, 'apply', '--target', consumer,
                                               '--plan-digest', plan['planDigest']])

    try:
        if mode == 'old':
            # F7's full composite failed its native entry bound. Use the five
            # actual clean-source component archives with native bundle planning;
            # do not import the rejected oversized composite or claim it passed.
            assets = ROOT / 'artifacts/f8-review-20261018/f7-packages'
            version = (ROOT / 'VERSION').read_text().strip()
            result['oldSourceCommit'] = F7
            result['oldCompositeStatus'] = 'failed: 524 entries exceeds 512; not used'
            for kind, name in [('extensions', 'program-kit-governance'), ('extensions', 'program-kit-dotnet'),
                               ('extensions', 'program-kit-building-blocks'), ('presets', 'program-kit-governance-preset'),
                               ('workflows', 'program-kit-bootstrap')]:
                archive = assets / (name + '-' + version + '.zip')
                if not archive.is_file():
                    raise ValueError('Exact retained F7 component archives required: ' + str(archive))
                extract(archive, release / kind / name)
                result.setdefault('archives', {})[archive.name] = sha(archive)
            for relative in ('VERSION', 'bundle.yml', 'scripts/invoke_specify.py', 'scripts/install_local_extension.py',
                             'scripts/native_phase_ownership.py', 'scripts/retired_sync_integration.py'):
                raw = subprocess.check_output(['git', 'show', F7 + ':' + relative], cwd=ROOT)
                path = release / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            install()
            from evaluation_review_fixture import scenario as evaluation
            result['coding'] = evaluation(review / 'coding', installed_consumer=consumer, qualification_only=True)
            assert result['coding']['status'] == 'passed'
            baseline('old')
            scripts = consumer / '.specify/extensions/program-kit-governance/scripts'
            run('old-current-check-after-native-context', [sys.executable, consumer / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py',
                '--repository', consumer, '--scope', 'Focused', '--check', 'snapshot-proof'])
            run('old-current-pattern-binding', [sys.executable, scripts / 'coding_patterns.py', 'bind-evidence', '--repository', consumer,
                '--feature-dir', 'specs/001-learn', '--configuration', 'Release', '--id', 'local-f7'])
            run('old-current-preparation', [sys.executable, scripts / 'phase_obligations.py', 'prepare', '--repository', consumer,
                '--feature-dir', 'specs/001-learn', '--configuration', 'Release', '--operation', 'report', '--format', 'json'])
            # Native SDK-produced lock, consumer-owned note and unrelated private
            # bytes are independently retained in addition to the qualified pattern.
            run('native-lock', ['dotnet', 'restore', consumer / 'tests/Proof/SnapshotProof.csproj', '--use-lock-file', '-m:1'])
            write(consumer / 'docs/private/unrelated.txt', 'FICTIONAL_PRIVATE_F8_CANARY_DO_NOT_PROMOTE\n')
            write(consumer / '.program-kit/evidence/original-f8.json', {'historicalOnly': True, 'source': F7,
                'claim': 'Fictional immutable witness; no approval or public provenance'})
            protected = ['src/Lookup/OwnerReport.cs', 'src/Lookup/SnapshotQuery.cs', 'docs/architecture/coding-patterns.json',
                         'docs/private/unrelated.txt', 'tests/Proof/packages.lock.json',
                         '.program-kit/evidence/original-f8.json', 'eng/building-blocks.lock.json',
                         'docs/architecture/building-block-selection.json', 'docs/architecture/architecture-map.json',
                         '.program-kit/dependency-profile.json', 'docs/architecture/bootstrap-decisions.json',
                         'specs/001-learn/spec.md', 'specs/001-learn/plan.md', 'specs/001-learn/tasks.md']
            protected += [p.relative_to(consumer).as_posix() for p in (consumer / '.program-kit/dependency-profiles').glob('*') if p.is_file()]
            protected += [reference['path'] for reference in json.loads((consumer / 'docs/architecture/coding-patterns.json').read_bytes())['codingUnits'][0]['pattern']['inputs']
                          if reference['root'] == 'repository' and (consumer / reference['path']).is_file()]
            protected += [p.relative_to(consumer).as_posix() for p in (consumer / '.specify/program-kit/render-profiles').glob('*.json')
                          if p.name != 'head.json']
            for family in ('runs', 'toolkit-runs'):
                protected += [p.relative_to(consumer).as_posix() for p in (consumer / 'artifacts/tests' / family).rglob('*') if p.is_file()]
            result['protected'] = {p: sha(consumer / p) for p in protected}
            result['oldReview'] = native_path(review)
            result['status'] = 'passed'
            # Pointer is convenience only: update validates the exact retained
            # source, pattern, archives and protected bytes before any mutation.
            write(ROOT / 'artifacts/f8-review-20261018/qualified-old.json', result)
        elif mode == 'human':
            packages(); install()
            from learning_review_fixture import seed
            seed(consumer, installed=True, features=False)
            app = consumer / 'src/Lookup/OwnerReport.cs'
            write(app, app.read_text().replace('SnapshotQuery', 'SnapshotScan'))
            baseline('human')
            # Native test setup is available but no feature or lesson is adopted.
            write(consumer / 'eng/verification.json', {'schemaVersion': 1, 'testGroups': [], 'toolkitChecks': [{
                'id': 'snapshot-proof', 'script': 'tests/Proof/check.py', 'arguments': [],
                'inputs': ['src/Lookup/**', 'tests/Proof/**', 'global.json', 'runtime.txt', 'NuGet.Config',
                           'Directory.Build.props', 'Directory.Build.targets'], 'timeoutSeconds': 60}]})
            write(consumer / 'eng/Invoke-RepositoryVerification.ps1', f'''param([string]$Scope='Focused',[string]$FeatureDirectory,[string]$ChangedFrom)
& '{sys.executable.replace("'", "''")}' (Join-Path $PSScriptRoot '../.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py') --repository (Split-Path $PSScriptRoot) --scope Focused --check snapshot-proof
exit $LASTEXITCODE
''')
            from specify_cli.presets import PresetResolver
            from validate_governance_state import constitution
            template = PresetResolver(Path(native_path(consumer))).resolve_content('constitution-template', 'template')
            amendment = template[template.index('## Application engineering principles'):]
            governance = consumer / '.specify/extensions/program-kit-governance/scripts'
            run('human-constitution-draft-begin', [sys.executable, governance / 'governance_state.py', 'begin'])
            write(consumer / '.specify/memory/constitution.md', constitution() + '\n' + amendment)
            run('human-constitution-review-only', [sys.executable, governance / 'governance_state.py', 'write-review', '--stage', 'constitution'])
            # Setup labels are not simulated approvals. The human and agent must
            # inspect/ratify this draft and confirm their actual feature intake.
            write(consumer / 'AGENTS.md', f'''# Fictional F8 human-operated Spec Kit review

This disposable consumer is a rehearsal over SDK/BCL source. The real human runs
the ordinary installed Spec Kit skills. No feature is specified, no private
pattern is registered, and no product/constitution decision is preapproved.
Review the constitution draft and its existing review packet with the human;
use its normal ratification command only after the human decides.

Use the installed skills and configured hooks through Specify, Clarify, Plan,
Tasks, Analyze and Implement. Preserve their real output and stopping boundaries.
Do not bypass failed hooks or replace missing evaluation with status-only JSON.
Do not launch outer bootstrap, automated workers, provider/account operations,
device installers or publication. The task uses the installed .NET SDK/BCL only.
The supplied independent oracle is tests/Proof/Program.cs; preserve it and its
expectations. Add meaningful tests under their normal owners if the agreed task
needs them. Keep routing, observed application and human acceptance distinct.

On Windows run every Git command as:
git -c safe.directory={native_path(consumer)} -c core.excludesFile= <command>
Never persist a global safe-directory override. Keep Python UTF-8.
''')
            write(consumer / 'docs/patterns/proposed-query.md', '''# Supplied local lesson for review

Repeated reads of an accepted immutable snapshot can use the supplied
SnapshotQuery implementation. Preserve exact ordinal owner identities, input
order, duplicates, copied input and immutable results. Rebuild for new input.
Review code, source ownership and adverse preparation/storage costs; qualify
through actual scoped checks and ordinary source review before selecting it.
The supplied code/recipe is a proposal, not an adopted private pattern or a
universal performance claim. No live store, database or network is involved.
''')
            git = ['git', '-c', 'safe.directory=' + native_path(consumer), '-c', 'core.excludesFile=']
            run('human-git-init', [*git, 'init', '-q'])
            run('human-git-add-baseline', [*git, 'add', '.'])
            run('human-git-baseline', [*git, '-c', 'user.name=Fictional F8 Fixture', '-c', 'user.email=fixture@example.invalid',
                                     'commit', '-qm', 'Fictional F8 starting source; human feature flow not begun'])
            run('human-intake-context-only', [sys.executable, governance / 'specification_intake.py', '--repository', consumer,
                                             'context', '--entry', 'RM-F8'])
            assert not (consumer / 'specs').exists() or not any((consumer / 'specs').iterdir())
            assert not (consumer / '.program-kit/specification-intake/RM-F8/brief.json').exists()
            assert not (consumer / 'docs/architecture/coding-patterns.json').exists()
            result['humanFlowExecuted'] = False
            result['constitutionRatified'] = False
            initial = {p.relative_to(consumer).as_posix(): sha(p) for p in consumer.rglob('*') if p.is_file()
                       and not {'.git', 'artifacts', 'bin', 'obj', '__pycache__'} & set(p.relative_to(consumer).parts)}
            write(review / 'initial-files.json', initial)
            for name in ('Program.cs', 'check.py'):
                target = review / 'independent-oracle' / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((consumer / 'tests/Proof' / name).read_bytes())
            write(review / 'human-handoff.md', human_guide(consumer))
            result['handoff'] = native_path(review / 'human-handoff.md')
            result['status'] = 'prepared-for-human'
        elif mode == 'adoption':
            packages(); install()
            profile_root = consumer  # Adoption needs the real installed governance owner too.
            result['profileConsumer'] = native_path(profile_root)
            helper = review / 'profile-setup.py'
            write(helper, '''import json,sys
from pathlib import Path
root=Path(sys.argv[1]); installed=Path(sys.argv[2]); tests=Path(sys.argv[3]); version=sys.argv[4]
sys.path[:0]=[str(installed/'program-kit-building-blocks/scripts'),str(tests)]
import building_blocks as blocks
from validate_building_blocks import accepted_fixture
registry=installed/'program-kit-building-blocks/references/dependency-profiles'
index=blocks.load_json(registry/'index.json')
historical='foundation-0.2.2-exporter-0.2.4-forms-0.2.0-localization-0.1.1'
catalog,profile=blocks.qualified_dependency_profile(registry,historical,blocks.load_json(installed/'program-kit-building-blocks/references/orbyss-building-blocks.json'))
old=root/'historical-catalog.json';blocks.atomic_write(old,blocks.pretty_json(catalog))
selection,architecture=accepted_fixture(blocks,root,catalog)
blocks.preserve_dependency_profile(root,blocks.load_json(selection),old)
plan=blocks.resolve(root,selection,old,version)
blocks.apply_materialization(root,root/'eng/building-blocks.lock.json',plan,catalog)
before=(root/'.program-kit/dependency-profile.json').read_bytes()
current=installed/'program-kit-building-blocks/references/orbyss-building-blocks.json'
actual=blocks.resolve(root,selection,current,version)
assert actual['inputs']['catalog']['resolutionSha256']==blocks.catalog_resolution_sha256(catalog)
assert before==(root/'.program-kit/dependency-profile.json').read_bytes()
print(json.dumps({'retained':historical,'availableDefault':index['default'],'retainedResolutionSha256':blocks.catalog_resolution_sha256(catalog),'automaticAdoption':False,'fictionalAcceptedArchitecture':True}))
''')
            installed = consumer / '.specify/extensions'
            run('qualified-profile-retention', [sys.executable, helper, profile_root, installed, ROOT / 'tests',
                                                (ROOT / 'VERSION').read_text().strip()])
            profiles = installed / 'program-kit-building-blocks/scripts/dependency_profiles.py'
            index = json.loads((installed / 'program-kit-building-blocks/references/dependency-profiles/index.json').read_text())
            protected = ['eng/building-blocks.lock.json', '.program-kit/dependency-profile.json',
                         'docs/architecture/building-block-selection.json']
            original = {p: (profile_root / p).read_bytes() for p in protected}
            run('available-qualified-profiles', [sys.executable, profiles, 'list', '--target', profile_root])
            draft = run('explicit-profile-draft', [sys.executable, profiles, 'draft', '--target', profile_root, '--profile', index['default']])
            assert not draft['approvalPerformed']
            assert all((profile_root / p).read_bytes() == raw for p, raw in original.items())
            transition = Path(native_path(Path(draft['draft']))).relative_to(Path(native_path(profile_root))).as_posix()
            acceptance = [sys.executable, profiles, 'accept', '--target', profile_root, '--transition', transition,
                          '--decision-id', 'profile-review', '--rationale', 'Explicit fictional exact-profile review; no runtime migration claim']
            run('profile-accept-without-decision-rejects', acceptance, 2, 'Accepted architecture decision')
            decision = profile_root / 'docs/architecture/decisions/profile-review.md'
            write(decision, '# Fictional exact-profile decision\nStatus: Accepted\nProfile ' + draft['profileSha256'] + '\nReview ' + draft['reviewSha256'] + '\nThis is simulated fixture authoring, no real consumer authority.\n')
            model_path = profile_root / 'docs/architecture/architecture-map.json'
            model = json.loads(model_path.read_text())
            model['decisions'].append({'id': 'profile-review', 'status': 'Accepted',
                'path': decision.relative_to(profile_root).as_posix(), 'sha256': sha(decision)})
            write(model_path, model)
            adopted = run('explicit-profile-acceptance', acceptance)
            assert adopted['materializationPerformed'] is False
            assert (profile_root / 'eng/building-blocks.lock.json').read_bytes() == original['eng/building-blocks.lock.json']
            assert (profile_root / '.program-kit/dependency-profile.json').read_bytes() != original['.program-kit/dependency-profile.json']
            result['profileAdoption'] = {'available': index['default'], 'automaticAdoption': False,
                'explicitFictionalDecision': True, 'nativeMaterializationAndRuntimeStillDue': True}
            # The installed managed transaction owner supplies actual rollback,
            # retry and conflict behavior in a distinct disposable setup scope.
            rollback = Path(filesystem_path(ROOT / 'artifacts/t' / ('m8-' + uuid.uuid4().hex[:8])))
            rollback.mkdir(parents=True)
            sync = [sys.executable, installed / 'program-kit-dotnet/scripts/dotnet_sync.py', '--target', rollback,
                    '--profile-selected', '--foundation-host-accepted', '--building-block-sources-approved']
            run('managed-before', [*sync, '--web-profile', 'bff-cookie'])
            from validate_mechanical_fixtures import snapshot
            previous = snapshot(rollback)
            environment['PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION'] = '2'
            try:
                run('managed-interruption-rolls-back', [*sync, '--web-profile', 'spa-pkce'], 2, 'rolled back')
            finally:
                environment.pop('PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION', None)
            assert snapshot(rollback) == previous
            run('managed-retry', [*sync, '--web-profile', 'spa-pkce'])
            custom = rollback / 'eng/spa-pkce.json'; custom.write_bytes(custom.read_bytes() + b'\nFictional authored customization\n')
            previous = snapshot(rollback)
            run('managed-conflict-preserves-all', [*sync, '--web-profile', 'bff-cookie'], 2)
            assert snapshot(rollback) == previous
            result['managedRecoveryConsumer'] = native_path(rollback)
            result['status'] = 'passed'
        elif mode in ('fresh', 'scaffold'):
            packages(); install()
            if mode == 'fresh':
                from evaluation_review_fixture import scenario as evaluation
                result['coding'] = evaluation(review / 'coding', installed_consumer=consumer)
            else:
                from scaffold_review_fixture import scenario as scaffold
                result['coding'] = scaffold(review / 'coding', installed_consumer=consumer)
            assert result['coding']['status'] == 'passed'
            result['status'] = 'passed'
        elif mode == 'update':
            old = json.loads((ROOT / 'artifacts/f8-review-20261018/qualified-old.json').read_text())
            assert old['status'] == 'passed' and old['oldSourceCommit'] == F7
            consumer = Path(filesystem_path(old['consumer']))
            result['consumer'] = native_path(consumer)
            result['originalOldReview'] = old['oldReview']
            assert all(sha(consumer / p) == expected for p, expected in old['protected'].items())
            result['beforeUpdate'] = old['protected']
            packages()
            import specify_cli
            site = Path(specify_cli.__file__).parent.parent
            environment.update(SPECIFY_INIT_DIR=native_path(consumer), PROGRAM_KIT_SPECIFY_SITE_PACKAGES=str(site))
            bridge = [sys.executable, release / 'scripts/invoke_specify.py', '--site-packages', site, '--']
            updater = [sys.executable, release / 'scripts/upgrade_program_kit.py', '--release-root', release,
                       '--target', consumer, '--integration', 'codex', '--offline',
                       '--specify-command-json', json.dumps([native_path(p) if isinstance(p, Path) else p for p in bridge])]
            run('update-preview', [*updater, '--plan'])
            # Actual native copied-output customization must refuse replacement.
            skill = consumer / '.agents/skills/speckit-program-kit-governance-sync/SKILL.md'
            original = skill.read_bytes(); edited = original + b'\nFictional consumer customization.\n'; skill.write_bytes(edited)
            run('managed-customization-refuses', updater, 2, 'consumer customization')
            assert skill.read_bytes() == edited
            skill.write_bytes(original)
            run('actual-packaged-update', updater)
            assert all(sha(consumer / p) == expected for p, expected in old['protected'].items())
            result['afterUpdate'] = {p: sha(consumer / p) for p in old['protected']}
            scripts = consumer / '.specify/extensions/program-kit-governance/scripts'
            run('retained-tooling-source', [sys.executable, scripts / 'tooling_witness.py', 'verify',
                                           '--receipt', '.program-kit/installation/migration.json'])
            phase = [sys.executable, scripts / 'phase_obligations.py']
            feature = ['--repository', consumer, '--feature-dir', 'specs/001-learn', '--configuration', 'Release']
            old_registry = (consumer / 'docs/architecture/coding-patterns.json').read_bytes()
            run('updated-adapter-stales-old-proof', [*phase, 'prepare', *feature, '--operation', 'report', '--format', 'json'], 2, 'PKP005')
            run('current-independent-check', [sys.executable, consumer / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py',
                                              '--repository', consumer, '--scope', 'Focused', '--check', 'snapshot-proof'])
            run('current-pattern-binding', [sys.executable, scripts / 'coding_patterns.py', 'bind-evidence', *feature, '--id', 'local-f7'])
            current = run('updated-qualified-prepare', [*phase, 'prepare', *feature, '--operation', 'report', '--format', 'json'])
            assert current['coding']['patterns'][0]['qualification']['status'] == 'qualified'
            query = consumer / 'src/Lookup/SnapshotQuery.cs'; original_query = query.read_bytes()
            query.write_bytes(original_query + b'\n// Fictional post-upgrade changed input.\n')
            run('changed-source-is-stale', [*phase, 'prepare', *feature, '--operation', 'report', '--format', 'json'], 2, 'PKP005')
            query.write_bytes(original_query)
            registry = consumer / 'docs/architecture/coding-patterns.json'
            registry_bytes = registry.read_bytes()
            unsupported = json.loads(registry_bytes)
            unsupported['codingUnits'][0]['when']['all'].append('unsupported-f8-runtime')
            write(registry, unsupported)
            run('unsupported-pattern-has-owner-repair', [*phase, 'prepare', *feature, '--operation', 'report', '--format', 'json'], 2, 'PKC003')
            registry.write_bytes(registry_bytes)
            legacy = consumer / 'specs/099-legacy'
            for name in ('spec.md', 'plan.md'):
                write(legacy / name, (consumer / 'specs/001-learn' / name).read_text())
            write(legacy / 'tasks.md', '- [ ] T901 Review src/Lookup/OwnerReport.cs using src/Lookup/Lookup.csproj.\n')
            run('legacy-missing-baseline-preserves-source', [*phase, 'reconcile', '--repository', consumer,
                '--feature-dir', 'specs/099-legacy', '--configuration', 'Release', '--format', 'json'], 2, 'PKC006')
            assert query.read_bytes() == original_query and registry.read_bytes() == registry_bytes
            task = consumer / 'specs/001-learn/tasks.md'; original_tasks = task.read_bytes()
            task.write_bytes(original_tasks.replace(b'- [ ]', b'- [X]'))
            checked = task.read_bytes()
            run('old-state-cannot-omit-evaluation', [*phase, 'finish', *feature], 2, 'PKC020')
            assert task.read_bytes() == checked
            task.write_bytes(original_tasks)
            renewed = json.loads(registry.read_bytes())
            original_evidence = json.loads(old_registry)['codingUnits'][0]['pattern']['evidence']
            assert renewed['codingUnits'][0]['pattern']['evidence'][:len(original_evidence)] == original_evidence
            run('current-ready-after-update', [*phase, 'prepare', *feature, '--operation', 'report', '--format', 'json'])
            result['status'] = 'passed'
        else:
            raise ValueError('Unsupported installed journey')
        write(review / 'index.md', '# F8 ' + mode + ' actual installed proof\n\n'
              'Start with [exact results](results.json), output/ and the retained consumer: ' + native_path(consumer) + '.\n\n'
              'Nested coding/index.md explains the maintained journey, independent controls and source diffs where applicable. '
              'Actual installed commands use native ownership/hooks. Fictional source/review/decisions grant no real acceptance. '
              'Routing remains separate from application execution. Human-operated Spec Kit review is a separate untouched consumer.\n')
        return result
    except BaseException as error:
        result.update(status='failed', failureKind=type(error).__name__, diagnostic=str(error))
        raise
    finally:
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        result['workingInputsUnchanged'] = input_snapshot() == before
        write(review / 'results.json', result)
        print('Retained F8 ' + mode + ': ' + native_path(review / 'index.md'), flush=True)


def human_guide(consumer):
    return f'''# Human-operated Spec Kit journey — ready to begin

Open **{native_path(consumer)}** in a new task yourself. This is a new fictional
SDK/BCL consumer installed from the actual candidate archives. The agent session
has not started. No feature intake, spec, plan, tasks, pattern binding or product
decision exists. The constitution is a reviewed **draft**, awaiting your decision.
No bootstrap workflow or worker is required for ordinary feature work.

## Starting request to paste

```text
Use the installed Program Kit / Spec Kit flow with me for this fictional owner-report task.
First show me the supplied constitution draft and its review packet. Ask for my
decision and use normal ratification only if I approve; do not fabricate approval.

Then perform Specify, Clarify, Plan, Tasks, Analyze and Implement through their
installed skills and configured hooks, with the real human checkpoints intact.
Use specification-intake for RM-F8 before writing the specification. I want to
inspect actual phase output, selected coding context/units, source diffs, executed
checks, evaluation duties and the final human handoff as we go.

The existing OwnerReport scans an accepted immutable snapshot for every request.
Teach and qualify the supplied local snapshot-query lesson, then apply it to the
report through ordinary consumer-owned editing. Preserve exact ordinal owner
identities, input order, duplicate rows, copied input and immutable results.
An old snapshot stays unchanged; new input requires rebuilding. The supplied
SnapshotQuery source is a proposal to inspect, not adopted or qualified evidence.
Compare repeated reads and preparation cost if making a performance claim; keep
raw scoped results and adverse tradeoffs. There is no live store or provider.

Keep tests/Proof/Program.cs as the fixed independent oracle. Add other meaningful
tests if needed. Use actual current checks and normal authored review to qualify
the private pattern and satisfy every applicable completion duty. Do not use a
simulated human decision, status-only JSON or a fake native result at handoff.
Stop for my real review of the useful outcome. Preserve failures and session output.
```

## What to look inside

1. Constitution: review the actual draft and installed engineering amendment;
   no approval was supplied during preparation.
2. Specify/Clarify: inspect intake questions, exact confirmed brief and resulting
   specification. Your answers and confirmation must be real session evidence.
3. Plan/Tasks/Analyze: inspect model/source ownership, selected private lesson,
   operation dependencies, verification duties and actual hook commands. Analyze
   remains read-only. Missing support or failed hooks stay visible.
4. Implement: compare `src/Lookup/OwnerReport.cs` before/after; inspect the
   canonical preparation, teaching/binding/choice and reconciliation output.
   Actual compiled checks must exercise the fixed oracle. Source review still
   owns semantics, invocation layout, documentation and matching type/file names.
5. Handoff: inspect current evaluation coverage and the actual runnable check.
   Decide on the presented outcome yourself; the agent must preserve waiting
   state and must not accept on your behalf.

The installed Codex skill names include `$speckit-specify`, `$speckit-clarify`,
`$speckit-plan`, `$speckit-tasks`, `$speckit-analyze`, `$speckit-implement` and
`$speckit-program-kit-governance-specification-intake`. Natural language may
select them; verify that the session actually uses the installed flow.

## Bring the session back for analysis

Return here with the exact task title/link or an explicitly selected exported
transcript. That authorizes read-only analysis of that session and this consumer;
no automatic polling or messages are scheduled. Keep the consumer and its Git
history, native check reports and both streams. Report any truncation or missing
tool output as unknown. Do not paste credentials or unrelated private sessions.

The initial authored/installed file identities are in [initial-files.json](initial-files.json);
the original fixed oracle is retained outside the consumer in `independent-oracle/`.
Candidate archive identities, preparation commands and streams are in [results.json](results.json).
Analysis will compare the actual request/answers, invoked phases/hooks, selected
guidance, edits, independent execution, failed/recovered checks, completion and
human decisions. It will distinguish routing from observed agent application and
actual behavior from authored claims. Any additional adversarial execution uses
a new disposable copy; this session's source/evidence stays retained.

This journey covers the finite .NET SDK/BCL report. Existing F5 provider/browser
proof keeps its original scope. No real provider, Foundation/runtime qualification,
universal agent obedience or complete F1–F8 acceptance follows from preparation.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('fresh', 'old', 'update', 'scaffold', 'adoption', 'human'))
    args = parser.parse_args()
    value = scenario(args.mode)
    print(json.dumps({'status': value['status'], 'elapsedSeconds': value['elapsedSeconds'], 'consumer': value['consumer']}))


if __name__ == '__main__':
    main()

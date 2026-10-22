"""F6 installed learning round. Fictional authoring, real compiled application/oracles.

No agents, providers, browsers or existing consumer are started. Review runs retain
their own new consumer, every failed command and source snapshot.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from coding_review_fixture import write, fictional_operation_maps
from owned_fixture import FixtureDirectory, filesystem_path, native_path

EXAMPLE = ROOT / 'extensions/program-kit-dotnet/references/examples/snapshot-query'


def ref(path, root='repository'):
    return {'root': root, 'path': path}


def seed(root, *, installed=False, features=True):
    if not installed:
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(filesystem_path(ROOT / 'extensions' / name), root / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('__pycache__', 'bin', 'obj'))
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
    from asset_sources import read as source_bytes
    example = root / '.specify/extensions/program-kit-dotnet/references/examples/snapshot-query'
    write(root / '.gitignore', '.specify/\nartifacts/\n**/bin/\n**/obj/\n')
    for name in ('Directory.Build.props', 'Directory.Build.targets'):
        write(root / name, '<Project/>\n')
    write(root / 'NuGet.Config', '<configuration><packageSources><clear/></packageSources></configuration>\n')
    sdk = subprocess.check_output(['dotnet', '--version'], text=True).strip()
    write(root / 'global.json', {'sdk': {'version': sdk, 'rollForward': 'disable'}})
    write(root / 'runtime.txt', subprocess.check_output(['dotnet', '--list-runtimes'], text=True))
    write(root / 'src/Lookup/Lookup.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup></Project>\n')
    for name in ('Note.cs', 'SnapshotQuery.cs', 'SnapshotScan.cs', 'OwnerReport.cs'):
        destination = root / 'src/Lookup' / name
        destination.write_bytes(source_bytes(example / name))
    for name in ('Program.cs', 'check.py'):
        write(root / 'tests/Proof' / name, source_bytes(example / name).decode('utf-8'))
    project = source_bytes(example / 'SnapshotProof.csproj').decode('utf-8').replace('</Project>', '<ItemGroup><ProjectReference Include="../../src/Lookup/Lookup.csproj" /></ItemGroup></Project>')
    write(root / 'tests/Proof/SnapshotProof.csproj', project)
    write(root / 'docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet']})
    write(root / 'docs/architecture/architecture-map.json', {
        'elements': [{'id': 'lookup', 'type': 'bounded-context', 'decision_refs': ['snapshot-owner']}],
        'decisions': [{'id': 'snapshot-owner', 'status': 'Accepted'}],
        'sources': [], 'strategic_model': {'bounded_contexts': [{'element': 'lookup', 'status': 'accepted'}], 'contracts': []}})
    write(root / 'eng/architecture.json', {'runtimeComposition': {'projects': [{
        'path': 'src/Lookup/Lookup.csproj', 'role': 'helper', 'projectReferences': [],
        'responsibilities': [{'name': 'SnapshotLookup', 'kind': 'pure-helper', 'effects': []}]}, {
        'path': 'tests/Proof/SnapshotProof.csproj', 'role': 'test', 'projectReferences': ['src/Lookup/Lookup.csproj'],
        'responsibilities': [{'name': 'SnapshotProof', 'kind': 'test', 'effects': [], 'testSeams': ['pure-core']}]}], 'bindings': []}})
    write(root / 'docs/architecture/building-block-selection.json', {'status': 'Accepted', 'targets': [{
        'id': 'lookup', 'kind': 'dotnet-project', 'path': 'src/Lookup/Lookup.csproj',
        'placement': {'owner': 'lookup', 'decisionIds': ['snapshot-owner']}}], 'instances': []})
    write(root / 'eng/Invoke-RepositoryVerification.ps1', '# Named checks use the native verification owner.\n')
    if not features:
        return sdk  # Human-operated flow must author its own feature/intake/state.
    for number, description in [('001-learn', 'immutable snapshot query'), ('002-apply', 'immutable snapshot query'), ('003-live', 'live mutable query')]:
        feature = root / 'specs' / number
        entry = 'RM-' + number[:3]
        write(root / '.program-kit/specification-intake' / entry / 'brief.json', {'architectureScope': ['lookup'], 'decisions': []})
        write(feature / 'spec.md', f'# Fictional owner report\n- **Specification roadmap entry**: {entry}\nOwner isolation, ordinal identities, order and duplicates are accepted. Input is an {description}.\n')
        write(feature / 'plan.md', '# Accepted fictional plan\nA pure .NET owner report over an ' + description + '. Own src/Lookup/Lookup.csproj. Snapshot changes require a new instance.\n')
        write(feature / 'tasks.md', f'''# Fictional task plan
- [ ] T001 [US1] Apply {description} in src/Lookup/OwnerReport.cs using src/Lookup/Lookup.csproj.
- [ ] T002 [US1] Verify actual results in tests/Proof/SnapshotProof.csproj.

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | report | none | none | none |
| T002 | report | T001 | none | none |
''')
        fictional_operation_maps(feature, 'report')
    git = ['git', '-c', 'safe.directory=' + native_path(root), '-c', 'core.excludesFile=']
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Fictional F6 Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fictional F6 accepted inputs']):
        subprocess.run([*git, *args], cwd=native_path(root), check=True, capture_output=True, timeout=30)
    baseline = subprocess.check_output([*git, 'rev-parse', 'HEAD'], cwd=native_path(root), text=True).strip()
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
    import task_draft
    for number in ('001-learn', '002-apply', '003-live'):
        task_draft.checkpoint(root / 'specs' / number, {'baseline': baseline, 'outcome': 'Fictional accepted F6 inputs', 'next': 'Apply lesson'})
    return sdk


def declaration(identity, version='1.0.0'):
    return {'id': identity, 'ruleIds': ['local.snapshot-query'], 'when': {'all': ['dotnet', 'snapshot-query'], 'not': ['web']},
            'requiredContext': ['request', 'model-owner', 'effective-projects', 'verification-owner'], 'route': 'manual-edit',
            'pattern': {'schemaVersion': 1, 'semanticId': 'snapshot-owner-query', 'version': version,
                'owner': 'fictional snapshot query maintainer', 'status': 'active',
                'invariantRuleIds': ['principle.compilation-boundaries'], 'compatibility': {'profiles': ['dotnet'], 'frameworks': ['net10.0']},
                'alternatives': [], 'replaces': [],
                'inputs': [ref(p) for p in ('src/Lookup/SnapshotQuery.cs', 'src/Lookup/Note.cs', 'src/Lookup/SnapshotScan.cs', 'global.json', 'runtime.txt', 'tests/Proof/Program.cs', 'tests/Proof/check.py', 'tests/Proof/SnapshotProof.csproj', 'src/Lookup/Lookup.csproj', 'NuGet.Config', 'Directory.Build.props', 'Directory.Build.targets')],
                'examples': {'positive': [ref('src/Lookup/SnapshotQuery.cs')], 'negative': [ref('docs/patterns/invalid-query.cs.txt')]},
                'checks': [{'kind': 'toolkit', 'id': 'snapshot-proof'}], 'review': ref('docs/patterns/review.md'), 'evidence': [],
                'limits': 'Finite .NET 10 immutable snapshot/owner report; measured local workload only. No database, live store, agent obedience or human acceptance.',
                'provenance': 'Fictional ordinary source review; source attribution does not authenticate authorship.'}}


def scenario(directory):
    review = Path(filesystem_path(Path(directory).resolve()))
    review.mkdir(parents=True, exist_ok=True)
    consumer = Path(filesystem_path(ROOT / 'artifacts/t' / ('f6-' + uuid.uuid4().hex[:8])))
    consumer.mkdir(parents=True)
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    started = time.perf_counter()
    result = {'status': 'running', 'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'workingInputsDigest': input_snapshot()['digest'], 'consumer': str(consumer), 'commands': [],
              'fixtureSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write(review / 'index.md', '# Incomplete F6 run\n\nInspect results.json and output/. No success inferred; preserve this run and its consumer.\n')

    def run(name, args, expected=0, marker=None, cwd=None):
        before = time.perf_counter()
        arguments = [native_path(a) if isinstance(a, Path) else str(a) for a in args]
        child = subprocess.run(arguments, cwd=native_path(cwd or consumer), capture_output=True,
                               text=True, encoding='utf-8', timeout=90)
        write(review / 'output' / (name + '.stdout.txt'), child.stdout)
        write(review / 'output' / (name + '.stderr.txt'), child.stderr)
        result['commands'].append({'name': name, 'arguments': list(map(str, args)), 'expectedExit': expected,
            'actualExit': child.returncode, 'elapsedSeconds': round(time.perf_counter() - before, 3),
            'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(), 'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        accepted = child.returncode in expected if isinstance(expected, tuple) else child.returncode == expected if expected is not None else child.returncode != 0
        assert accepted, name + ': inspect retained streams'
        if marker:
            assert marker in child.stdout + child.stderr, name + ': missing intended independent failure marker'
        try:
            return json.loads(child.stdout)
        except ValueError:
            return child.stdout

    try:
        result['sdk'] = seed(consumer)
        scripts = consumer / '.specify/extensions/program-kit-governance/scripts'
        pattern = scripts / 'coding_patterns.py'
        native = consumer / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py'
        phase = scripts / 'phase_obligations.py'
        local_path = consumer / 'docs/architecture/coding-patterns.json'
        def prepare(name, feature='001-learn', expected=0, code=None, source=False):
            value = run(name, [sys.executable, phase, 'prepare', '--repository', consumer, '--feature-dir', 'specs/' + feature,
                              '--operation', 'report', '--format', 'json', *([] if source else ['--stage', 'setup'])], expected)
            if code:
                streams = ''.join((review / 'output' / (name + '.' + stream + '.txt')).read_text(encoding='utf-8') for stream in ('stdout', 'stderr'))
                assert code in streams, name + ': missing intended context diagnostic'
            return value
        def bind(name, identity='local-snapshot-v1'):
            return run(name, [sys.executable, pattern, 'bind-evidence', '--repository', consumer, '--feature-dir', 'specs/001-learn', '--operation', 'report', '--id', identity])
        def choice(feature, identity, version):
            path = consumer / 'specs' / feature / 'plan.md'
            base = path.read_text(encoding='utf-8').split('<!-- program-kit:pattern-choices -->')[0]
            block = {'snapshot-owner-query': {'id': identity, 'version': version, 'reason': 'Explicit finite immutable read-many workload; reviewed correctness and measured preparation tradeoff.'}}
            write(path, base + '<!-- program-kit:pattern-choices -->\n' + json.dumps(block) + '\n<!-- /program-kit:pattern-choices -->\n')
        def check(name, identity='snapshot-proof', expected=0, marker=None):
            return run(name, [sys.executable, native, '--repository', consumer, '--scope', 'Focused', '--check', identity], expected, marker)

        app = consumer / 'src/Lookup/OwnerReport.cs'
        applied_source = app.read_text(encoding='utf-8')
        before_source = applied_source.replace('SnapshotQuery', 'SnapshotScan')
        write(app, before_source)
        write(review / 'snapshots/application-before.cs', before_source)
        code = consumer / 'src/Lookup/SnapshotQuery.cs'
        valid_code = code.read_text(encoding='utf-8')
        write(consumer / 'docs/patterns/lesson.md', (EXAMPLE / 'README.md').read_text(encoding='utf-8'))
        write(consumer / 'docs/patterns/invalid-query.cs.txt', valid_code.replace('StringComparer.Ordinal)', 'StringComparer.OrdinalIgnoreCase)'))
        write(consumer / 'docs/patterns/review.md', '# Fictional ordinary source review\nAccept exact ordinal ownership/order/duplicates, copied immutable input/results and rebuild boundaries. Inspect actual independent oracle and benchmark output. Index costs preparation/storage; keep scan for one-shot work. No real human acceptance or universal performance claim.\n')
        write(consumer / 'docs/private-unrelated.md', 'PRIVATE_F6_UNRELATED_CANARY\n')
        write(consumer / 'docs/patterns/private-review.md', 'PRIVATE_F6_REVIEW_CANARY\n')
        inputs = ['src/Lookup/Note.cs', 'src/Lookup/SnapshotScan.cs', 'src/Lookup/SnapshotQuery.cs', 'src/Lookup/OwnerReport.cs', 'tests/Proof/Program.cs', 'tests/Proof/SnapshotProof.csproj', 'src/Lookup/Lookup.csproj', 'global.json', 'runtime.txt', 'NuGet.Config', 'Directory.Build.props', 'Directory.Build.targets']
        config = {'schemaVersion': 1, 'testGroups': [], 'toolkitChecks': [
            {'id': 'snapshot-proof', 'script': 'tests/Proof/check.py', 'arguments': ['--benchmark'], 'inputs': inputs, 'timeoutSeconds': 65}]}
        write(consumer / 'eng/verification.json', config)
        gap = prepare('01-supported-task-gap')
        assert gap['coding']['canProceed'] and not gap['coding']['patterns']
        check('02-baseline-correctness-and-performance')
        request = {'schemaVersion': 1, 'id': 'local-snapshot-v1', 'intent': 'new',
                   'problem': 'Repeated scans of the accepted immutable owner snapshot lack a qualified local specialization. Compare an index without weakening identity/order/duplicates or claiming live data.',
                   'submission': 'docs/patterns/lesson.md', 'invariants': ['principle.compilation-boundaries'],
                   'changes': {'guidance': [ref('docs/patterns/lesson.md')], 'scaffolds': [], 'checks': [ref('tests/Proof/check.py'), ref('tests/Proof/Program.cs')],
                               'examples': [ref('src/Lookup/SnapshotQuery.cs'), ref('docs/patterns/invalid-query.cs.txt')], 'acceptedArtifacts': [ref('specs/001-learn/plan.md')]}}
        write(consumer / 'docs/patterns/teach.json', request)
        run('03-teach-reviewable-contribution', [sys.executable, pattern, 'teach', '--repository', consumer, '--request', 'docs/patterns/teach.json', '--output', 'artifacts/teaching.json'])
        local = {'schemaVersion': 1, 'sources': [{'id': 'local.snapshot-source', 'locator': {'kind': 'repository', 'path': 'docs/patterns/lesson.md'}}],
                 'rules': {'local.snapshot-query': {'source': 'local.snapshot-source', 'selector': {'kind': 'document'}, 'owner': 'fictional snapshot owner', 'level': 'recommended',
                           'limits': 'Finite snapshot query only; canonical .NET duties remain.'}}, 'codingUnits': [declaration('local-snapshot-v1')]}
        write(local_path, local)
        choice('001-learn', 'local-snapshot-v1', '1.0.0')
        prepare('04-selected-missing-proof', expected=2, code='PKP005')
        source_entry = prepare('04b-actual-source-profile-gate', expected=(0, 2), source=True)
        missing_capability = [b for b in source_entry['coding']['blockers'] if b['code'] == 'PKC024']
        if missing_capability:
            assert all(b['code'] in {'PKC024', 'PKC025', 'PKP005'} for b in source_entry['coding']['blockers']), source_entry['coding']['blockers']
            # Keep real compiled adverse behavior separate from the unsupported
            # profile. Compiler/setup failure cannot satisfy this negative.
            for name, invalid, marker in [
                ('owner-leak', valid_code.replace('byOwner.TryGetValue(owner, out var notes)', 'byOwner.TryGetValue("alice", out var notes)'), 'owner-isolation-and-duplicate-count'),
                ('reversed-order', valid_code.replace('var rows = group.ToArray();', 'group.Reverse();\n            var rows = group.ToArray();'), 'stable-owner-order')]:
                assert invalid != valid_code
                write(code, invalid)
                check('04c-compiled-invalid-' + name, expected=2)
                nested = sorted((consumer / 'artifacts/tests/toolkit-runs').glob('*/result.json'), key=lambda p: p.stat().st_mtime_ns)[-1]
                streams = ''.join(p.read_text(encoding='utf-8') for p in nested.parent.glob('*.log'))
                assert 'BUILD_SUCCEEDED_BEFORE_BEHAVIOR' in streams and marker in streams
                write(code, valid_code)
            check('04d-restored-current-proof')
            run('04e-native-scope-binding-remains-blocked', [sys.executable, pattern, 'bind-evidence', '--repository', consumer,
                '--feature-dir', 'specs/001-learn', '--operation', 'report', '--id', 'local-snapshot-v1'], 2)
            result.update(status='passed', sourceCompletion='blocked-publication-dependency', sourceBlockers=missing_capability,
                          workingInputsUnchanged=input_snapshot()['digest'] == result['workingInputsDigest'],
                          scope='Setup-only .NET owner context, data-only teaching draft, real finite compiled/benchmark positive, independent compiled owner/order negatives and restored proof. Native-scope qualification/application remains blocked by actual missing public analyzer capability.')
            write(review / 'index.md', '# F6 staged source-profile dependency\n\n'
                  'Inspect output/01–04 for setup context, actual baseline correctness/finite benchmark, data-only teaching and missing pattern proof. '
                  'Output/04b retains PKC024. Both output/04c negative controls require successful compilation before their exact owner/order failure marker; '
                  '04d restores actual proof and 04e rejects unsupported native-scope binding. '
                  'Full qualification, later source application, refinement/shared promotion and C# completion remain blocked until actual qualified analyzer/profile adoption. '
                  'No public native capability, provider behavior, agent obedience or real human product acceptance is inferred.\n')
            return result
        bind('05-bind-actual-check-and-review')
        local = json.loads(local_path.read_text())
        selected = prepare('06-qualified-local-selection')
        assert any(p['selected'] for p in selected['coding']['patterns'])

        # Later task source application is real authoring, not inferred agent obedience.
        choice('002-apply', 'local-snapshot-v1', '1.0.0')
        prepare('07-fresh-task-selects-lesson', '002-apply')
        write(app, applied_source)
        write(review / 'snapshots/application-after.cs', applied_source)
        write(review / 'snapshots/application.diff', ''.join(difflib.unified_diff(before_source.splitlines(True), applied_source.splitlines(True), fromfile='before/OwnerReport.cs', tofile='after/OwnerReport.cs')))
        prepare('08-application-change-stales-check', '002-apply', 2, 'PKP005')
        check('09-actually-applied-application-and-performance')
        bind('10-rebind-after-application')
        final = prepare('11-later-applied-task', '002-apply')
        assert any(u['id'] == 'local-snapshot-v1' and not u['applicationObserved'] for u in final['coding']['skills'])
        excluded = prepare('12-live-task-excludes-index', '003-live')
        assert not any(p['selected'] for p in excluded['coding']['patterns'])

        # Every invalid source must compile first and then fail its fixed behavior oracle.
        for name, invalid, marker in [
            ('owner-leak', valid_code.replace('byOwner.TryGetValue(owner, out var notes)', 'byOwner.TryGetValue("alice", out var notes)'), 'owner-isolation-and-duplicate-count'),
            ('reversed-order', valid_code.replace('var rows = group.ToArray();', 'group.Reverse();\n            var rows = group.ToArray();'), 'stable-owner-order')]:
            write(code, invalid)
            write(review / 'snapshots' / (name + '.cs'), invalid)
            check('13-invalid-' + name, expected=2)
            text = (review / 'output' / ('13-invalid-' + name + '.stdout.txt')).read_text()
            # Runner points at retained native logs: inspect the actual nested check streams.
            nested = sorted((consumer / 'artifacts/tests/toolkit-runs').glob('*/result.json'), key=lambda p: p.stat().st_mtime_ns)[-1]
            streams = ''.join(p.read_text(encoding='utf-8') for p in nested.parent.glob('*.log'))
            assert 'BUILD_SUCCEEDED_BEFORE_BEHAVIOR' in streams and marker in streams
            write(code, valid_code)
        check('14-restored-current-proof')
        bind('15-restored-pattern-binding')
        write(code, valid_code + '\n// Changed reviewed source invalidates content-bound proof.\n')
        prepare('16-changed-input-stales-qualification', expected=2, code='PKP005')
        write(code, valid_code)
        prepare('17-restored-source-is-current')

        # Focused adapter diagnostics through installed commands.
        local = json.loads(local_path.read_text())
        changed = copy.deepcopy(local)
        changed['codingUnits'][0]['when']['all'].append('unregistered-technology')
        write(local_path, changed)
        prepare('18-unknown-context-adapter', expected=2, code='PKC003')
        changed = copy.deepcopy(local)
        changed['codingUnits'][0]['pattern']['compatibility']['frameworks'] = ['net9.0']
        write(local_path, changed)
        prepare('19-incompatible-pattern', expected=2, code='PKP002')
        changed = copy.deepcopy(local)
        extra = copy.deepcopy(changed['codingUnits'][0]); extra['id'] = 'overlap'
        changed['codingUnits'].append(extra)
        write(local_path, changed)
        prepare('20-undeclared-overlap', expected=2, code='PKP004')
        changed = copy.deepcopy(local)
        changed['codingUnits'][0]['route'] = 'execute-submission'
        write(local_path, changed)
        prepare('21-unsupported-executable-adapter', expected=2, code='PKC003')
        changed = copy.deepcopy(local)
        changed['sources'][0]['locator']['path'] = 'docs/patterns/absent-canonical-source.md'
        write(local_path, changed)
        prepare('21b-missing-canonical-support', expected=2, code='PKC019')
        write(local_path, local)

        # Refinement is a new declaration/version; old choice never silently advances.
        request.update(intent='refine', id='local-snapshot-v11', basedOn={'id': 'local-snapshot-v1', 'version': '1.0.0'})
        write(consumer / 'docs/patterns/refine.json', request)
        run('22-prepare-refinement', [sys.executable, pattern, 'teach', '--repository', consumer, '--request', 'docs/patterns/refine.json', '--output', 'artifacts/refinement.json'])
        refined = copy.deepcopy(local['codingUnits'][0]); refined['id'] = 'local-snapshot-v11'
        refined['pattern'].update(version='1.1.0', alternatives=['local-snapshot-v1'], evidence=[])
        local['codingUnits'].append(refined)
        write(local_path, local)
        choice('001-learn', 'local-snapshot-v11', '1.0.0')
        prepare('23-unadopted-version-rejected', expected=2, code='PKP002')
        choice('001-learn', 'local-snapshot-v11', '1.1.0')
        bind('24-qualify-refined-version', 'local-snapshot-v11')
        prepare('25-explicit-version-adoption')
        local = json.loads(local_path.read_text())
        write(review / 'snapshots/versions-before-retirement.json', local)
        request.update(intent='replace', id='replacement-proposal')
        write(consumer / 'docs/patterns/replace.json', request)
        run('26-prepare-replacement', [sys.executable, pattern, 'teach', '--repository', consumer, '--request', 'docs/patterns/replace.json', '--output', 'artifacts/replacement.json'])
        local['codingUnits'][1]['pattern'].update(alternatives=[], replaces=['local-snapshot-v1'])
        write(local_path, local)
        bind('26b-qualify-explicit-replacement', 'local-snapshot-v11')
        replacement = prepare('26c-select-explicit-replacement')
        assert any(p['selected'] and p['precedence']['replaces'] == ['local-snapshot-v1'] for p in replacement['coding']['patterns'])
        local = json.loads(local_path.read_text())
        request.update(intent='retire', id='local-snapshot-v1')
        write(consumer / 'docs/patterns/retire.json', request)
        run('27-prepare-retirement', [sys.executable, pattern, 'teach', '--repository', consumer, '--request', 'docs/patterns/retire.json', '--output', 'artifacts/retirement.json'])
        local['codingUnits'][0]['pattern']['status'] = 'retired'
        write(local_path, local)
        prepare('28-retired-version-blocks-old-task', '002-apply', 2, 'PKP002')
        prepare('29-refined-alternative-still-usable')
        write(review / 'snapshots/versions-after-retirement.json', local)

        shared_preparation(review, consumer, run, pattern, prepare)
        result.update(status='passed', workingInputsUnchanged=input_snapshot()['digest'] == result['workingInputsDigest'])
        assert result['workingInputsUnchanged']
        write(review / 'index.md', guide(consumer, result))
        return result
    except BaseException as error:
        result.update(status='failed', error=str(error))
        raise
    finally:
        result['elapsedSeconds'] = round(time.perf_counter() - started, 3)
        write(review / 'results.json', result)


def shared_preparation(review, consumer, run, pattern, prepare):
    """Ordinary upstream source change preparation, then isolated installed proof."""
    public = consumer / 'publishable'
    base = 'program-kit-dotnet/references/examples/shared-snapshot-query'
    files = []
    for name in ('README.md', 'Note.cs', 'SnapshotScan.cs', 'SnapshotQuery.cs', 'OwnerReport.cs', 'Program.cs', 'SnapshotProof.csproj', 'check.py'):
        write(public / name, (EXAMPLE / name).read_text(encoding='utf-8'))
        files.append({'source': 'publishable/' + name, 'target': 'extensions/' + base + '/' + name})
    write(public / 'review.md', '# Fictional publishable source review\nFinite example only. Requalify exact shared paths/runtime/checks before use. Source attribution is not authenticated authorship.\n')
    write(public / 'invalid.cs.txt', (EXAMPLE / 'SnapshotQuery.cs').read_text().replace('StringComparer.Ordinal)', 'StringComparer.OrdinalIgnoreCase)'))
    for name in ('review.md', 'invalid.cs.txt'):
        files.append({'source': 'publishable/' + name, 'target': 'extensions/' + base + '/' + name})
    unit = declaration('shared-snapshot-query')
    unit['ruleIds'] = ['example.shared-snapshot-query']
    p = unit['pattern']
    p.update(status='draft', inputs=[ref(base + '/' + n, 'extensions') for n in ('Note.cs', 'SnapshotScan.cs', 'SnapshotQuery.cs', 'OwnerReport.cs', 'Program.cs', 'check.py', 'SnapshotProof.csproj')],
             examples={'positive': [ref(base + '/SnapshotQuery.cs', 'extensions')], 'negative': [ref(base + '/invalid.cs.txt', 'extensions')]},
             review=ref(base + '/review.md', 'extensions'), checks=[{'kind': 'toolkit', 'id': 'shared-snapshot-proof'}], evidence=[])
    additions = {'schemaVersion': 1, 'sources': [{'id': 'example.shared-snapshot-source', 'locator': {'kind': 'extension', 'path': base + '/README.md'}}],
                 'rules': {'example.shared-snapshot-query': {'source': 'example.shared-snapshot-source', 'selector': {'kind': 'document'}, 'owner': 'fictional shared maintainer', 'level': 'recommended', 'limits': 'Finite immutable snapshot example only.'}},
                 'codingUnits': [unit]}
    write(public / 'declaration.json', additions)
    selection = {'schemaVersion': 1, 'declaration': 'publishable/declaration.json', 'files': files}
    write(public / 'selection.json', selection)
    output = consumer / 'artifacts/shared-contribution'
    command = [sys.executable, pattern, 'prepare-shared', '--repository', consumer, '--selection', 'publishable/selection.json', '--output', 'artifacts/shared-contribution']
    run('30-prepare-only-selected-shared-lesson', command)
    exported = b''.join(path.read_bytes() for path in output.rglob('*') if path.is_file())
    assert b'PRIVATE_F6_' not in exported and b'private-review' not in exported
    assert len(list(output.rglob('*.log'))) == 0
    run('31-existing-contribution-preserved', command, 2)
    # Bindings cannot be copied to the shared proposal.
    additions['codingUnits'][0]['pattern']['evidence'] = [{'fingerprint': '0' * 64}]
    write(public / 'declaration.json', additions)
    blocked = [*command[:-1], 'artifacts/invalid-shared-contribution']
    run('32-consumer-evidence-transfer-rejected', blocked, 2)
    assert not (consumer / 'artifacts/invalid-shared-contribution').exists()
    additions['codingUnits'][0]['pattern']['evidence'] = []
    write(public / 'declaration.json', additions)
    # Apply the prepared source changes only to a separate disposable installed copy.
    shared = consumer.parent / (consumer.name + '-shared')
    shared.mkdir()
    seed(shared)
    for path in output.rglob('*'):
        if path.is_file() and path.relative_to(output).parts[0] == 'extensions':
            target = shared / '.specify' / path.relative_to(output)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    scripts = shared / '.specify/extensions/program-kit-governance/scripts'
    catalog_path = scripts.parent / 'references/phase-obligations.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    for key in ('sources', 'codingUnits'):
        catalog[key].extend(additions[key])
    catalog['rules'].update(additions['rules'])
    catalog['codingUnits'][-1]['pattern']['status'] = 'active'
    write(catalog_path, catalog)
    public_example = shared / '.specify/extensions' / base
    # Isolate native build policy and package sources in the actual example directory.
    for name in ('Directory.Build.props', 'Directory.Build.targets', 'NuGet.Config', 'global.json', 'runtime.txt'):
        shutil.copyfile(shared / name, public_example / name)
    check_inputs = ['.specify/extensions/' + base + '/' + n for n in ('Note.cs', 'SnapshotScan.cs', 'SnapshotQuery.cs', 'OwnerReport.cs', 'Program.cs', 'SnapshotProof.csproj', 'Directory.Build.props', 'Directory.Build.targets', 'NuGet.Config', 'global.json', 'runtime.txt')]
    write(shared / 'eng/verification.json', {'schemaVersion': 1, 'testGroups': [], 'toolkitChecks': [{
        'id': 'shared-snapshot-proof', 'script': '.specify/extensions/' + base + '/check.py', 'arguments': ['--benchmark'],
        'inputs': check_inputs, 'timeoutSeconds': 65}]})
    native = shared / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py'
    shared_check = [sys.executable, native, '--repository', shared, '--scope', 'Focused', '--check', 'shared-snapshot-proof']
    shared_code = public_example / 'SnapshotQuery.cs'
    valid_shared = shared_code.read_bytes()
    shared_code.write_bytes(valid_shared.replace(b'StringComparer.Ordinal)', b'StringComparer.OrdinalIgnoreCase)'))
    run('33a-shared-independent-invalid-case-identity', shared_check, 2, cwd=shared)
    nested = sorted((shared / 'artifacts/tests/toolkit-runs').glob('*/result.json'), key=lambda p: p.stat().st_mtime_ns)[-1]
    streams = ''.join(p.read_text(encoding='utf-8') for p in nested.parent.glob('*.log'))
    assert 'BUILD_SUCCEEDED_BEFORE_BEHAVIOR' in streams and 'owner-isolation-and-duplicate-count' in streams
    write(review / 'snapshots/shared-invalid.cs', shared_code.read_text(encoding='utf-8'))
    shared_code.write_bytes(valid_shared)
    run('33-shared-rewritten-paths-actual-proof', shared_check, cwd=shared)
    # Ordinary maintainer source authoring, in an isolated process importing installed owners.
    write(shared / 'tests/bind_shared.py', '''from pathlib import Path
from datetime import datetime, timezone
import json
import sys
root = Path(__file__).resolve().parents[1]
scripts = root / '.specify/extensions/program-kit-governance/scripts'
sys.path.insert(0, str(scripts))
import coding_patterns as patterns
from coding_context import prepare
from phase_obligations import catalog
registry = catalog()
unit = registry['codingUnits'][-1]
observed = prepare(root, root / 'specs/001-learn', operation='report')['coding']['patternsContext']
extensions = root / '.specify/extensions'
record = {'fingerprint': patterns.binding(unit, patterns.resolved_rules(registry, unit, root, extensions), root, extensions, observed),
          'checks': [patterns.current_check(root, c) for c in unit['pattern']['checks']], 'boundAtUtc': datetime.now(timezone.utc).isoformat()}
unit['pattern']['evidence'].append(record)
path = scripts.parent / 'references/phase-obligations.json'
path.write_text(json.dumps(registry, indent=2) + '\\n', encoding='utf-8')
print(json.dumps(record))
''')
    proof = run('33b-reviewed-shared-source-binding', [sys.executable, shared / 'tests/bind_shared.py'], cwd=shared)
    selected = run('34-shared-installed-selection', [sys.executable, scripts / 'phase_obligations.py', 'prepare', '--repository', shared,
         '--feature-dir', 'specs/001-learn', '--operation', 'report', '--format', 'json'], cwd=shared)
    assert any(p['id'] == 'shared-snapshot-query' and p['selected'] for p in selected['coding']['patterns'])
    write(review / 'shared-review.json', {'consumer': str(shared), 'sourceAdditions': str(output / 'catalog-additions.json'), 'freshBinding': proof,
          'publicationOccurred': False, 'limits': 'Fictional reviewed source application in isolated copy; no real upstream adoption or authenticated review.'})


def guide(consumer, result):
    consumer = Path(native_path(consumer))
    return f'''# F6 actual learning/application review — human review pending

This new fictional consumer is [retained here]({consumer.as_posix()}). Review is not complete merely because execution passed. No worker/provider/browser or stopped consumer was started. [Actual command identities/results](results.json) retain both streams, exits and timings for all {len(result['commands'])} commands.

1. Inspect [supported gap](output/01-supported-task-gap.stdout.txt), [actual baseline](output/02-baseline-correctness-and-performance.stdout.txt) and [teaching contribution](output/03-teach-reviewable-contribution.stdout.txt). The problem/change plan is reviewable; empty scaffold changes mean this is a manual recipe, not a new renderer.
2. [Missing proof](output/04-selected-missing-proof.stdout.txt) blocks selection. [Actual binding](output/05-bind-actual-check-and-review.stdout.txt) then permits [qualified selection](output/06-qualified-local-selection.stdout.txt). Review source and ordinary fictional review independently of routing.
3. The [fresh task](output/07-fresh-task-selects-lesson.stdout.txt) uses the lesson. Compare [before](snapshots/application-before.cs), [after](snapshots/application-after.cs) and [actual application diff](snapshots/application.diff). The applied OwnerReport really compiles and executes in [the check](output/09-actually-applied-application-and-performance.stdout.txt), including fixed owner/order/duplicate/mutation expectations. Preparation still reports `applicationObserved: false`; execution is separate proof.
4. Follow [live-task exclusion](output/12-live-task-excludes-index.stdout.txt), compiled invalid [owner leak](snapshots/owner-leak.cs) and [reverse ordering](snapshots/reversed-order.cs), [restored checks](output/14-restored-current-proof.stdout.txt), [changed source rejection](output/16-changed-input-stales-qualification.stdout.txt) and [restoration](output/17-restored-source-is-current.stdout.txt). Nested check logs and the original failures remain in the retained consumer.
5. Inspect installed unknown/incompatible/overlapping/executable-adapter controls `18`–`21`. New responsibility detection uses the existing context owner. Registration alone is not qualification; [finite source/check recipe]({(EXAMPLE / 'README.md').as_posix()}) defines the extension contract and limits.
6. Compare [prior versions](snapshots/versions-before-retirement.json), [retired history](snapshots/versions-after-retirement.json), `22`–`29` for refinement/replacement/retirement preparation, wrong-version rejection, exact adoption and preserved alternatives. Earlier evidence is neither rewritten nor silently adopted.
7. Inspect [explicit shared preparation](output/30-prepare-only-selected-shared-lesson.stdout.txt), its [actual files]({(consumer / 'artifacts/shared-contribution').as_posix()}), [fresh isolated shared proof](output/33-shared-rewritten-paths-actual-proof.stdout.txt), [installed shared selection](output/34-shared-installed-selection.stdout.txt) and [source/binding details](shared-review.json). Private canaries are absent. Existing output and consumer-evidence transfer reject (`31`/`32`). Public source review, publication and real consumer adoption have not happened.

## Measured scope and limits

Read the raw benchmark JSON inside actual named-check streams under `{consumer.as_posix()}/artifacts/tests/toolkit-runs/`. It records .NET runtime, OS/architecture/CPU count, Release, 8,192 rows, 64 owners, 256 lookups and five alternating rounds. Compare read-many samples with construction plus one lookup; retain all allocations and timing variation. Allocations are thread-local managed bytes, not retained memory/RSS. The index copies and stores grouped rows; a one-shot scan can cost less. Mutable stores require rebuilding and are excluded. No universal speed or database guarantee follows.

Authoring and review decisions are fictional; attribution does not authenticate authors. Selection does not prove agent consultation. This is installed-layout finite .NET application/extension proof, not F8 packaged installation/update, F7 general completion, real security/session/provider behavior, human product acceptance or complete F1–F8 acceptance. F1–F5 failures, costs and limits remain unchanged. No deferred development skill was created.

Rerun only for changed contracts: `python tests/learning_review_fixture.py --review` through the prepared interpreter, or the named `validate_coding_learning` check with `--suite Affected --check ... --reason ...`. Every review run preserves previous material.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true')
    args = parser.parse_args()
    folder = ROOT / 'artifacts/f6-review' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6])
    print('Retained F6 review: ' + str(folder / 'index.md'), flush=True)
    result = scenario(folder)
    print(json.dumps({'status': result['status'], 'elapsedSeconds': json.loads((folder / 'results.json').read_text())['elapsedSeconds'], 'review': str(folder / 'index.md')}))


if __name__ == '__main__':
    main()

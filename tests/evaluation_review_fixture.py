"""F7 retained installed evaluation/admission journey; fictional authorship only.

Real .NET compilation/behavior and native rule consumption are independent of
authored review. No coding agent, provider, browser or prior consumer starts.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from coding_review_fixture import write
from learning_review_fixture import seed, declaration, EXAMPLE, ref
from owned_fixture import filesystem_path, native_path


def scenario(review, *, installed_consumer=None, qualification_only=False):
    review = Path(filesystem_path(review.resolve()))
    consumer = Path(filesystem_path(installed_consumer or ROOT / 'artifacts/t' / ('f7-' + uuid.uuid4().hex[:8])))
    consumer.mkdir(parents=True, exist_ok=installed_consumer is not None)
    started = time.monotonic()
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    inputs_before = input_snapshot()
    # The maintained runner records complete dirty input identities as well.
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    result = {'sourceCommit': source, 'fixtureSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'consumer': native_path(consumer), 'status': 'running', 'commands': [], 'fictionalAuthorship': True,
              'workingInputs': inputs_before}
    write(review / 'index.md', '# Incomplete F7 review\n\nInspect results.json, output/ and the retained consumer. No success inferred.\n')

    def run(name, command, expected=0, marker=None):
        command = [native_path(v) if isinstance(v, Path) else str(v) for v in command]
        step = time.monotonic()
        child = subprocess.run(command, cwd=native_path(consumer), capture_output=True, text=True, encoding='utf-8', timeout=100)
        write(review / 'output' / (name + '.stdout.txt'), child.stdout)
        write(review / 'output' / (name + '.stderr.txt'), child.stderr)
        result['commands'].append({'name': name, 'command': command, 'expectedExit': expected, 'actualExit': child.returncode,
                                   'elapsedSeconds': round(time.monotonic() - step, 3),
                                   'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(),
                                   'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        if child.returncode != expected or marker and marker not in child.stdout + child.stderr:
            raise AssertionError(name + ': unexpected outcome; inspect both retained streams')
        try:
            return json.loads(child.stdout)
        except ValueError:
            return child.stdout

    try:
        seed(consumer, installed=installed_consumer is not None)
        baseline = subprocess.check_output(['git', '-c', 'safe.directory=' + native_path(consumer), '-c', 'core.excludesFile=',
                                            'rev-parse', 'HEAD'], cwd=native_path(consumer), text=True).strip()
        result['consumerBaseline'] = baseline
        write(consumer / 'artifacts/fixture-baseline.txt', baseline)
        feature = consumer / 'specs/001-learn'
        extensions = consumer / '.specify/extensions'
        governance = extensions / 'program-kit-governance/scripts'
        engine = extensions / 'program-kit-dotnet/templates/dotnet/files/eng'
        phase = governance / 'phase_obligations.py'
        task = governance / 'task_draft.py'
        pattern = governance / 'coding_patterns.py'
        native = engine / 'repository_verification.py'
        # Give the row contract its accepted Core owner; this edge is the mutation subject.
        core = consumer / 'src/Rows.Core'
        core.mkdir()
        shutil.move(consumer / 'src/Lookup/Note.cs', core / 'Note.cs')
        write(core / 'Rows.Core.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup></Project>\n')
        lookup = consumer / 'src/Lookup/Lookup.csproj'
        write(lookup, lookup.read_text().replace('</Project>', '<ItemGroup><ProjectReference Include="../Rows.Core/Rows.Core.csproj" /></ItemGroup></Project>'))
        graph = json.loads((consumer / 'eng/architecture.json').read_text())
        graph['runtimeComposition']['projects'][0]['projectReferences'] = ['src/Rows.Core/Rows.Core.csproj']
        graph['runtimeComposition']['projects'].append({'path': 'src/Rows.Core/Rows.Core.csproj', 'role': 'core', 'projectReferences': [],
             'responsibilities': [{'name': 'SnapshotRows', 'kind': 'contract', 'effects': []}]})
        write(consumer / 'eng/architecture.json', graph)
        accepted = json.loads((consumer / 'docs/architecture/building-block-selection.json').read_text())
        accepted['targets'].append({'id': 'rows', 'kind': 'dotnet-project', 'path': 'src/Rows.Core/Rows.Core.csproj',
                                   'placement': {'owner': 'lookup', 'decisionIds': ['snapshot-owner']}})
        write(consumer / 'docs/architecture/building-block-selection.json', accepted)
        write(feature / 'tasks.md', '''# Fictional F7 task plan
<!-- program-kit:story-delivery-v1 -->
- [ ] T001 [US1] Apply immutable snapshot query in src/Lookup/OwnerReport.cs using src/Lookup/Lookup.csproj and src/Rows.Core/Rows.Core.csproj.
- [ ] T002 [US1] Verify owned results in tests/Proof/SnapshotProof.csproj and inspect actual source responsibilities and invocation style.

## Operation dependency map
| Operation | Depends on operations |
|-----------|-----------------------|
| report | none |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | report | none | none | none |
| T002 | report | T001 | none | none |

## Story delivery map
| Story | Operations | Useful outcome | Independent walkthrough | Active minutes to review | Larger-story rationale |
|-------|------------|----------------|-------------------------|--------------------------|------------------------|
| US1 | report | Owner reads an immutable report | Run the compiled report oracle | 45 | none |
''')
        for name in ('spec.md', 'plan.md'):
            write(feature / name, '<!-- program-kit:story-delivery-v1 -->\n' + (feature / name).read_text())
        app = consumer / 'src/Lookup/OwnerReport.cs'
        applied = app.read_text()
        before = applied.replace('SnapshotQuery', 'SnapshotScan')
        write(app, before)
        write(review / 'snapshots/application-before.cs', before)
        from asset_sources import read as source_bytes
        example = consumer / '.specify/extensions/program-kit-dotnet/references/examples/snapshot-query'
        write(consumer / 'docs/patterns/lesson.md', source_bytes(example / 'README.md').decode('utf-8'))
        write(consumer / 'docs/patterns/invalid-query.cs.txt', 'Independent invalid owner-identity control; actual source is retained in this review.\n')
        write(consumer / 'docs/patterns/review.md', '''# Fictional scoped F7 source review

The immutable owner report uses a Core-owned row and a pure helper. OwnerReport
delegates to the selected snapshot query; it introduces no provider or transport.
Inspect exact ordinal ownership, stable order, duplicates, copied snapshots,
immutable results and rebuild behavior against the independently authored oracle.
Review one named type per correctly named C# file, purposeful XML documentation,
entrypoint/helper ordering and mandatory prepared-argument/list/fluent layout.
The compiler does not certify all these semantic/source duties. This is authored
fixture review, not authenticated authorship or consumer human product acceptance.
Native role constraints resolve architecture_rules.py; no second role table belongs here.
''')
        unit = declaration('local-f7')
        unit['ruleIds'].append('native.allowed-role-references')
        unit['pattern']['inputs'] = [ref(p) for p in ('src/Rows.Core/Note.cs', 'src/Rows.Core/Rows.Core.csproj',
              'src/Lookup/SnapshotQuery.cs', 'src/Lookup/SnapshotScan.cs', 'src/Lookup/OwnerReport.cs',
              'src/Lookup/Lookup.csproj', 'tests/Proof/Program.cs', 'tests/Proof/check.py', 'tests/Proof/SnapshotProof.csproj',
              'global.json', 'runtime.txt', 'NuGet.Config', 'Directory.Build.props', 'Directory.Build.targets', 'eng/verification-runner.py')]
        unit['pattern']['checks'] = [{'kind': 'toolkit', 'id': 'snapshot-proof'}]
        write(consumer / 'docs/architecture/coding-patterns.json', {'schemaVersion': 1,
            'sources': [{'id': 'local.lesson', 'locator': {'kind': 'repository', 'path': 'docs/patterns/lesson.md'}}],
            'rules': {'local.snapshot-query': {'source': 'local.lesson', 'selector': {'kind': 'document'},
                      'owner': 'fictional snapshot maintainer', 'level': 'recommended', 'limits': 'Finite immutable owner report',
                      'bindings': {'recipes': ['extensions/program-kit-dotnet/references/examples/snapshot-query/README.md']}}}, 'codingUnits': [unit]})
        inputs = [r['path'] for r in unit['pattern']['inputs']]
        write(consumer / 'eng/verification-runner.py', '''"""Finite supported native adapter: one actual compiled oracle suite, no reuse claim."""
import argparse,json,subprocess
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--request',type=Path,required=True)
parser.add_argument('--result',type=Path,required=True)
args=parser.parse_args()
request=json.loads(args.request.read_text())
root=Path(request['repository'])
assembly=root/'tests/Proof/bin'/request['configuration']/'net10.0/SnapshotProof.dll'
actual=subprocess.run(['dotnet',str(assembly)],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=15)
directory=Path(request['outputDirectory'])
stdout=directory/'oracle.stdout.log'
stderr=directory/'oracle.stderr.log'
stdout.write_text(actual.stdout,encoding='utf-8')
stderr.write_text(actual.stderr,encoding='utf-8')
assert actual.returncode==0 and 'PASS: owner isolation' in actual.stdout, 'actual compiled oracle suite failed'
args.result.write_text(json.dumps({'schemaVersion':1,'status':'completed','executedTests':1,
 'evidence':[p.relative_to(root).as_posix() for p in (stdout,stderr)]}))
print('PASS: one actual compiled oracle suite through the native adapter; no reusable qualification claimed')
''')
        write(consumer / 'eng/verification.json', {'schemaVersion': 1, 'runner': 'adapter', 'testGroups': [{'id': 'snapshot',
            'projects': ['tests/Proof/SnapshotProof.csproj'], 'inputs': ['src/Lookup/**', 'src/Rows.Core/**']}],
            'toolkitChecks': [{'id': 'snapshot-proof', 'script': 'tests/Proof/check.py', 'arguments': [], 'inputs': inputs, 'timeoutSeconds': 60}]})
        # A real finite engineering command delegates to the existing named-check owner.
        write(consumer / 'eng/Invoke-RepositoryVerification.ps1', f'''param([string]$Scope, [string]$FeatureDirectory, [string]$ChangedFrom)
$proofPython = '{sys.executable.replace("'", "''")}'
$proofScript = Join-Path $PSScriptRoot '../.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py'
& $proofPython $proofScript --repository (Split-Path $PSScriptRoot) --scope Focused --check snapshot-proof
exit $LASTEXITCODE
''')
        # Separate accepted browser ownership; it has no native source dependency.
        browser = consumer / 'specs/004-browser'
        write(browser / 'spec.md', '# Fictional browser presentation\n- **Specification roadmap entry**: RM-004\n')
        write(browser / 'plan.md', 'TypeScript presentation only.\n')
        write(browser / 'tasks.md', '- [ ] T101 Style the browser page.\n')
        write(consumer / '.program-kit/specification-intake/RM-004/brief.json', {'architectureScope': ['browser'], 'decisions': []})
        architecture = json.loads((consumer / 'docs/architecture/architecture-map.json').read_text())
        architecture['elements'].append({'id': 'browser', 'type': 'bounded-context', 'decision_refs': []})
        write(consumer / 'docs/architecture/architecture-map.json', architecture)

        helper = consumer / 'fixture.py'
        write(helper, '''import copy,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'.specify/extensions/program-kit-governance/scripts'))
import task_draft as task
import coding_context as coding
import coding_patterns as patterns
feature=root/'specs/001-learn'
action=sys.argv[1]
if action=='initialize':
    baseline=(root/'artifacts/fixture-baseline.txt').read_text()
    with patch.object(task,'require_policy'):
        value=task.transition(root,feature,{'action':'initialize','baseline':baseline,'source':'Fictional fixture author; no ratification or real human acceptance claim'})
    task.checkpoint(root/'specs/004-browser',{'baseline':baseline,'outcome':'Independent fictional browser scope','next':'Prepare browser'})
elif action=='request':
    prepared=coding.prepare(root,feature,task_ids=['T001','T002'],reconcile=True,configuration='Release')
    coding.require_ready(prepared)
    duties=prepared['coding']['evaluation']['duties']
    actual=patterns.current_check(root,{'kind':'toolkit','id':'snapshot-proof'})
    native_reference=(root/'artifacts/native-proof-reference.txt').read_text()
    native_declaration={'kind':'native','project':'tests/Proof/SnapshotProof.csproj','arguments':[],'configuration':'Release'}
    claims=[{'rules':[d['rule'] for d in duties if d['required']], 'checks':[{'kind':'toolkit','id':'snapshot-proof'},native_declaration],
      'review':'docs/patterns/review.md','conclusion':'Scoped source review and independent compiled owner/order/duplicate/snapshot results inspected.',
      'limits':'Finite .NET/BCL application and native planned graph; authored review is fictional and unauthenticated. No provider/browser/human acceptance.'}]
    value={'action':'engineering','checkpoint':'US1','configuration':'Release','checks':[actual['run'],native_reference], 'evaluation':claims}
    (root/'request.json').write_text(json.dumps(value,indent=2))
elif action=='native-limits':
    declaration={'kind':'native','project':'tests/Proof/SnapshotProof.csproj','arguments':[],'configuration':'Release'}
    try:
        patterns.current_check(root,declaration)
    except ValueError:
        pass
    else:
        raise AssertionError('Non-reusable native observation became reusable pattern qualification')
    reference=(root/'artifacts/native-proof-reference.txt').read_text()
    observed=patterns.current_check(root,declaration,reference,handoff=True)
    assert observed['reuse']=='execution-observation-only'
    from phase_obligations import catalog
    extensions=root/'.specify/extensions'
    registry=patterns.merge(catalog(),root)
    unit=copy.deepcopy(next(u for u in registry['codingUnits'] if u['id']=='local-f7'))
    unit['pattern']['checks']=[declaration]
    rules=patterns.resolved_rules(registry,unit,root,extensions)
    context=coding.prepare(root,feature,configuration='Release')['coding']['patternsContext']
    unit['pattern']['evidence']=[{'fingerprint':patterns.binding(unit,rules,root,extensions,context),
       'checks':[observed],'boundAtUtc':datetime.now(timezone.utc).isoformat()}]
    replay=patterns.qualify(unit,rules,root,extensions,context)
    assert replay['status']!='qualified', 'Execution observation was replayed as reusable pattern qualification'
    value={'qualificationReusable':False,'replayedObservationQualification':replay['status'],'actualNativeHandoff':observed}
elif action=='waiting':
    value=task.load_delivery(feature)
    assert value['clock']['waiting'] and value['active']['operation']=='report'
    before=value['stories']['US1']['seconds']
    control=copy.deepcopy(value)
    control['clock']['waiting']=False
    task.accrue(control,control['clock']['at']+3600)
    assert control['stories']['US1']['seconds']>before
    task.accrue(value,value['clock']['at']+3600)
    assert value['stories']['US1']['seconds']==before
    value={'waiting':True,'simulatedClockAdvanceSeconds':3600,'engineeringSecondsChargedDuringHumanWait':0,
           'activeControlChargedSeconds':control['stories']['US1']['seconds']-before,'humanAcceptanceEstablished':False}
elif action=='native-failure':
    import repository_verification as native
    declaration={'kind':'native','project':'tests/Proof/SnapshotProof.csproj','arguments':[],'configuration':'Release'}
    planned=native.plan(root,{'scope':'Focused','projects':[declaration['project']],'toolkitChecks':[]},[],'Release')
    assert any(row['project']==declaration['project'] for row in planned['unresolved'])
    reference=(root/'artifacts/native-proof-reference.txt').read_text()
    try:
        patterns.current_check(root,declaration,reference,handoff=True)
    except ValueError:
        value={'oldNativeObservationRejectedAfterFailure':True,'unresolved':planned['unresolved']}
    else:
        raise AssertionError('Older successful native observation concealed a later failed suite')
else:
    raise ValueError(action)
print(json.dumps(value))
''')
        run('00-fictional-authoring-setup', [sys.executable, helper, 'initialize'])

        def prepare(name, expected=0, target=feature):
            return run(name, [sys.executable, phase, 'prepare', '--repository', consumer, '--feature-dir', target.relative_to(consumer), '--configuration', 'Release', '--format', 'json'], expected)

        def check(name, expected=0):
            return run(name, [sys.executable, native, '--repository', consumer, '--scope', 'Focused', '--check', 'snapshot-proof'], expected)

        def delivery(name, request, expected=0):
            write(consumer / 'request-action.json', request)
            return run(name, [sys.executable, task, 'delivery', '--repository', consumer, '--feature-dir', feature.relative_to(consumer),
                              '--content-file', consumer / 'request-action.json'], expected)

        initial = prepare('01-prepared-duties')
        assert initial['coding']['canProceed']
        delivery('01b-start-actual-operation', {'action': 'start', 'operation': 'report'})
        write(app, applied)
        write(review / 'snapshots/application-after.cs', applied)
        write(review / 'snapshots/application.diff', ''.join(difflib.unified_diff(before.splitlines(True), applied.splitlines(True), fromfile='before/OwnerReport.cs', tofile='after/OwnerReport.cs')))
        check('02-actual-compiled-application')
        run('02b-actual-native-adapter-suite', [sys.executable, native, '--repository', consumer, '--scope', 'Focused',
               '--project', 'tests/Proof/SnapshotProof.csproj', '--configuration', 'Release'])
        native_results = sorted((consumer / 'artifacts/tests/runs').glob('*/result.json'), key=lambda p: json.loads(p.read_text()).get('startedAtUtc', ''))
        write(consumer / 'artifacts/native-proof-reference.txt', native_results[-1].relative_to(consumer).as_posix())
        run('02c-native-observation-does-not-qualify-reuse', [sys.executable, helper, 'native-limits'])
        run('03-bind-qualified-pattern', [sys.executable, pattern, 'bind-evidence', '--repository', consumer, '--feature-dir', feature.relative_to(consumer), '--configuration', 'Release', '--id', 'local-f7'])
        selected_plan = (feature / 'plan.md').read_text() + '\n<!-- program-kit:pattern-choices -->\n' + json.dumps({
            'snapshot-owner-query': {'id': 'local-f7', 'version': '1.0.0', 'reason': 'Explicit qualified immutable owner-report implementation.'}}) + '\n<!-- /program-kit:pattern-choices -->\n'
        write(feature / 'plan.md', selected_plan)
        qualified = prepare('04-qualified-task')
        assert qualified['coding']['patterns'][0]['qualification']['status'] == 'qualified'
        run('04b-native-linked-positive', [sys.executable, engine / 'repository_architecture.py', '--repository', consumer,
                                          '--manifest', 'eng/architecture.json', '--planned'])
        if installed_consumer is not None:
            run('04c-actual-installed-implementation-prehook', [sys.executable, governance / 'implementation_preflight.py',
                '--feature-dir', feature.relative_to(consumer), '--configuration', 'Release'])
        if qualification_only:
            result.update(status='passed', scope='Actual installed old pattern qualification; completion and human acceptance remain due.')
            write(review / 'index.md', '# Qualified old fictional consumer\n\nInspect results.json and output/01–04b. Actual compiled/native checks and local qualification ran; no completion or human decision was supplied.\n')
            return result
        tasks = feature / 'tasks.md'
        write(tasks, tasks.read_text().replace('- [ ]', '- [X]'))
        checked_bytes = tasks.read_bytes()
        finish_command = [sys.executable, phase, 'finish', '--repository', consumer, '--feature-dir', feature.relative_to(consumer), '--configuration', 'Release']
        run('05-checked-boxes-omit-evaluation', finish_command, 2, 'PKC020')
        assert tasks.read_bytes() == checked_bytes
        run('06-author-scoped-engineering-request', [sys.executable, helper, 'request'])
        request = json.loads((consumer / 'request.json').read_text())
        omitted = copy.deepcopy(request)
        omitted_rule = omitted['evaluation'][0]['rules'].pop()
        delivery('07-omitted-mandatory-duty', omitted, 2)
        assert tasks.read_bytes() == checked_bytes
        write(review / 'snapshots/omitted-duty.json', {'rule': omitted_rule, 'tasksUnchanged': True})
        write(consumer / 'artifacts/fabricated.json', {'status': 'completed'})
        fabricated = {**request, 'checks': ['artifacts/fabricated.json']}
        delivery('08-fabricated-completion', fabricated, 2)
        write(consumer / 'artifacts/replayed.json', json.loads((consumer / request['checks'][0]).read_text()))
        delivery('09-replayed-check-owner', {**request, 'checks': ['artifacts/replayed.json']}, 2)
        replay = 'artifacts/tests/toolkit-runs/replayed/result.json'
        write(consumer / replay, json.loads((consumer / request['checks'][0]).read_text()))
        delivery('09b-replayed-under-maintained-owner', {**request, 'checks': [replay]}, 2)
        check('09c-current-execution-after-replay')
        unsupported = copy.deepcopy(request)
        unsupported['evaluation'][0]['checks'] = [{'kind': 'registered-only', 'id': 'no-actual-mechanism'}]
        delivery('10-unsupported-actual-mechanism', unsupported, 2)
        delivery('11-complete-engineering-handoff', request)
        presentation = {**request, 'action': 'present', 'basisPaths': ['src/Lookup/OwnerReport.cs', 'src/Lookup/SnapshotQuery.cs'],
                        'entryPoint': 'python tests/Proof/check.py', 'preparedData': 'Fixed fictional immutable rows',
                        'walkthrough': 'Run compiled owner report; inspect source and independent invalid controls',
                        'expected': 'Exact owner/order/duplicates and immutable snapshot results',
                        'limitations': 'Fictional source review; no real consumer human/product/provider/browser acceptance'}
        delivery('12-present-for-human-review', presentation)
        run('13-waiting-does-not-consume-engineering', [sys.executable, helper, 'waiting'])
        run('14-feature-closure-awaits-human', finish_command, 2, 'Required human reviews remain due')

        browser_before = prepare('15-independent-browser-before', target=browser)
        rules_file = engine / 'architecture_rules.py'
        original_rules = rules_file.read_bytes()
        changed_rules = original_rules.replace(b'"helper": {"core", "helper"}', b'"helper": {"helper"}')
        assert changed_rules != original_rules
        write(review / 'snapshots/canonical-before.py', original_rules.decode())
        rules_file.write_bytes(changed_rules)
        write(review / 'snapshots/canonical-after.py', changed_rules.decode())
        changed = prepare('16-canonical-mutation-stales-task', 2)
        assert any(b['code'] == 'PKP005' for b in changed['coding']['blockers'])
        before_rule = next(r for u in qualified['coding']['skills'] for r in u['rules'] if r['id'] == 'native.allowed-role-references')
        after_rule = next(r for u in changed['coding']['skills'] for r in u['rules'] if r['id'] == 'native.allowed-role-references')
        assert before_rule['fingerprint'] != after_rule['fingerprint'] and before_rule['text'] != after_rule['text']
        run('17-native-linked-expectation-changes', [sys.executable, engine / 'repository_architecture.py', '--repository', consumer,
                                                   '--manifest', 'eng/architecture.json', '--planned'], 2)
        browser_after = prepare('18-independent-browser-after', target=browser)
        assert browser_before == browser_after
        write(review / 'snapshots/canonical-consumption.json', {'before': before_rule, 'after': after_rule,
              'linkedRecipe': 'program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py',
              'duplicatePolicyStringsEdited': False, 'browserViewUnchanged': True})
        tasks_before_stale = tasks.read_bytes()
        run('19-stale-completion-preserves-progress', finish_command, 2)
        assert tasks.read_bytes() == tasks_before_stale
        delivery('19b-start-scoped-repair', {'action': 'start', 'operation': 'report', 'purpose': 'repair'})
        query = consumer / 'src/Lookup/SnapshotQuery.cs'
        valid_query = query.read_text()
        invalid_query = valid_query.replace('StringComparer.Ordinal)', 'StringComparer.OrdinalIgnoreCase)')
        assert invalid_query != valid_query
        write(query, invalid_query)
        write(review / 'snapshots/independent-invalid-query.cs', invalid_query)
        run('20-independent-invalid-behavior', [sys.executable, consumer / 'tests/Proof/check.py'], 1,
            'owner-isolation-and-duplicate-count')
        # The independent oracle runs even while the deliberately wrong role rule
        # blocks normal native selection. Restore that rule before recording the
        # same invalid behavior through the supported named-check owner.
        rules_file.write_bytes(original_rules)
        check('20b-retained-named-behavior-failure', 2)
        run('20c-actual-native-invalid-suite', [sys.executable, native, '--repository', consumer, '--scope', 'Focused',
               '--project', 'tests/Proof/SnapshotProof.csproj', '--configuration', 'Release'], 2)
        failed_native = sorted((consumer / 'artifacts/tests/runs').glob('*/result.json'), key=lambda p: json.loads(p.read_text()).get('startedAtUtc', ''))[-1]
        assert 'owner-isolation-and-duplicate-count' in (failed_native.parent / 'oracle.stderr.log').read_text()
        write(review / 'snapshots/native-negative.json', {'run': failed_native.relative_to(consumer).as_posix(),
              'actualCompiledOracleFailed': True, 'marker': 'owner-isolation-and-duplicate-count'})
        # A genuine compiled behavioral failure, never a setup failure, satisfies this control.
        failed_runs = sorted((consumer / 'artifacts/tests/toolkit-runs').glob('*/result.json'), key=lambda p: json.loads(p.read_text()).get('startedAtUtc', ''))
        failed = json.loads(failed_runs[-1].read_text())
        streams = '\n'.join((consumer / p).read_text() for p in failed['outcomes'][0]['evidence'])
        assert 'BUILD_SUCCEEDED_BEFORE_BEHAVIOR' in streams and 'owner-isolation-and-duplicate-count' in streams
        write(review / 'snapshots/independent-negative-observation.json', {'compiledSuccessfully': True, 'marker': 'owner-isolation-and-duplicate-count',
              'oracleSha256': hashlib.sha256((consumer / 'tests/Proof/Program.cs').read_bytes()).hexdigest(), 'failureRetained': failed_runs[-1].relative_to(consumer).as_posix()})
        rules_file.write_bytes(original_rules)
        write(query, valid_query)
        check('21-restored-independent-proof')
        run('21a-old-native-pass-cannot-conceal-failure', [sys.executable, helper, 'native-failure'])
        run('21b-fresh-native-recovery', [sys.executable, native, '--repository', consumer, '--scope', 'Focused',
               '--project', 'tests/Proof/SnapshotProof.csproj', '--configuration', 'Release'])
        native_results = sorted((consumer / 'artifacts/tests/runs').glob('*/result.json'), key=lambda p: json.loads(p.read_text()).get('startedAtUtc', ''))
        write(consumer / 'artifacts/native-proof-reference.txt', native_results[-1].relative_to(consumer).as_posix())
        run('22-rebind-restored-pattern', [sys.executable, pattern, 'bind-evidence', '--repository', consumer, '--feature-dir', feature.relative_to(consumer), '--configuration', 'Release', '--id', 'local-f7'])
        local_file = consumer / 'docs/architecture/coding-patterns.json'
        local = json.loads(local_file.read_text())
        incompatible = copy.deepcopy(local)
        incompatible['codingUnits'][0]['pattern']['compatibility']['frameworks'] = ['net9.0']
        write(local_file, incompatible)
        prepare('23-incompatible-qualified-input', 2)
        write(local_file, local)
        manual = consumer / 'unowned/Surprise.cs'
        write(manual, 'namespace Surprise; internal sealed class Unexpected {}\n')
        write(review / 'snapshots/unowned-manual.cs', manual.read_text())
        before_manual_tasks = tasks.read_bytes()
        run('24-manual-source-cannot-bypass-finish', finish_command, 2, 'PKC011')
        assert manual.is_file() and tasks.read_bytes() == before_manual_tasks
        write(review / 'snapshots/manual-preservation.json', {'sourcePreserved': True, 'tasksPreserved': True,
            'tasksSha256': hashlib.sha256(before_manual_tasks).hexdigest()})
        manual.unlink()
        # The selector uses actual native dependency closure, not the task's prose list.
        selection = run('25-affected-native-prerequisite-closure', [sys.executable, native, '--repository', consumer, '--scope', 'Affected',
              '--changed-path', 'src/Rows.Core/Note.cs', '--select-only'])
        assert selection['projects'] == ['tests/Proof/SnapshotProof.csproj'] and selection['toolkitChecks'] == ['snapshot-proof']
        run('26-refresh-authored-request-after-repair', [sys.executable, helper, 'request'])
        request = json.loads((consumer / 'request.json').read_text())
        delivery('27-current-engineering-after-repair', request)
        delivery('28-current-human-handoff-after-repair', {**presentation, **request, 'action': 'present'})
        delivery('29-fictional-human-decision', {'action': 'decision', 'checkpoint': 'US1', 'actor': 'requester', 'verdict': 'accepted',
                                                'source': 'Simulated fixture human decision; supplies no real human product acceptance'})
        run('30-supported-feature-completion', finish_command)
        result['status'] = 'passed'
        write(review / 'index.md', guide(consumer))
        return result
    except BaseException as error:
        result.update(status='failed', failureKind=type(error).__name__, diagnostic=str(error))
        raise
    finally:
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        result['workingInputsUnchanged'] = input_snapshot() == inputs_before
        write(review / 'results.json', result)


def guide(consumer):
    return f'''# F7 actual evaluation/admission — human review pending

Start with [actual results/commands](results.json) and the [new fictional consumer]({native_path(consumer)}).
Setup simulates accepted authoring/ratification; application execution is real. No agent/provider/browser or prior consumer started.

1. Compare [application before](snapshots/application-before.cs), [after](snapshots/application-after.cs) and [diff](snapshots/application.diff).
   [Compiled positive](output/02-actual-compiled-application.stdout.txt) executes the fixed owner/order/duplicate/snapshot oracle.
2. Read [derived duties](output/01-prepared-duties.stdout.txt), [qualified selection](output/04-qualified-task.stdout.txt),
   [omitted-duty rejection](output/07-omitted-mandatory-duty.stdout.txt) and [actual engineering handoff](output/11-complete-engineering-handoff.stdout.txt).
   Checked boxes, status-only JSON, copied evidence and unsupported mechanisms reject (05, 08–10); task/source bytes survive.
3. Inspect the [canonical before](snapshots/canonical-before.py), [after](snapshots/canonical-after.py) and [consumption comparison](snapshots/canonical-consumption.json).
   The same source reaches the brief and [native linked check](output/17-native-linked-expectation-changes.stderr.txt).
   Affected qualification becomes stale (16/19), while the independent browser view stays equal (15/18).
4. The [invalid case-insensitive owner implementation](snapshots/independent-invalid-query.cs) compiles then fails the fixed exact-case oracle.
   Inspect [independent observation](snapshots/independent-negative-observation.json) and the actual retained failed check/streams in the consumer.
   Canonical metadata cannot rewrite that oracle. Restoration and real rerun retain the failed history (21/22).
5. Incompatible input and unowned manual source reject (23/24). [Affected selection](output/25-affected-native-prerequisite-closure.stdout.txt)
   uses native dependency closure. [Human handoff](output/28-current-human-handoff-after-repair.stdout.txt) is separate from
   [waiting-time accounting](output/13-waiting-does-not-consume-engineering.stdout.txt) and [completion](output/30-supported-feature-completion.stdout.txt).
   The final human decision is explicitly simulated; no real human acceptance follows.

## Evidence owners and limits

The .NET SDK compiles and the fixed console oracle executes finite BCL application behavior through a named toolkit check.
The supported native adapter separately executes one actual compiled oracle suite and reports one suite through the native owner (02b).
Its result is non-reusable qualification but can support an explicit current execution-observation handoff (02c).
Neither route establishes xUnit/MTP discovery, analyzer acceptance, Foundation/provider/browser qualification or agent obedience.
Native planned architecture checks enforce their exact role table. Authored source review covers semantic ownership,
mandatory invocation layout, file/type documentation and ordering; file hashes do not establish review truth or authenticated identity.
Existing F5 provider/HTTP/browser results remain separately attributable historical application evidence. They are not rerun or relabeled here.
Actual consumer human product review, F8 packaged adoption and complete F1–F8 acceptance remain unproven.
Local evidence rejects supported stale/corrupt/replayed inputs; it is not resistant to maliciously forged local history.

Rerun only for changed contracts: `python tests/evaluation_review_fixture.py --review` using the prepared interpreter,
or the maintained named check with explicit `--suite Affected --check validate_coding_evaluation_journey --reason ...`.
Every run retains its consumer, commands, both streams, source/input identities, snapshots and failures. No cleanup is implied.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true')
    parser.parse_args()
    review = ROOT / 'artifacts/f7-review' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6])
    print('Retained F7 review: ' + str(review / 'index.md'), flush=True)
    result = scenario(review)
    print(json.dumps({'status': result['status'], 'elapsedSeconds': result['elapsedSeconds'], 'review': str(review / 'index.md')}))


if __name__ == '__main__':
    main()

"""Retained F4 installed-command journey. Fictional authoring, real source/app checks."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from owned_fixture import FixtureDirectory, filesystem_path, native_path
from coding_review_fixture import seed, write as write_value
from coding_label_check import ORACLE
from pattern_review_fixture import declaration, ref


def write(path, value):
    if isinstance(value, bytes):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    else:
        write_value(path, value)


def scenario(directory, *, installed_consumer=None):
    review = Path(filesystem_path(Path(directory).resolve()))
    review.mkdir(parents=True, exist_ok=True)
    consumer = Path(filesystem_path(installed_consumer)) if installed_consumer is not None else review / 'consumer'
    consumer.mkdir(parents=True, exist_ok=installed_consumer is not None)
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    result = {'status': 'running', 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
              'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'workingInputsDigest': input_snapshot()['digest'], 'fixtureSourceSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'commands': [], 'scope': 'Installed-layout F4 creation/editing and independent actual .NET application checks. Fictional model/contracts/review; native HTTP/provider/client qualification is separate.'}
    started = time.perf_counter(); write(review / 'results.json', result)
    write(review / 'index.md', '# F4 incomplete review\n\nInspect [results](results.json) and output/. No completed fixture or human acceptance is inferred.\n')

    def run(name, args, expected=0, python=True):
        command = [sys.executable, *map(str, args)] if python else list(map(str, args))
        before = time.perf_counter()
        child = subprocess.run(command, cwd=native_path(consumer), capture_output=True, text=True, encoding='utf-8', timeout=120)
        write(review / 'output' / (name + '.stdout.txt'), child.stdout)
        write(review / 'output' / (name + '.stderr.txt'), child.stderr)
        result['commands'].append({'name': name, 'command': command, 'cwd': native_path(consumer), 'expectedExit': expected,
            'actualExit': child.returncode, 'elapsedSeconds': round(time.perf_counter() - before, 3),
            'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(), 'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        assert child.returncode == expected, name + ': expected ' + str(expected) + ', actual ' + str(child.returncode) + '; inspect retained output'
        try: return json.loads(child.stdout)
        except ValueError: return child.stdout

    def snap(name, paths):
        for p in paths:
            path = consumer / p
            if path.is_file(): write(review / 'snapshots' / name / p, path.read_bytes())

    try:
        if installed_consumer is None:
            for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
                shutil.copytree(filesystem_path(ROOT / 'extensions' / name), consumer / '.specify/extensions' / name,
                                ignore=shutil.ignore_patterns('__pycache__'))
        feature = seed(consumer)
        extensions = consumer / '.specify/extensions'; scripts = extensions / 'program-kit-governance/scripts'
        phase, pattern, scaffold = (scripts / n for n in ('phase_obligations.py', 'coding_patterns.py', 'coding_scaffold.py'))
        native = extensions / 'program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py'
        owners = {'core': 'src/Notes.Core/Notes.Core.csproj', 'runtime': 'src/Notes.Runtime/Notes.Runtime.csproj',
                  'api': 'src/Notes.Http/Notes.Http.csproj', 'provider': 'src/Notes.Store/Notes.Store.csproj',
                  'test': 'tests/Label.Tests/Label.Tests.csproj', 'frontend': 'web/app', 'generatedTypes': 'tools/openapi/labels/generated/types.ts'}
        graph = json.loads((consumer / 'eng/architecture.json').read_bytes())
        for key, role in [('runtime', 'implementation'), ('test', 'test')]:
            references = [owners['core']] + ([owners['runtime']] if key == 'test' else [])
            graph['runtimeComposition']['projects'].append({'path': owners[key], 'role': role, 'projectReferences': references,
                'responsibilities': [{'name': key + 'Labels', 'kind': 'runtime' if key == 'runtime' else 'test',
                                      'effects': [], **({'testSeams': ['pure-core']} if key == 'test' else {})}]})
            refs = ''.join('<ProjectReference Include="' + Path(native_path(consumer / r)).as_posix() + '" />' for r in references)
            write(consumer / owners[key], '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
                + ('<OutputType>Exe</OutputType>' if key == 'test' else '') + '<NuGetAudit>false</NuGetAudit></PropertyGroup><ItemGroup>'
                + refs + '<FrameworkReference Include="Microsoft.AspNetCore.App" /></ItemGroup></Project>')
        write(consumer / 'eng/architecture.json', graph)
        # These are attributable package declarations evaluated without restore.
        # The separate native qualifier owns actual Foundation API/provider proof.
        api = consumer / owners['api']
        api.write_text(api.read_text().replace('</Project>', '<ItemGroup>'
            '<PackageReference Include="Orbyss.Foundation.Json.AspNetCore" Version="0.3.6" />'
            '<PackageReference Include="Orbyss.Foundation.Web.ProblemDetails" Version="0.3.6" />'
            + '</ItemGroup></Project>'), encoding='utf-8')
        provider = consumer / owners['provider']
        provider.write_text(provider.read_text().replace('</Project>', '<ItemGroup>'
            '<PackageReference Include="Orbyss.Foundation.PostgreSql" Version="0.3.6" /></ItemGroup></Project>'), encoding='utf-8')
        adopted_path = consumer / 'docs/architecture/building-block-selection.json'
        adopted = json.loads(adopted_path.read_bytes())
        for key in ('runtime', 'test'):
            adopted['targets'].append({'id': key, 'kind': 'dotnet-project', 'path': owners[key], 'placement': {'owner': 'notes', 'decisionIds': ['notes-runtime']}})
        write(adopted_path, adopted)
        write(consumer / '.program-kit/managed.json', {'schemaVersion': 2, 'files': {}})
        write(consumer / 'web/app/package.json', {'name': 'fictional-labels', 'private': True, 'devDependencies': {'typescript': '7.0.2'}})
        write(consumer / 'eng/openapi-contracts.json', {'schemaVersion': 1, 'contracts': ['contracts/labels.contract.json']})
        write(consumer / 'contracts/labels.contract.json', {'identity': 'labels', 'generator': {'generatedTypes': owners['generatedTypes']}, 'application': {'directory': owners['frontend']}})
        write(feature / 'spec.md', '# Fictional sample label\nAn authenticated actor reads/updates one explicitly prepared label row in the notes owner.\n- **Specification roadmap entry**: RM-01\n')
        write(feature / 'plan.md', '# Fictional accepted label sample\nUse the Core label contracts, runtime orchestration, HTTP admission/mapping and owned PostgreSQL provider. Native client generation remains due. No retry or atomic write/read snapshot is promised.\n')
        tasks = (feature / 'tasks.md').read_text()
        lines=tasks.splitlines()
        lines=[('- [ ] T001 [US1] Realize the sample label across ' + ', '.join(owners.values()) + '.') if line.startswith('- [ ] T001') else
               '- [ ] T002 [US1] Verify label update/read, caller cancellation, failure propagation and scoped registration in tests/Label.Tests/Label.Tests.csproj.'
               if line.startswith('- [ ] T002') else line for line in lines]
        tasks='\n'.join(lines).replace('Owner lists private notes | Request owner notes and inspect result',
                                       'Actor reads/updates the prepared sample label | Update one label and observe its current value')+'\n'
        write(feature / 'tasks.md', tasks)
        schema = consumer / 'contracts/notes.schema.json'
        write(schema, {'type': 'object', 'required': ['policy'], 'additionalProperties': False, 'properties': {'policy': {'type': 'string'}}})
        model_path = consumer / 'docs/architecture/architecture-map.json'
        model = json.loads(model_path.read_bytes()); model['sources'][0]['sha256'] = hashlib.sha256(schema.read_bytes()).hexdigest()
        model['strategic_model']['contracts']=[{'id':'label-read','owner':'notes','kind':'query','status':'accepted','evidence':['notes-schema']},
                                               {'id':'label-update','owner':'notes','kind':'command','status':'accepted','evidence':['notes-schema']}]
        write(model_path, model)
        write(consumer / owners['test'].replace('Label.Tests.csproj', 'Program.cs'), ORACLE)
        write(consumer / 'tests/coding_label_check.py', (ROOT / 'tests/coding_label_check.py').read_bytes())
        write(consumer / 'tests/application_check.py', 'import subprocess,sys\nfrom pathlib import Path\nroot=Path.cwd()\nsys.path.insert(0,str(root/".specify/extensions/program-kit-dotnet/templates/dotnet/files/eng"))\nfrom owned_scratch import native_path\nproject=native_path(root/"tests/Label.Tests/Label.Tests.csproj")\ncode=subprocess.call(["dotnet","build",project,"-m:1","--nologo"],cwd=native_path(root))\nif code: raise SystemExit(code)\nraise SystemExit(subprocess.call(["dotnet","run","--project",project,"--no-build","--no-restore"],cwd=native_path(root)))\n')
        write(consumer / 'docs/patterns/invalid-label.txt', 'Deliberate invalid variant: omit the write, then return the prior stored value. The independent oracle must fail.\n')
        write(consumer / 'docs/architecture/label-pattern-review.md', '# Fictional source review\nBounded acceptance of source creation and the independently tested application capability. Real native HTTP/provider/client evaluation remains a separate required route. No actual human/product acceptance is asserted.\n')
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
        from typed_operation import FILES, RECIPE
        qualified_inputs = [ref('program-kit-dotnet/references/examples/typed-operation/' + n, 'extensions') for names in FILES.values() for n in names]
        qualified_inputs += [ref(p, 'extensions') for p in ('program-kit-dotnet/references/examples/typed-operation/client.ts',
            RECIPE.removeprefix('extensions/'), 'program-kit-dotnet/scripts/typed_operation.py', 'program-kit-dotnet/scripts/reconciliation.py',
            'program-kit-governance/scripts/coding_scaffold.py')]
        unit = declaration('local-label-realization', 'guidance.component-adoption.foundation-web-and-json')
        unit.update(when={'all': ['dotnet']}, route='bound-recipes', requiredContext=['request', 'model-owner', 'contract-owner', 'effective-projects', 'verification-owner'])
        unit['pattern'].update(semanticId='typed-label', compatibility={'profiles': ['dotnet'], 'frameworks': ['net10.0'],
            'packages': {'Orbyss.Foundation.Web.ProblemDetails': '0.3.6'}}, inputs=qualified_inputs,
            examples={'positive': [ref('program-kit-dotnet/references/examples/typed-operation/LabelOperations.cs', 'extensions')], 'negative': [ref('docs/patterns/invalid-label.txt')]},
            checks=[{'kind': 'toolkit', 'id': 'label-source'}], review=ref('docs/architecture/label-pattern-review.md'),
            limits='Source-realization mechanics and the independent .NET label application oracle only. Native HTTP/provider/generated-client execution requires its separate maintained qualifier.')
        write(consumer / 'docs/architecture/coding-patterns.json', {'schemaVersion': 1, 'sources': [], 'rules': {}, 'codingUnits': [unit]})
        from asset_sources import PACK
        check_inputs = ['.specify/extensions/' + r['path'] for r in qualified_inputs] + [
            '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/owned_scratch.py',
            '.specify/extensions/program-kit-governance/scripts/asset_sources.py']
        check_inputs += [p.relative_to(consumer).as_posix() for p in extensions.glob('*/' + PACK)]
        write(consumer / 'eng/verification.json', {'schemaVersion': 1, 'testGroups': [], 'toolkitChecks': [
            {'id': name, 'script': 'tests/coding_label_check.py', 'arguments': args,
             'inputs': check_inputs, 'timeoutSeconds': 90}
            for name, args in [('label-source', []), ('label-source-invalid', ['--invalid'])]] + [
            {'id': 'label-application', 'script': 'tests/application_check.py', 'arguments': [],
             'inputs': [owners[k] for k in ('core','runtime','test')] +
                       [str(Path(owners[k]).parent / n).replace('\\','/') for k in ('core','runtime') for n in FILES[k]] +
                       ['tests/Label.Tests/Program.cs'], 'timeoutSeconds': 90}]})
        write(feature / 'label-owners.json', owners)
        def command(action, scope='specs/001-notes'):
            return [phase, action, '--repository', consumer, '--feature-dir', scope, '--format', 'json', *(['--operation', 'list'] if scope.endswith('001-notes') else [])]
        def realization(action='preview', digest=None, selected='local-label-realization'):
            return [scaffold, action, '--repository', consumer, '--feature-dir', 'specs/001-notes', '--operation', 'list', '--unit', selected,
                    '--owners', 'specs/001-notes/label-owners.json', *(['--plan-digest', digest] if digest else [])]
        def checks(name, check, expected=0):
            reports = consumer / 'artifacts/tests/toolkit-runs'
            before_reports = set(reports.glob('*/result.json'))
            value = run(name, [native, '--repository', consumer, '--scope', 'Focused', '--check', check], expected)
            if expected:
                created = set(reports.glob('*/result.json')) - before_reports
                assert len(created) == 1, 'Independent negative needs its own actual execution'
                report = json.loads(created.pop().read_bytes())
                outcomes = [row for row in report['outcomes'] if row['check'] == check]
                assert len(outcomes) == 1 and outcomes[0]['status'] == 'failed' and outcomes[0]['exitCode'] != 0
                output = '\n'.join((consumer / p).read_text(encoding='utf-8') for p in outcomes[0]['evidence'])
                assert 'committed label representation' in output, 'Setup/compiler failure is not the intended behavioral red'
                result['commands'][-1]['independentBehaviorMarker'] = 'committed label representation'
                write(review / 'results.json', result)
            return value
        run('01-unqualified-realization', realization(), 2)
        checks('02-independent-pattern-positive', 'label-source')
        checks('03-independent-invalid-pattern', 'label-source-invalid', 2)
        run('04-bind-actual-pattern-proof', [pattern, 'bind-evidence', '--repository', consumer, '--feature-dir', 'specs/001-notes', '--operation', 'list', '--id', unit['id']])
        prepared = run('05-prepared-qualified-route', command('prepare'))
        assert next(u for u in prepared['coding']['skills'] if u['id'] == unit['id'])['realization']['available']
        state_before = (consumer / '.program-kit/managed.json').read_bytes()
        preview = run('06-inspect-source-preview', realization())
        paths = [a['path'] for a in preview['actions']]
        assert all(a['kind'] == 'create' and a['ownership'] == 'consumer' for a in preview['actions'])
        assert all(not (consumer / p).exists() for p in paths)
        write(review / 'snapshots/preview.json', preview)
        original_model = model_path.read_bytes(); changed = copy.deepcopy(model); changed['strategic_model']['bounded_contexts'] = []; write(model_path, changed)
        run('07-missing-model-owner-preserves-source', realization('apply', preview['planDigest']), 2); model_path.write_bytes(original_model)
        template = extensions / 'program-kit-dotnet/references/examples/typed-operation/LabelOperations.cs'
        from asset_sources import read as source_bytes, owner as asset_owner, packed, encoded, PACK
        component = asset_owner(template)
        original_template = source_bytes(template)
        original_pack = (component / PACK).read_bytes() if component else None
        if component:
            values = packed(component)
            values[template.relative_to(component).as_posix()] = original_template + b'\n// Changed qualified input\n'
            (component / PACK).write_bytes(encoded(values))
        else:
            template.write_bytes(original_template + b'\n// Changed qualified input\n')
        run('08-stale-selected-proof', realization(), 2)
        if component:
            (component / PACK).write_bytes(original_pack)
        else:
            template.write_bytes(original_template)
        destination = consumer / 'src/Notes.Runtime/LabelOperations.cs'
        write(destination, '// Consumer-authored collision; preserve this file.\n')
        run('09-destination-invalidates-preview', realization('apply', preview['planDigest']), 2)
        conflict = run('10-collision-preview', realization(), 2)
        assert conflict['conflicts']; snap('collision', ['src/Notes.Runtime/LabelOperations.cs'])
        assert all(not (consumer / p).exists() for p in paths if p != 'src/Notes.Runtime/LabelOperations.cs')
        destination.unlink()
        applied = run('11-create-consumer-source', realization('apply', preview['planDigest']))
        assert len(applied['created']) == len(paths)
        assert (consumer / '.program-kit/managed.json').read_bytes() == state_before
        snap('created', paths)
        rerun = run('12-identical-preview', realization())
        assert all(a['kind'] == 'unchanged' for a in rerun['actions'])
        noop = run('13-idempotent-apply', realization('apply', rerun['planDigest']))
        assert noop['transactionId'] is None and noop['created'] == []
        checks('14-actual-created-application', 'label-application')
        original_application = destination.read_bytes()
        destination.write_bytes(original_application.replace(b'await store.WriteAsync(value, cancellationToken);', b'// Deliberately omitted write.'))
        checks('15-actual-invalid-application', 'label-application', 2)
        snap('invalid-application', ['src/Notes.Runtime/LabelOperations.cs'])
        destination.write_bytes(original_application + b'\n// Consumer-authored customization retained by regeneration.\n')
        checks('16-manual-customization-application', 'label-application')
        snap('customized', paths)
        run('17-regeneration-conflict-preserves-customization', realization(), 2)
        assert destination.read_bytes().endswith(b'// Consumer-authored customization retained by regeneration.\n')
        run('18-manual-edit-reconciliation', command('reconcile'))
        task_bytes = (feature / 'tasks.md').read_bytes()
        write(consumer / 'loose/Unowned.cs', 'namespace Fixture; public sealed class Unowned {}\n')
        snap('unowned-change', ['loose/Unowned.cs'])
        blocked = run('19-manual-unowned-change', command('reconcile'), 2)
        assert any(b['code'] == 'PKC011' for b in blocked['coding']['blockers'])
        finish = run('20-unowned-change-blocks-finish', [*command('finish'), '--handoff'], 2)
        assert not finish['canProceed'] and (feature / 'tasks.md').read_bytes() == task_bytes
        (consumer / 'loose/Unowned.cs').unlink()
        run('21-unsupported-recipe-manual-route', realization(selected='http-operation-contracts'), 2)
        browser = run('22-unrelated-browser', command('prepare', 'specs/002-browser'))
        assert unit['id'] not in {u['id'] for u in browser['coding']['skills']}
        run('23-restored-context', command('reconcile'))
        result.update(status='passed', elapsedSeconds=round(time.perf_counter() - started, 3),
                      finalWorkingInputsDigest=input_snapshot()['digest'], retainedConsumer=native_path(consumer))
        assert result['workingInputsDigest'] == result['finalWorkingInputsDigest'], 'Maintained source changed during fixture execution'
        write(review / 'index.md', '''# F4 guided actual-output review

This fictional single-label operation reuses the F2 notes-owner preparation fixture and F3 local qualification. Authoring/decisions/review are simulated. Actual commands run installed-layout copies; actual .NET checks execute the owned label capability. No stopped consumer, worker or paid/provider account is used.

1. Inspect [unqualified rejection](output/01-unqualified-realization.stdout.txt), [actual source check](output/02-independent-pattern-positive.stdout.txt), [independent invalid check](output/03-independent-invalid-pattern.stdout.txt) and [bound evidence](output/04-bind-actual-pattern-proof.stdout.txt). The fixed [C# oracle](consumer/tests/Label.Tests/Program.cs) supplies expected values, sequence, cancellation, faults and scope identity independently of pattern metadata.
2. Open [prepared qualified route](output/05-prepared-qualified-route.stdout.txt), [owner input](consumer/specs/001-notes/label-owners.json) and [preview](output/06-inspect-source-preview.stdout.txt). Inspect every diff, absent-byte precondition, consumer ownership, exact selected unit/evidence and remaining integration duties. API owns HTTP admission/mapping; Core owns ports; runtime owns orchestration; provider owns its query. Native settings binding, generated types, feature registration and meaningful tests remain due.
3. Read [missing owner](output/07-missing-model-owner-preserves-source.stdout.txt), [stale proof](output/08-stale-selected-proof.stdout.txt), [stale destination](output/09-destination-invalidates-preview.stdout.txt) and [collision diff](output/10-collision-preview.stdout.txt). Compare the [preserved collision](snapshots/collision/src/Notes.Runtime/LabelOperations.cs). No other proposed source was created on these failures.
4. Follow [apply](output/11-create-consumer-source.stdout.txt), [unchanged preview](output/12-identical-preview.stdout.txt) and [idempotent apply](output/13-idempotent-apply.stdout.txt). Inspect [created Core](snapshots/created/src/Notes.Core/ILabelOperations.cs), [runtime](snapshots/created/src/Notes.Runtime/LabelOperations.cs), [endpoint](snapshots/created/src/Notes.Http/LabelEndpoint.cs) and [provider](snapshots/created/src/Notes.Store/PostgreSqlLabelStore.cs). The native [managed state](consumer/.program-kit/managed.json) stays byte-identical; these new business files never enter toolkit ownership.
5. Compare [created application check](output/14-actual-created-application.stdout.txt), [actual invalid source](snapshots/invalid-application/src/Notes.Runtime/LabelOperations.cs), [failed application check](output/15-actual-invalid-application.stdout.txt) and [manual customization check](output/16-manual-customization-application.stdout.txt). Native verification retains the actual streams and unresolved failure/recovery history. The independent expected `edited` result catches an omitted write; generator metadata cannot manufacture it.
6. Inspect [regeneration conflict](output/17-regeneration-conflict-preserves-customization.stdout.txt), [customized source](snapshots/customized/src/Notes.Runtime/LabelOperations.cs) and [manual reconciliation](output/18-manual-edit-reconciliation.stdout.txt). Ordinary editing is supported. [Unowned C#](snapshots/unowned-change/loose/Unowned.cs) triggers [reconciliation](output/19-manual-unowned-change.stdout.txt) and [completion rejection](output/20-unowned-change-blocks-finish.stdout.txt) while preserving tasks/progress. [Unsupported realization](output/21-unsupported-recipe-manual-route.stdout.txt) does not remove the unit's manual route or mandatory duties. [Unrelated browser scope](output/22-unrelated-browser.stdout.txt) excludes the label pattern; [restored context](output/23-restored-context.stdout.txt) is ready for its remaining native/integration duties.

## Rerun and proof limits

Run `python tests/scaffold_review_fixture.py --review`. Each run retains a new consumer, both streams, exact commands/exits/timings/hashes and source identities in [results](results.json). Existing reviews are never removed. Native package/HTTP/PostgreSQL/options/generated-client/browser execution belongs to the separate maintained typed-operation qualifier and is reported in the F4 checkpoint. This guide alone proves only source realization, native target-free context, independent .NET Core/runtime behavior and editing/ownership mechanics. No automatic registration, schema deployment, transaction/retry guarantee, arbitrary semantic analysis, packaged adoption, agent obedience or human product acceptance follows. Framework updates and complete seed-family proof retain their normal F5/F8 owners.
''')
        return result
    except BaseException as error:
        result.update(status='failed', failureType=type(error).__name__, elapsedSeconds=round(time.perf_counter() - started, 3))
        raise
    finally:
        write(review / 'results.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--review', action='store_true'); args = parser.parse_args()
    if args.review:
        directory = ROOT / 'artifacts/f4-review' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])
        print('Retained F4 review: ' + str(directory / 'index.md'), flush=True)
        scenario(directory)
    else:
        with FixtureDirectory() as directory: scenario(directory)


if __name__ == '__main__': main()

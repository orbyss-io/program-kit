"""F2 retained installed-layout preparation/reconciliation fixture; no coding agent.

Fictional task/decision setup is explicit. Native MSBuild evaluates real input but
never restores/builds these illustrative projects or starts a database/application.
"""
from __future__ import annotations
import argparse
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
from owned_fixture import FixtureDirectory, filesystem_path


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def seed(consumer):
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
    import task_draft
    feature = consumer / 'specs/001-notes'
    write(consumer / '.gitignore', '.specify/\nartifacts/\n**/bin/\n**/obj/\n')
    write(feature / 'spec.md', '<!-- program-kit:story-delivery-v1 -->\n# Private notes\nA signed-in owner lists only their notes.\n- **Specification roadmap entry**: RM-01\n')
    write(feature / 'plan.md', '<!-- program-kit:story-delivery-v1 -->\n# Notes query\nUse the accepted Notes owner. HTTP admission delegates to an owned query and PostgreSQL provider.\nProjects: src/Notes.Core/Notes.Core.csproj, src/Notes.Http/Notes.Http.csproj, src/Notes.Store/Notes.Store.csproj.\nNo browser or domain-event reactions are required.\n')
    tasks = '''# Fictional task plan
<!-- program-kit:story-delivery-v1 -->
- [ ] T001 [US1] Implement HTTP query in src/Notes.Http/Endpoint.cs and provider query in src/Notes.Store/Reader.cs; use src/Notes.Core/Notes.Core.csproj.
- [ ] T002 [US1] Verify owner isolation and cancellation through tests/NotesTests.cs.

## Operation dependency map
| Operation | Depends on operations |
|-----------|-----------------------|
| list | none |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | list | none | none | none |
| T002 | list | T001 | none | none |

## Story delivery map
| Story | Operations | Useful outcome | Independent walkthrough | Active minutes to review | Larger-story rationale |
|-------|------------|----------------|-------------------------|--------------------------|------------------------|
| US1 | list | Owner lists private notes | Request owner notes and inspect result | 45 | none |
'''
    write(feature / 'tasks.md', tasks)
    write(consumer / '.program-kit/specification-intake/RM-01/brief.json', {'architectureScope': ['notes'], 'decisions': []})
    write(consumer / 'docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet', 'typescript-web']})
    schema = consumer / 'contracts/notes.schema.json'
    write(schema, {'type': 'object', 'required': ['ownerId'], 'properties': {'ownerId': {'type': 'string'}}})
    write(consumer / 'docs/architecture/architecture-map.json', {
        'elements': [{'id': 'notes', 'type': 'bounded-context', 'decision_refs': ['notes-runtime']},
                     {'id': 'browser', 'type': 'bounded-context', 'decision_refs': []}],
        'decisions': [{'id': 'notes-runtime', 'status': 'Accepted'}],
        'sources': [{'id': 'notes-schema', 'path': 'contracts/notes.schema.json', 'sha256': hashlib.sha256(schema.read_bytes()).hexdigest()}],
        'strategic_model': {'bounded_contexts': [{'element': 'notes', 'status': 'accepted'}, {'element': 'browser', 'status': 'accepted'}],
                           'contracts': [{'id': 'notes-query', 'owner': 'notes', 'kind': 'query', 'status': 'accepted', 'evidence': ['notes-schema']}]}})
    rows = []
    for name, role, kind, effect in [('Notes.Core', 'core', 'contract', []), ('Notes.Http', 'implementation', 'http', ['http']),
                                     ('Notes.Store', 'provider', 'persistence', ['persistence']), ('Other', 'helper', 'pure-helper', [])]:
        relative = f'src/{name}/{name}.csproj'
        refs = [] if name in ('Notes.Core', 'Other') else ['src/Notes.Core/Notes.Core.csproj']
        rows.append({'path': relative, 'role': role, 'projectReferences': refs,
                     'responsibilities': [{'name': name.replace('.', '') + 'Work', 'kind': kind, 'effects': effect}]})
        sdk = 'Microsoft.NET.Sdk.Web' if name == 'Notes.Http' else 'Microsoft.NET.Sdk'
        extra = '<ItemGroup><ProjectReference Include="../Notes.Core/Notes.Core.csproj" /></ItemGroup>' if refs else ''
        if name == 'Notes.Store':
            extra += '<Import Project="../../provider.props" />'
        write(consumer / relative, f'<Project Sdk="{sdk}"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>{extra}</Project>')
        write(consumer / f'src/{name}/Marker.cs', 'namespace Fixture; internal sealed class Marker {}\n')
    write(consumer / 'provider.props', '<Project><ItemGroup Condition="\'$(Configuration)\' == \'Debug\'"><PackageReference Include="Npgsql" Version="10.0.0" /></ItemGroup></Project>')
    write(consumer / 'src/Notes.Http/Endpoint.cs', '// Small transport fixture; no business behavior claimed.\nnamespace Fixture; internal sealed class Endpoint {}\n')
    write(consumer / 'src/Notes.Store/Reader.cs', '// Owned query and cancellation are preparation duties; runtime implementation is later.\nnamespace Fixture; internal sealed class Reader {}\n')
    write(consumer / 'eng/architecture.json', {'runtimeComposition': {'projects': rows, 'bindings': []}})
    write(consumer / 'docs/architecture/building-block-selection.json', {'status': 'Accepted',
        'targets': [{'id': row['path'].split('/')[1], 'kind': 'dotnet-project', 'path': row['path'],
                     'placement': {'owner': 'notes', 'decisionIds': ['notes-runtime']}}
                    for row in rows if row['path'].startswith('src/Notes')], 'instances': []})
    write(consumer / 'eng/Invoke-RepositoryVerification.ps1', 'throw "F2 routing fixture: application acceptance intentionally unimplemented"\n')
    browser = consumer / 'specs/002-browser'
    write(browser / 'spec.md', '# Browser presentation\nFrontend-only browser presentation.\n- **Specification roadmap entry**: RM-02\n')
    write(browser / 'plan.md', 'A TypeScript browser presentation; no backend changes.\n')
    write(browser / 'tasks.md', '- [ ] T101 Style the browser page.\n')
    write(consumer / '.program-kit/specification-intake/RM-02/brief.json', {'architectureScope': ['browser'], 'decisions': []})
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Fictional Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fictional F2 inputs']):
        subprocess.run(['git', *args], cwd=consumer, check=True, capture_output=True, timeout=30)
    baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=consumer, text=True, timeout=30).strip()
    # Same explicit fictional setup convention as maintained story-delivery tests.
    # This does not exercise or claim ratification or human product acceptance.
    with patch.object(task_draft, 'require_policy'):
        task_draft.transition(consumer, feature, {'action': 'initialize', 'baseline': baseline,
            'source': 'simulated F2 fixture requester; no human product acceptance'}, now=0)
    task_draft.checkpoint(browser, {'baseline': baseline, 'outcome': 'Fictional browser preparation', 'next': 'Prepare presentation'})
    return feature


def scenario(directory):
    review = Path(filesystem_path(Path(directory).resolve()))
    review.mkdir(parents=True, exist_ok=True)
    consumer = review / 'consumer'
    consumer.mkdir()
    from datetime import datetime, timezone
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    result = {'status': 'running', 'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'workingInputsDigest': input_snapshot()['digest'], 'fixtureSourceSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'commands': [], 'scope': 'F2 installed-layout routing and real target-free MSBuild evaluation; fictional inputs, no application or agent execution'}
    write(review / 'results.json', result)
    started = time.perf_counter()

    def run(name, args, expected=0):
        before = time.perf_counter()
        child = subprocess.run([sys.executable, *map(str, args)], cwd=consumer, capture_output=True, text=True, encoding='utf-8', timeout=90)
        write(review / 'output' / (name + '.stdout.txt'), child.stdout)
        write(review / 'output' / (name + '.stderr.txt'), child.stderr)
        result['commands'].append({'name': name, 'command': [sys.executable, *map(str, args)], 'expectedExit': expected,
            'actualExit': child.returncode, 'elapsedSeconds': round(time.perf_counter()-before, 3),
            'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(), 'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        if child.returncode != expected:
            raise AssertionError(name + ': expected ' + str(expected) + ', actual ' + str(child.returncode) + '; inspect retained output')
        return json.loads(child.stdout) if child.stdout.lstrip().startswith('{') else child.stdout

    try:
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(filesystem_path(ROOT / 'extensions' / name), consumer / '.specify/extensions' / name, ignore=shutil.ignore_patterns('__pycache__'))
        feature = seed(consumer)
        script = consumer / '.specify/extensions/program-kit-governance/scripts/phase_obligations.py'
        def command(action, feature='specs/001-notes', operation=True):
            return [script, action, '--repository', consumer, '--feature-dir', feature, '--format', 'json', *(['--operation', 'list'] if operation else [])]
        before = run('01-prepared', command('prepare'))
        skills = {s['id'] for s in before['coding']['skills']}
        assert {'http-operation-contracts', 'persistence-adoption', 'owned-provider-contract'} <= skills
        assert 'browser-experience' not in skills
        store = next(p for p in before['coding']['projects'] if p['path'].endswith('Notes.Store.csproj'))
        assert {'id': 'Npgsql', 'version': '10.0.0'} in store['packages'], 'Imported conditional package was not evaluated'
        brief = run('02-bounded-brief', [script, 'prepare', '--repository', consumer, '--feature-dir', 'specs/001-notes', '--operation', 'list'])
        assert len(brief.split()) < 1600, 'Ordinary coding brief exceeded its unchanged bound'
        browser = run('03-browser', command('prepare', 'specs/002-browser', False))
        assert 'persistence-adoption' not in {s['id'] for s in browser['coding']['skills']}
        catalog = script.parent.parent / 'references/phase-obligations.json'
        original = catalog.read_bytes()
        data = json.loads(original)
        data['codingUnits'].append({'id': 'fixture-query-review', 'ruleIds': ['principle.compilation-boundaries'],
            'when': {'all': ['persistence']}, 'requiredContext': ['contract-owner'], 'route': 'manual-edit'})
        write(catalog, data)
        extended = run('04-added-unit', command('prepare'))
        assert 'fixture-query-review' in {s['id'] for s in extended['coding']['skills']}
        excluded = run('05-added-unit-excluded', command('prepare', 'specs/002-browser', False))
        assert 'fixture-query-review' not in {s['id'] for s in excluded['coding']['skills']}
        write(review / 'snapshots/registry-added-unit.json', data['codingUnits'][-1])
        focused = run('04b-focused-unit', [*command('prepare'), '--unit', 'fixture-query-review'])
        assert len(focused['coding']['skills']) == 1 and focused['coding']['skills'][0]['rules']
        data['codingUnits'][-1]['route'] = 'bound-recipes'
        write(catalog, data)
        unsupported = run('04c-missing-recipe', command('prepare'), 2)
        assert any(b['code'] == 'PKC004' for b in unsupported['coding']['blockers'])
        catalog.write_bytes(original)
        model_path = consumer / 'docs/architecture/architecture-map.json'
        model_bytes = model_path.read_bytes()
        model = json.loads(model_bytes)
        model['strategic_model']['bounded_contexts'] = []
        write(model_path, model)
        missing = run('06-missing-model-owner', command('prepare'), 2)
        assert any(b.get('context') == 'model-owner' for b in missing['coding']['blockers'])
        model_path.write_bytes(model_bytes)
        contract = consumer / 'contracts/notes.schema.json'
        contract_bytes = contract.read_bytes()
        write(contract, '{}\n')
        stale = run('07-stale-contract', command('prepare'), 2)
        assert any(b.get('context') == 'contract-owner' for b in stale['coding']['blockers'])
        contract.write_bytes(contract_bytes)
        verify = consumer / 'eng/Invoke-RepositoryVerification.ps1'
        verify_bytes = verify.read_bytes()
        verify.unlink()
        missing = run('08-missing-verification', command('prepare'), 2)
        assert any(b.get('context') == 'verification-owner' for b in missing['coding']['blockers'])
        verify.write_bytes(verify_bytes)
        project = consumer / 'src/Notes.Http/Notes.Http.csproj'
        project_bytes = project.read_bytes()
        write(project, project.read_text().replace('</Project>', '<ItemGroup><ProjectReference Include="../Notes.Store/Notes.Store.csproj" /></ItemGroup></Project>'))
        conflict = run('09-dependency-conflict', command('prepare'), 2)
        assert any(b['code'] == 'PKC010' for b in conflict['coding']['blockers'])
        independent = run('09b-independent-browser', command('reconcile', 'specs/002-browser', False))
        assert 'src/Notes.Http/Notes.Http.csproj' in independent['coding']['independentChangedInputs']
        assert not independent['coding']['projects']
        project.write_bytes(project_bytes)
        store_project = consumer / 'src/Notes.Store/Notes.Store.csproj'
        planned_project = store_project.with_suffix('.planned')
        store_project.rename(planned_project)
        missing_effective = run('09c-missing-effective-project', command('prepare'), 2)
        assert any(b.get('context') == 'effective-projects' for b in missing_effective['coding']['blockers'])
        assert 'persistence-adoption' in {s['id'] for s in missing_effective['coding']['skills']}
        setup = run('09d-project-setup-only', [*command('prepare'), '--stage', 'setup'])
        assert setup['coding']['nativeContext']['sourceReady'] is False
        planned_project.rename(store_project)
        # A manual source change in a project absent from plan/tasks must be found
        # by ordinary progress completion, not by an explicit --affected-path hint.
        manual = consumer / 'src/Other/Surprise.cs'
        write(manual, 'using Npgsql; // A new unplanned persistence responsibility needs source/owner review.\nnamespace Fixture; internal sealed class Surprise {}\n')
        progress = run('10-manual-progress', command('finish', operation=False), 2)
        assert progress['status'] == 'needs-attention'
        assert any(b['code'] == 'PKC012' for b in progress['coding']['blockers'])
        assert any(p['path'] == 'src/Other/Other.csproj' for p in progress['coding']['projects'])
        assert 'src/Other/Surprise.cs' in progress['coding']['changedInputs']
        task_path = feature / 'tasks.md'
        task_bytes = task_path.read_bytes()
        write(task_path, task_path.read_text().replace('- [ ]', '- [X]'))
        write(review / 'snapshots/manually-completed-tasks.md', task_path.read_text())
        write(review / 'engineering-request.json', {'action': 'engineering', 'checkpoint': 'US1', 'checks': []})
        direct = run('10b-direct-task-completion', [script.with_name('task_draft.py'), 'delivery', '--repository', consumer,
                     '--feature-dir', 'specs/001-notes', '--content-file', review / 'engineering-request.json'], 2)
        assert 'PKC012' in direct
        task_path.write_bytes(task_bytes)
        write(review / 'snapshots/manual-source.cs', manual.read_text())
        manual.unlink()
        restored = run('11-removed-manual-change', command('reconcile'))
        assert not any(p['path'] == 'src/Other/Other.csproj' for p in restored['coding']['projects'])
        other = consumer / 'src/Other/Other.csproj'
        other_bytes = other.read_bytes()
        write(other, other.read_text().replace('</Project>', '<ItemGroup><Compile Include="../../shared/Surprise.cs" /></ItemGroup></Project>'))
        linked = consumer / 'shared/Surprise.cs'
        write(linked, 'using Npgsql;\nnamespace Fixture; internal sealed class Surprise {}\n')
        linked_result = run('11b-linked-source', command('reconcile'), 2)
        assert any(b['code'] == 'PKC012' and b.get('project') == 'src/Other/Other.csproj' for b in linked_result['coding']['blockers'])
        assert 'persistence-adoption' in {s['id'] for s in linked_result['coding']['skills']}
        linked.unlink()
        other.write_bytes(other_bytes)
        unsupported_framework = run('11c-undeclared-framework', [*command('prepare'), '--framework', 'net9.0'], 2)
        assert any(b['code'] == 'PKC016' for b in unsupported_framework['coding']['blockers'])
        # Missing source support is an actual command failure, not a green unit list.
        canonical = consumer / '.specify/extensions/program-kit-governance/references/modularity-and-contracts.md'
        canonical_bytes = canonical.read_bytes()
        canonical.rename(canonical.with_suffix('.missing'))
        run('12-missing-canonical-source', command('prepare'), 2)
        canonical.with_suffix('.missing').rename(canonical)
        assert canonical.read_bytes() == canonical_bytes
        write(review / 'snapshots/prepared-before.json', before['coding'])
        write(review / 'snapshots/prepared-after-extension.json', extended['coding'])
        write(review / 'snapshots/extension.diff', ''.join(difflib.unified_diff(
            json.dumps([s['id'] for s in before['coding']['skills']], indent=2).splitlines(True),
            json.dumps([s['id'] for s in extended['coding']['skills']], indent=2).splitlines(True), 'before', 'added-declaration')))
        result.update(status='passed', elapsedSeconds=round(time.perf_counter()-started, 3), workingInputsUnchanged=input_snapshot()['digest'] == result['workingInputsDigest'])
        write(review / 'index.md', '''# F2 guided output review

This fictional private-notes task demonstrates **preparation and reconciliation** using copied installed extension commands and real target-free MSBuild evaluation. It does not implement or run the application. All task/decision setup is simulated, including initialization that bypasses ratification only in this fixture's setup.

1. Open [prepared context](snapshots/prepared-before.json). Inspect `scope`, `inputs`, `architecture`, `contractOwners`, `profiles`, `projects`, `skills` and `excludedSkills`. The `list` operation selects endpoint + provider duties together. Each skill has canonical text/provenance, reasons, manual-edit/recipe routes, and evaluation duties. `applicationObserved` remains false.
2. Compare the [ordinary brief](output/02-bounded-brief.stdout.txt) with the [browser context](output/03-browser.stdout.txt). Backend duties must stay out of the browser task; the detailed view retains exclusions and links.
3. Inspect the Store project's evaluated packages in step 1 and [provider.props](consumer/provider.props). Npgsql 10.0.0 comes from the actual Debug import, not a parser guess. This illustrative pin is not a runtime compatibility qualification. Roles remain declared; evaluated Compile and dependency facts are separately identified.
4. Open the [added declaration](snapshots/registry-added-unit.json), [skill-list difference](snapshots/extension.diff), [extended context](output/04-added-unit.stdout.txt) and [excluded context](output/05-added-unit-excluded.stdout.txt). Only registry data changes; no composer algorithm changes or supplied code execution. This is extension/routing proof, not F3 pattern qualification.
   The [focused unit](output/04b-focused-unit.stdout.txt) is the actual agent lookup. The [unsupported recipe route](output/04c-missing-recipe.stdout.txt) must fail rather than silently substituting manual work.
5. Deliberate negatives: [missing model owner](output/06-missing-model-owner.stdout.txt), [stale schema evidence](output/07-stale-contract.stdout.txt), [missing verification owner](output/08-missing-verification.stdout.txt), [dependency conflict](output/09-dependency-conflict.stdout.txt), and [missing canonical source](output/12-missing-canonical-source.stdout.txt). Each command must exit 2. Inspect the actual owner and repair instruction, not just the exit.
   During the dependency conflict, [independent browser reconciliation](output/09b-independent-browser.stdout.txt) still succeeds and explains its excluded changed inputs.
   [Missing effective project](output/09c-missing-effective-project.stdout.txt) must block source production while retaining the declared persistence duty. [Setup-only output](output/09d-project-setup-only.stdout.txt) permits project materialization but explicitly leaves `sourceReady` false. A planned graph cannot substitute for evaluated settings.
6. Open [manual source snapshot](snapshots/manual-source.cs) and [ordinary progress output](output/10-manual-progress.stdout.txt). `Other` is absent from plan/tasks but the retained-baseline comparison finds its new source and evaluated owner, then returns needs-attention for its unresolved pure/runtime boundary. Even [manually checked tasks](snapshots/manually-completed-tasks.md) cannot bypass the [direct completion command](output/10b-direct-task-completion.stdout.txt). [After removal](output/11-removed-manual-change.stdout.txt), it no longer selects that project. Pending tasks remain pending; application acceptance never runs.
   The [linked-source negative](output/11b-linked-source.stdout.txt) must also select persistence and flag its pure owner: evaluated Compile membership, not physical folders, owns the file. The [undeclared-framework negative](output/11c-undeclared-framework.stdout.txt) must reject net9.0 before an override can invent support; these projects declare net10.0.
7. Inspect [results](results.json): exact commands, expected/actual exits, stream hashes, timings, source commit and working-input digest. Both streams remain under `output/`. The restored consumer and all review snapshots stay available until human review is finished.

## Rerun

From the feature worktree: `python tests/coding_review_fixture.py --review`. It creates another unique retained run. To inspect an individual command, copy its exact invocation from results.json; `prepare --format json` is read-only. Do not run the fictional application's verification command: it deliberately rejects an application-acceptance claim.

## Proof limits

No archive-install/update qualification, compilation, actual endpoint/PostgreSQL/browser execution, selected API runtime compatibility, semantic purity, agent obedience, F3 learning/qualification or F4 generation is established. Lexical discovery can miss indirect, generated or aliased behavior and can overselect; unresolved semantic ownership needs ordinary source review. No global write interception or human product acceptance is claimed. F1's package-budget overrun remains independent.
''')
        return result
    except BaseException as error:
        result.update(status='failed', error=str(error), elapsedSeconds=round(time.perf_counter()-started, 3))
        raise
    finally:
        write(review / 'results.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true')
    args = parser.parse_args()
    if args.review:
        from datetime import datetime, timezone
        output = ROOT / 'artifacts/f2-review' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6])
        print('Retained review: ' + str(output / 'index.md'), flush=True)
        scenario(output)
    else:
        with FixtureDirectory(prefix='coding-review-', native=True) as output:
            scenario(output)


if __name__ == '__main__':
    main()

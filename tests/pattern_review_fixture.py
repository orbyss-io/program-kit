"""F3 guided installed-command fixture. Fictional reviews, real scoped check output.

The tiny Python query proves owner filtering only, not .NET/PostgreSQL/HTTP behavior.
No pattern submission, provider or coding agent is dispatched by preparation.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
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
from owned_fixture import FixtureDirectory, filesystem_path
from coding_review_fixture import seed, write


def ref(path, root='repository'):
    return {'root': root, 'path': path}


def declaration(identity, rule, *, replaces=()):
    return {'id': identity, 'ruleIds': [rule], 'when': {'all': ['persistence'], 'not': ['web']},
            'requiredContext': ['request', 'contract-owner'], 'route': 'manual-edit', 'pattern': {
                'schemaVersion': 1, 'semanticId': 'notes-owner-query', 'version': '1.0.0',
                'owner': 'fictional notes pattern reviewer', 'status': 'active',
                'invariantRuleIds': ['principle.compilation-boundaries'],
                'compatibility': {'profiles': ['dotnet'], 'frameworks': ['net10.0'], 'packages': {'Npgsql': '10.0.0'}},
                'alternatives': [], 'replaces': list(replaces),
                'inputs': [ref('src/query_example.py')],
                'examples': {'positive': [ref('src/query_example.py')], 'negative': [ref('src/query_invalid.py')]},
                'checks': [{'kind': 'toolkit', 'id': 'notes-query'}],
                'review': ref('docs/architecture/notes-pattern-review.md'), 'evidence': [],
                'limits': 'Only pure Python owner-filter behavior and declared applicability are demonstrated. No native API, database, performance or human product acceptance.',
                'provenance': 'Fictional F3 review setup; actual maintained checks run independently. No real consumer approval is asserted.'}}


def scenario(directory):
    review = Path(filesystem_path(Path(directory).resolve()))
    review.mkdir(parents=True, exist_ok=True)
    consumer = review / 'consumer'
    consumer.mkdir()
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    result = {'status': 'running', 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
              'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'workingInputsDigest': input_snapshot()['digest'], 'fixtureSourceSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'commands': [], 'scope': 'Installed-layout F3 pattern inputs, real maintained Python owner-filter check, target-free .NET evaluation; fictional review/authoring setup.'}
    started = time.perf_counter()
    write(review / 'results.json', result)
    write(review / 'index.md', '# F3 incomplete review run\n\nOpen [actual results](results.json) and the named streams under output/. This run has not completed; no success or human acceptance is inferred. Failures and the disposable consumer are retained.\n')

    def run(name, args, expected=0):
        before = time.perf_counter()
        child = subprocess.run([sys.executable, *map(str, args)], cwd=consumer, capture_output=True, text=True, encoding='utf-8', timeout=90)
        write(review / 'output' / (name + '.stdout.txt'), child.stdout)
        write(review / 'output' / (name + '.stderr.txt'), child.stderr)
        result['commands'].append({'name': name, 'command': [sys.executable, *map(str, args)], 'cwd': str(consumer),
            'expectedExit': expected, 'actualExit': child.returncode, 'elapsedSeconds': round(time.perf_counter() - before, 3),
            'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(), 'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        assert child.returncode == expected, name + ': inspect retained actual output; expected ' + str(expected) + ', actual ' + str(child.returncode)
        try:
            return json.loads(child.stdout)
        except ValueError:
            return child.stdout

    try:
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(filesystem_path(ROOT / 'extensions' / name), consumer / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('__pycache__'))
        feature = seed(consumer)
        extensions = consumer / '.specify/extensions'
        scripts = extensions / 'program-kit-governance/scripts'
        phase, pattern = scripts / 'phase_obligations.py', scripts / 'coding_patterns.py'
        catalog_path = scripts.parent / 'references/phase-obligations.json'
        local_path = consumer / 'docs/architecture/coding-patterns.json'
        native = extensions / 'program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py'
        def command(name='prepare', scope='specs/001-notes', operation=True):
            return [phase, name, '--repository', consumer, '--feature-dir', scope, '--format', 'json',
                    *(['--operation', 'list'] if operation else [])]
        def pattern_command(name, identity='local-notes-query'):
            return [pattern, name, '--repository', consumer, '--feature-dir', 'specs/001-notes', '--operation', 'list', '--id', identity]
        def choice(identity, version='1.0.0', reason='Use the reviewed private owner-filter specialization for this notes operation.'):
            write(feature / 'plan.md', plan + '\n<!-- program-kit:pattern-choices -->\n' + json.dumps({
                'notes-owner-query': {'id': identity, 'version': version, 'reason': reason}})
                + '\n<!-- /program-kit:pattern-choices -->\n')
        def checks(name, identity='notes-query', expected=0):
            return run(name, [native, '--repository', consumer, '--scope', 'Focused', '--check', identity], expected)

        write(consumer / 'src/query_example.py', 'def notes_for(owner, rows):\n    return [r["id"] for r in rows if r["owner"] == owner]\n')
        write(consumer / 'src/query_invalid.py', 'def notes_for(owner, rows):\n    return [r["id"] for r in rows]\n')
        write(consumer / 'src/query_alternative.py', 'def notes_for(owner, rows):\n    result = []\n    for row in rows:\n        if row["owner"] == owner:\n            result.append(row["id"])\n    return result\n')
        write(consumer / 'tests/query_pattern_check.py', '''"""Independent fixed oracle; does not derive expected values from pattern metadata."""
import importlib.util
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
name = 'query_invalid.py' if '--invalid' in sys.argv else 'query_alternative.py' if '--alternative' in sys.argv else 'query_example.py'
spec = importlib.util.spec_from_file_location('query', root / 'src' / name)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rows = [{'id': 'n1', 'owner': 'alice'}, {'id': 'n2', 'owner': 'bob'}, {'id': 'n3', 'owner': 'alice'}]
assert module.notes_for('alice', rows) == ['n1', 'n3'], 'owner isolation failed'
assert module.notes_for('bob', rows) == ['n2'], 'other owner isolation failed'
assert module.notes_for('nobody', rows) == [], 'empty owner query failed'
assert module.notes_for('alice', []) == [], 'empty collection failed'
print('4 independent owner-filter assertions passed; no database/native runtime acceptance.')
''')
        config = {'schemaVersion': 1, 'testGroups': [], 'toolkitChecks': [
            {'id': identity, 'script': 'tests/query_pattern_check.py', 'arguments': arguments,
             'inputs': ['src/query_example.py', 'src/query_invalid.py', 'src/query_alternative.py'], 'timeoutSeconds': 20}
            for identity, arguments in [('notes-query', []), ('notes-query-invalid', ['--invalid']), ('notes-query-alternative', ['--alternative'])]]}
        write(consumer / 'eng/verification.json', config)
        write(consumer / 'docs/architecture/notes-pattern-review.md', '# Fictional ordinary source review\nThe independent oracle fixes expected owner results. This simulated reviewer accepts only this tiny pure-Python semantic example. Provider/HTTP/native application behavior remains due.\n')
        write(consumer / 'docs/patterns/private-query.md', 'LOCAL_OWNER_FILTER: filter by the admitted owner before returning query results. Preserve accepted model/contracts and use the selected provider checks. This fixture qualifies only its tiny Python example.\n')
        write(consumer / 'docs/private-unrelated.md', 'PRIVATE_CANARY_DO_NOT_EXPORT\n')
        plan = (feature / 'plan.md').read_text()
        base = run('01-f2-route-before-patterns', command())
        run('02-draft-submission', [pattern, 'draft', '--repository', consumer, '--submission', 'docs/patterns/private-query.md',
            '--id', 'local-notes-query', '--invariant', 'principle.compilation-boundaries', '--output', 'artifacts/local-pattern-draft.json'])
        assert load(consumer / 'artifacts/local-pattern-draft.json')['codingUnits'][0]['pattern']['status'] == 'draft'
        checks('03-real-positive-check')
        checks('04-independent-invalid-implementation', 'notes-query-invalid', 2)
        # Shared producer setup is fictional reviewed authoring, not an upstream promotion.
        # Both shared/local evidence use exactly the maintained binding implementation.
        sys.path.insert(0, str(scripts))
        import coding_patterns as patterns
        from coding_context import prepare
        shared_rule = 'fixture.shared-owner-query'
        shared_source = 'program-kit-governance/references/fixture-query.md'
        write(extensions / shared_source, 'SHARED_OWNER_FILTER: return results only for the admitted owner. Qualify actual provider behavior separately.\n')
        catalog = load(catalog_path)
        catalog['sources'].append({'id': shared_source, 'locator': {'kind': 'extension', 'path': shared_source}})
        catalog['rules'][shared_rule] = {'source': shared_source, 'selector': {'kind': 'document'}, 'owner': 'fixture shared maintainer', 'level': 'recommended', 'limits': 'Fictional shared declaration; only bounded owner-filter evidence.'}
        shared = declaration('shared-notes-query', shared_rule)
        catalog['codingUnits'].append(shared)
        write(catalog_path, catalog)
        # Use isolated imported catalog explicitly. The fixture's parent process may
        # already have modules loaded from maintained source, with identical algorithms.
        observed = base['coding'].copy()
        ctx = patterns.context(observed['profiles'], observed['projects'])
        record = {'fingerprint': patterns.binding(shared, patterns.resolved_rules(catalog, shared, consumer, extensions), consumer, extensions, ctx),
                  'checks': [patterns.current_check(consumer, c) for c in shared['pattern']['checks']],
                  'boundAtUtc': datetime.now(timezone.utc).isoformat()}
        shared['pattern']['evidence'].append(record)
        write(catalog_path, catalog)
        shared_output = run('05-qualified-shared-pattern', command())
        assert next(r for r in shared_output['coding']['patterns'] if r['id'] == shared['id'])['selected']
        local = load(consumer / 'artifacts/local-pattern-draft.json')
        local_unit = declaration('local-notes-query', 'local.local-notes-query', replaces=['shared-notes-query'])
        local['codingUnits'] = [local_unit]
        write(local_path, local)
        run('06-ambiguous-alternatives', command(), 2)
        choice('local-notes-query')
        run('07-chosen-missing-evidence', command(), 2)
        run('08-bind-local-actual-evidence', pattern_command('bind-evidence'))
        chosen = run('09-qualified-private-replacement', command())
        chosen_ids = {u['id'] for u in chosen['coding']['skills']}
        assert 'local-notes-query' in chosen_ids and 'shared-notes-query' not in chosen_ids
        assert {u['id'] for u in base['coding']['skills']} <= chosen_ids, 'Local preference removed an F2 duty'
        assert any('LOCAL_OWNER_FILTER' in r['text'] for u in chosen['coding']['skills'] for r in u['rules'])
        choice('shared-notes-query')
        retained_shared = run('09a-explicit-shared-alternative', command())
        assert any(p['selected'] and p['id'] == 'shared-notes-query' for p in retained_shared['coding']['patterns'])
        choice('local-notes-query', '2.0.0')
        run('09b-unadopted-pattern-version', command(), 2)
        local = load(local_path)
        alternative = declaration('local-query-alternative', 'local.local-notes-query')
        alternative['pattern']['alternatives'] = ['shared-notes-query', 'local-notes-query']
        alternative['pattern']['inputs'] = [ref('src/query_alternative.py')]
        alternative['pattern']['examples']['positive'] = [ref('src/query_alternative.py')]
        alternative['pattern']['checks'] = [{'kind': 'toolkit', 'id': 'notes-query-alternative'}]
        local['codingUnits'].append(alternative)
        write(local_path, local)
        choice('local-query-alternative', reason='Choose the reviewed projection variant for this consumer context; no replacement or performance advantage is claimed.')
        checks('09c-real-contextual-alternative-check', 'notes-query-alternative')
        run('09d-bind-contextual-alternative', pattern_command('bind-evidence', 'local-query-alternative'))
        contextual = run('09e-contextual-suitability-selection', command())
        contextual_pattern = next(p for p in contextual['coding']['patterns'] if p['id'] == 'local-query-alternative')
        assert contextual_pattern['selected'] and not contextual_pattern['precedence']['replaces']
        choice('local-notes-query')
        fresh = consumer / 'specs/003-later-notes'
        for name in ('spec.md', 'plan.md', 'tasks.md'):
            write(fresh / name, (feature / name).read_text())
        later = run('10-later-fresh-task', command(scope='specs/003-later-notes'))
        assert any(p['selected'] and p['id'] == 'local-notes-query' for p in later['coding']['patterns'])
        browser = run('11-unrelated-browser-excluded', command(scope='specs/002-browser', operation=False))
        assert not any(p['selected'] for p in browser['coding']['patterns'])
        code = consumer / 'src/query_example.py'
        code.write_text(code.read_text() + '# Reviewed implementation change; behavior remains bounded.\n')
        run('12-changed-code-stales-chosen-proof', command(), 2)
        tasks_before = (feature / 'tasks.md').read_bytes()
        progress = run('12b-blocked-progress-preserves-checkpoint', command(name='finish'), 2)
        assert progress['status'] == 'needs-attention' and 'currentCheckpoint' in progress
        assert (feature / 'tasks.md').read_bytes() == tasks_before
        run('13-independent-browser-still-prepares', command(scope='specs/002-browser', operation=False))
        checks('14-check-changed-code')
        run('15-rebind-preserves-history', pattern_command('bind-evidence'))
        local = load(local_path)
        assert len(local['codingUnits'][0]['pattern']['evidence']) == 2
        canonical = consumer / 'docs/patterns/private-query.md'
        original = canonical.read_bytes()
        canonical.write_bytes(original + b'Changed canonical instruction needs fresh review.\n')
        run('16-canonical-change-stales-proof', command(), 2)
        canonical.write_bytes(original)
        profiles = consumer / 'docs/architecture/bootstrap-decisions.json'
        profile_bytes = profiles.read_bytes()
        write(profiles, {'selected_profiles': ['dotnet', 'typescript-web', 'unqualified-profile']})
        run('17-profile-change-stales-proof', command(), 2)
        profiles.write_bytes(profile_bytes)
        props = consumer / 'provider.props'
        prop_bytes = props.read_bytes()
        props.write_bytes(prop_bytes.replace(b'10.0.0', b'11.0.0'))
        run('18-incompatible-evaluated-package', command(), 2)
        props.write_bytes(prop_bytes)
        review_source = consumer / 'docs/architecture/notes-pattern-review.md'
        review_bytes = review_source.read_bytes()
        review_source.unlink()
        run('19-missing-normal-review', command(), 2)
        review_source.write_bytes(review_bytes)
        local['codingUnits'][0]['pattern']['status'] = 'retired'
        write(local_path, local)
        run('20-retired-chosen-version', command(), 2)
        local['codingUnits'][0]['pattern']['status'] = 'active'
        local['codingUnits'][0]['pattern']['invariantRuleIds'] = []
        write(local_path, local)
        conflict = run('21-cannot-weaken-invariant', command(), 2)
        assert 'PRIVATE_CANARY_DO_NOT_EXPORT' not in conflict and 'LOCAL_OWNER_FILTER' not in conflict
        local['codingUnits'][0]['pattern']['invariantRuleIds'] = ['principle.compilation-boundaries']
        local['codingUnits'][0]['pattern']['run'] = 'submitted-code.py'
        write(local_path, local)
        run('22-submitted-execution-not-admitted', command(), 2)
        del local['codingUnits'][0]['pattern']['run']
        write(local_path, local)
        final = run('23-restored-qualified-context', command())
        brief = run('24-bounded-ordinary-brief', [phase, 'prepare', '--repository', consumer, '--feature-dir', 'specs/001-notes', '--operation', 'list'])
        assert len(brief.split()) < 1600
        result['ordinaryBriefWords'] = len(brief.split())
        browser_command = [phase, 'prepare', '--repository', consumer, '--feature-dir', 'specs/002-browser']
        browser_brief = run('25-browser-before-canonical-mutation', browser_command)
        style = extensions / 'program-kit-dotnet/references/dotnet-engineering.md'
        style_bytes = style.read_bytes()
        style.write_bytes(style_bytes.replace(b'in four files', b'in four independently named files'))
        changed_brief = run('26-canonical-style-reaches-brief', [phase, 'prepare', '--repository', consumer, '--feature-dir', 'specs/001-notes', '--operation', 'list'])
        assert 'four independently named files' in changed_brief and changed_brief != brief
        assert run('27-unrelated-browser-brief-unchanged', browser_command) == browser_brief
        write(review / 'snapshots/canonical-style-before.md', style_bytes.decode('utf-8'))
        write(review / 'snapshots/canonical-style-after.md', style.read_text(encoding='utf-8'))
        style.write_bytes(style_bytes)
        assert final['coding']['canProceed']
        write(review / 'snapshots/shared-registry.json', catalog)
        write(review / 'snapshots/local-pattern-input.json', local)
        write(review / 'snapshots/before-patterns.json', base['coding'])
        write(review / 'snapshots/after-private-selection.json', chosen['coding'])
        write(review / 'snapshots/final-context.json', final['coding'])
        result.update(status='passed', workingInputsUnchanged=input_snapshot()['digest'] == result['workingInputsDigest'])
        write(review / 'index.md', '''# F3 guided output review

This disposable private-notes repository reuses F2's fictional accepted architecture/tasks and real target-free MSBuild evaluation. Shared/local pattern reviews and initial shared authoring are explicitly simulated. The existing named-check runner executes a real tiny **Python owner-filter example** with a fixed independent oracle. No pattern command executes submitted code. This is not a .NET endpoint or PostgreSQL implementation.

1. Start with [before patterns](output/01-f2-route-before-patterns.stdout.txt), [draft assistance](output/02-draft-submission.stdout.txt), and the [single draft](consumer/artifacts/local-pattern-draft.json). The helper preserves a source reference, supplies editable maintained fields and lists missing proof. It neither registers nor qualifies the draft.
2. Read [positive actual check](output/03-real-positive-check.stdout.txt) and [invalid implementation](output/04-independent-invalid-implementation.stdout.txt). Follow the retained runner directories in those outputs to both streams. Inspect [the independent fixed oracle](consumer/tests/query_pattern_check.py), [working code](consumer/src/query_example.py) and [invalid code](consumer/src/query_invalid.py). Expected owner IDs do not come from the registry. The negative must exit 2 and remain failed history.
3. Inspect [shared selection](output/05-qualified-shared-pattern.stdout.txt) and [shared declaration](snapshots/shared-registry.json). In `coding.patterns`, qualification and suitability are separate. Shared setup simulates source review but binds the actual maintained execution through the same evidence functions.
4. Compare [ambiguous alternatives](output/06-ambiguous-alternatives.stdout.txt), [chosen but unqualified](output/07-chosen-missing-evidence.stdout.txt), [binding actual evidence](output/08-bind-local-actual-evidence.stdout.txt), and [private selection](output/09-qualified-private-replacement.stdout.txt). Read the ordinary [plan choice](consumer/specs/001-notes/plan.md) and [local declaration](snapshots/local-pattern-input.json). Explicit precedence does not establish suitability or qualification. F2's mandatory duties remain selected. The consumer can also [retain the shared alternative](output/09a-explicit-shared-alternative.stdout.txt); it cannot [silently adopt another pattern version](output/09b-unadopted-pattern-version.stdout.txt). A second implementation gets its own [actual check](output/09c-real-contextual-alternative-check.stdout.txt), [binding](output/09d-bind-contextual-alternative.stdout.txt) and [contextual selection](output/09e-contextual-suitability-selection.stdout.txt). Its `alternatives` and reason establish contextual suitability; `replaces` stays empty. Both implementations face the same fixed independent oracle; neither is declared faster or universally preferable.
5. [Later fresh task](output/10-later-fresh-task.stdout.txt) selects the same private lesson without upstream publication. [Browser task](output/11-unrelated-browser-excluded.stdout.txt) explains exclusion. `applicationObserved` remains false: emitted guidance is not proof an agent followed it.
6. Follow stale/unsupported negatives: [code change](output/12-changed-code-stales-chosen-proof.stdout.txt), [blocked progress](output/12b-blocked-progress-preserves-checkpoint.stdout.txt), [independent scope](output/13-independent-browser-still-prepares.stdout.txt), [fresh check](output/14-check-changed-code.stdout.txt), [append-only rebinding](output/15-rebind-preserves-history.stdout.txt), [canonical change](output/16-canonical-change-stales-proof.stdout.txt), [profile change](output/17-profile-change-stales-proof.stdout.txt), [actual incompatible package](output/18-incompatible-evaluated-package.stdout.txt), [missing normal review](output/19-missing-normal-review.stdout.txt), [retirement](output/20-retired-chosen-version.stdout.txt), [invariant weakening](output/21-cannot-weaken-invariant.stdout.txt), and [submitted execution field](output/22-submitted-execution-not-admitted.stdout.txt). Each affected preparation must exit 2. Blocked progress also exits 2 and reports needs-attention plus the retained checkpoint without modifying tasks. No fallback or private source text appears in public error diagnostics.
7. [Restored context](output/23-restored-qualified-context.stdout.txt) succeeds; inspect both historical bindings in the local declaration. The [ordinary brief](output/24-bounded-ordinary-brief.stdout.txt) retains the existing 1,600-word bound. [Results](results.json) records every actual invocation/exit/timing/stream hash plus source identities and unchanged-input comparison.
8. Compare the [canonical style before](snapshots/canonical-style-before.md) and [after](snapshots/canonical-style-after.md), then inspect the [actual changed brief](output/26-canonical-style-reaches-brief.stdout.txt). Search for `four independently named files`: only the disposable canonical prose changed; no adapter policy string was edited. The [browser brief before](output/25-browser-before-canonical-mutation.stdout.txt) and [after](output/27-unrelated-browser-brief-unchanged.stdout.txt) are identical. The fixture restores the canonical source after this demonstration. Native analyzer declarations and independent compiled enforcement are separate owners.

## Rerun and limits

Run `python tests/pattern_review_fixture.py --review` from the feature worktree. Each run retains a new consumer and outputs; no earlier review is cleaned up. Individual commands are recorded verbatim in results.json. Check execution is explicit through the existing verification owner; preparation/binding only inspect its evidence.

Hashes detect changes within declared ownership, not maliciously forged local history or hidden external state. Authored review identity is not authenticated. This fixture establishes only installed-layout command behavior, scoped evidence handling and four pure Python owner-filter assertions. No packaged installation/update, .NET compilation, API/provider/browser behavior, automatic code application, performance improvement, F4 scaffolding, complete F6 learning workflow or human product acceptance is claimed. Existing F1/F2 failures and budget disclosures remain independent. Human review is still pending.
''')
        return result
    except BaseException as error:
        result.update(status='failed', error=str(error))
        raise
    finally:
        result['elapsedSeconds'] = round(time.perf_counter() - started, 3)
        write(review / 'results.json', result)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true')
    args = parser.parse_args()
    if args.review:
        folder = ROOT / 'artifacts/f3-review' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6])
        print('Retained F3 review: ' + str(folder / 'index.md'), flush=True)
        scenario(folder)
    else:
        with FixtureDirectory(native=True) as folder:
            scenario(folder)


if __name__ == '__main__':
    main()

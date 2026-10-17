"""F1 inspectable installed-command journey. No agents, services or paid I/O.

--review keeps a uniquely owned run for human inspection. It never cleans up an
earlier review. Ordinary validation supplies an owned temporary directory instead.
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
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from owned_fixture import FixtureDirectory, filesystem_path


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def scenario(directory):
    review = Path(filesystem_path(Path(directory).resolve()))
    review.mkdir(parents=True, exist_ok=True)
    consumer = review / 'consumer'
    consumer.mkdir()
    results = {'scope': 'F1 canonical discovery/resolution and installed guidance; no application/agent/human acceptance.',
               'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'commands': [], 'observations': {}, 'status': 'running'}
    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import input_snapshot
    initial_inputs = input_snapshot()
    results['workingInputsDigest'] = initial_inputs['digest']
    results['fixtureSourceSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(review / 'results.json', results)

    def run(name, arguments, expected=0, cwd=consumer):
        result = subprocess.run([sys.executable, *map(str, arguments)], cwd=cwd,
                                capture_output=True, text=True, encoding='utf-8', timeout=45)
        write(review / 'output' / (name + '.stdout.txt'), result.stdout)
        write(review / 'output' / (name + '.stderr.txt'), result.stderr)
        results['commands'].append({'name': name, 'command': [sys.executable, *map(str, arguments)],
                                    'cwd': str(cwd), 'expectedExit': expected, 'actualExit': result.returncode,
                                    'stdoutSha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                                    'stderrSha256': hashlib.sha256(result.stderr.encode()).hexdigest()})
        write(review / 'results.json', results)
        if result.returncode != expected:
            raise AssertionError(name + ': expected exit ' + str(expected) + ', got ' + str(result.returncode)
                                 + '; inspect retained stdout/stderr')
        return result.stdout

    try:
        for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
            shutil.copytree(filesystem_path(ROOT / 'extensions' / name), consumer / '.specify/extensions' / name,
                            ignore=shutil.ignore_patterns('__pycache__'))
        # Reuse the maintained adopted-context fixture, but own retention here.
        from validate_knowledge_application import KnowledgeApplicationTests
        seed = KnowledgeApplicationTests()
        seed.root = consumer
        seed.feature = consumer / 'specs/001-notes'
        write(seed.feature / 'spec.md', 'Private named notes with durable saves.\n- **Specification roadmap entry**: RM-01\n')
        seed.adopted()
        browser = consumer / 'specs/002-browser'
        write(browser / 'spec.md', 'Frontend-only browser presentation.\n- **Specification roadmap entry**: RM-01\n')
        seed.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet', 'typescript-web']})
        phase = consumer / '.specify/extensions/program-kit-governance/scripts/phase_obligations.py'
        discovery = phase.with_name('knowledge_discovery.py')
        catalog_path = phase.parent.parent / 'references/phase-obligations.json'
        catalog_bytes = catalog_path.read_bytes()
        catalog = json.loads(catalog_bytes)
        base = [phase, 'project', '--repository', consumer, '--phase', 'planning']
        api_command = [*base, '--feature-dir', 'specs/001-notes']
        browser_command = [*base, '--feature-dir', 'specs/002-browser']
        api_before = run('01-api-before', api_command)
        browser_before = run('02-browser-before', browser_command)
        if 'ALLOWED_ROLE_REFERENCES' not in api_before or 'ALLOWED_ROLE_REFERENCES' in browser_before:
            raise AssertionError('The actual task briefs did not distinguish API/native from frontend-only scope')

        run('03-catalog', [discovery, 'catalog'])
        tree_output = run('04-tree-discovery', [ROOT / 'extensions/program-kit-governance/scripts/knowledge_discovery.py',
                                               'scan', '--repository', ROOT, '--format', 'json'], cwd=ROOT)
        sources = json.loads(tree_output)['sources']
        examples = ('extensions/program-kit-dotnet/templates/dotnet/files/eng/architecture_rules.py',
                    'extensions/program-kit-dotnet/templates/dotnet/files/eng/label-validation.schema.json',
                    'extensions/program-kit-dotnet/templates/dotnet/files/.editorconfig',
                    'extensions/program-kit-governance/scripts/phase_obligations.py',
                    'extensions/program-kit-dotnet/templates/dotnet/files/eng/source_quality.py')
        guide = ['# Discovery inspection guide', '',
                 'These are observations from the actual scan. Candidate declarations are lookup leads, not automatically active rules.', '',
                 '| Actual source | Disposition | Declaration candidates | What to inspect |', '| --- | --- | --- | --- |']
        for path in examples:
            row = next(row for row in sources if row['path'] == path)
            candidates = row.get('inspection', {}).get('candidates', [])
            guide.append('| ' + path + ' | ' + row['disposition'] + ' | ' + str(len(candidates))
                         + ' | Search this path in the [full scan](output/04-tree-discovery.stdout.txt); inspect the symbols/pointers/lines, then follow the actual source. |')
        guide += ['', 'The readable [catalog](output/03-catalog.stdout.txt) is grouped by purpose. Inspect its owner, applicability, level, evaluation and limits fields.',
                  'In the full scan, search for `git-history`, `history`, `policy-carrier-review`, or `captured-version`. Historical sources and captured documents do not imply current use.',
                  'Look at `inspection.status`: a parse/bound gap is explicit. Deliberately malformed counterexamples can also fail parsing; the source owner decides their disposition.',
                  'The migration rows in the catalog JSON view distinguish replaced rendering from remaining F3/F8 carrier work. Candidate literals are not printed or hashed.']
        write(review / 'discovery-guide.md', '\n'.join(guide) + '\n')
        profile_index = consumer / '.specify/extensions/program-kit-building-blocks/references/dependency-profiles/index.json'
        profile = json.loads(profile_index.read_text())['default']
        results['explicitFixtureProfile'] = profile
        run('05-exact-publisher', [discovery, 'catalog', '--rule', 'publisher.domain-event-dispatcher', '--profile', profile, '--resolve'])
        run('06-repository-only-unavailable', [discovery, 'catalog', '--rule', 'decision.0007', '--installed', '--resolve'], expected=2)

        def fingerprints(name):
            value = run(name, [discovery, 'catalog', '--requirement', 'dotnet-boundaries', '--installed', '--resolve', '--format', 'json'])
            return {row['id']: row['resolved']['fingerprint'] for row in json.loads(value)['rules']}

        before = fingerprints('07-fingerprints-before')
        prose = consumer / '.specify/extensions/program-kit-governance/references/modularity-and-contracts.md'
        original_bytes = prose.read_bytes()
        original = original_bytes.decode('utf-8')
        marker = '<!-- program-kit:knowledge-rule principle.compilation-boundaries -->'
        change = 'FICTIONAL FIXTURE CHANGE: review the canonical source before making this decision.'
        prose.write_text(original.replace(marker, marker + '\n' + change, 1), encoding='utf-8')
        api_after = run('08-api-after-prose', api_command)
        browser_after = run('09-browser-after-prose', browser_command)
        after_prose = fingerprints('10-fingerprints-after-prose')
        if change not in api_after or browser_before != browser_after:
            raise AssertionError('Canonical change did not reach the applicable producer or changed an unrelated brief')
        changed_prose = [identity for identity in before if before[identity] != after_prose[identity]]
        if changed_prose != ['principle.compilation-boundaries']:
            raise AssertionError('Prose mutation invalidated an incorrect rule scope: ' + str(changed_prose))
        write(review / 'output/api-prose.diff', ''.join(difflib.unified_diff(api_before.splitlines(True), api_after.splitlines(True), 'before', 'after-canonical-prose')))
        write(review / 'snapshots/canonical-prose-before.md', original)
        write(review / 'snapshots/canonical-prose-after.md', prose.read_text(encoding='utf-8'))
        prose.write_bytes(original_bytes)

        native = consumer / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/architecture_rules.py'
        original_native_bytes = native.read_bytes()
        original_native = original_native_bytes.decode('utf-8')
        native.write_text(original_native.replace('"core": {"core"}', '"core": set()', 1))
        native_after = run('11-api-after-native', api_command)
        after_native = fingerprints('12-fingerprints-after-native')
        if '"core": set()' not in native_after:
            raise AssertionError('Native table declaration did not reach actual produced guidance')
        changed_native = [identity for identity in before if before[identity] != after_native[identity]]
        if changed_native != ['native.allowed-role-references']:
            raise AssertionError('Native change invalidated an incorrect rule scope: ' + str(changed_native))
        write(review / 'output/api-native.diff', ''.join(difflib.unified_diff(api_before.splitlines(True), native_after.splitlines(True), 'before', 'after-native-table')))
        write(review / 'snapshots/native-before.py', original_native)
        write(review / 'snapshots/native-after.py', native.read_text())
        native.write_bytes(original_native_bytes)

        for name, replacement in [('13-missing-rule', '<!-- fixture removed marker -->'), ('14-ambiguous-rule', marker + '\nDuplicate.\n<!-- /program-kit:knowledge-rule -->\n' + marker)]:
            prose.write_text(original.replace(marker, replacement, 1), encoding='utf-8')
            write(review / 'snapshots' / (name + '.md'), prose.read_text(encoding='utf-8'))
            output = run(name, api_command, expected=2)
            if 'Missing/ambiguous canonical decision rule' not in output:
                raise AssertionError('Missing/ambiguous rule did not produce its bounded diagnostic')
        prose.write_bytes(original_bytes)
        altered = json.loads(catalog_path.read_text())
        altered['rules']['native.allowed-role-references']['selector']['name'] = 'ABSENT_NATIVE_SYMBOL'
        write(catalog_path, altered)
        write(review / 'snapshots/15-missing-native-symbol.json', altered)
        run('15-missing-native-symbol', api_command, expected=2)
        catalog_path.write_bytes(catalog_bytes)

        # Independent negative graph, run through the installed native validator.
        probe = consumer / 'independent_negative.py'
        write(probe, 'from pathlib import Path\nimport sys\n'
              'sys.path.insert(0, str(Path(__file__).parent / ".specify/extensions/program-kit-dotnet/templates/dotnet/files/eng"))\n'
              'from repository_architecture import validate_planned\n'
              'graph = {"runtimeComposition": {"projects": ['
              '{"path":"src/Notes.Core/Notes.Core.csproj","role":"core","projectReferences":["src/Notes.Store/Notes.Store.csproj"]},'
              '{"path":"src/Notes.Store/Notes.Store.csproj","role":"provider","projectReferences":[]}],"bindings":[]}}\n'
              'try:\n    validate_planned(Path.cwd(), graph)\n'
              'except ValueError as error:\n    print("EXPECTED REJECTION:", error)\n    raise SystemExit(0)\n'
              'raise SystemExit("FAIL: invalid Core-to-provider edge was accepted")\n')
        run('16-independent-native-negative', [probe])
        results['observations'] = {'canonicalProseReachedActualBrief': True, 'unrelatedBrowserBriefUnchanged': True,
                                   'changedProseRules': changed_prose, 'changedNativeRules': changed_native,
                                   'priorAffectedFingerprint': 'stale after the corresponding source mutation',
                                   'fixtureSourcesRestored': True,
                                   'limits': 'Native declaration/template resolution, not evaluated consumer configuration or DomainEvents runtime qualification.'}
        if input_snapshot()['digest'] != initial_inputs['digest']:
            raise AssertionError('Feature working inputs changed during the review fixture; rerun against stable source')
        results['status'] = 'passed'
    except Exception as error:
        results['status'] = 'failed'
        results['failure'] = str(error)
        raise
    finally:
        write(review / 'results.json', results)
        write(review / 'index.md', review_index(results))
    return results


def review_index(results):
    return '''# F1 — guided fixture review

This fictional Notes API and frontend-only task use the actual shipped extension
sources copied into an installed layout. Nothing runs against a real consumer,
provider or coding agent. This is not a packaged-installation qualification.

Start here, then inspect the linked files in order. The result is **''' + results['status'] + '''**.
Every command, exit status and output digest is in [results.json](results.json).

| Step | Open | What to look for and why it matters |
| --- | --- | --- |
| 1. Actual prepared guidance | [API before](output/01-api-before.stdout.txt), [browser before](output/02-browser-before.stdout.txt) | The API selects the native compilation duties. The frontend-only task excludes them. These are actual command outputs, not illustrative desired output. |
| 2. Discovery breadth | [Start with the discovery guide](discovery-guide.md), then [catalog](output/03-catalog.stdout.txt) and [actual source tree](output/04-tree-discovery.stdout.txt) | The guide names concrete paths and search terms. Look for code/build/schema declarations as well as prose, explicit history and unknown consultation. Available does not mean applied. |
| 3. Exact source context | [Captured publisher](output/05-exact-publisher.stdout.txt), [unavailable repository-only source](output/06-repository-only-unavailable.stdout.txt) | The capture has an exact profile/commit/digest. Installed-only lookup must diagnose the missing repository authority, never silently substitute something else. |
| 4. Change canonical prose | [Guidance diff](output/api-prose.diff), [before](snapshots/canonical-prose-before.md), [after](snapshots/canonical-prose-after.md) | Find the explicitly fictional added sentence. It reaches the API brief. Compare browser output before/after: it stays identical. We did not edit a duplicate instruction string. |
| 5. Change native authority | [Native guidance diff](output/api-native.diff), [native before](snapshots/native-before.py), [native after](snapshots/native-after.py) | Only the Core reference table is changed in the disposable copy. Guidance resolves the real declaration. This mutation is a demonstration, not an approved architectural improvement. |
| 6. Scope and freshness | [Fingerprints before](output/07-fingerprints-before.stdout.txt), [after prose](output/10-fingerprints-after-prose.stdout.txt), [after native](output/12-fingerprints-after-native.stdout.txt) | Each mutation changes only its applicable rule fingerprint. The original full source digest remains attributable; old affected output cannot establish current proof. |
| 7. Deliberate failures | [Missing marker](output/13-missing-rule.stdout.txt), [ambiguous marker](output/14-ambiguous-rule.stdout.txt), [missing native symbol](output/15-missing-native-symbol.stdout.txt) | Expected exit is 2. Check that the diagnostic identifies the missing/ambiguous owner. The matching input snapshots are [missing](snapshots/13-missing-rule.md), [ambiguous](snapshots/14-ambiguous-rule.md) and [native](snapshots/15-missing-native-symbol.json). |
| 8. Independent boundary oracle | [Native rejection](output/16-independent-native-negative.stdout.txt) | A fictional Core project referencing a provider is rejected by the installed native validator. This expectation is authored independently of the catalog values. |

The retained [consumer](consumer/) has its source changes restored after the
demonstration. The exact rerun commands for each step are in results.json. Commands
for mutation/failure steps need the corresponding saved snapshot or mutation; rerunning
against the restored consumer shows baseline behavior. To reproduce the full sequence,
run `python tests/knowledge_review_fixture.py --review` from the feature worktree.
That creates a new review directory and preserves this one.

This proves F1 discovery/resolution and scoped installed guidance. It does not prove
application compilation, runtime registrations, DomainEvents handler behavior, browser
quality, F2–F8, agent obedience or human product acceptance. Complementary semantic
architecture duties still require their source-backed review and behavior tests.

Review stays open until you say it is finished. Inspect anomalies with the agent;
then the owned disposable consumer and scratch snapshots may be cleaned up while
retaining the bounded results/output used as proof. No cleanup has run.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', action='store_true', help='Retain output until human review finishes')
    args = parser.parse_args()
    if args.review:
        directory = ROOT / 'artifacts/f1-review' / uuid.uuid4().hex[:10]
        try:
            scenario(directory)
        finally:
            print('Review index: ' + str(directory / 'index.md'))
    else:
        with FixtureDirectory() as directory:
            scenario(directory)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Real archive/native installation and fictional nonnative repair-before-resume.

All engine calls are installed subprocesses. No worker, provider, publication or
public-profile C# analyzer acceptance is inferred from this finite state journey.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

from coding_review_fixture import write
from local_bundle_fixture import install_local_bundle
from owned_fixture import filesystem_path, native_path
from validate_package_smoke import extract

ROOT = Path(__file__).resolve().parents[1]
POLICY = '<!-- program-kit:story-delivery-v1 -->'


def scenario(archives):
    token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6]
    review = Path(filesystem_path(ROOT / 'artifacts/conformance-installed' / token))
    consumer = Path(filesystem_path(ROOT / 'artifacts/t' / ('ci-' + uuid.uuid4().hex[:8])))
    review.mkdir(parents=True)
    consumer.mkdir(parents=True)
    started = time.monotonic()
    result = {'status': 'running', 'scope': 'Actual archive/native installation and fictional text-state pre-code/repair/review/resume; no native analyzer or human product acceptance.',
              'commands': [], 'consumer': native_path(consumer), 'fictionalAuthorship': True}
    write(review / 'index.md', '# Incomplete installed conformance journey\n\nInspect results.json and both output streams.\n')

    def run(label, arguments, expected=0, marker=None):
        command = [native_path(a) if isinstance(a, Path) else str(a) for a in arguments]
        before = time.monotonic()
        child = subprocess.run(command, cwd=native_path(consumer), capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=120)
        write(review / 'output' / (label + '.stdout.txt'), child.stdout)
        write(review / 'output' / (label + '.stderr.txt'), child.stderr)
        result['commands'].append({'label': label, 'command': command, 'expectedExit': expected,
            'actualExit': child.returncode, 'elapsedSeconds': round(time.monotonic() - before, 3),
            'stdoutSha256': hashlib.sha256(child.stdout.encode()).hexdigest(),
            'stderrSha256': hashlib.sha256(child.stderr.encode()).hexdigest()})
        write(review / 'results.json', result)
        if child.returncode != expected or marker and marker not in child.stdout + child.stderr:
            raise AssertionError(label + ': inspect retained installed-process output')
        try:
            return json.loads(child.stdout)
        except ValueError:
            return child.stdout

    try:
        version = (ROOT / 'VERSION').read_text().strip()
        archive = archives / ('program-kit-tooling-' + version + '.zip')
        assert archive.is_file(), 'Build actual local archives first; this fixture never fabricates installed capability'
        result['archive'] = {'path': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
        release = review / 'release'
        extract(archive, release)
        import specify_cli
        bridge = [sys.executable, release / 'scripts/invoke_specify.py', '--site-packages',
                  Path(specify_cli.__file__).parent.parent, '--']
        run('01-native-init', [*bridge, 'init', '.', '--force', '--non-interactive', '--integration',
                               'copilot', '--script', 'py', '--ignore-agent-tools'])
        install_local_bundle(consumer, release, bridge,
                             lambda label, argv: run('02-' + label, argv), integration='copilot')
        records = json.loads((consumer / '.specify/bundle-records.json').read_text(encoding='utf-8'))
        assert any(row['bundle_id'] == 'program-kit' for row in records['bundles'])
        scripts = consumer / '.specify/extensions/program-kit-governance/scripts'
        phase, task = scripts / 'phase_obligations.py', scripts / 'task_draft.py'
        native = consumer / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/scripts/repository_verification.py'
        assert phase.is_file() and task.is_file() and (scripts / 'operation_readiness.py').is_file()
        feature = consumer / 'specs/001-record'
        write(consumer / '.gitignore', '.specify/\n.github/\nartifacts/\nrequest.json\n')
        write(feature / 'spec.md', POLICY + '\n# Fictional record\nThe fixed uppercase record identity ALPHA remains unchanged; only its owned textual representation is maintained.\n')
        write(feature / 'plan.md', POLICY + '\n# Fictional record plan\n\n## Decisions\nThe finite owned representation preserves the already admitted record identity.\n\n'
              '## Operation implementation map\n| Operation | Decision | Resolution | Source |\n|---|---|---|---|\n'
              '| maintain | ownership | The existing text-record owner maintains src/Record.txt; authority and public identity remain fixed. | plan.md#Decisions |\n'
              '| maintain | results | Whitespace representation changes preserve the admitted uppercase ALPHA identity and exact result. | spec.md |\n'
              '| maintain | limits | No applicable limits: whitespace repair changes no behavioral/resource ceiling; ALPHA identity remains invariant. | spec.md |\n'
              '| continue | ownership | The same existing owner writes src/Next.txt only after maintained-record prerequisites. | plan.md#Decisions |\n'
              '| continue | results | Continuation observes the same admitted ALPHA identity; no new product meaning is approved. | spec.md |\n'
              '| continue | limits | No applicable limits: this continuation preserves the existing identity without a resource/policy ceiling. | spec.md |\n')
        write(feature / 'tasks.md', POLICY + '''
# Fictional record tasks
- [ ] T001 [US1] Maintain admitted identity in src/Record.txt
- [ ] T002 [US2] Continue existing result in src/Next.txt

## Operation dependency map
| Operation | Depends on operations |
|---|---|
| maintain | none |
| continue | maintain |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|---|---|---|---|---|
| T001 | maintain | none | none | retained-record |
| T002 | continue | T001 | retained-record | none |

## Story delivery map
| Story | Operations | Useful outcome | Independent walkthrough | Active minutes to review | Larger-story rationale |
|---|---|---|---|---|---|
| US1 | maintain | Preserve admitted record | Read fixed ALPHA identity | 5 | none |
| US2 | continue | Continue admitted record | Read unchanged fixed identity | 5 | none |

## Operation implementation map
| Operation | Pattern / example | Compatibility / alternative | First adverse cases | Test owner / command | First coherent check |
|---|---|---|---|---|---|
| maintain | Supported manual text-owner maintenance | Finite Python/text fixture with unchanged identity, no native project | changed identity must fail; whitespace preserves admitted identity | checks/record.py through record-fixture named owner | Execute record-fixture at first coherent fixture increment |
| continue | Existing text-owner continuation | Same admitted identity and runtime | pending repair must block continuation | checks/record.py through record-fixture named owner | Execute record-fixture before continued result |
''')
        write(consumer / 'src/Record.txt', 'ALPHA  \n')
        write(consumer / 'src/Next.txt', 'ALPHA\n')
        write(consumer / 'checks/record.py', 'from pathlib import Path\nassert Path("src/Record.txt").read_text().strip() == "ALPHA", "record-identity-changed"\nprint("Actual finite record identity preserved; no application acceptance")\n')
        write(consumer / 'config/program-kit/verification.json', {'schemaVersion': 1, 'toolkitChecks': [{
            'id': 'record-fixture', 'script': 'checks/record.py', 'arguments': [],
            'inputs': ['checks/record.py', 'src/Record.txt'], 'timeoutSeconds': 10}]})
        write(consumer / 'config/program-kit/architecture.json', {'runtimeComposition': {'projects': [], 'bindings': []}})
        write(consumer / 'review.md', '# Fictional source review\nThe finite text owner preserves admitted ALPHA identity while removing insignificant trailing whitespace. The named check asserts the actual same value. Grouped authored findings exercise the installed review contract, not human product acceptance.\n')
        constitution = consumer / '.specify/memory/constitution.md'
        write(constitution, POLICY + '\n# Fictional fixture constitution\n**Status**: Draft\n**Version**: 1.0.0\n**Ratified**: PENDING_RATIFICATION\n**Last Amended**: 2026-10-22\n\n## Governance\nAmendments update the version and require compliance review. All decisions in this disposable fixture are simulated authoring; no consumer authority or product acceptance.\n')
        governance = scripts / 'governance_state.py'
        run('03-native-draft', [sys.executable, governance, 'begin'])
        run('04-native-review', [sys.executable, governance, 'write-review', '--stage', 'constitution'])
        run('05-fictional-automatic-ratification', [sys.executable, governance, 'ratify', '--verdict', 'ratify', '--approval-mode', 'automatic'])

        def prepare(label, operation='maintain', expected=0):
            return run(label, [sys.executable, phase, 'prepare', '--repository', consumer,
                '--feature-dir', 'specs/001-record', '--operation', operation, '--affected-path', 'src/Record.txt', '--format', 'json'], expected)

        plan = feature / 'plan.md'
        original_plan = plan.read_bytes()
        plan.write_bytes(b'\n'.join(line for line in original_plan.split(b'\n') if not line.startswith(b'| maintain | results |')))
        blocked = prepare('06-missing-precode-decision', expected=2)
        assert any(row['code'] == 'PKC020' for row in blocked['coding']['blockers'])
        plan.write_bytes(original_plan)
        prepare('07-recovered-precode-decision')
        plan.write_bytes(b'\n'.join(line for line in original_plan.split(b'\n') if not line.startswith(b'| maintain | limits |')))
        missing_limits = prepare('07a-missing-individual-limit-inventory', expected=2)
        assert any(row['code'] == 'PKC020' and row.get('decision') == 'limits' for row in missing_limits['coding']['blockers'])
        plan.write_bytes(original_plan)
        prepare('07b-recovered-limit-inventory')
        git = ['git', '-c', 'safe.directory=' + native_path(consumer), '-c', 'core.excludesFile=']
        for label, args in [('08-git-init', ['init', '-q']), ('09-git-add', ['add', '.']),
                            ('10-git-baseline', ['-c', 'user.name=Fictional Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fictional installed inputs'])]:
            run(label, [*git, *args])
        baseline = subprocess.check_output([*git, 'rev-parse', 'HEAD'], cwd=native_path(consumer), text=True).strip()
        result['baseline'] = baseline

        def delivery(label, request, expected=0, marker=None):
            write(consumer / 'request.json', request)
            return run(label, [sys.executable, task, 'delivery', '--repository', consumer,
                '--feature-dir', 'specs/001-record', '--content-file', 'request.json'], expected, marker)

        delivery('11-initialize-installed-engine', {'action': 'initialize', 'baseline': baseline,
            'source': 'Fictional disposable test authoring; no real human ratification/product acceptance claim'})
        target = feature / 'tasks.md'
        write(target, target.read_text().replace('- [ ] T001', '- [X] T001'))

        def execute_check(label):
            run(label, [sys.executable, native, '--repository', consumer, '--scope', 'Focused', '--check', 'record-fixture'])
            runs = sorted((consumer / 'artifacts/tests/toolkit-runs').glob('*/result.json'),
                          key=lambda p: json.loads(p.read_text())['startedAtUtc'])
            return runs[-1].relative_to(consumer).as_posix()

        def request_for(label, check_reference, **extra):
            coding = prepare(label)['coding']
            groups = {}
            for duty in coding['evaluation']['duties']:
                if duty['required']:
                    groups.setdefault((duty['reviewFamily'], duty['owner']), []).append(duty['rule'])
            claims = [{'rules': rules, 'checks': [{'kind': 'toolkit', 'id': 'record-fixture'}],
                       'review': 'review.md',
                       'authorship': {'implementationAuthors': ['fictional-text-owner'], 'reviewer': 'fictional-independent-reviewer', 'kind': 'agent'},
                       'inspections': [{'rules': rules, 'sources': [{'path': 'src/Record.txt', 'start': 1, 'end': 1}],
                           'boundary': 'Existing admitted ALPHA identity and its insignificant owned textual whitespace',
                           'findings': ['Actual text still admits exactly ALPHA; finite negative changes identity and fails the named check. This is fictional source-review authoring.'],
                           'assessment': 'Inspected current finite text representation against canonical family ' + family + '; no provider/native application behavior is claimed.'}],
                       'conclusion': 'Finite record identity preserved; grouped fictional source review has its explicit state-test scope.',
                       'limits': 'No authenticated reviewer, real product acceptance, provider/browser or native analyzer qualification.'}
                      for (family, owner), rules in groups.items()]
            for claim in claims:
                if 'principle.operational-setting-lifecycle' in claim['rules']:
                    assert all(op['limits']['inventory'] == [] for op in coding['operationBrief']['operations'])
                    claim['inspections'][0]['limitReconciliation'] = [
                        {'operation': op['operation'], 'limit': None, 'disposition': 'compliant',
                         'assessment': 'Fictional current text representation changes no resource/policy bound; fixed ALPHA identity is an invariant.'}
                        for op in coding['operationBrief']['operations']]
            return {'action': 'engineering', 'checkpoint': 'US1', 'checks': [check_reference],
                    'basisPaths': ['src/Record.txt'], 'evaluation': claims, **extra}

        reference = execute_check('12-actual-finite-check')
        initial = request_for('13-initial-grouped-source-request', reference, action='present',
            entryPoint='checks/record.py', preparedData='Fixed fictional ALPHA text', walkthrough='Read the admitted identity',
            expected='ALPHA remains fixed', limitations='Fictional text-state journey only')
        delivery('14-present-existing-outcome', initial)
        accepted = delivery('15-simulated-human-decision', {'action': 'decision', 'checkpoint': 'US1',
            'actor': 'requester', 'verdict': 'accepted', 'source': 'Simulated disposable fixture human; no real product acceptance'})
        original_decisions = accepted['delivery']['checkpoints']['US1']['decisions']
        finding = {'id': 'record-representation', 'rule': 'guidance.software-language.identity',
            'sourcePaths': ['src/Record.txt'], 'operations': ['maintain'],
            'repair': 'Remove insignificant trailing whitespace from existing admitted record representation',
            'checks': 'record-fixture through installed native Focused owner', 'materialEffect': 'preserving'}
        registered = delivery('16-register-existing-source-repair', {'action': 'conformance-register',
            'source': 'Fictional current source inspection', 'findings': [finding]})
        state = registered['delivery']
        assert state['checkpoints']['US1']['decisions'] == original_decisions
        repair_task = state['conformanceRepairs'][0]['taskIds'][0]
        assert repair_task == 'T003' and '- [X] T001' in target.read_text() and '- [ ] T002' in target.read_text()
        delivery('17-dependent-product-blocked', {'action': 'start', 'operation': 'continue'}, 2, 'PKC023')
        delivery('18-start-registered-conformance', {'action': 'start', 'operation': 'maintain', 'purpose': 'conformance'})
        write(consumer / 'src/Record.txt', 'BETA\n')
        run('19-real-negative-record-identity', [sys.executable, consumer / 'checks/record.py'], 1, 'record-identity-changed')
        write(consumer / 'src/Record.txt', 'ALPHA\n')
        reference = execute_check('20-real-repaired-check')
        write(target, target.read_text().replace('- [ ] ' + repair_task, '- [X] ' + repair_task))
        completion = request_for('21-repair-grouped-source-request', reference, action='conformance-complete', findings=['record-representation'])
        completion.pop('checkpoint')
        delivery('22-independent-impact-is-required', completion, 2, 'outcome assessment')
        completion['outcomeAssessment'] = {'review': 'review.md', 'reviewer': 'fictional-independent-reviewer',
            'conclusion': 'Whitespace representation repair preserves the same admitted ALPHA identity; no human outcome changed.',
            'materialEffects': {'record-representation': 'preserving'}}
        completed = delivery('23-complete-conformance', completion)
        assert completed['delivery']['conformanceRepairs'][0]['status'] == 'complete'
        delivery('24-engineering-refresh-remains-due', {'action': 'start', 'operation': 'continue'}, 2, 'engineering checks remain due')
        refreshed = delivery('25-refresh-existing-story-engineering', request_for('25a-current-story-request', reference))
        assert refreshed['delivery']['checkpoints']['US1']['human'] == 'accepted'
        assert refreshed['delivery']['checkpoints']['US1']['decisions'] == original_decisions
        resumed = delivery('26-resume-dependent-product', {'action': 'start', 'operation': 'continue'})
        assert resumed['delivery']['active']['operation'] == 'continue'
        retained = run('27-retained-original-baseline', [sys.executable, task, 'current', '--repository', consumer,
            '--feature-dir', 'specs/001-record', '--history'])
        assert retained['current']['baseline'] == baseline
        result.update(status='passed', repairTask=repair_task, priorHumanDecisionPreserved=True,
                      originalTaskIdentitiesPreserved=True, dependentProductResumed=True,
                      nativeSourceAcceptance='Not exercised; staged public analyzer capability remains a separate source gate')
        write(review / 'index.md', '# Installed conformance journey\n\n'
              'Inspect results.json for exact archive hash and installed subprocesses. Native bundle registration, missing-decision rejection/recovery, '
              'registered existing-source repair, dependent product blocking, actual finite identity negative/repaired positive, independent outcome assessment, '
              'story engineering refresh and resume ran through installed bytes. Original decisions and task identities were preserved. '
              'All authorship/human decisions are fictional. This text-state fixture does not qualify C# analyzers, provider/browser behavior or real product acceptance.\n')
        return result
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error))
        raise
    finally:
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        write(review / 'results.json', result)
        print('Installed conformance review: ' + native_path(review / 'index.md'), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path, default=ROOT / 'artifacts')
    args = parser.parse_args()
    result = scenario(args.archives.resolve())
    print(json.dumps({'status': result['status'], 'elapsedSeconds': result['elapsedSeconds']}))


if __name__ == '__main__':
    main()

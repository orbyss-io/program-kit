"""Resumable consumer decisions and scoped migrations; installation stays with the updater.

All mutating operations are explicit local commands. Scans are regenerable views.
Normal architecture/dependency authority and application acceptance remain independent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

RECORD = '.program-kit/consumer-upgrade.json'
PHASES = ('upgrade', 'specification', 'planning', 'tasks', 'implementation', 'delivery', 'production')
STATUSES = {'conditional', 'planned', 'analysis', 'implementation', 'deferred', 'blocked', 'completed', 'superseded'}
DISPOSITIONS = {'optional', 'retained', 'required', 'deferred', 'unresolved', 'not-applicable', 'corrected', 'adopted'}
CAUSES = {'detectable-omission', 'activated-condition', 'changed-inputs', 'new-scope', 'unresolved-cause'}
EXCLUDED = {'.git', 'bin', 'obj', 'node_modules', '__pycache__', '.auth', 'dist'}


class State(dict):
    expected_hash = None


@contextmanager
def record_lock(root):
    path = inside(root, 'artifacts/program-kit/consumer-upgrade/coordination.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def require(condition, message):
    if not condition:
        raise ValueError('PKU140 ' + message)


def inside(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute()
            and '..' not in Path(relative.replace('\\', '/')).parts, 'Expected a repository-relative path')
    path = root / relative
    # Reject even in-root links: snapshots and recovery must address the actual owned file.
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *path.parents) if p != root.parent), 'Linked mutation/evidence path: ' + relative)
    path = path.resolve()
    require(path.is_relative_to(root.resolve()), 'Path escapes the consumer: ' + relative)
    return path


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    sibling = path.with_name(path.name + '.' + uuid.uuid4().hex)
    try:
        with sibling.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        sibling.replace(path)
    finally:
        sibling.unlink(missing_ok=True)


def git(root, *args):
    excludes = '' if os.name == 'nt' else '/dev/null'
    result = subprocess.run(['git', '-c', 'safe.directory=' + str(root), '-c', 'core.excludesFile=' + excludes,
                             '-C', str(root), *args], capture_output=True, check=True)
    output = result.stdout.decode('utf-8')
    return output if '-z' in args else output.strip()


def inputs(root):
    """Whole consumer, including authored ignored intake; exclude generated caches/evidence."""
    paths = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0')
    for relative in ('docs/architecture', '.program-kit/specification-intake', 'eng', 'src', 'web', 'specs', 'contracts'):
        directory = inside(root, relative)
        if directory.is_dir():
            paths.extend(p.relative_to(root).as_posix() for p in directory.rglob('*') if p.is_file())
    return {p: sha(inside(root, p)) for p in sorted(set(paths)) if p and p != RECORD
            and p != '.program-kit/managed.json'
            and not EXCLUDED.intersection(Path(p).parts) and not p.startswith(('artifacts/', '.specify/', '.program-kit/sync/',
                '.program-kit/lifecycle/', '.program-kit/installation/', '.program-kit/selection-history/'))}


def capture(root, value):
    """Content-addressed diagnostic/input view; the coordination record keeps only its link."""
    relative = 'artifacts/program-kit/consumer-upgrade/inputs/' + digest(value) + '.json'
    path = inside(root, relative)
    if path.exists():
        require(read(path) == value, 'Captured input view changed')
    else:
        atomic(path, value)
    return {'path': relative, 'sha256': sha(path)}


def captured(root, value):
    if isinstance(value, dict) and set(value) == {'path', 'sha256'}:
        path = inside(root, value['path'])
        require(sha(path) == value['sha256'], 'Required local input view is missing or changed; reassess the affected scope')
        return read(path)
    return value or {}


def installation_inputs(root):
    files = {}
    directory = inside(root, '.specify')
    for path in directory.rglob('*') if directory.is_dir() else []:
        relative = path.relative_to(root).as_posix()
        if path.is_file() and not path.name.endswith('.lock') and not EXCLUDED.intersection(path.relative_to(root).parts) and not (
                '/cache/' in relative or relative.startswith('.specify/workflows/runs/')):
            files[relative] = sha(inside(root, relative))
    for manifest in directory.glob('integrations/*.manifest.json'):
        for relative in read(manifest).get('files', {}):
            files[relative] = sha(inside(root, relative))
    return files


def evidence(root, references):
    require(isinstance(references, list) and references, 'Concrete local evidence is required')
    result = {}
    for relative in references:
        path = inside(root, relative.split('#', 1)[0])
        require(path.is_file(), 'Missing evidence: ' + relative)
        result[relative] = sha(path)
    return result


def current(root, hashes):
    return all(sha(inside(root, p.split('#', 1)[0])) == expected for p, expected in hashes.items())


def preset_baseline(root, relative, agent):
    """Read-only native rendering of an active replacement preset's core skill.

    Core's initial integration hash predates preset overrides. Redirect only the
    native renderer's output and suppress registry writes; never install/reconcile
    into this consumer while inspecting it. Unsupported rendering stays unresolved.
    """
    path = inside(root, relative)
    if path.name != 'SKILL.md' or not path.parent.name.startswith('speckit-'):
        return None
    try:
        import tempfile
        from unittest.mock import patch
        from specify_cli.presets import PresetManager, PresetManifest, PresetResolver
        command = 'speckit.' + path.parent.name[len('speckit-'):].replace('-', '.')
        layers = PresetResolver(root).collect_all_layers(command, 'command')
        if not layers or layers[0].get('strategy') != 'replace':
            return None
        source = Path(layers[0]['path'])
        presets = inside(root, '.specify/presets')
        if not source.is_relative_to(presets):
            return None
        preset = presets / source.relative_to(presets).parts[0]
        inside(root, source.relative_to(root).as_posix())
        manifest = PresetManifest(preset / 'preset.yml')
        manager = PresetManager(root)
        with tempfile.TemporaryDirectory(prefix='consumer-upgrade-preset-view-') as name:
            output = Path(name)
            (output / path.parent.name).mkdir()
            with patch.object(manager, '_merge_pack_registered_skills'):
                manager._register_skills(manifest, preset, target_dir=output, target_agent=agent)
            rendered = output / path.parent.name / 'SKILL.md'
            return sha(rendered)
    except (ImportError, AttributeError, TypeError, ValueError, OSError):
        return None


def inventory(root):
    files = inputs(root)
    model = read(inside(root, 'docs/architecture/architecture-map.json'), {})
    selection = read(inside(root, 'docs/architecture/building-block-selection.json'), {})
    features = []
    for relative in files:
        if relative.startswith('specs/') and relative.endswith('/spec.md'):
            directory = str(Path(relative).parent).replace('\\', '/')
            phase = next((phase for phase, name in (('implementation', 'tasks.md'), ('tasks', 'plan.md'))
                          if inside(root, directory + '/' + name).is_file()), 'planning')
            from feature_context import feature_scope
            scope = feature_scope(root, inside(root, directory))
            features.append({'path': directory, 'nextPhase': phase,
                             'owners': scope['brief'].get('architectureScope', []), 'entry': scope['entry']})
    installed, customizations = {}, []
    for manifest in inside(root, '.specify/integrations').glob('*.manifest.json'):
        for relative, expected in read(manifest).get('files', {}).items():
            observed = sha(inside(root, relative))
            installed[relative] = {'sha256': observed, 'baselineSha256': expected if isinstance(expected, str) else None}
            if isinstance(expected, str) and observed != expected.removeprefix('sha256:'):
                preset = preset_baseline(root, relative, manifest.name.removesuffix('.manifest.json'))
                if preset:
                    installed[relative].update(baselineSha256=preset, baselineOwner='active-native-preset')
                if preset != observed:
                    customizations.append(relative)
    managed = read(inside(root, '.program-kit/managed.json'), {})
    for relative, item in managed.get('files', {}).items():
        expected = item.get('installedHash', item.get('baselineHash', item.get('templateHash')))
        observed = sha(inside(root, relative))
        installed[relative] = {'sha256': observed, 'baselineSha256': expected}
        if item.get('ownership') == 'managed' and expected and expected != observed:
            customizations.append(relative)
    return {'commit': git(root, 'rev-parse', 'HEAD'), 'files': files, 'ownedInstallation': installed,
            'customizations': sorted(set(customizations)), 'elements': model.get('elements', []),
            'contracts': model.get('strategic_model', {}).get('contracts', []), 'features': features,
            'dependencySelection': selection, 'projects': [p for p in files if p.endswith(('.csproj', '/package.json'))],
            'limitations': ([] if model.get('elements') else ['Ownership history is incomplete; inspect actual layout.'])}


def validate_scope(scope):
    require(isinstance(scope, dict) and set(scope) == {'owners', 'contracts', 'paths', 'features', 'shared'},
            'Scope needs owners, contracts, paths, features and shared')
    require(isinstance(scope['shared'], bool), 'shared must be boolean')
    for key in ('owners', 'contracts', 'paths', 'features'):
        require(isinstance(scope[key], list) and all(isinstance(v, str) and v for v in scope[key]), 'Invalid scope ' + key)
    require(scope['shared'] or any(scope[k] for k in ('owners', 'contracts', 'paths', 'features')), 'Scope cannot be empty')


def overlap(left, right):
    if left['shared'] or right['shared']:
        return True
    if any(set(left[k]) & set(right[k]) for k in ('owners', 'contracts', 'features')):
        return True
    return any(a == b or a.startswith(b.rstrip('/') + '/') or b.startswith(a.rstrip('/') + '/')
               for a in left['paths'] for b in right['paths'])


def load(root):
    payload = inside(root, RECORD).read_bytes()
    value = json.loads(payload)
    require(isinstance(value, dict) and value.get('schemaVersion') == 1, 'No supported consumer upgrade record')
    require(isinstance(value.get('migrations'), list) and isinstance(value.get('findings'), list), 'Invalid coordination record')
    identities = [m['id'] for m in value['migrations']]
    require(len(set(identities)) == len(identities), 'Duplicate migrations')
    for m in value['migrations']:
        validate_brief(m)
    state = State(value)
    state.expected_hash = hashlib.sha256(payload).hexdigest()
    return state


def method(identity):
    recipes = read(Path(__file__).resolve().parents[1] / 'references/consumer-migration-recipes.json')['recipes']
    selected = next((r for r in recipes if r['id'] == identity), None)
    require(selected is not None or identity == 'consumer-specific', 'Unknown maintained migration recipe')
    return selected or {'id': 'consumer-specific', 'version': 1,
                        'instruction': 'Bound the proposal against actual inputs and use existing substantive review.'}


def save(root, value, action, detail=None):
    with record_lock(root):
        if isinstance(value, State):
            require(value.expected_hash == sha(inside(root, RECORD)), 'Coordination changed concurrently; reload and reassess before saving')
        value.setdefault('events', []).append({'at': datetime.now(timezone.utc).isoformat(), 'action': action, 'detail': detail})
        atomic(inside(root, RECORD), value)
        if isinstance(value, State):
            value.expected_hash = sha(inside(root, RECORD))
    return value


def assess(root, guidance):
    from release_guidance import semantic_changes
    value = load(root)
    observed = inventory(root)
    changes = semantic_changes(guidance, value['sourceVersion'], value['targetVersion'])
    findings = []
    for change in changes['changes']:
        paths = [p for p in observed['files'] if any(Path(p).match(pattern) for pattern in change['selectors']['paths'])]
        # Signals identify candidates. They never establish consumer semantic compatibility.
        selection = observed['dependencySelection']
        selected = bool(selection.get('dependencyProfile')) or bool(selection.get('status') == 'Accepted')
        applies = change['selectors'].get('wholeConsumer', False) or paths or (
            change['selectors'].get('selectedDependencies') and selected)
        if not applies:
            continue
        scope = {'owners': sorted({t.get('placement', {}).get('owner') for t in selection.get('targets', [])
                                  if t.get('placement', {}).get('owner')}), 'contracts': [], 'paths': paths,
                 'features': [], 'shared': change['selectors'].get('wholeConsumer', False)}
        if not scope['shared'] and not any(scope[k] for k in ('owners', 'contracts', 'paths')):
            scope['shared'] = True
        previous = next((f for f in value['findings'] if f['changeId'] == change['id']), None)
        if previous and current(root, previous.get('evidence', {})) and captured(root, previous.get('scopeInputs')) == scoped_files(observed['files'], previous['scope']):
            findings.append(previous)
        else:
            findings.append({'changeId': change['id'], 'summary': change['summary'], 'scope': scope,
                             'disposition': 'optional' if change['kind'] == 'default' else 'unresolved',
                             'duePhase': change['duePhase'], 'alternatives': change['alternatives'],
                             'supportedRetention': change['supportedRetention'], 'method': change['method'],
                             'verification': change['verification'], 'assessedInputs': digest(observed['files']),
                             'scopeInputs': capture(root, scoped_files(observed['files'], scope)),
                             'evidence': {}, 'rationale': 'Inspect actual adoption and relevant code; signals are not a semantic verdict.'})
    if observed['customizations']:
        custom_scope = {'owners': [], 'contracts': [], 'paths': observed['customizations'], 'features': [], 'shared': False}
        old = next((f for f in value['findings'] if f['changeId'] == 'installed-customization'), None)
        finding = {'changeId': 'installed-customization', 'summary': 'Owned installed files differ from their recorded baseline',
                         'scope': custom_scope, 'scopeInputs': capture(root, scoped_files(observed['files'], custom_scope)),
                         'disposition': 'unresolved', 'duePhase': 'upgrade', 'evidence': {},
                         'rationale': 'Preserve these actual edits and establish a supported retained customization or reviewed affected remedy before replacement.',
                         'alternatives': ['Preserve supported customization', 'Reconcile affected edits under consumer authority']}
        findings.append(old if old and old['scope'] == custom_scope and current(root, old.get('evidence', {})) else finding)
    # Preserve earlier findings (including discoveries) as history, and do not erase local corrections.
    for old in value['findings']:
        if old['changeId'] not in {f['changeId'] for f in findings}:
            if any(m['origin'] == old['changeId'] and m['status'] not in {'completed', 'superseded'} for m in value['migrations']):
                findings.append({**old, 'targetReassessmentRequired': value.get('assessmentTargetVersion') != value['targetVersion']})
            else:
                value.setdefault('findingHistory', []).append(old)
    value.update(findings=findings, assessedInputs=capture(root, observed['files']), inventory=capture(root, observed),
                 historyLimitations=changes['limitations'], stage='assess')
    value['assessmentTargetVersion'] = value['targetVersion']
    return save(root, value, 'assess')


def decision(root, finding_id, amendment):
    value = load(root)
    finding = next((f for f in value['findings'] if f['changeId'] == finding_id), None)
    require(finding is not None, 'Unknown finding')
    require(amendment.get('disposition') in DISPOSITIONS and amendment.get('rationale'), 'Disposition and rationale required')
    validate_scope(amendment['scope'])
    hashes = evidence(root, amendment['evidence'])
    if amendment['disposition'] in {'retained', 'deferred'}:
        require(amendment.get('retainedCompatibility'), 'State concrete supported retained compatibility')
    if amendment.get('substantiveChange'):
        # Existing architecture review owns consequential changes; this record cannot accept an ADR.
        model = read(inside(root, 'docs/architecture/architecture-map.json'), {})
        accepted = [d for d in model.get('decisions', []) if d['id'] == amendment.get('decisionId') and d.get('status') == 'Accepted']
        require(len(accepted) == 1 and current(root, {accepted[0]['path']: accepted[0]['sha256']}),
                'Substantive change needs its existing Accepted ADR and current evidence')
    if amendment.get('adoptDependencyProfile'):
        # No invented parallel transition: its accepted output must already be the selected profile.
        selection = read(inside(root, 'docs/architecture/building-block-selection.json'), {})
        binding = read(inside(root, '.program-kit/dependency-profile.json'), {})
        require(selection.get('status') == 'Accepted' and binding.get('resolutionSha256') == amendment['adoptDependencyProfile'],
                'Use dependency_profiles.py draft/accept for the exact reviewed transition first')
        require(selection.get('catalog', {}).get('resolutionSha256') == binding['resolutionSha256']
                and current(root, {binding['catalogPath']: binding['catalogSha256'], binding['profilePath']: binding['profileSha256']}),
                'Accepted exact dependency transition inputs differ')
    if amendment['disposition'] == 'corrected':
        selected = [m for m in value['migrations'] if m['id'] in amendment.get('resolutionMigrations', [])]
        require(selected and all(m['origin'] == finding_id and m['status'] == 'completed' and checks_current(root, m.get('checks', []))
                                and current(root, m['semanticReview']['evidence']) for m in selected),
                'Correction requires current executed and reviewed migration outcomes')
        required_scope = amendment['scope']
        require(any(m['scope']['shared'] for m in selected) or not required_scope['shared'] and
                all(set(required_scope[k]) <= {v for m in selected for v in m['scope'][k]} for k in ('owners', 'contracts', 'features'))
                and all(any(p == q or p.startswith(q.rstrip('/') + '/') for m in selected for q in m['scope']['paths']) for p in required_scope['paths']),
                'Executed migrations do not cover the affected finding')
    value.setdefault('findingHistory', []).append(dict(finding))
    finding.update(amendment, evidence=hashes, assessedInputs=digest(inputs(root)))
    require(finding.get('duePhase') in PHASES, 'Invalid finding due phase')
    finding['scopeInputs'] = capture(root, scoped_files(inputs(root), finding['scope']))
    value['stage'] = 'decide'
    return save(root, value, 'decision', finding_id)


def validate_brief(brief):
    for key in ('id', 'origin', 'reason', 'outcome', 'trigger', 'method', 'nextAction'):
        require(isinstance(brief.get(key), str) and brief[key].strip(), 'Migration requires ' + key)
    require(re.fullmatch(r'[a-z][a-z0-9-]{0,63}', brief['id']), 'Migration needs a stable ID')
    validate_scope(brief['scope'])
    require(brief.get('duePhase') in PHASES and brief.get('status') in STATUSES, 'Invalid migration phase/status')
    for key in ('invariants', 'dependencies', 'uncertainties'):
        require(isinstance(brief.get(key), list) and all(isinstance(v, str) and v for v in brief[key]), 'Migration requires ' + key)
    require(bool(brief['invariants']), 'Preserved behavior/invariants required')
    require(bool(brief.get('evidence')), 'Migration requires applicability evidence')
    require(not (brief['status'] == 'deferred' and brief['duePhase'] == 'upgrade'), 'An immediate incompatibility cannot be deferred')
    require(not (brief['status'] == 'conditional' and brief['duePhase'] == 'upgrade'),
            'Resolve applicability of an immediate incompatibility before upgrade completion')
    if brief['status'] == 'deferred':
        require(brief.get('retainedCompatibility'), 'Deferred migration needs supported retained compatibility')


def add_migration(root, brief, cause=None):
    value = load(root)
    require(brief['id'] not in {m['id'] for m in value['migrations']}, 'Group shared work once; ID already exists')
    require(brief['status'] in {'planned', 'conditional', 'deferred', 'blocked'}, 'New brief cannot imply implementation/completion')
    brief = dict(brief, evidence=evidence(root, brief['evidence']))
    validate_brief(brief)
    brief['recipe'] = method(brief['method'])
    known = {m['id'] for m in value['migrations']}
    require(set(brief['dependencies']) <= known, 'Migration dependencies must already exist')
    if cause:
        require(cause in CAUSES, 'Unknown discovery cause')
        require(brief.get('discoveryEvidence') and brief.get('recovery'), 'Discovery requires classification evidence and local recovery action')
        brief['cause'] = cause
        brief['regressionRequired'] = cause == 'detectable-omission'
    value['migrations'].append(brief)
    return save(root, value, 'discovery' if cause else 'migration-brief', brief['id'])


def revise_migration(root, identity, amendment, cause):
    value = load(root)
    item = next(m for m in value['migrations'] if m['id'] == identity)
    require(cause in CAUSES and amendment.get('discoveryEvidence') and amendment.get('recovery'),
            'Classify changed scope/condition with evidence and local recovery')
    require(amendment.get('status') in {'planned', 'conditional', 'deferred', 'blocked', 'superseded'}, 'Revised scope needs fresh analysis before completion')
    if amendment['status'] == 'superseded':
        require(amendment.get('retirementReason') and amendment.get('reviewProvenance'), 'Retirement needs actual target-semantic/consumer-intent review; it is not execution completion')
    value.setdefault('migrationHistory', []).append(dict(item))
    updated = {**item, **amendment, 'id': identity, 'cause': cause,
               'evidence': evidence(root, amendment['evidence']), 'regressionRequired': cause == 'detectable-omission'}
    validate_brief(updated)
    require(set(updated['dependencies']) <= {m['id'] for m in value['migrations']} - {identity}, 'Invalid migration dependencies')
    updated.pop('checks', None)
    updated.pop('semanticReview', None)
    item.clear()
    item.update(updated)
    return save(root, value, 'migration-local-recovery', identity)


def scoped_files(files, scope):
    # Architecture/dependency changes may affect the scoped interpretation, irrespective of code paths.
    return {p: h for p, h in files.items() if scope['shared'] or p in {'global.json', 'Directory.Packages.props', 'NuGet.config', 'package.json', 'package-lock.json'}
            or p.startswith(('docs/architecture/', 'eng/', '.program-kit/dependency-profile'))
            or any(p == d or p.startswith(d.rstrip('/') + '/') for d in scope['paths'] + scope['features'])}


def pickup(root, identity, plan=None):
    value = load(root)
    migration = next(m for m in value['migrations'] if m['id'] == identity)
    require(migration['status'] != 'superseded', 'Superseded work needs a reviewed new scope before pickup')
    require(migration['scope']['shared'] or migration['scope']['paths'],
            'Resolve actual affected code/contract paths during focused analysis before pickup; owner names alone cannot bind verification')
    require(all(next(m for m in value['migrations'] if m['id'] == dep)['status'] == 'completed'
                for dep in migration['dependencies']), 'Resolve migration prerequisites before pickup')
    files = scoped_files(inputs(root), migration['scope'])
    previous = captured(root, migration.get('pickupInputs'))
    changed = sorted(p for p in files.keys() | previous.keys() if files.get(p) != previous.get(p))
    if migration['status'] == 'completed' and not changed:
        return migration
    migration.update(status='analysis', pickupInputs=capture(root, files), changedInputs=changed,
                     nextAction='Inspect current code/dependencies, resolve material choices, then use normal plan/tasks/tests. ' + migration['method'])
    if plan:
        require(inside(root, plan).name == 'plan.md', 'Use the ordinary detailed migration plan.md')
        migration['plan'] = plan
        migration['planEvidence'] = evidence(root, [plan])
    save(root, value, 'migration-pickup', identity)
    return migration


def checks_current(root, checks):
    return bool(checks) and all(c['exitCode'] == 0 and check_inputs_current(root, c)
                              and current(root, c['evidence']) for c in checks)


def check_inputs_current(root, check):
    if check.get('executionRoot') and check['executionRoot'] != str(root):
        return False
    observed = inputs(root)
    expected = scoped_files(observed, check['scope']) if check.get('scope') else observed
    return expected == captured(root, check['inputs'])


def run_checks(root, commands, affected=None):
    require(isinstance(commands, list) and commands, 'Explicit local verification commands required')
    files = inputs(root)
    directory = inside(root, 'artifacts/program-kit/consumer-upgrade/' + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    results = []
    for offset, check in enumerate(commands):
        require(isinstance(check.get('command'), list) and check['command'] and
                all(isinstance(v, str) and v for v in check['command']), 'Use argument vectors, never shell strings')
        from compatibility_process import run
        paths = [directory / f'{offset}-{name}.log' for name in ('stdout', 'stderr')]
        with paths[0].open('wb') as out, paths[1].open('wb') as err:
            code = run(check['command'], root, out, err, check.get('timeout', 300),
                       env={**os.environ, 'SPECIFY_INIT_DIR': str(root)})
        logs = [p.relative_to(root).as_posix() for p in paths]
        results.append({'id': check['id'], 'command': check['command'], 'exitCode': code,
                        'executionRoot': str(root),
                        'affected': check.get('affected', True), 'scope': affected, 'inputs': capture(root, scoped_files(files, affected) if affected else files),
                        'resultSignature': digest({'exitCode': code, 'streams': [sha(p) for p in paths]}),
                        'evidence': evidence(root, logs)})
    atomic(directory / 'checks.json', results)
    require(inputs(root) == files, 'Verification changed authored inputs; inspect preserved results and rerun with stable inputs')
    return results


def verify(root, commands, identity=None, baseline=False):
    value = load(root)
    migration = next((m for m in value['migrations'] if m['id'] == identity), None) if identity else None
    if identity:
        require(migration is not None and migration['status'] in {'analysis', 'implementation', 'blocked'}, 'Pick up migration first')
        require(migration.get('plan') and current(root, migration['planEvidence']), 'Current normal migration plan required')
        plan_path = inside(root, migration['plan'])
        require(plan_path.with_name('tasks.md').is_file(), 'Create normal detailed migration tasks and tests at pickup')
    results = run_checks(root, commands, migration['scope'] if migration else None)
    if baseline:
        value['baselineChecks'] = results
    else:
        previous = {c['id']: c for c in value.get('baselineChecks', [])}
        for result in results:
            old = previous.get(result['id'])
            result['classification'] = ('passed' if result['exitCode'] == 0 else
                'pre-existing' if old and old['command'] == result['command'] and old.get('resultSignature') == result['resultSignature'] else 'introduced-or-unresolved')
        if migration:
            migration['checks'] = results
            migration['status'] = 'implementation' if all(c['exitCode'] == 0 for c in results) else 'blocked'
        else:
            value['checks'] = results
            value['stage'] = 'validate'
    return save(root, value, 'baseline-checks' if baseline else 'verification', identity)


def complete(root, identity, review):
    review = dict(review)
    value = load(root)
    migration = next(m for m in value['migrations'] if m['id'] == identity)
    require(checks_current(root, migration.get('checks', [])), 'Executed current passing checks required; planning is not completion')
    require(review.get('outcome') and review.get('invariantsVerified') and review.get('provenance'), 'Actual semantic review and invariant results required')
    review['evidence'] = evidence(root, review['evidence'])
    if migration.get('regressionRequired'):
        regression = review.get('regression')
        require(isinstance(regression, dict) and regression.get('path') and regression.get('checkId'),
                'Demonstrated omission needs a reproducible regression path and executed checkId')
        require(any(c['id'] == regression['checkId'] for c in migration['checks']),
                'Demonstrated omission regression check was not executed')
        review['regressionEvidence'] = evidence(root, [regression['path']])
    migration.update(status='completed', semanticReview=review, nextAction='Retain evidence; changed inputs reopen affected work')
    migration['completedInputs'] = capture(root, scoped_files(inputs(root), migration['scope']))
    return save(root, value, 'migration-completed', identity)


def request_scope(root, brief=None, feature=None):
    if feature:
        from feature_context import feature_scope
        resolved = feature_scope(root, feature)
        brief = resolved['brief']
        paths = [feature.relative_to(root).as_posix()]
        text = '\n'.join((feature / n).read_text(encoding='utf-8') for n in ('spec.md', 'plan.md', 'tasks.md') if (feature / n).is_file())
        # Exact referenced project/contract paths are scope signals, not compatibility proof.
        paths += [p.relative_to(root).as_posix() for name in ('src', 'web', 'contracts') for p in (root / name).rglob('*')
                  if p.is_file() and not EXCLUDED.intersection(p.relative_to(root).parts) and p.relative_to(root).as_posix() in text]
    else:
        paths = (brief or {}).get('affectedPaths', [])
    brief = brief or {}
    from feature_knowledge import project
    projection = project(root, brief.get('architectureScope')) if brief.get('architectureScope') else None
    contracts = brief.get('contracts', [])
    owners = brief.get('architectureScope', [])
    if projection:
        owned = set(owners)
        elements = projection['elements']
        while True:
            expanded = owned | {e['id'] for e in elements if e.get('parent') in owned}
            if expanded == owned: break
            owned = expanded
        while True:
            parents = {e['parent'] for e in elements if e['id'] in owned and e.get('parent')}
            if parents <= owned: break
            owned |= parents
        owners = sorted(owned)
        contracts = sorted(set(contracts) | {c['id'] for c in projection['strategic_model']['contracts']})
    return {'owners': owners, 'contracts': contracts, 'paths': paths, 'features': paths[:1] if feature else [], 'shared': False}


def scan(root, scope, phase):
    """Read-only, pre-directory compatible; absence of scope yields an honest limited view."""
    validate_scope(scope) if any(scope[k] for k in ('owners', 'contracts', 'paths', 'features')) or scope['shared'] else None
    require(phase in PHASES, 'Unknown work phase')
    if not inside(root, RECORD).is_file():
        return {'recordPresent': False, 'canProceed': True, 'migrations': [], 'findings': [],
                'limitations': ['No upgrade assessment exists; use actual architecture/code and normal review.']}
    value = load(root)
    known = scope['shared'] or any(scope[k] for k in ('owners', 'contracts', 'paths', 'features'))
    files = inputs(root)
    matches, blockers = [], []
    for m in value['migrations']:
        if m['status'] == 'superseded':
            continue
        if not overlap(m['scope'], scope):
            continue
        previous = m.get('completedInputs', m.get('pickupInputs'))
        compared = captured(root, previous) if previous else scoped_files(captured(root, value.get('assessedInputs')), m['scope'])
        changed = scoped_files(files, m['scope']) != compared
        done = m['status'] == 'completed' and checks_current(root, m.get('checks', [])) and current(root, m['semanticReview']['evidence'])
        pending = not done
        due = PHASES.index(m['duePhase']) <= PHASES.index(phase)
        condition_assessment = m['status'] == 'conditional' and known and not scope['shared']
        blocks = pending and due and (m['status'] != 'conditional' or condition_assessment)
        matches.append({'id': m['id'], 'status': 'stale' if m['status'] == 'completed' and pending else m['status'],
                        'changedInputs': changed, 'duePhase': m['duePhase'], 'blocksNow': blocks, 'nextAction': m['nextAction']})
        matches[-1]['conditionAssessmentRequired'] = condition_assessment
        if blocks:
            blockers.append(m['id'])
    findings = []
    for finding in value['findings']:
        if not overlap(finding['scope'], scope):
            continue
        fresh = current(root, finding.get('evidence', {})) and (
            scoped_files(files, finding['scope']) == (captured(root, finding['scopeInputs']) if finding.get('scopeInputs') else
                scoped_files(captured(root, value.get('assessedInputs')), finding['scope'])))
        pending = finding['disposition'] in {'unresolved', 'required'} or not fresh
        covered = any(m['origin'] == finding['changeId'] and overlap(m['scope'], finding['scope']) for m in value['migrations'])
        # Retained compatibility must resolve the finding itself; a plan alone cannot discharge it.
        blocks = pending and PHASES.index(finding['duePhase']) <= PHASES.index(phase)
        findings.append({'id': finding['changeId'], 'disposition': finding['disposition'], 'stale': not fresh,
                         'blocksNow': blocks, 'migrationRecorded': covered, 'nextAction': finding['rationale']})
        if blocks:
            blockers.append(finding['changeId'])
    model = read(inside(root, 'docs/architecture/architecture-map.json'), {})
    limitations = [] if known else ['Scope is unknown; refine owners/contracts before claiming scoped compatibility.']
    if not model.get('elements') or not scope['owners'] and not scope['shared']:
        limitations.append('Ownership provenance is incomplete; inspect actual code/contracts before a semantic compatibility verdict.')
    return {'recordPresent': True, 'canProceed': not blockers, 'blockers': blockers, 'migrations': matches,
            'findings': findings, 'limitations': limitations,
            'applicationAcceptanceEstablished': False}


def readiness(root):
    value = load(root)
    scope = {'owners': [], 'contracts': [], 'paths': [], 'features': [], 'shared': True}
    result = scan(root, scope, 'upgrade')
    checks = value.get('checks', [])
    valid = bool(checks) and all(check_inputs_current(root, c) and current(root, c['evidence']) and
                                (c['exitCode'] == 0 or c.get('classification') == 'pre-existing' and not c['affected']) for c in checks)
    convergence = read(inside(root, '.program-kit/installation/migration.json'), {})
    from release_guidance import completion
    declared_plan = convergence.get('plan')
    expected = completion(declared_plan, convergence.get('checks', {})) if isinstance(declared_plan, dict) else {}
    installed_expected = captured(root, value.get('installedInputs'))
    installed_actual = installation_inputs(root)
    toolkit = (convergence.get('toVersion') == value['targetVersion'] and expected.get('migrationCompletionEstablished') is True
               and convergence.get('migrationCompletionEstablished') is True
               and expected.get('planSha256') == convergence.get('planSha256')
               and installed_expected == installed_actual)
    assessed = value.get('assessmentTargetVersion') == value['targetVersion'] and bool(value.get('inventory'))
    resolved = assessed and all(f['disposition'] not in {'unresolved', 'required'} and current(root, f.get('evidence', {}))
                   and scoped_files(inputs(root), f['scope']) == (captured(root, f['scopeInputs']) if f.get('scopeInputs') else
                       scoped_files(captured(root, value.get('assessedInputs')), f['scope']))
                   for f in value['findings'])
    return {**result, 'toolkitConverged': toolkit, 'requiredChecksCurrent': valid,
            'toolkitChecks': {'targetVersionMatched': convergence.get('toVersion') == value['targetVersion'],
                              'migrationCompletionEstablished': expected.get('migrationCompletionEstablished') is True,
                              'planDigestMatched': expected.get('planSha256') == convergence.get('planSha256'),
                              'changedInstallationInputs': [p for p in installed_expected.keys() | installed_actual.keys()
                                                            if installed_expected.get(p) != installed_actual.get(p)][:20]},
            'assessmentPerformed': assessed, 'assessmentResolved': resolved,
            'upgradePrepared': toolkit and valid and resolved and result['canProceed'],
            'activated': value.get('stage') == 'activated' and toolkit and valid and resolved and result['canProceed'],
            'nextAction': 'Resolve due findings and verify affected behavior; integrate and activate separately.'}


def reconcile(root):
    """Suggest affected phases; never regenerate specifications or saved task IDs."""
    value = load(root)
    actions = []
    for feature in inventory(root)['features']:
        directory = inside(root, feature['path'])
        scope = request_scope(root, feature=directory)
        result = scan(root, scope, feature['nextPhase'])
        affected = result['migrations'] + result['findings']
        if not affected:
            continue
        phases = {f['changeId']: f['duePhase'] for f in value['findings']}
        due = min((item['duePhase'] if 'duePhase' in item else phases[item['id']] for item in affected), key=PHASES.index)
        resume = min((feature['nextPhase'], due), key=PHASES.index)
        actions.append({'feature': feature['path'], 'resumeFrom': resume, 'impacts': affected,
                        'instruction': 'Edit affected existing documents in place; retain requirements, intake, task IDs and completed work. Run normal consistency/preflight at the repaired boundary.'})
    return {'actions': actions, 'bootstrapRestartRequired': False, 'confirmationPerformed': False}


def export_report(root, destination):
    from compatibility_diagnostics import sanitize
    value = load(root)
    # Field allowlist: no inventory, full source/architecture, environment or raw archives.
    selected = {k: value.get(k) for k in ('sourceVersion', 'targetVersion', 'historyLimitations')}
    binding = read(inside(root, '.program-kit/dependency-profile.json'), {})
    selected['profiles'] = {'source': value.get('sourceProfile'),
                            'target': {k: binding.get(k) for k in ('id', 'resolutionSha256', 'familyReleases')}}
    selected['findings'] = [{k: f.get(k) for k in ('changeId', 'disposition', 'duePhase', 'rationale')} for f in value['findings']]
    selected['migrations'] = [{**{k: m.get(k) for k in ('id', 'origin', 'cause', 'scope', 'method', 'duePhase', 'status', 'reason', 'outcome', 'recovery', 'uncertainties')},
                              'observedOutcome': m.get('semanticReview', {}).get('outcome'),
                              'checks': [{k: c.get(k) for k in ('id', 'exitCode', 'classification', 'resultSignature')} for c in m.get('checks', [])]}
                              for m in value['migrations']]
    selected['checks'] = [{k: c.get(k) for k in ('id', 'exitCode', 'classification')} for c in value.get('checks', [])]
    selected['reproduction'] = value.get('reproduction', 'Use the named maintained method and disposable resources; local logs remain local.')
    selected['recoveryOutcome'] = value.get('recoveryOutcome', 'Not recorded')
    redactions, truncations = 0, 0
    def bound(obj, limit=20, text_limit=1024, depth=0):
        nonlocal redactions, truncations
        if depth > 8:
            truncations += 1
            return '[TRUNCATED]'
        if isinstance(obj, str):
            safe = sanitize(obj)
            safe = re.sub(r'[A-Za-z]:[\\/][^"\n,;|]*|(?<![\w:])/(?:Users|home)/[^"\n,;|]*', '[LOCAL-PATH]', safe)
            safe = re.sub(r'(?i)(https?://)[^/\s"@]+@', r'\1[REDACTED]@', safe)
            safe = re.sub(r'(?i)((?:api[_-]?key|token|secret|credential)["\s]*[:=]["\s]*)[^\s,"}]+', r'\1[REDACTED]', safe)
            safe = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[EMAIL]', safe)
            redactions += safe != obj
            truncations += len(safe) > text_limit
            return safe[:text_limit]
        if isinstance(obj, list):
            truncations += len(obj) > limit
            return [bound(v, limit, text_limit, depth + 1) for v in obj[:limit]]
        if isinstance(obj, dict):
            items = list(obj.items())
            maximum = len(items) if depth == 0 else max(1, limit)
            truncations += len(items) > maximum
            return {bound(k, limit, text_limit, depth + 1): bound(v, limit, text_limit, depth + 1) for k, v in items[:maximum]}
        return obj
    bounded = bound(selected)
    # Cap the entire portable report as well as individual fields. Keep the original
    # local record and state the reduction instead of exporting a run archive.
    limit = 20
    while len(json.dumps(bounded, ensure_ascii=False, indent=2).encode('utf-8')) > 60000:
        limit //= 2
        bounded = bound(bounded, limit, max(64, 1024 * max(1, limit) // 20))
    report = {'schemaVersion': 1, 'report': bounded, 'provenance': {'recordSha256': sha(inside(root, RECORD)),
              'derivedAt': datetime.now(timezone.utc).isoformat(), 'redacted': bool(redactions),
              'truncated': bool(truncations), 'redactedFields': redactions, 'truncatedFields': truncations,
              'maximumBytes': 65536, 'rawLogsIncluded': False, 'sent': False}}
    require(destination != inside(root, RECORD) and not destination.exists(), 'Export needs a fresh local file; originals are immutable')
    atomic(destination, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'assess', 'decide', 'brief', 'discover', 'revise', 'pickup', 'verify', 'baseline', 'complete', 'scan', 'reconcile', 'status', 'export'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--input', help='Local JSON amendment, brief, request, review or check vectors')
    parser.add_argument('--guidance', default=str(Path(__file__).resolve().parents[1] / 'references/release-guidance'))
    parser.add_argument('--id')
    parser.add_argument('--cause', choices=sorted(CAUSES))
    parser.add_argument('--feature-dir')
    parser.add_argument('--phase', choices=PHASES, default='specification')
    parser.add_argument('--plan')
    parser.add_argument('--output')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        data = read(inside(root, args.input)) if args.input else None
        if args.action == 'inventory': result = inventory(root)
        elif args.action == 'assess': result = assess(root, Path(args.guidance).resolve())
        elif args.action == 'decide': result = decision(root, args.id, data)
        elif args.action in ('brief', 'discover'): result = add_migration(root, data, args.cause if args.action == 'discover' else None)
        elif args.action == 'revise': result = revise_migration(root, args.id, data, args.cause)
        elif args.action == 'pickup': result = pickup(root, args.id, args.plan)
        elif args.action in ('verify', 'baseline'): result = verify(root, data, args.id, args.action == 'baseline')
        elif args.action == 'complete': result = complete(root, args.id, data)
        elif args.action == 'scan': result = scan(root, request_scope(root, data, inside(root, args.feature_dir) if args.feature_dir else None), args.phase)
        elif args.action == 'reconcile': result = reconcile(root)
        elif args.action == 'status': result = readiness(root)
        else: result = export_report(root, inside(root, args.output))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration, subprocess.SubprocessError) as error:
        print('PKU140 ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

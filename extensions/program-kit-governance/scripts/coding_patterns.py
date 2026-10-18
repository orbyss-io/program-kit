"""Versioned pattern inputs for the existing coding-unit composer.

No submitted command is executed. Qualification references ordinary maintained
verification and authored review; content binding is attribution, not approval.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from knowledge_sources import confined, effective_rule, resolve, select

LOCAL = 'docs/architecture/coding-patterns.json'
CHOICES = re.compile(r'<!-- program-kit:pattern-choices -->\s*(.*?)\s*<!-- /program-kit:pattern-choices -->', re.S)
IDENTITY = re.compile(r'[a-z][a-z0-9.-]{0,95}')


def fail(message):
    # Deliberately exclude submitted prose, source, native streams and private paths.
    raise ValueError('PKP001 ' + message + '; owner: pattern maintainer; repair: inspect the local declaration and prepare again')


def require(condition, message):
    if not condition:
        fail(message)


def decode(content):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate declaration key')
            value[key] = item
        return value
    return json.loads(content, object_pairs_hook=pairs,
                      parse_constant=lambda _: fail('invalid numeric declaration'))


def load(path):
    return decode(path.read_text(encoding='utf-8-sig'))


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def strings(value):
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value) and len(set(value)) == len(value)


def reference(value):
    require(isinstance(value, dict) and set(value) <= {'root', 'path', 'selector'}
            and value.get('root') in ('repository', 'extensions') and isinstance(value.get('path'), str) and bool(value['path']), 'invalid source reference')
    if 'selector' in value:
        require(isinstance(value['selector'], dict), 'invalid source selector')


def referenced(ref, root, extensions):
    reference(ref)
    path = confined(root if ref['root'] == 'repository' else extensions, ref['path'])
    require(path.is_file(), 'missing declared input')
    raw = path.read_bytes()
    if ref.get('selector'):
        raw = select(raw.decode('utf-8-sig').replace('\r\n', '\n'), ref['selector']).encode()
    require(bool(raw.strip()), 'empty declared input')
    return {'reference': ref, 'sha256': sha(raw)}


def merge(catalog, root):
    """Local data extends the same catalog; identities can never shadow an owner."""
    value = copy.deepcopy(catalog)
    if root is None or not (root / LOCAL).is_file():
        return value
    local = load(root / LOCAL)
    require(isinstance(local, dict) and set(local) == {'schemaVersion', 'sources', 'rules', 'codingUnits'}
            and type(local['schemaVersion']) is int and local['schemaVersion'] == 1, 'unsupported local pattern document')
    require(isinstance(local['sources'], list) and isinstance(local['rules'], dict) and isinstance(local['codingUnits'], list), 'invalid local pattern collections')
    ids = {s['id'] for s in value['sources']}
    for source in local['sources']:
        require(isinstance(source, dict) and set(source) == {'id', 'locator'} and isinstance(source['id'], str)
                and IDENTITY.fullmatch(source['id']) and source['id'] not in ids, 'duplicate or invalid local source identity')
        require(isinstance(source['locator'], dict) and set(source['locator']) == {'kind', 'path'}
                and source['locator']['kind'] == 'repository' and isinstance(source['locator']['path'], str), 'local source must remain repository-owned')
        try:
            confined(root, source['locator']['path'])
        except ValueError:
            fail('local source escapes repository')
        ids.add(source['id'])
        value['sources'].append(source)
    for identity, rule in local['rules'].items():
        require(IDENTITY.fullmatch(identity) and identity not in value['rules'], 'local rule cannot shadow a canonical owner')
        require(isinstance(rule, dict) and set(rule) <= {'source', 'selector', 'owner', 'level', 'limits', 'bindings', 'display'}
                and {'source', 'selector', 'owner', 'level', 'limits'} <= set(rule)
                and rule['source'] in {s['id'] for s in local['sources']}
                and rule['level'] in ('mandatory', 'conditional', 'recommended'), 'invalid local canonical binding')
        require(isinstance(rule['selector'], dict) and isinstance(rule['selector'].get('kind'), str)
                and all(isinstance(rule[k], str) and rule[k].strip() for k in ('owner', 'limits')), 'invalid local canonical selector or owner')
        bindings = rule.get('bindings', {})
        require(isinstance(bindings, dict) and set(bindings) <= {'producers', 'checks', 'recipes', 'review'}
                and all(strings(bindings[k]) for k in ('producers', 'checks', 'recipes') if k in bindings)
                and ('review' not in bindings or isinstance(bindings['review'], str)), 'invalid local execution/evaluation bindings')
        value['rules'][identity] = rule
    for unit in local['codingUnits']:
        require(isinstance(unit, dict) and 'pattern' in unit, 'local coding unit requires a versioned pattern')
    value['codingUnits'].extend(local['codingUnits'])
    return value


def validate(catalog):
    units = {u['id']: u for u in catalog.get('codingUnits', [])}
    patterns = {i: u['pattern'] for i, u in units.items() if 'pattern' in u}
    for identity, p in patterns.items():
        require(IDENTITY.fullmatch(identity), 'invalid bounded pattern identity')
        allowed = {'schemaVersion', 'semanticId', 'version', 'owner', 'status', 'invariantRuleIds', 'compatibility',
                   'alternatives', 'replaces', 'inputs', 'examples', 'checks', 'review', 'evidence', 'limits', 'provenance'}
        require(isinstance(p, dict) and set(p) == allowed and type(p['schemaVersion']) is int and p['schemaVersion'] == 1, 'unsupported pattern contract')
        require(isinstance(p['semanticId'], str) and IDENTITY.fullmatch(p['semanticId'])
                and isinstance(p['version'], str) and re.fullmatch(r'\d+\.\d+\.\d+', p['version'])
                and p['status'] in ('draft', 'active', 'retired'), 'invalid pattern identity, version or status')
        require(all(isinstance(p[k], str) and p[k].strip() for k in ('owner', 'limits', 'provenance')), 'missing owner, provenance or limits')
        for key in ('invariantRuleIds', 'alternatives', 'replaces'):
            require(strings(p[key]), 'invalid pattern rule or relationship list')
        require(set(p['invariantRuleIds']) <= catalog['rules'].keys(), 'unknown invariant rule')
        require(isinstance(p['inputs'], list) and isinstance(p['examples'], dict) and set(p['examples']) == {'positive', 'negative'}
                and all(isinstance(p['examples'][k], list) for k in ('positive', 'negative')), 'invalid pattern inputs or examples')
        for ref in p['inputs'] + p['examples']['positive'] + p['examples']['negative']:
            reference(ref)
        require(isinstance(p['compatibility'], dict) and set(p['compatibility']) <= {'profiles', 'excludeProfiles', 'frameworks', 'packages'}, 'unknown compatibility field')
        for key in ('profiles', 'excludeProfiles', 'frameworks'):
            require(strings(p['compatibility'].get(key, [])), 'invalid compatibility list')
        packages = p['compatibility'].get('packages', {})
        require(isinstance(packages, dict) and all(isinstance(k, str) and isinstance(v, str) and v for k, v in packages.items()), 'package compatibility requires exact observed versions')
        require(isinstance(p['checks'], list) and isinstance(p['evidence'], list), 'invalid evidence declarations')
        for record in p['evidence']:
            require(isinstance(record, dict) and set(record) <= {'fingerprint', 'checks', 'boundAtUtc', 'expiresAt'}
                    and {'fingerprint', 'checks', 'boundAtUtc'} <= set(record)
                    and isinstance(record['fingerprint'], str) and re.fullmatch('[a-f0-9]{64}', record['fingerprint'])
                    and isinstance(record['checks'], list) and isinstance(record['boundAtUtc'], str)
                    and ('expiresAt' not in record or isinstance(record['expiresAt'], str)), 'invalid historical evidence binding')
        for check in p['checks']:
            require(isinstance(check, dict) and (set(check) == {'kind', 'id'} and check['kind'] == 'toolkit'
                    or set(check) == {'kind', 'project', 'arguments', 'configuration'} and check['kind'] == 'native'), 'unsupported check adapter; submitted commands are not admitted')
            if check['kind'] == 'toolkit':
                require(isinstance(check['id'], str) and IDENTITY.fullmatch(check['id']), 'invalid check identity')
            else:
                require(isinstance(check['project'], str) and isinstance(check['arguments'], list)
                        and all(isinstance(v, str) for v in check['arguments']) and isinstance(check['configuration'], str), 'invalid native check binding')
        if p['review'] is not None:
            reference(p['review'])
    # Validate every shape before traversing cross-declaration relationships.
    for identity, p in patterns.items():
        for other in p['alternatives'] + p['replaces']:
            require(other in patterns and other != identity and patterns[other]['semanticId'] == p['semanticId'], 'pattern relationship has no compatible pattern owner')
            require(set(patterns[other]['invariantRuleIds']) <= set(p['invariantRuleIds']), 'alternative cannot omit an accepted invariant')
            mandatory = set(patterns[other]['invariantRuleIds'])
            other_unit = units[other]
            identities = set(other_unit.get('ruleIds', []))
            for requirement in catalog['requirements']:
                if requirement['id'] in other_unit.get('requirementIds', []):
                    identities.update(requirement.get('ruleIds', []))
            mandatory.update(i for i in identities if effective_rule(catalog, i)['level'] in ('mandatory', 'conditional'))
            selected_rules = set(p['invariantRuleIds']) | set(units[identity].get('ruleIds', []))
            require(mandatory <= selected_rules, 'replacement cannot omit a mandatory canonical contract')
        require(not any(identity in patterns[o]['replaces'] for o in p['replaces']), 'cyclic pattern replacement')
    return patterns


def context(profiles, projects, configuration='Debug', framework=None):
    evaluated = [p for p in projects if p.get('status') == 'evaluated']
    # Reuse native evaluated SDK facts and the installed runtime's read-only inventory.
    # A retained text file alone must not conceal a changed runtime installation.
    runtimes = subprocess.check_output(['dotnet', '--list-runtimes'], text=True, encoding='utf-8', timeout=10).splitlines() if evaluated else []
    return {'profiles': sorted(profiles), 'configuration': configuration, 'framework': framework,
            'sdks': sorted({p['properties'].get('NETCoreSdkVersion', '') for p in evaluated}), 'runtimeInventory': runtimes,
            'frameworks': sorted({p['properties'].get('TargetFramework', '') for p in projects if p.get('status') == 'evaluated'}),
            'packages': sorted({(r['id'], r.get('version')) for p in projects for r in p.get('packages', [])})}


def compatibility(pattern, observed):
    c = pattern['compatibility']
    reasons = []
    if not set(c.get('profiles', [])) <= set(observed['profiles']):
        reasons.append('required profile absent')
    if set(c.get('excludeProfiles', [])) & set(observed['profiles']):
        reasons.append('excluded profile present')
    if c.get('frameworks') and (not observed['frameworks'] or not set(observed['frameworks']) <= set(c['frameworks'])):
        reasons.append('evaluated framework incompatible or unavailable')
    packages = observed['packages']
    for name, version in c.get('packages', {}).items():
        values = {v for n, v in packages if n.casefold() == name.casefold()}
        if values != {version}:
            reasons.append('exact selected package incompatible or unavailable')
    return reasons


def current_check(root, declaration, retained=None):
    """Inspect existing owners. This function never dispatches a check."""
    from dotnet_adapter import bootstrap
    bootstrap()
    from owned_scratch import native_path
    root = Path(native_path(root)).resolve()
    import repository_verification as native
    import toolkit_verification as toolkit
    if declaration['kind'] == 'native':
        project = declaration['project']
        require(confined(root, project).is_file(), 'missing native test owner')
        selection = {'scope': 'Focused', 'projects': [project], 'toolkitChecks': []}
        planned = native.plan(root, selection, declaration['arguments'], declaration['configuration'])
        require(len(planned['reusable']) == 1 and not planned['needed'], 'native evidence missing, stale or unresolved')
        run = planned['reusable'][0]['run']
        if retained and retained != run:
            path = confined(root, retained)
            require(path.name == 'result.json' and path.parent.parent == root / 'artifacts/tests/runs', 'native evidence has no retained owner')
            matching = [outcome for _, candidate, coverage, outcome in native.history(root)
                        if candidate == path and coverage == tuple(declaration['arguments']) and outcome.get('project') == project
                        and outcome.get('fingerprint') == planned['fingerprints'][project] and native.evidence_valid(root, path, outcome)]
            require(bool(matching), 'retained native evidence is not current')
            run = retained
    else:
        rows = native.toolkit_declarations(root)
        identity = declaration['id']
        require(identity in rows and identity not in toolkit.pending(root), 'named check missing or has unresolved failure')
        expected = toolkit.fingerprint(root, rows[identity])
        candidates = []
        directory = root / 'artifacts/tests/toolkit-runs'
        paths = [confined(root, retained)] if retained else directory.glob('*/result.json')
        for path in paths:
            require(path.name == 'result.json' and path.parent.parent == directory, 'named check evidence has no retained owner')
            value = load(path)
            for outcome in value.get('outcomes', []):
                if outcome.get('check') == identity:
                    candidates.append((value.get('startedAtUtc', ''), path.as_posix(), path, value, outcome))
        require(bool(candidates), 'check execution evidence missing')
        _, _, path, value, outcome = sorted(candidates)[-1]
        require(value.get('status') == 'completed' and outcome.get('status') == 'completed' and outcome.get('exitCode') == 0
                and outcome.get('fingerprint') == expected and bool(outcome.get('evidence')), 'check evidence missing or stale')
        for relative, digest in outcome['evidence'].items():
            target = confined(root, relative)
            require(target.is_relative_to(path.parent) and target.is_file() and sha(target.read_bytes()) == digest, 'check evidence changed')
        run = path.relative_to(root).as_posix()
    return {'check': declaration, 'run': run, 'sha256': sha(confined(root, run).read_bytes())}


def binding(unit, rules, root, extensions, observed):
    pattern = {k: v for k, v in unit['pattern'].items() if k != 'evidence'}
    refs = pattern['inputs'] + pattern['examples']['positive'] + pattern['examples']['negative']
    if pattern['review']:
        refs += [pattern['review']]
    state = {'unit': {k: v for k, v in unit.items() if k != 'pattern'}, 'pattern': pattern,
             'rules': {r['id']: r['fingerprint'] for r in rules},
             'inputs': [referenced(r, root, extensions) for r in refs], 'context': observed,
             'adapters': {name: sha(Path(__file__).with_name(name).read_bytes())
                          for name in ('coding_patterns.py', 'coding_context.py', 'knowledge_sources.py', 'feature_context.py')}}
    return fingerprint(state)


def qualify(unit, rules, root, extensions, observed):
    p = unit['pattern']
    try:
        require(bool(p['invariantRuleIds']) and bool(p['inputs']) and bool(p['examples']['positive'])
                and bool(p['examples']['negative']) and bool(p['checks']) and p['review'] is not None, 'pattern needs invariants, examples, actual checks and ordinary semantic review')
        expected = binding(unit, rules, root, extensions, observed)
        checks = [current_check(root, c) for c in p['checks']]
        for record in reversed(p['evidence']):
            if record.get('fingerprint') != expected or len(record.get('checks', [])) != len(checks):
                continue
            # A second identical successful execution does not invalidate an
            # intact earlier pass. The normal owner still rejects later failures.
            retained_checks = []
            for declaration, retained, latest in zip(p['checks'], record['checks'], checks):
                require(isinstance(retained, dict) and retained.get('check') == declaration and isinstance(retained.get('run'), str), 'invalid retained check reference')
                retained_checks.append(latest if retained == latest else current_check(root, declaration, retained['run']))
            if retained_checks != record['checks']:
                continue
            if record.get('expiresAt'):
                expiry = datetime.fromisoformat(record['expiresAt'].replace('Z', '+00:00'))
                if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
                    continue
            return {'status': 'qualified', 'fingerprint': expected, 'evidence': record,
                    'limits': p['limits'], 'reviewAuthority': 'Ordinary authored review; source binding does not authenticate its author or establish human acceptance.'}
        return {'status': 'stale-or-unbound', 'fingerprint': expected, 'repair': 'Run affected maintained checks, review changed semantics in the existing owner and bind current evidence; preserve historical records.'}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return {'status': 'missing-proof', 'repair': 'Restore declared inputs, examples, normal review and current maintained check evidence; no submitted command is executed.'}


def choices(feature):
    path = feature / 'plan.md'
    content = path.read_text(encoding='utf-8') if path.is_file() else ''
    matches = CHOICES.findall(content)
    require(len(matches) <= 1 and content.count('<!-- program-kit:pattern-choices -->') == len(matches), 'missing or ambiguous pattern choice block')
    if not matches:
        return {}
    value = decode(matches[0])
    require(isinstance(value, dict), 'pattern choices must be an object')
    for identity, choice in value.items():
        require(IDENTITY.fullmatch(identity) and isinstance(choice, dict) and set(choice) == {'id', 'version', 'reason'}
                and isinstance(choice['id'], str) and IDENTITY.fullmatch(choice['id'])
                and isinstance(choice['version'], str) and isinstance(choice['reason'], str) and choice['reason'].strip(), 'choice needs identity, exact version and contextual reason')
    return value


def apply(catalog, selected, excluded, root, extensions, observed, chosen):
    patterns = validate(catalog)
    declarations = {u['id']: u for u in catalog['codingUnits']}
    output, reports, blockers, groups = [], [], [], {}
    applicable = {u['id']: u for u in selected}
    for identity, p in patterns.items():
        row = {'id': identity, 'semanticId': p['semanticId'], 'version': p['version'], 'owner': p['owner'],
               'status': p['status'], 'precedence': {'replaces': p['replaces'], 'requiresExplicitChoice': bool(p['replaces'])},
               'suitability': {'alternatives': p['alternatives']}, 'qualification': {'status': 'not-evaluated'}, 'selected': False}
        reports.append(row)
        if identity not in applicable:
            row['suitability']['reason'] = 'coding-unit applicability excluded this scope'
            continue
        mismatches = compatibility(p, observed)
        row['suitability']['reasons'] = mismatches
        row['qualification'] = qualify(declarations[identity], applicable[identity]['rules'], root, extensions, observed)
        if p['status'] == 'active' and not mismatches:
            groups.setdefault(p['semanticId'], []).append(row)
    for semantic in sorted(set(groups) | set(chosen)):
        candidates = groups.get(semantic, [])
        choice = chosen.get(semantic)
        winner = None
        if choice:
            require(choice['id'] not in patterns or patterns[choice['id']]['semanticId'] == semantic, 'choice has a different semantic owner')
            if choice['id'] in patterns and choice['id'] not in applicable and not candidates:
                continue  # A feature-wide choice cannot pull an unrelated operation into scope.
            winner = next((r for r in candidates if r['id'] == choice['id'] and r['version'] == choice['version']), None)
            if winner is None:
                blockers.append({'code': 'PKP002', 'pattern': choice['id'], 'owner': 'pattern/context owner', 'repair': 'Chosen pattern/version is excluded, retired, incompatible or unavailable. Review the scoped plan choice; no fallback was selected.'})
        elif len(candidates) > 1:
            blockers.append({'code': 'PKP003', 'semanticId': semantic, 'owner': 'pattern/context owner', 'repair': 'Compatible alternatives are ambiguous. Record an exact version and contextual reason in the existing plan pattern-choices block.'})
        elif len(candidates) == 1 and not patterns[candidates[0]['id']]['replaces']:
            if candidates[0]['qualification']['status'] == 'qualified' or patterns[candidates[0]['id']]['evidence']:
                winner = candidates[0]
        if winner:
            p = patterns[winner['id']]
            # Preserve actionable context/source findings even when qualification
            # also fails. A stale pattern must not hide the missing canonical owner.
            blockers += applicable[winner['id']].get('blockers', [])
            others = {r['id'] for r in candidates} - {winner['id']}
            related = set(p['alternatives']) | set(p['replaces']) | {i for i in others
                if winner['id'] in patterns[i]['alternatives'] + patterns[i]['replaces']}
            if others - related:
                blockers.append({'code': 'PKP004', 'pattern': winner['id'], 'owner': 'pattern/invariant owner', 'repair': 'Overlapping patterns lack a declared compatible alternative or replacement relationship. Resolve their canonical invariants through normal review.'})
            elif winner['qualification']['status'] != 'qualified':
                blockers.append({'code': 'PKP005', 'pattern': winner['id'], 'owner': 'pattern/evidence owner', 'repair': winner['qualification']['repair']})
            else:
                winner['selected'] = True
                unit = applicable[winner['id']]
                unit['pattern'] = copy.deepcopy(winner)
                unit['alternativeReason'] = choice['reason'] if choice else 'Single applicable qualified pattern; no replacement inferred.'
                output.append(unit)
    output = [u for u in selected if u['id'] not in patterns] + output
    return output, reports, blockers


def resolved_rules(catalog, unit, root, extensions):
    identities = set(unit.get('ruleIds', [])) | set(unit['pattern']['invariantRuleIds'])
    for req in catalog['requirements']:
        if req['id'] in unit.get('requirementIds', []):
            identities.update(req.get('ruleIds', []))
    return [resolve(catalog, identity, extensions=extensions, repository=root) for identity in sorted(identities)]


def draft(root, submission, identity, invariants):
    require(IDENTITY.fullmatch(identity), 'invalid draft identity')
    path = confined(root, submission)
    require(path.is_file(), 'submission is unavailable')
    rule_id, source_id = 'local.' + identity, 'local-source.' + identity
    return {'schemaVersion': 1, 'sources': [{'id': source_id, 'locator': {'kind': 'repository', 'path': submission}}],
            'rules': {rule_id: {'source': source_id, 'selector': {'kind': 'document'}, 'owner': 'consumer pattern owner',
                              'level': 'recommended', 'limits': 'Draft submission; applicability, semantics and proof need ordinary review.'}},
            'codingUnits': [{'id': identity, 'ruleIds': [rule_id], 'when': {'all': [], 'any': [], 'not': []},
                'requiredContext': ['request'], 'route': 'manual-edit', 'pattern': {
                    'schemaVersion': 1, 'semanticId': identity, 'version': '1.0.0', 'owner': 'consumer pattern owner', 'status': 'draft',
                    'invariantRuleIds': invariants, 'compatibility': {}, 'alternatives': [], 'replaces': [],
                    'inputs': [{'root': 'repository', 'path': submission}], 'examples': {'positive': [], 'negative': []},
                    'checks': [], 'review': None, 'evidence': [], 'limits': 'Unqualified draft; no implementation or runtime acceptance.',
                    'provenance': 'Explicit local submission; source remains private; no upstream promotion.'}}]}


def teach(root, request_path, catalog):
    """Prepare a single editable contribution. Never register or execute its inputs."""
    request = load(confined(root, request_path))
    allowed = {'schemaVersion', 'id', 'intent', 'problem', 'submission', 'invariants', 'basedOn', 'changes', 'performance'}
    require(isinstance(request, dict) and set(request) <= allowed
            and {'schemaVersion', 'id', 'intent', 'problem', 'changes'} <= set(request)
            and type(request['schemaVersion']) is int and request['schemaVersion'] == 1, 'invalid teaching request')
    require(request['intent'] in ('new', 'refine', 'replace', 'retire') and isinstance(request['problem'], str)
            and request['problem'].strip() and len(request['problem']) <= 8192, 'teaching needs a bounded problem and intent')
    invariants = request.get('invariants', [])
    require(strings(invariants) and set(invariants) <= catalog['rules'].keys(), 'unknown teaching invariant')
    identity = request['id']
    require(isinstance(identity, str) and IDENTITY.fullmatch(identity) and len(identity) <= 70, 'invalid teaching identity')
    changes = request['changes']
    require(isinstance(changes, dict) and set(changes) == {'guidance', 'scaffolds', 'checks', 'examples', 'acceptedArtifacts'}, 'teaching needs a complete change plan')
    for refs in changes.values():
        require(isinstance(refs, list), 'invalid teaching change plan')
        for ref in refs:
            referenced(ref, root, Path(__file__).resolve().parents[2])
    submission = request.get('submission', request_path)
    proposal = draft(root, submission, identity, invariants)
    if request['intent'] != 'new':
        base = request.get('basedOn')
        require(isinstance(base, dict) and set(base) == {'id', 'version'}, 'improvement needs an exact prior version')
        prior = next((u for u in catalog['codingUnits'] if u['id'] == base['id'] and u.get('pattern', {}).get('version') == base['version']), None)
        require(prior is not None, 'prior pattern/version unavailable')
        require(request['intent'] == 'retire' or identity != prior['id'], 'preserve prior version under its original identity')
        require(request['intent'] != 'retire' or identity == prior['id'], 'retirement keeps its original identity')
        unit = copy.deepcopy(prior)
        unit['id'] = identity
        if request['intent'] != 'retire':
            unit['pattern']['evidence'] = []
        unit['pattern']['status'] = 'retired' if request['intent'] == 'retire' else 'draft'
        unit['pattern']['replaces'] = [prior['id']] if request['intent'] == 'replace' else []
        unit['pattern']['alternatives'] = [prior['id']] if request['intent'] == 'refine' else []
        proposal = {'schemaVersion': 1, 'sources': [], 'rules': {}, 'codingUnits': [unit]}
    else:
        require(not request.get('basedOn'), 'new teaching cannot imply replacement')
    if 'performance' in request:
        referenced(request['performance'], root, Path(__file__).resolve().parents[2])
    return {'schemaVersion': 1, 'intent': request['intent'], 'problem': request['problem'], 'basedOn': request.get('basedOn'),
            'proposal': proposal, 'changes': changes, 'performance': request.get('performance'),
            'executionAuthorized': False, 'approvalInferred': False,
            'missingProof': ['Review canonical guidance, applicability/exclusions, exact new version and compatibility.',
                             'Review relevant scaffold/check/example changes; explain empty change categories.',
                             'Route changed architectural invariants through existing accepted plans/ADRs.',
                             'Run independent positive/negative checks; review workload/runtime/resources, correctness, adverse cases and counterexamples for performance claims.',
                             'Merge reviewed declarations explicitly; append current evidence and adopt exact versions in the existing plan. Retirement changes status in place and preserves the original declaration/evidence; refinement/replacement keeps prior versions/failures.']}


def prepare_shared(root, selection_path, output, catalog):
    """Copy only an explicitly authored publishable set into a new local contribution.

    This is an allowlist, not a private-text sanitizer. The author reviews every
    selected byte. No consumer registry, inspection view or evidence is exported.
    """
    selection = load(confined(root, selection_path))
    require(isinstance(selection, dict) and set(selection) == {'schemaVersion', 'declaration', 'files'}
            and type(selection['schemaVersion']) is int and selection['schemaVersion'] == 1
            and isinstance(selection['files'], list) and 0 < len(selection['files']) <= 64, 'invalid publishable selection')
    declaration_path = confined(root, selection['declaration'])
    require(declaration_path.relative_to(root).parts[0] not in ('artifacts', '.program-kit', '.specify', '.git'), 'publishable declaration needs an authored source')
    additions = load(declaration_path)
    require(isinstance(additions, dict) and set(additions) == {'schemaVersion', 'sources', 'rules', 'codingUnits'}
            and type(additions['schemaVersion']) is int and additions['schemaVersion'] == 1
            and isinstance(additions['sources'], list) and isinstance(additions['rules'], dict)
            and isinstance(additions['codingUnits'], list) and len(additions['codingUnits']) == 1, 'select one standalone publishable lesson')
    payload, total = {}, 0
    for item in selection['files']:
        require(isinstance(item, dict) and set(item) == {'source', 'target'}, 'invalid publishable file selection')
        source = confined(root, item['source'])
        target = item['target']
        require(isinstance(target, str) and '\\' not in target and target == Path(target).as_posix()
                and not Path(target).is_absolute() and '..' not in Path(target).parts
                and target.split('/')[0] in ('extensions', 'tests'), 'invalid shared contribution target')
        require(source.relative_to(root).parts[0] not in ('artifacts', '.program-kit', '.specify', '.git')
                and not {'.git', 'node_modules', '__pycache__'} & set(source.relative_to(root).parts), 'execution history is not a publishable lesson source')
        require(target.casefold() not in {p.casefold() for p in payload}, 'duplicate shared target')
        raw = source.read_bytes()
        total += len(raw)
        require(0 < len(raw) <= 262144 and total <= 1048576, 'publishable lesson exceeds bounded source size')
        payload[target] = raw
    merged = copy.deepcopy(catalog)
    require(not set(additions['rules']) & set(merged['rules']), 'shared rule cannot shadow an owner')
    source_ids = {s['id'] for s in merged['sources']}
    for source in additions['sources']:
        require(isinstance(source, dict) and set(source) == {'id', 'locator'} and source['id'] not in source_ids, 'invalid shared source identity')
        locator = source['locator']
        require(isinstance(locator, dict) and set(locator) == {'kind', 'path'} and locator['kind'] == 'extension'
                and 'extensions/' + locator['path'] in payload, 'shared canonical source must be explicitly selected')
        source_ids.add(source['id'])
    for rule in additions['rules'].values():
        require(isinstance(rule, dict) and rule.get('source') in {s['id'] for s in additions['sources']}, 'shared rule needs its selected canonical source')
    for unit in additions['codingUnits']:
        p = unit.get('pattern', {})
        require(p.get('evidence') == [] and p.get('status') == 'draft', 'shared contribution must start draft with no consumer evidence')
        refs = p.get('inputs', []) + p.get('examples', {}).get('positive', []) + p.get('examples', {}).get('negative', [])
        if p.get('review'):
            refs += [p['review']]
        for ref in refs:
            reference(ref)
            target = ('extensions/' if ref['root'] == 'extensions' else '') + ref['path']
            require(target in payload, 'shared proof reference needs an explicitly selected publishable file')
    merged['sources'].extend(additions['sources'])
    merged['rules'].update(additions['rules'])
    merged['codingUnits'].extend(additions['codingUnits'])
    from coding_context import validate_units
    validate_units(merged)
    validate(merged)
    require(not output.exists(), 'shared preparation output exists; preserve prior contribution')
    output.mkdir(parents=True)
    for relative, raw in payload.items():
        path = confined(output, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (output / 'catalog-additions.json').write_text(json.dumps(additions, indent=2) + '\n', encoding='utf-8')
    manifest = {'status': 'prepared-for-source-review', 'files': {p: sha(raw) for p, raw in payload.items()},
                'evidenceTransferred': False, 'publicationAuthorized': False, 'authorshipAuthenticated': False,
                'limits': 'Only explicitly selected bytes; author must review them for privacy. No automatic secret detection, upstream adoption or execution.',
                'next': 'Review these files and catalog-additions.json in a normal Program Kit source diff. Merge additions into phase-obligations.json without shadowing owners; maintain checks/examples, run installed proof and bind fresh shared evidence through binding/current_check in reviewed source. Adoption is a separate exact-version plan/update decision.'}
    (output / 'contribution.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('draft', 'teach', 'prepare-shared', 'inspect', 'bind-evidence'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir')
    parser.add_argument('--operation')
    parser.add_argument('--id')
    parser.add_argument('--submission')
    parser.add_argument('--output')
    parser.add_argument('--invariant', action='append', default=[])
    parser.add_argument('--configuration', default='Debug')
    parser.add_argument('--framework')
    parser.add_argument('--expires-at')
    parser.add_argument('--request')
    parser.add_argument('--selection')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        if args.command in ('teach', 'prepare-shared'):
            from phase_obligations import catalog
            require(bool(args.output), 'contribution needs a new local output')
            output = confined(root, args.output)
            if args.command == 'prepare-shared':
                require(bool(args.selection), 'shared preparation needs explicitly selected publishable inputs')
                value = prepare_shared(root, args.selection, output, catalog())
            else:
                require(bool(args.request) and not output.exists(), 'teaching needs a request and new output')
                value = teach(root, args.request, merge(catalog(), root))
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(value, indent=2))
            return 0
        if args.command == 'draft':
            require(bool(args.submission and args.id and args.output), 'draft needs submission, identity and output')
            from phase_obligations import catalog
            require(len(args.id) <= 70 and set(args.invariant) <= merge(catalog(), root)['rules'].keys(), 'draft requires known invariant bindings and a bounded identity')
            output = confined(root, args.output)
            require(not output.exists(), 'draft output already exists; preserve authored content')
            value = draft(root, args.submission, args.id, args.invariant)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'status': 'draft', 'executionAuthorized': False,
                  'missingProof': ['review semantic identity/invariants and applicability', 'declare exact compatibility and relationships',
                                   'supply positive/counterexamples, maintained checks and ordinary review', 'bind actual evidence before selection'],
                  'next': 'Review this single draft; merge its sources/rules/codingUnits into docs/architecture/coding-patterns.json. No automatic registration or promotion.'}, indent=2))
            return 0
        require(bool(args.feature_dir), 'inspection needs the normal feature context')
        from coding_context import prepare
        result = prepare(root, confined(root, args.feature_dir), operation=args.operation, configuration=args.configuration, framework=args.framework)
        if args.command == 'inspect':
            print(json.dumps(result['coding']['patterns'], indent=2))
            return 0 if result['coding']['canProceed'] else 2
        require(bool(args.id), 'evidence binding needs an exact pattern identity')
        extensions = Path(__file__).resolve().parents[2]
        from phase_obligations import catalog
        registry = merge(catalog(), root)
        from coding_context import validate_units
        validate_units(registry)
        validate(registry)
        unit = next((u for u in registry['codingUnits'] if u['id'] == args.id and 'pattern' in u), None)
        require(unit is not None, 'pattern identity unavailable')
        reports = result['coding']['patterns']
        report = next(r for r in reports if r['id'] == args.id)
        require(report['suitability'].get('reason') is None and not report['suitability'].get('reasons')
                and unit['pattern']['status'] == 'active', 'evidence cannot bind an excluded, draft or retired pattern')
        p = unit['pattern']
        require(p['invariantRuleIds'] and p['inputs'] and p['examples']['positive'] and p['examples']['negative'] and p['checks'] and p['review'], 'missing examples, checks or ordinary review; draft remains unqualified')
        require(not any(not b['code'].startswith('PKP') for b in result['coding']['blockers']), 'resolve mandatory coding context before binding pattern evidence')
        observed = result['coding']['patternsContext']
        record = {'fingerprint': binding(unit, resolved_rules(registry, unit, root, extensions), root, extensions, observed),
                  'checks': [current_check(root, c) for c in p['checks']], 'boundAtUtc': datetime.now(timezone.utc).isoformat()}
        if args.expires_at:
            expiry = datetime.fromisoformat(args.expires_at.replace('Z', '+00:00'))
            require(expiry.tzinfo is not None and expiry > datetime.now(timezone.utc), 'evidence expiry must be a future timezone-aware instant')
            record['expiresAt'] = args.expires_at
        # Only the explicit local input is writable. Shipped declarations are reviewed upstream.
        local_path = root / LOCAL
        local = load(local_path)
        target = next((u for u in local['codingUnits'] if u['id'] == args.id), None)
        require(target is not None, 'shared evidence is maintained in its source repository; no local rewrite')
        target['pattern']['evidence'].append(record)
        local_path.write_text(json.dumps(local, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'bound', 'record': record, 'approvalInferred': False}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        print('PKP001 pattern input/evidence is unavailable or invalid; owner: pattern maintainer; inspect local declarations, normal checks and review. No submitted code was executed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

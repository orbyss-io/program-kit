"""Provide applicable knowledge; ordinary engineering commands enforce completion.

The historical evidence reader is historical_phase_evidence.py. This command
never creates feature dossiers or consumes bootstrap/ratification receipts.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import subprocess
from pathlib import Path
from feature_context import context, adopted_context
from decision_knowledge import constraints


_engineering = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(_engineering))
from test_results import test_results, require, text
from repository_architecture import validate_planned, lifecycle_findings

def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Feature path escapes repository')
    return path


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def catalog():
    return read(Path(__file__).resolve().parents[1] / 'references/phase-obligations.json')


def intent(root, feature, phase='implementation', affected_paths=()):
    return context(root, feature, phase, affected_paths)


def retained_proofs(root, feature, phase):
    """Keep actual executed prerequisites separate from reviewed plan decisions."""
    from feature_context import feature_scope
    from bootstrap_lifecycle import current_compatibility_evidence, TRIGGER_PHASE, PHASE_ORDER, verification_kind
    entry = feature_scope(root, feature)['entry']
    if entry is None:
        return []
    items = read(root / 'docs/architecture/bootstrap-prerequisites.json', {}).get('prerequisites', [])
    selected = [i for i in items if entry in i.get('affected_slices', []) and i.get('status') != 'closed'
                and not (i.get('disposition') == 'feature' and i.get('trigger') == 'feature-plan'
                         and verification_kind(i) == 'decision')]
    if not selected:
        return []
    from governance_state import roadmap_records
    roadmap = root / 'docs/architecture/specification-roadmap.md'
    records = roadmap_records(roadmap) if roadmap.is_file() else []
    brief = read(root / '.program-kit/specification-intake' / entry / 'brief.json', {})
    answered = {d.get('bootstrapPrerequisite') for d in brief.get('decisions', [])
                if d.get('disposition') in {'answered', 'default'}}
    if answered:
        from specification_intake import check
        try:
            check(root, entry, later=True)
        except (ValueError, OSError):
            answered = set()

    def satisfied(item):
        if verification_kind(item) == 'compatibility':
            return current_compatibility_evidence(root, records, item)
        return item.get('disposition') == 'feature' and item['id'] in answered

    current_phase = {'after-plan': 'planning', 'tasks': 'planning', 'after-tasks': 'planning'}.get(phase, phase)
    return [{'id': i['id'], 'owner': i['owner'], 'task': i['task'], 'due': TRIGGER_PHASE[i['trigger']],
             'requiredNow': PHASE_ORDER.index(TRIGGER_PHASE[i['trigger']]) <= PHASE_ORDER.index(current_phase),
             'kind': verification_kind(i),
             'status': 'satisfied' if satisfied(i) else 'pending-' + verification_kind(i)}
            for i in selected]


def require_due_proofs(root, feature, phase):
    pending = [p for p in retained_proofs(root, feature, phase) if p['requiredNow'] and p['status'] != 'satisfied']
    if pending:
        raise ValueError('Retained compatibility/delivery or authority prerequisites require their actual evidence: '
                         + '; '.join(p['id'] + ' (' + p['owner'] + '): ' + p['task'] for p in pending))


def foundation_applicability(root, feature, inherited, tags):
    """A bounded mechanism brief from the selected publisher's immutable capture."""
    if not {'api', 'web'}.intersection(tags):
        return None
    targets = {identity for source in inherited['sources'] for identity in source.get('targets', [])}
    selection = read(root / 'docs/architecture/building-block-selection.json', {})
    if not targets or not selection.get('catalog'):
        return None  # Proposed/unbound context is not exact publisher adoption.
    instances = []
    for instance in selection.get('instances', []):
        bound = {identity for value in instance.get('targetBindings', {}).values()
                 for identity in (value if isinstance(value, list) else [value]) if isinstance(identity, str)}
        if bound & targets and instance.get('composition') in {'api_baseline', 'browser_bff', 'browser_spa_pkce', 'hosted_pages'}:
            instances.append(instance)
    if not instances:
        return None
    from repository_sync import provider
    blocks = provider('program-kit-building-blocks/scripts/building_blocks.py')
    effective = blocks.effective_dependency_context(root)
    version = effective['catalog']['families']['foundation']['releaseVersion']
    capture = effective['publisherKnowledge']
    if not capture:
        return {'version': version, 'profile': effective['profile'], 'sourceCommit': None,
                'guidance': ['This exact selection has no captured publisher mechanism knowledge. Resolve its exact profile before choosing an unverified Foundation mechanism; no newer default is substituted.']}
    capabilities = provider('program-kit-building-blocks/scripts/wire_capabilities.py').project(blocks, effective)
    registry = Path(effective['registryPath'])
    def document(name):
        row = next((item for item in capture['documents'] if item['publisherPath'] == name), None)
        return blocks.publisher_document_bytes(registry, row).decode('utf-8') if row else ''
    metadata = document('src/Orbyss.Foundation.WebDefaults/WebResponseMetadata.cs')
    writer = document('src/Orbyss.Foundation.WebDefaults/WebResponsePoliciesMiddleware.cs')
    permission = document('src/Orbyss.Foundation.Authentication/PermissionPolicyProvider.cs')
    guidance = []
    if 'WebResponseMetadata' in metadata and 'OnStarting' in writer:
        guidance += ['Shell Foundation:Web:ResponsePolicies selects response policies; endpoints declare WebResponseMetadata(Private: true). WebDefaults owns the final header writer across success, denial, error and redirect. Admit public immutable assets separately.']
    else:
        guidance += ['This exact capture does not expose the current response-policy/private-metadata/final-writer contract. Resolve that capability before relying on it; headers alone supply no admission.']
    if 'permission:' in permission:
        guidance += ['Where BFF is selected, it supplies session admission; endpoints require canonical permission:<owned id> through Foundation authorization. Application code retains resource/state/effect checks.']
    guidance += ['Use the exact package schemas and typed configuration for shell deployment values. Keep application permission/route identities in owned constants and use captured framework identifiers; literals are assessed by ownership and lifecycle.']
    if capabilities['problem']:
        guidance += ['Selected problem writer fields: ' + ', '.join(capabilities['problem']['fields'])
                     + '; closed envelope. Put recovery metadata in typed operation responses/UI with retained server-issued operation identity.']
    if capabilities['json']:
        guidance += ['Selected JSON profiles require Strict numeric tokens. Use demonstrated scoped JsonNumberHandling.Strict DTO metadata; regenerate actual producer/client output and prove reader/writer parity. Custom converters or shared types under distinct profiles require exact binding proof.']
    guidance += ['Unresolved selected wire capability: ' + message for message in capabilities['unresolved']]
    prose = '\n'.join((feature / name).read_text(encoding='utf-8') for name in ('spec.md', 'plan.md') if (feature / name).is_file())
    hosted = [instance for instance in instances if instance['composition'] == 'hosted_pages']
    if hosted:
        options = document('src/Orbyss.Foundation.Web.HostedPages/HostedPageOptions.cs')
        feature_source = document('src/Orbyss.Foundation.Web.HostedPages/FoundationHostedPagesFeature.cs')
        access_mode = document('src/Orbyss.Foundation.Web.HostedPages/HostedPageAccessMode.cs')
        private_contract = 'HostedPageRouteOptions' in options and 'Routes' in options and 'Authenticated' in access_mode
        for instance in hosted:
            purpose = str(instance.get('purpose', '')).lower()
            identity = str(instance.get('id', '')).lower().replace('-', ' ')
            public_assets = 'public assets' in identity or bool(re.search(r'public(?:ly)?\s+(?:immutable\s+)?(?:code\s+)?assets', purpose))
            private_intent = bool(re.search(r'(?:private|authenticated)\s+(?:html\s+)?(?:pages?|entries|bootstrap)', identity + ' ' + purpose + ' ' + prose, re.I))
            if private_intent and not public_assets and not private_contract:
                raise ValueError('Foundation ' + version + ' HostedPages is public-only in its exact captured contract; selected private-page intent requires a demonstrated qualified private-page mechanism before affected source work. Public immutable assets remain separately valid.')
        if private_contract:
            guidance += ['This capture exposes typed HostedPages Routes. Bind distinct route IDs/paths/revisions and page/bootstrap access; qualify the actual admission behavior, including inherited bootstrap requirements and shared-revision isolation.']
        elif 'AllowAnonymous' in feature_source:
            guidance += ['HostedPages in this exact capture serves public HTML/bootstrap. An instance name or response policy cannot confer private admission.']
    return {'version': version, 'profile': effective['profile'], 'sourceCommit': capture['sourceCommit'],
            'wireCapabilities': capabilities, 'guidance': guidance}


def model(root, feature, phase='planning', affected_paths=()):
    tags = intent(root, feature, phase, affected_paths)
    registry_phase = 'after-plan' if phase == 'tasks' else phase
    inherited = adopted_context(root, feature)
    from feature_plan_decisions import project as decisions
    from consumer_upgrade import scan, request_scope
    compatibility = scan(root, request_scope(root, feature=feature), {'after-plan': 'planning', 'after-tasks': 'tasks'}.get(phase, phase))
    manifest = read(root / 'eng/architecture.json')
    scoped = {p for row in inherited['sources'] for p in row.get('targetPaths', [])}
    declarations = '\n'.join((feature/name).read_text(encoding='utf-8') for name in ('spec.md', 'plan.md', 'research.md', 'tasks.md') if (feature/name).is_file())
    if manifest:
        scoped.update(p['path'] for p in manifest.get('runtimeComposition', {}).get('projects', [])
                      if p['path'] in declarations or Path(p['path']).parent.as_posix() in declarations
                      or any(str(path).replace('\\', '/').startswith(Path(p['path']).parent.as_posix()+'/') for path in affected_paths))
    return {'schemaVersion': 1, 'feature': feature.relative_to(root).as_posix(), 'upgradeCompatibility': compatibility,
            'foundationApplicability': foundation_applicability(root, feature, inherited, tags),
            'lifecycleFindings': lifecycle_findings(root, manifest, scoped) if manifest and 'dotnet' in tags else [],
            'context': {'sources': inherited['sources'], 'diagnostics': inherited['diagnostics']},
            'decisions': decisions(root, feature),
            'prerequisites': retained_proofs(root, feature, phase),
            'requirements': [r for r in catalog()['requirements']
                             if r['when'] in tags and registry_phase in r['phases']
                             and (not r.get('mechanism') or r['mechanism'] in tags)]}


def project(root, feature, phase, affected_paths=()):
    """Return regenerable context without writing into the feature's design files."""
    return model(root, feature, phase, affected_paths)


def render(value, phase, detailed=False):
    canonical = constraints(catalog(), value['requirements'], Path(__file__).resolve().parents[2])
    lines = [f'# Applicable guidance: {phase}', '',
             'Record concrete decisions and tests in plan.md/tasks.md. No separate review receipts are required.',
             'Conditional guidance applies only when its stated conditions hold.',
             'Canonical decision constraints below apply before choosing a design. Use focused lookup for an unresolved mechanism; this is not a reading checklist.',
             'Use --only <id> for its example, diagnostics and focused reference sections.', '']
    actions = {
        'planning': 'Make design decisions and name their cheapest reliable tests. No application tests run during planning.',
        'after-plan': 'Review changed design decisions and the planned graph. Carry real-provider tests into the tasks.',
        'tasks': 'Size coherent runnable stories; name risk, verification sequence and exact prerequisites. Materialize known scaffolds first, run maintained checks, then add missing consumer tests. Do not execute proofs while drafting.',
        'after-tasks': 'Check the finalized graph and run normal read-only analyze once. Drafting is not implementation.',
        'implementation': 'Use verification selected by risk. Review runnable stories with the assigned human; required checkpoints pause further product work unless explicitly deferred. Progress saves and resumes are not full acceptance boundaries.',
        'delivery': 'Run complete acceptance at feature/domain closure or formal review handoff, then review changed responsibilities.',
    }
    lines += [actions[phase], '']
    if value.get('foundationApplicability'):
        brief = value['foundationApplicability']
        lines += ['Selected Foundation ' + brief['version'] + '; profile ' + str(brief['profile'])
                  + '; captured source ' + str(brief['sourceCommit']) + '.', *brief['guidance'], '']
    if value.get('validation'):
        lines += [('Declared graph: PASS.' if value['validation']['declaredGraphPassed'] else
                   'Declared graph: not supplied; no graph check was established.')
                  + ' Semantic responsibility review remains required; no overall boundary acceptance is established.', '']
    if value.get('execution'):
        lines += ['Engineering command: PASS for Acceptance scope. Semantic/human acceptance is not established.', '']
    compatibility = value.get('upgradeCompatibility', {})
    if compatibility.get('recordPresent'):
        for item in compatibility.get('migrations', []) + compatibility.get('findings', []):
            lines += ['Upgrade impact ' + item['id'] + ': ' + item.get('status', item.get('disposition', 'unresolved'))
                      + ('; blocks affected work now.' if item['blocksNow'] else '; preserve its due phase.'), '']
        for limitation in compatibility.get('limitations', []):
            lines += ['Compatibility scope: ' + limitation, '']
    for diagnostic in value.get('context', {}).get('diagnostics', []):
        lines += ['Context finding: ' + diagnostic, '']
    for finding in value.get('lifecycleFindings', []):
        lines += ['Semantic review finding ' + finding['id'] + ': ' + finding['project'],
                  finding['message'], 'Evidence: ' + finding.get('source', 'eng/architecture.json')
                  + ('; owner ' + finding['ownerSource'] if finding.get('ownerSource') else ''), '']
    for source in value.get('context', {}).get('sources', []):
        lines += ['Scoped context: ' + source['path'], '']
    for decision in value.get('decisions', []):
        lines += [f"Decision {decision['id']}: {decision['status']} ({decision['owner']})",
                  decision['task'], decision['diagnostic'], '']
    for proof in value.get('prerequisites', []):
        lines += [f"Retained prerequisite {proof['id']}: {proof['status']} (due {proof['due']}; {proof['owner']})",
                  proof['task'], 'Gate scope: retained roadmap-feature prerequisite; operation dependency declarations cannot defer or waive it.',
                  'A reviewed plan cannot substitute for its required proof or governing authority.', '']
    for rule in value['requirements']:
        guidance = rule['requirement'] if detailed else rule.get('guidance', {}).get(phase, rule['requirement'])
        lines += [f"## {rule['id']}", guidance,
                  'Enforcement: ' + rule['enforcement']['kind']]
        lines += canonical[rule['id']]
        if detailed:
            lines.append('Example: ' + rule['example'])
        if detailed and rule['enforcement'].get('diagnostics'):
            lines.append('Compiler diagnostics: ' + ', '.join(rule['enforcement']['diagnostics']))
        for source, sections in rule.get('sections', {}).items() if detailed else ():
            lines.append('Focused lookup: ' + source + ': ' + '; '.join(sections))
        lines.append('')
    return '\n'.join(lines)


def check(root, feature, phase, affected_paths=(), operation=None, repair=False):
    graph_checked, execution = None, None
    from consumer_upgrade import scan, request_scope
    compatibility = scan(root, request_scope(root, feature=feature), {'after-plan': 'planning', 'after-tasks': 'tasks'}.get(phase, phase))
    if not compatibility['canProceed']:
        raise ValueError('Affected upgrade work is due: ' + ', '.join(compatibility['blockers']) + '; use migration pickup/local recovery. Unaffected work remains available.')
    if phase in ('after-plan', 'after-tasks', 'implementation'):
        graph_checked = validate_planned_architecture(root, feature)
        # This uses the existing registered .json document, never a companion
        # wire schema. Missing/prose-only/success-only promises are unresolved.
        tags = intent(root, feature, phase, affected_paths)
        if 'api' in tags and foundation_applicability(root, feature, adopted_context(root, feature), tags):
            from openapi_capabilities import check_registered
            check_registered(root, feature, 'planning')
    if phase in ('after-tasks', 'implementation') and (feature / 'tasks.md').is_file():
        from task_draft import validate_operation_graph, load
        task_content, task_state = load(feature / 'tasks.md')
        validate_operation_graph(task_content, required=bool(task_state and task_state.get('format') == 'operation-plan'), root=root)
    if phase in ('implementation', 'delivery'):
        from feature_plan_decisions import require_resolved
        require_resolved(root, feature)
        require_due_proofs(root, feature, phase)
        from task_draft import guard
        guard(root, feature, operation=operation, closure=phase == 'delivery', repair=repair)
    if phase == 'delivery':
        execution = execute(root, feature)
    value = model(root, feature, phase, affected_paths)
    if phase in ('after-plan', 'after-tasks', 'implementation'):
        value['validation'] = {'declaredGraphPassed': True if graph_checked else None, 'semanticReviewEstablished': False,
                               'scope': 'Declared structure; actual semantic ownership requires normal review.'}
    if execution:
        value['execution'] = execution
    return value


def validate_planned_architecture(root, feature):
    """Fail on incompatible planned ownership before affected source/build work."""
    path = root / 'eng/architecture.json'
    if not path.is_file():
        declarations = '\n'.join((feature / name).read_text(encoding='utf-8')
            for name in ('plan.md', 'research.md', 'data-model.md') if (feature / name).is_file())
        if '.csproj' in declarations:
            raise ValueError('Declare the planned compilation graph in eng/architecture.json before affected implementation')
        return False
    manifest = read(path)
    declarations = '\n'.join((feature / name).read_text(encoding='utf-8')
        for name in ('spec.md', 'plan.md', 'research.md', 'data-model.md') if (feature / name).is_file())
    scoped = {p for s in adopted_context(root, feature)['sources'] for p in s.get('targetPaths', [])}
    scoped.update(p['path'] for p in manifest.get('runtimeComposition', {}).get('projects', [])
                  if p['path'] in declarations or str(Path(p['path']).parent).replace('\\', '/') in declarations)
    # Existing unrelated manifests retain their structural scope; review metadata
    # is added to the selected design rather than migrating every old project.
    required = (scoped or True) if 'dotnet' in intent(root, feature) else False
    validate_planned(root, manifest, require_responsibilities=required)
    return True


def execute(root, feature, scope='Acceptance', changed_from=None):
    if scope == 'Acceptance':
        from feature_plan_decisions import require_resolved
        require_resolved(root, feature)
        require_due_proofs(root, feature, 'delivery')
    command = root / 'eng/Invoke-RepositoryVerification.ps1'
    if not command.is_file():
        raise ValueError('Application verification is not configured. Supply eng/Invoke-RepositoryVerification.ps1 or run the project build/tests; no completion claim is established.')
    import shutil
    executable = shutil.which('pwsh') or shutil.which('powershell')
    if not executable:
        raise ValueError('PowerShell is required by the configured engineering command')
    from datetime import datetime, timezone
    import uuid
    from execution_history import cleanup
    directory = root / 'artifacts/program-kit/runs' / uuid.uuid4().hex
    directory.mkdir(parents=True)
    marker = directory / 'run.json'
    value = {'schemaVersion':1, 'owner':'program-kit', 'status':'running',
             'scope':scope, 'feature':feature.relative_to(root).as_posix(),
             'startedAtUtc':datetime.now(timezone.utc).isoformat(),
             'command':[executable, '-NoProfile', '-File', str(command)]}
    if scope != 'Acceptance':
        value['command'] += ['-Scope', scope, '-FeatureDirectory', feature.relative_to(root).as_posix()]
        if changed_from:
            value['command'] += ['-ChangedFrom', changed_from]
    marker.write_text(json.dumps(value))
    try:
        with (directory / 'stdout.log').open('w',encoding='utf-8') as out, (directory / 'stderr.log').open('w',encoding='utf-8') as err:
            result = subprocess.run(value['command'], cwd=root, stdout=out, stderr=err, timeout=900)
    except (OSError, subprocess.SubprocessError) as error:
        value.update(status='failed', diagnostic=str(error), finishedAtUtc=datetime.now(timezone.utc).isoformat())
        marker.write_text(json.dumps(value))
        raise
    value.update(status='completed' if result.returncode == 0 else 'failed', exitCode=result.returncode,
                 finishedAtUtc=datetime.now(timezone.utc).isoformat())
    marker.write_text(json.dumps(value))
    cleanup(root)
    print('Engineering logs: ' + directory.relative_to(root).as_posix())
    if result.returncode:
        raise ValueError(f'Application verification failed ({result.returncode}); correct the reported code/configuration issue and rerun eng/Invoke-RepositoryVerification.ps1')
    return {'applicationChecksPassed': scope == 'Acceptance', 'scopedChecksPassed': True,
            'engineeringAcceptanceEstablished': scope == 'Acceptance',
            'acceptanceEstablished': False, 'semanticReviewEstablished': False,
            'releaseReadinessEstablished': False,
            'instruction': 'Engineering command passed for its stated scope. Complete required consumer behavior and normal semantic/human review before overall acceptance.'}


def finish(root, feature, handoff=False):
    """A task checkpoint is progress; only actual closure/handoff runs acceptance."""
    tasks = feature / 'tasks.md'
    require(tasks.is_file(), 'Locate tasks.md before claiming feature closure')
    from task_draft import load, current
    content, draft_state = load(tasks)
    pending = len(re.findall(r'^\s*-\s+\[ \]\s+', content, re.M))
    draft = '> Draft:' in content or bool(draft_state and draft_state.get('status') != 'complete')
    if not handoff and (pending or draft):
        from task_draft import current
        can_proceed, review_diagnostic = False, 'Initialize fresh story delivery before implementation; old partial progress grants no continuation authority.'
        if (current(feature) or {}).get('delivery'):
            from task_draft import guard
            try:
                guard(root, feature)
                can_proceed, review_diagnostic = True, None
            except ValueError as error:
                if not str(error).startswith('Pause for required human review:'):
                    raise
                can_proceed, review_diagnostic = False, str(error)
        return {'status': 'in-progress', 'pendingTasks': pending, 'draft': draft,
                'applicationChecksPassed': False, 'acceptanceEstablished': False,
                'canProceed': can_proceed, 'reviewDiagnostic': review_diagnostic,
                'currentCheckpoint': current(feature),
                'instruction': 'Replace the compact current checkpoint in tasks.md with task_draft.py checkpoint; preserve unresolved failures and the implementation baseline. Run only checks required by changed inputs. No full acceptance at this checkpoint.'}
    require(handoff or bool(re.search(r'^\s*-\s+\[[xX]\]\s+', content, re.M)),
            'Feature closure requires completed tasks or an explicit formal handoff')
    from task_draft import guard
    guard(root, feature, closure=True)
    result = execute(root, feature)
    result['humanReviewsPassed'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('project', 'check', 'verify', 'finish'))
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--phase', default='planning', choices=('planning','after-plan','tasks','after-tasks','implementation','delivery'))
    parser.add_argument('--only', help='Return one applicable obligation for a focused follow-up')
    parser.add_argument('--affected-path', action='append', default=[], help='Focus implementation source lookup on these paths')
    parser.add_argument('--scope', choices=('Acceptance','Affected'), default='Acceptance')
    parser.add_argument('--changed-from', help='Git baseline for Affected verification including worktree and untracked changes')
    parser.add_argument('--handoff', action='store_true', help='Explicit formal review handoff, including intentionally unfinished work')
    parser.add_argument('--operation', help='Explicit operation for scoped deferred work or repair')
    parser.add_argument('--repair', action='store_true', help='Repair/diagnose only the active presented outcome')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    feature = inside(root, args.feature_dir)
    try:
        affected = [inside(root, p).relative_to(root).as_posix() for p in args.affected_path]
        result = (finish(root, feature, args.handoff) if args.command == 'finish' else
                  execute(root, feature, args.scope, changed_from=args.changed_from) if args.command == 'verify' else
                  project(root, feature, args.phase, affected) if args.command == 'project' else
                  check(root, feature, args.phase, affected, args.operation, args.repair))
        if args.only and args.command not in ('verify', 'finish'):
            result['requirements'] = [r for r in result['requirements'] if r['id'] == args.only]
            if not result['requirements']:
                raise ValueError('Requested obligation is not applicable in this phase')
        print(json.dumps(result) if args.command in ('verify', 'finish') else render(result, args.phase, bool(args.only)))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

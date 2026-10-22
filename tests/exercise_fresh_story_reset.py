"""One deterministic reset exercise in the existing installed consumer.

No installation loop or coding agent; every human decision below is simulated.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys


def exercise(project, source_root):
    # Reuse the actual installed consumer without changing the enclosing updater's
    # captured inputs or leaving fictional source/ratification as consumer authority.
    names = ['.specify/memory/constitution.md', '.specify/memory/constitution-ratification.json',
             'docs/architecture/bootstrap-decisions.json', '.specify/integration.json',
             'docs/architecture/reviews/constitution-review.md', 'src/AbandonedStory.txt',
             'tests/AbandonedStory.txt', 'src/SharedStory.txt', 'docs/DeliveredStory.txt',
             '.program-kit/specification-intake/RESET/brief.json',
             '.program-kit/consumer.lock', 'artifacts/story-reset-request.json', 'artifacts/story-reset-body.md']
    before = {name: (project / name).read_bytes() if (project / name).is_file() else None for name in names}
    feature = project / 'specs/998-fresh-story-reset'
    assert not feature.exists(), 'Fixture cannot overwrite existing feature work'
    archive_root = project / '.program-kit/abandoned-features'
    prior_archives = set(archive_root.glob('998-fresh-story-reset-*'))
    try:
        _exercise(project, source_root)
    finally:
        for name, payload in before.items():
            target = project / name
            if payload is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(payload)
        for directory in [feature, *(set(archive_root.glob('998-fresh-story-reset-*')) - prior_archives)]:
            assert directory.resolve().is_relative_to(project.resolve())
            if directory.is_dir():
                shutil.rmtree(directory)


def _exercise(project, source_root):
    from validate_governance_state import constitution
    scripts = project / '.specify/extensions/program-kit-governance/scripts'
    feature = project / 'specs/998-fresh-story-reset'
    feature.mkdir(parents=True)
    relative = feature.relative_to(project).as_posix()
    prior_archives = set((project / '.program-kit/abandoned-features').glob('998-fresh-story-reset-*'))
    def run(script, *arguments, fail=None):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(scripts / script), *arguments],
                                cwd=project, capture_output=True, text=True, encoding='utf-8')
        if fail:
            assert result.returncode == 2 and fail in result.stdout + result.stderr, result.stdout + result.stderr
        else:
            assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout
    # The owning archive-install fixture has already checked actual command resolution.
    memory = project / '.specify/memory/constitution.md'
    memory.parent.mkdir(parents=True, exist_ok=True)
    strict = constitution() + '\nEvery changed behavior requires tests before implementation.\n'
    memory.write_text(strict, encoding='utf-8')
    run('governance_state.py', 'begin')
    run('governance_state.py', 'write-review', '--stage', 'constitution')
    run('governance_state.py', 'ratify', '--verdict', 'ratify', '--approval-mode', 'automatic')
    for name, body in (('spec.md', 'Old layer-oriented partial feature'), ('plan.md', 'All future foundations first'),
                       ('tasks.md', '- [X] T001 Old partial code\n- [ ] T002 Old unfinished UI')):
        (feature / name).write_text(body, encoding='utf-8')
    old_code = project / 'src/AbandonedStory.txt'
    old_test = project / 'tests/AbandonedStory.txt'
    for target in (old_code, old_test):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Old feature partial implementation/test; not new progress.', encoding='utf-8')
    preserved = ['docs/architecture/bootstrap-decisions.json', '.specify/extensions/program-kit-governance/extension.yml',
                 '.program-kit/specification-intake/RESET/brief.json',
                 '.specify/integration.json', 'src/SharedStory.txt', 'docs/DeliveredStory.txt', '.program-kit/consumer.lock']
    for name in preserved:
        target = project / name
        if not target.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('{}' if name.endswith('.json') else 'Designated bootstrap/shared/delivered/lock fixture input.', encoding='utf-8')
    before = {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in preserved}
    request_file = project / 'artifacts/story-reset-request.json'
    request_file.parent.mkdir(exist_ok=True)
    request_file.write_text(json.dumps({'action': 'initialize', 'baseline': 'fixture-commit', 'source': 'simulated reviewer'}), encoding='utf-8')
    run('task_draft.py', 'delivery', '--feature-dir', relative, '--content-file', str(request_file), fail='Amend and ratify')
    run('governance_state.py', 'begin')
    # Replace the old sequencing principle with the resolved installed amendment, never coexist.
    from specify_cli.presets import PresetResolver
    resolved = PresetResolver(project).resolve_content('constitution-template', 'template')
    assert 'Verification selected by risk' in resolved and 'Runnable stories and human review' in resolved
    amendment = resolved[resolved.index('## Application engineering principles'):]
    memory.write_text(constitution() + '\n' + amendment, encoding='utf-8')
    run('task_draft.py', 'delivery', '--feature-dir', relative, '--content-file', str(request_file), fail='completed ratification')
    run('governance_state.py', 'write-review', '--stage', 'constitution')
    run('governance_state.py', 'ratify', '--verdict', 'ratify', '--approval-mode', 'automatic')
    run('task_draft.py', 'delivery', '--feature-dir', relative, '--content-file', str(request_file), fail='Fresh specification')
    selected = [relative + '/' + name for name in ('spec.md', 'plan.md', 'tasks.md')] + ['src/AbandonedStory.txt', 'tests/AbandonedStory.txt']
    request = {'method': 'fresh-feature-delete-v1', 'feature': relative, 'reviewSource': 'simulated explicit inventory review', 'selectionSource': 'simulated exact selected reset',
        'files': [{'path': name, 'owner': relative, 'sha256': hashlib.sha256((project / name).read_bytes()).hexdigest()} for name in selected],
        'preserve': preserved}
    request_file.write_text(json.dumps(request), encoding='utf-8')
    run('task_draft.py', 'reset', '--feature-dir', relative, '--content-file', str(request_file))
    result = json.loads(run('task_draft.py', 'reset', '--feature-dir', relative, '--content-file', str(request_file), '--apply'))
    assert result['status'] == 'deleted' and 'archive' not in result
    assert all(not (project / name).exists() for name in selected) and not feature.exists()
    assert set((project / '.program-kit/abandoned-features').glob('998-fresh-story-reset-*')) == prior_archives
    assert before == {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in preserved}
    # Fresh phases use the actual installed resolver and native validators, with fictional authoring.
    feature.mkdir(parents=True)
    from validate_story_delivery import story_tasks
    policy = '<!-- program-kit:story-delivery-v1 -->\n'
    spec = PresetResolver(project).resolve_content('spec-template', 'template')
    plan = PresetResolver(project).resolve_content('plan-template', 'template')
    assert 'independent runnable walkthrough' in spec and 'risk and verification sequence' in plan
    (feature / 'spec.md').write_text(policy + 'Fresh specify and clarification: confirmed fictional actor intent, useful owned outcome, non-goals and material failures.\n', encoding='utf-8')
    (feature / 'plan.md').write_text(policy + 'Fresh plan: coherent known scaffold first, maintained checks, missing consumer tests; explicit story review and advisory effort.\n'
        '\n## Operation implementation map\n| Operation | Decision | Resolution | Source |\n|---|---|---|---|\n'
        + '\n'.join('| ' + operation + ' | ' + key + ' | ' + resolution + ' | spec.md |'
                    for operation in ('create', 'integrate', 'export')
                    for key, resolution in (
                        ('ownership', 'The fictional text owner maintains finite task-state artifacts; provider or application behavior is outside this fixture.'),
                        ('results', 'Fresh uncompleted story tasks preserve the fictional owned outcome and carry no prior implementation progress.'),
                        ('limits', 'No applicable limits: this fresh fictional text-state authoring changes no behavioral/resource ceiling.')))
        + '\n', encoding='utf-8')
    for phase in ('planning', 'after-plan', 'tasks'):
        output = run('phase_obligations.py', 'project' if phase != 'after-plan' else 'check', '--feature-dir', relative, '--phase', phase)
        if phase == 'tasks':
            assert 'Materialize known scaffolds first' in output
    run('task_draft.py', 'prepare', '--feature-dir', relative, '--phases', 'stories')
    body = project / 'artifacts/story-reset-body.md'; body.write_text(story_tasks(), encoding='utf-8')
    run('task_draft.py', 'save-phase', '--feature-dir', relative, '--phase', 'stories', '--content-file', str(body))
    run('task_draft.py', 'finalize', '--feature-dir', relative)
    run('phase_obligations.py', 'check', '--feature-dir', relative, '--phase', 'after-tasks')
    analyze = (project / '.agents/skills/speckit-analyze/SKILL.md').read_text(encoding='utf-8')
    assert 'STRICTLY READ-ONLY' in analyze and 'risk-selected sequence overrides' in analyze and 'Story delivery map' in analyze
    baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=project, text=True, encoding='utf-8', timeout=30).strip()
    request_file.write_text(json.dumps({'action': 'initialize', 'baseline': baseline, 'source': 'simulated reviewer; no real human acceptance'}), encoding='utf-8')
    run('task_draft.py', 'delivery', '--feature-dir', relative, '--content-file', str(request_file))
    run('implementation_preflight.py', '--feature-dir', relative)
    assert not list(feature.glob('*Abandoned*')) and '[X]' not in (feature / 'tasks.md').read_text(encoding='utf-8')
    print('Installed fresh-story reset: deleted old partial work without an archive; normal constitution ratification; retained intake/designated inputs; fresh phase contracts consumed. Simulated humans only.', flush=True)

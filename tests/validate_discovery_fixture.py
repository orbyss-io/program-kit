"""Protect discovery-input isolation; optionally inspect real PrepareOnly evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'tests/live/scenarios/repair-desk/v1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path)
    args = parser.parse_args()
    fixture = json.loads((CASE / 'fixture.json').read_text())
    assert fixture['kind'] == 'human-intake-discovery'
    assert fixture['consumerInputs'] == ['PROJECT_REQUEST.md']
    assert not fixture['acceptanceContractsAtIntake'] and not fixture['preconfirmedIntake']
    assert fixture['preselectedRoadmapEntry'] is None
    assert fixture['executionBudget']['featureSlices'] == 1
    assert fixture['roadmapSelection'] == 'after-bootstrap-human-review'
    expected = set(fixture['consumerInputs'] + fixture['operatorOnly'] + ['fixture.json'])
    assert {p.name for p in CASE.iterdir()} == expected
    idea = (CASE / 'PROJECT_REQUEST.md').read_bytes()
    assert 400 < len(idea) < 2500, 'Keep the consumer vision brief, not an implementation contract'
    assert not re.search(rb'RM0[12]|IWebShellFeature|PostgreSQL|EF Core|NuGet|\.Core|endpoint|/api/|spec\.md', idea, re.I)
    if args.session:
        state = json.loads((args.session / 'session.json').read_text(encoding='utf-8-sig'))
        project = Path(state['workspace'])
        assert (project / 'product-idea.md').read_bytes() == idea
        assert state['initialIdea']['sha256'] == hashlib.sha256(idea).hexdigest()
        assert not state.get('acceptanceContracts') and not (project / 'acceptance').exists()
        assert not list((project / '.specify/workflows/runs').glob('*/state.json'))
        assert not (project / 'docs/architecture/bootstrap-intake.json').exists()
        for name in fixture['operatorOnly'] + ['fixture.json']:
            assert not (project / name).exists(), f'Operator material leaked: {name}'
        assert (project / '.agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md').is_file()
    print('Discovery vision isolation verified; no preselected slice, acceptance contracts or agent execution.')


if __name__ == '__main__':
    main()

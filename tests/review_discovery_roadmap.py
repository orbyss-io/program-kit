"""Extract a reviewer worksheet without changing or approving consumer artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    if output.is_relative_to(project):
        parser.error('Keep the independent reviewer worksheet outside the consumer workspace')
    if output.exists():
        parser.error('Preserve existing reviews; choose a new output filename')
    scripts = project / '.specify/extensions/program-kit-governance/scripts'
    if not (scripts / 'governance_state.py').is_file():
        parser.error('The consumer must have its installed Program Kit governance parser')
    sys.path.insert(0, str(scripts))
    import governance_state as governance
    previous = Path.cwd()
    try:
        os.chdir(project)
        governance.configure_paths()
        model_path = project / governance.ARCHITECTURE_MAP
        roadmap_path = project / governance.ROADMAP
        model = json.loads(model_path.read_text(encoding='utf-8'))
        entries = governance.roadmap_records(roadmap_path)
    finally:
        os.chdir(previous)
    strategy = model.get('strategic_model', {})
    journeys = strategy.get('journeys', [])
    sources = [model_path, roadmap_path, project / 'docs/architecture/bootstrap-intake.json']
    result = {
        'status': 'awaiting-human-review', 'project': str(project),
        'evidence': [{'path': str(path.relative_to(project)),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sources],
        'journeys': journeys, 'candidate_slices': strategy.get('candidate_slices', []),
        'roadmap_entries': entries,
        'journey_dispositions': [{'journey_id': item['id'], 'entry_ids': [],
            'classification': None, 'rationale': None, 'evidence': []} for item in journeys],
        'first_slice_selection': {'entry_id': None, 'smallest_usable_outcome': None,
            'remaining_manual_handoff': None, 'future_entry_ids': [], 'human_confirmation': None},
        'review_findings': [], 'producer_interventions': [],
        'note': 'Extraction is not roadmap acceptance. Review coverage, grouping, dependencies and value using the separate scenario rubric.'
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({'review': str(output), 'journeys': len(journeys),
                      'roadmap_entries': len(entries), 'status': result['status']}))


if __name__ == '__main__':
    main()

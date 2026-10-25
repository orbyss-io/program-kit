"""Read historical workflow checkpoints; paid workflow execution is retired."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from live.v2.authorization import require_active_phase
from live.v2.common import LiveContractError, file_inventory, load_object, safe_relative, sha256_file, validate

PHASES = ('workflow-fresh', 'workflow-failure', 'workflow-resume')


def schemas(root: Path) -> Path:
    return root / 'tests/live/schemas/v2'


def walk(value):
    if isinstance(value, list):
        for child in value:
            yield from walk(child)
    elif isinstance(value, dict):
        if 'id' in value and 'type' in value:
            yield value
        for child in value.values():
            if isinstance(child, (list, dict)):
                yield from walk(child)


def review_gate(project: Path, run_id: str) -> dict | None:
    import yaml
    directory = project / '.specify/workflows/runs' / run_id
    state = load_object(directory / 'state.json')
    if state['status'] != 'paused':
        return None
    definition = yaml.safe_load((directory / 'workflow.yml').read_text(encoding='utf-8'))
    gate = next((step for step in walk(definition['steps'])
                 if step['id'] == state['current_step_id'] and step['type'] == 'gate'), None)
    if not gate:
        return None
    path = gate.get('show_file')
    if path:
        for key, value in load_object(directory / 'inputs.json')['inputs'].items():
            path = path.replace('{{ inputs.' + key + ' }}', str(value))
        packet = project / safe_relative(path)
        if not packet.resolve().is_relative_to(project.resolve()):
            raise LiveContractError('LIVE_REVIEW_PACKET_OUTSIDE_PROJECT')
        digest = sha256_file(packet)
    else:
        digest = None
    return {'step': gate['id'], 'input': gate.get('verdict_input'), 'options': gate['options'],
            'packet': path, 'sha256': digest, 'message': gate.get('message', '')}


def parent_checkpoint(root: Path, path: Path) -> tuple[dict, Path]:
    parent = load_object(path)
    validate(parent, load_object(schemas(root) / 'workflow-run.schema.json'))
    if parent.get('kind') != 'workflow-lifecycle' or parent.get('schemaVersion') not in {'2.1', '2.2'}:
        raise LiveContractError('LIVE_WORKFLOW_PARENT_REQUIRED')
    project = (root / safe_relative(parent['workspace'])).resolve()
    if not project.is_relative_to((root / 'artifacts/live-v2-w').resolve()):
        raise LiveContractError('LIVE_WORKFLOW_PARENT_NOT_DISPOSABLE')
    if parent['projectInventory'] != file_inventory(project):
        raise LiveContractError('LIVE_WORKFLOW_PARENT_CHANGED')
    if not parent['process']['cleanupComplete'] or not parent['process']['logsDrained']:
        raise LiveContractError('LIVE_WORKFLOW_PARENT_CLEANUP_INCOMPLETE')
    if parent['native']['status'] in {'completed', 'aborted'}:
        raise LiveContractError('LIVE_WORKFLOW_PARENT_NOT_RESUMABLE')
    if review_gate(project, parent['native']['run_id']) != parent['review']:
        raise LiveContractError('LIVE_WORKFLOW_REVIEW_CHANGED')
    return parent, project


def reviewed_input(parent: dict | None, verdict: str | None) -> dict:
    gate = parent.get('review') if parent else None
    if gate:
        if not gate['input'] or verdict not in gate['options']:
            raise LiveContractError('LIVE_WORKFLOW_ACTUAL_GATE_VERDICT_REQUIRED')
        return {'verdictInput': gate['input'], 'verdict': verdict}
    if verdict:
        raise LiveContractError('LIVE_WORKFLOW_FUTURE_VERDICT_FORBIDDEN')
    return {'verdictInput': None, 'verdict': None}


def reported_usage(state: dict, dispatches: list[dict], run_id: str) -> dict:
    selected = {record['step'] for record in dispatches if record['run_id'] == run_id}
    totals = {}
    reports = 0
    for identity in selected:
        output = state.get('step_results', {}).get(identity, {}).get('output', {})
        for line in output.get('stdout', '').splitlines():
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(event, dict) or event.get('type') != 'turn.completed' or not isinstance(event.get('usage'), dict):
                continue
            reports += 1
            for key, value in event['usage'].items():
                if isinstance(value, int) and not isinstance(value, bool):
                    totals[key] = totals.get(key, 0) + value
    return {'tokens': totals or None, 'reportedTurns': reports, 'cost': None,
            'note': 'Only usage emitted by current-segment Codex turn.completed events is counted; monetary cost is unavailable.'}


def issue(args) -> int:
    require_active_phase('workflow-fresh')


def reserve_dispatch(*args, **kwargs) -> None:
    require_active_phase('workflow-fresh')


def controlled_fault(*args, **kwargs) -> None:
    require_active_phase('workflow-failure')


def driver(job_path: Path) -> int:
    require_active_phase('workflow-fresh')


def run(args) -> int:
    require_active_phase('workflow-fresh')


def main() -> int:
    try:
        # Historical inspection stays read-only and grants no resume authority.
        if len(sys.argv) > 1 and sys.argv[1] == 'inspect-parent':
            parser = argparse.ArgumentParser(description=__doc__)
            parser.add_argument('command', choices=['inspect-parent'])
            parser.add_argument('--checkpoint', required=True)
            args = parser.parse_args()
            root = Path(__file__).resolve().parents[3]
            parent, _ = parent_checkpoint(root, Path(args.checkpoint).resolve())
            print(parent.get('review'))
            return 0
        require_active_phase('workflow-fresh')
    except (LiveContractError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())

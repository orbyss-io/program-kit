"""Read-only validation of historical Program Kit workflow completion.

The founding workflow is retired. Saved workflow/proof bytes are never migrated
into completion or resumed by this compatibility entrypoint.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
import bootstrap_lifecycle as lifecycle
import governance_state as governance
import bootstrap_recovery as recovery

RETIREMENT = ("PROGRAM_KIT_BOOTSTRAP_WORKFLOW_RETIRED: invoke "
    "$speckit-program-kit-governance-product-intake in the current session. "
    "Preserve saved workflow runs and old proof bytes; review existing intent and "
    "decisions explicitly. Incomplete old runs remain incomplete. Do not restart or convert them.")

class WorkflowLifecycleError(ValueError):
    pass

def run_directory(root: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise WorkflowLifecycleError('Invalid historical workflow run ID')
    return root / '.specify/workflows/runs' / run_id

def validate_engine_completion(root: Path) -> None:
    record = lifecycle.load(root / governance.BOOTSTRAP_COMPLETION)
    binding = record.get('workflow')
    if not isinstance(binding, dict):
        raise WorkflowLifecycleError('Project completion has no workflow-engine completion binding')
    directory = run_directory(root, binding['run_id'])
    state = lifecycle.load(directory / 'state.json')
    definition_path = directory / 'workflow.yml'
    last = state.get('step_results', {}).get('complete-bootstrap', {})
    if (state.get('run_id') != binding['run_id'] or state.get('workflow_id') != 'program-kit-bootstrap'
            or state.get('status') != 'completed'
            or last.get('status') != 'completed' or last.get('output', {}).get('exit_code') != 0
            or lifecycle.digest(definition_path) != binding.get('workflow_sha256')):
        raise WorkflowLifecycleError('Bootstrap completion requires the bound workflow engine to finish successfully')
    inputs = lifecycle.load(directory / 'inputs.json')['inputs']
    if binding.get('source_run') != inputs.get('source_run'):
        raise WorkflowLifecycleError('Completion source lineage differs from the native run')
    if binding.get('source_run'):
        source_run = binding['source_run']
        recovery.manifest(root, source_run)
        mapping = lifecycle.load(root / '.specify/workflows/resumptions' / f'{source_run}.json')
        if mapping['continuation_run'] != binding['run_id']:
            raise WorkflowLifecycleError('Completion is not the recorded native continuation')


def main() -> int:
    if sys.argv[1:] != ['validate-completion']:
        print(RETIREMENT, file=sys.stderr)
        return 2
    try:
        validate_engine_completion(Path.cwd().resolve())
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'Historical completion is not valid: {error}', file=sys.stderr)
        return 1
    print('Historical bound workflow completion validates; no current founding or runtime acceptance asserted.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

"""Prepare the bootstrap scenario from a completed human-owned intake; no agent starts."""
import argparse
from pathlib import Path
from live.v2.intake_handoff import capture

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decision-id', action='append', help='Exact reviewed founding decision; required when the intake has multiple choices')
    args = parser.parse_args()
    scenario = capture(Path(__file__).resolve().parents[1], args.session.resolve(), args.output.resolve(), args.decision_id)
    print('Actual intake captured for bootstrap: ' + scenario['id'] + '; no paid authorization issued.')

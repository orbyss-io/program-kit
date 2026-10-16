"""Read actual evidence repository/rules; no mutations or inferred provisioning."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extensions/program-kit-governance/scripts'))
from repair_feedback import GitHub, verify_deployment, now

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-commit', required=True)
    parser.add_argument('--validator-commit', required=True)
    parser.add_argument('--gh', help='Explicit installed CLI when outside PATH')
    args = parser.parse_args()
    try:
        api = GitHub(args.gh)
        api.auth()
        print(json.dumps(verify_deployment(api, args.base_commit, args.validator_commit), indent=2))
    except (ValueError, OSError, KeyError):
        print(json.dumps({'availability': 'unavailable', 'retrievedAt': now(), 'provisioning': 'not-established'}))
        raise SystemExit(1)

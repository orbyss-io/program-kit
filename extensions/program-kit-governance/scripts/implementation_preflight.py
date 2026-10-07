"""Validate the planned compilation graph and supply implementation guidance."""
import argparse
from pathlib import Path
from phase_obligations import inside, check, render

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--stage', choices=('setup','source'), default='source', help='Compatibility option; neither stage consumes governance receipts')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        print(render(check(root, inside(root, args.feature_dir), 'implementation'), 'implementation'))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())

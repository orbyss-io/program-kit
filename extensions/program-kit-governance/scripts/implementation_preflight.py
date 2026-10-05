"""Supply implementation guidance without a parallel lifecycle gate."""
import argparse
from pathlib import Path
from phase_obligations import inside, project, render

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--stage', choices=('setup','source'), default='source', help='Compatibility option; neither stage consumes governance receipts')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    print(render(project(root, inside(root, args.feature_dir), 'implementation'), 'implementation'))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

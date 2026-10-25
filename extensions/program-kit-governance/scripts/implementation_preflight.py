"""Read relevant guidance before native implementation; execute no engineering work."""
import argparse
from pathlib import Path
import sys
from phase_obligations import inside, check, render, text_page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    args = parser.parse_args()
    try:
        root = Path(args.repository).resolve()
        feature = inside(root, args.feature_dir)
        if not feature.is_dir():
            raise ValueError('Locate the existing native Spec Kit feature directory')
        print(text_page(render(check(root, feature, 'implementation'), 'implementation')))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

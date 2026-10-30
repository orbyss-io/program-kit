"""Read-only optional native autosave capability check against the selected public package/source capture."""
import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path('.'))
    args = parser.parse_args()
    root = args.repository.resolve()
    candidates = [root / '.specify/extensions/program-kit-dotnet/scripts',
                  root / 'extensions/program-kit-dotnet/scripts']
    scripts = next((path for path in candidates if (path / 'foundation_composition.py').is_file()), None)
    if scripts is None:
        parser.error('Locate the existing installed Program Kit .NET adapter.')
    sys.path.insert(0, str(scripts))
    from foundation_composition import browser_declarations
    try:
        browser_declarations(root, require_autosave=True)
    except (ValueError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print('Selected native autosave module/declaration match their public package/source capture; no runtime acceptance claimed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

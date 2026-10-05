"""Bound local toolkit execution history; preview is the default.

Only artifacts/program-kit/runs/<id>/run.json with owner=program-kit is owned
here. Application results, old receipts and troubleshooting files are excluded.
"""
import argparse
import json
import shutil
import stat
from pathlib import Path


def linked(path):
    if not path.exists() and not path.is_symlink():
        return False
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def preview(repository, include_failed=False):
    base = repository.resolve() / 'artifacts/program-kit/runs'
    runs = []
    if any(linked(path) for path in (base, base.parent, base.parent.parent)):
        raise ValueError('Execution history root must not be a symlink')
    for directory in base.glob('*'):
        if linked(directory) or not directory.is_dir():
            continue
        marker = directory / 'run.json'
        if not marker.is_file() or linked(marker):
            continue
        try:
            value = json.loads(marker.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            continue  # Damaged diagnostics remain available for explicit inspection.
        if not isinstance(value, dict):
            continue
        if value.get('owner') != 'program-kit' or value.get('schemaVersion') != 1:
            continue
        if any(linked(p) for p in directory.rglob('*')):
            continue
        runs.append((directory, value))
    complete = sorted((r for r in runs if r[1].get('status') == 'completed' and isinstance(r[1].get('finishedAtUtc'), str)),
                      key=lambda r: (r[1]['finishedAtUtc'], r[0].name), reverse=True)
    removable = complete[5:]
    if include_failed:
        removable += [r for r in runs if r[1].get('status') == 'failed']
    return [directory.relative_to(repository.resolve()).as_posix() for directory, _ in removable]


def cleanup(repository, include_failed=False):
    candidates = preview(repository, include_failed)
    base = (repository.resolve() / 'artifacts/program-kit/runs').resolve()
    for relative in candidates:
        path = (repository / relative).resolve()
        if path.parent != base:
            raise ValueError('Cleanup path escapes owned execution history')
        # Reinspect immediately before deletion; never follow a newly added link.
        if relative not in preview(repository, include_failed):
            raise ValueError('History changed after preview; retry')
        shutil.rmtree(path)
    return candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--plan', action='store_true', help='Explicit preview (also the default)')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--include-failed', action='store_true', help='Explicitly remove failed owned runs; interrupted runs are always retained')
    args = parser.parse_args()
    if args.plan and args.apply:
        parser.error('--plan and --apply are mutually exclusive')
    root = Path(args.repository).resolve()
    print(json.dumps({'removed' if args.apply else 'wouldRemove':
                      cleanup(root, args.include_failed) if args.apply else preview(root, args.include_failed)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def main() -> int:
    if len(sys.argv) < 5 or sys.argv[1] != "--site-packages" or sys.argv[3] != "--":
        print(
            "Program Kit Specify bridge requires --site-packages <absolute-directory> -- <arguments>.",
            file=sys.stderr,
        )
        return 2
    site_packages = Path(sys.argv[2])
    if not site_packages.is_absolute() or not site_packages.is_dir():
        print(f"Program Kit Specify bridge rejected site-packages: {site_packages}", file=sys.stderr)
        return 2
    site_packages = site_packages.resolve()
    sys.path.insert(0, str(site_packages))
    specification = importlib.util.find_spec("specify_cli")
    origin = Path(specification.origin).resolve() if specification and specification.origin else None
    if origin is None or not inside(site_packages, origin):
        print(
            f"Program Kit Specify bridge did not resolve specify_cli inside {site_packages}.",
            file=sys.stderr,
        )
        return 2
    from specify_cli import main as specify_main

    sys.argv = ["specify", *sys.argv[4:]]
    result = specify_main()
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())

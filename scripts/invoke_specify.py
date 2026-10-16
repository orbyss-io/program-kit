from __future__ import annotations

import importlib.util
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def launcher_site_packages(launcher: Path) -> Path:
    """Resolve the same native installed environment; never install or guess a fallback."""
    launcher=launcher.resolve(strict=True)
    payload=launcher.read_bytes()
    if launcher.suffix.lower()=='.exe':
        marker=payload.rfind(b'#!')
        if marker<0 or b'from specify_cli import main' not in payload[marker:]:
            raise ValueError('PKU142 unsupported Spec Kit launcher; pass its exact --site-packages environment')
        interpreter=Path(payload[marker+2:].splitlines()[0].decode().strip().strip('"'))
    else:
        import shlex
        line=payload.splitlines()[0].decode()
        words=shlex.split(line[2:]) if line.startswith('#!') else []
        if len(words)!=1:raise ValueError('PKU142 unsupported native launcher shebang; pass exact --site-packages')
        interpreter=Path(words[0])
    if not interpreter.is_absolute() or not interpreter.is_file():
        raise ValueError('PKU142 original Spec Kit launcher interpreter is unavailable')
    environment=interpreter.parent.parent
    candidates=[environment/'Lib/site-packages',*environment.glob('lib/python*/site-packages')]
    matches=[path.resolve() for path in candidates if (path/'specify_cli/__init__.py').is_file()]
    if len(set(matches))!=1:raise ValueError('PKU142 ambiguous/missing native Spec Kit package environment')
    return matches[0]


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def install_loopback_http_only_opener() -> None:
    original_http_handler = urllib.request.HTTPHandler

    class LoopbackHTTPHandler(original_http_handler):
        def http_open(self, request):
            hostname = urllib.parse.urlsplit(request.full_url).hostname
            if hostname not in {"127.0.0.1", "::1", "localhost"}:
                raise urllib.error.URLError(
                    "Program Kit loopback setup rejected non-loopback HTTP"
                )
            return super().http_open(request)

    class DisabledHTTPSHandler(urllib.request.BaseHandler):
        def https_open(self, request):
            raise urllib.error.URLError(
                "Program Kit loopback setup disables HTTPS in this process"
            )

    urllib.request.HTTPHandler = LoopbackHTTPHandler
    urllib.request.HTTPSHandler = DisabledHTTPSHandler
    urllib.request.install_opener(urllib.request.build_opener())


def main() -> int:
    if len(sys.argv) < 5 or sys.argv[1] not in ("--site-packages","--launcher"):
        print(
            "Program Kit Specify bridge requires --site-packages <absolute-directory> "
            "[--loopback-http-only] -- <arguments>.",
            file=sys.stderr,
        )
        return 2
    argument_index = 3
    loopback_http_only = False
    if sys.argv[argument_index] == "--loopback-http-only":
        loopback_http_only = True
        argument_index += 1
    if argument_index >= len(sys.argv) or sys.argv[argument_index] != "--":
        print(
            "Program Kit Specify bridge requires --site-packages <absolute-directory> "
            "[--loopback-http-only] -- <arguments>.",
            file=sys.stderr,
        )
        return 2
    try:
        site_packages = launcher_site_packages(Path(sys.argv[2])) if sys.argv[1]=='--launcher' else Path(sys.argv[2])
    except (OSError,ValueError) as error:
        print(str(error),file=sys.stderr)
        return 2
    if not site_packages.is_absolute() or not site_packages.is_dir():
        print(f"Program Kit Specify bridge rejected site-packages: {site_packages}", file=sys.stderr)
        return 2
    site_packages = site_packages.resolve()
    sys.path.insert(0, str(site_packages))
    if loopback_http_only:
        install_loopback_http_only_opener()
    specification = importlib.util.find_spec("specify_cli")
    origin = Path(specification.origin).resolve() if specification and specification.origin else None
    if origin is None or not inside(site_packages, origin):
        print(
            f"Program Kit Specify bridge did not resolve specify_cli inside {site_packages}.",
            file=sys.stderr,
        )
        return 2
    from specify_cli import main as specify_main
    arguments=sys.argv[argument_index + 1 :]
    sys.argv = ["specify", *arguments]
    if {'--help','--version'}&set(arguments):
        result=specify_main()
        return result if isinstance(result,int) else 0
    profile_source=Path(__file__).resolve().parents[1]/'extensions/program-kit-governance/scripts/render_profile.py'
    if not profile_source.is_file():
        print('PKU142 native CLI bridge lacks its release-owned generation profile recorder.',file=sys.stderr)
        return 2
    profile_spec=importlib.util.spec_from_file_location('program_kit_native_render_capture',profile_source)
    profile=importlib.util.module_from_spec(profile_spec)
    profile_spec.loader.exec_module(profile)

    with profile.capture(Path.cwd(),sys.argv[1:]):
        result = specify_main()
        if isinstance(result,int) and result!=0:
            raise SystemExit(result)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())

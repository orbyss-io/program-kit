from __future__ import annotations

import argparse
import contextlib
import http.server
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Iterator

import yaml


REPOSITORY = "https://raw.githubusercontent.com/orbyss-io/program-kit"
CURRENT = f"{REPOSITORY}/{os.environ.get('PROGRAM_KIT_PUBLIC_REF', 'main')}/catalogs"
EXPECTED_HOOKS = {
    "before_constitution",
    "after_constitution",
    "before_specify",
    "after_specify",
    "before_plan",
    "before_tasks",
    "after_plan",
    "after_tasks",
    "before_implement",
    "after_implement",
}


def run(*args: str, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    command = args
    specify_site_packages = environment.get("PROGRAM_KIT_SPECIFY_SITE_PACKAGES")
    if args and args[0] == "specify" and specify_site_packages:
        command = (
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "scripts/invoke_specify.py"),
            "--site-packages",
            specify_site_packages,
            "--loopback-http-only",
            "--",
            *args[1:],
        )
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        output = "\n".join(value.strip() for value in (exc.stdout, exc.stderr) if value.strip())
        if output:
            print(output, file=sys.stderr)
        raise


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile, length=64 * 1024)


@contextlib.contextmanager
def running_catalog_server(server, directory: Path):
    """Use the established Windows archive transport under suite supervision."""
    thread = None
    process = None
    server_log = None
    try:
        if os.name == "nt":
            port = server.server_port
            server.server_close()
            server_log = (directory / "catalog-server.log").open("w", encoding="utf-8")
            script = Path(__file__).resolve().parents[1] / "scripts/local_catalog_server.py"
            # This stdlib-only server must be the actual process we wait for:
            # a uv venv launcher can outlive termination through its Python child.
            interpreter = getattr(sys, "_base_executable", sys.executable)
            process = subprocess.Popen(
                [interpreter, str(script), str(port), "--directory", str(directory)],
                stdin=subprocess.DEVNULL, stdout=server_log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            deadline = time.monotonic() + 10
            while True:
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Upgrade catalog server did not start; see catalog-server.log")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
        else:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
        yield
    finally:
        if thread is not None:
            server.shutdown()
            thread.join(timeout=10)
        server.server_close()
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if server_log is not None:
            server_log.close()


@contextlib.contextmanager
def candidate_catalogs(root: Path, artifacts: Path | None) -> Iterator[str]:
    if artifacts is None:
        yield CURRENT
        return

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    required = {
        "extensions.json": root / "catalogs/extensions.json",
        "presets.json": root / "catalogs/presets.json",
        "workflows.json": root / "catalogs/workflows.json",
        "bundles.json": root / "catalogs/bundles.json",
        f"program-kit-governance-{version}.zip": artifacts / f"program-kit-governance-{version}.zip",
        f"program-kit-building-blocks-{version}.zip": artifacts / f"program-kit-building-blocks-{version}.zip",
        f"program-kit-dotnet-{version}.zip": artifacts / f"program-kit-dotnet-{version}.zip",
        f"program-kit-governance-preset-{version}.zip": artifacts / f"program-kit-governance-preset-{version}.zip",
        f"program-kit-{version}.zip": artifacts / f"program-kit-{version}.zip",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Candidate upgrade inputs are missing: {missing}")

    with tempfile.TemporaryDirectory(prefix="program-kit-candidate-catalog-") as directory:
        server_root = Path(directory)
        handler = lambda *args, **kwargs: QuietHandler(  # noqa: E731
            *args, directory=str(server_root), **kwargs
        )
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            for name, source in required.items():
                if name.endswith(".json"):
                    continue
                shutil.copyfile(source, server_root / name)

            for name in ("extensions.json", "presets.json", "workflows.json", "bundles.json"):
                value = json.loads(required[name].read_text(encoding="utf-8"))
                if name == "extensions.json":
                    for entry in value["extensions"].values():
                        entry["download_url"] = f"{base}/{Path(entry['download_url']).name}"
                elif name == "presets.json":
                    for entry in value["presets"].values():
                        entry["download_url"] = f"{base}/{Path(entry['download_url']).name}"
                elif name == "workflows.json":
                    for entry in value["workflows"].values():
                        entry["url"] = f"{base}/program-kit-bootstrap-{version}.yml"
                else:
                    for entry in value["bundles"].values():
                        entry["download_url"] = f"{base}/{Path(entry['download_url']).name}"
                (server_root / name).write_text(
                    json.dumps(value, indent=2) + "\n", encoding="utf-8"
                )
            with running_catalog_server(server, server_root):
                yield base
        finally:
            server.server_close()


def tag_file(root: Path, tag: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{tag}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return result.stdout


@contextlib.contextmanager
def previous_release_catalogs(
    root: Path,
    tag: str,
    version: str,
    artifacts: Path | None,
) -> Iterator[str]:
    if artifacts is None:
        yield f"{REPOSITORY}/{tag}/catalogs"
        return

    archive_names = (
        f"program-kit-governance-{version}.zip",
        f"program-kit-dotnet-{version}.zip",
        f"program-kit-governance-preset-{version}.zip",
        f"program-kit-{version}.zip",
    )
    missing = [
        str(artifacts / name)
        for name in archive_names
        if not (artifacts / name).is_file()
    ]
    if missing:
        raise FileNotFoundError(f"Previous release archives are missing: {missing}")

    with tempfile.TemporaryDirectory(prefix="program-kit-previous-catalog-") as directory:
        server_root = Path(directory)
        handler = lambda *args, **kwargs: QuietHandler(  # noqa: E731
            *args, directory=str(server_root), **kwargs
        )
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            for name in archive_names:
                shutil.copyfile(artifacts / name, server_root / name)
            workflow_name = f"program-kit-bootstrap-{version}.yml"
            (server_root / workflow_name).write_bytes(
                tag_file(root, tag, "workflows/program-kit-bootstrap/workflow.yml")
            )
            for name in ("extensions.json", "presets.json", "workflows.json", "bundles.json"):
                value = json.loads(tag_file(root, tag, f"catalogs/{name}"))
                if name == "extensions.json":
                    for entry in value["extensions"].values():
                        entry["download_url"] = f"{base}/{Path(entry['download_url']).name}"
                elif name == "presets.json":
                    for entry in value["presets"].values():
                        entry["download_url"] = f"{base}/{Path(entry['download_url']).name}"
                elif name == "workflows.json":
                    for entry in value["workflows"].values():
                        entry["url"] = f"{base}/{workflow_name}"
                else:
                    for entry in value["bundles"].values():
                        entry["download_url"] = f"{base}/{Path(entry['download_url']).name}"
                (server_root / name).write_text(
                    json.dumps(value, indent=2) + "\n", encoding="utf-8"
                )
            with running_catalog_server(server, server_root):
                yield base
        finally:
            server.server_close()


def replace_catalogs(project: Path, base: str) -> None:
    specify = project / ".specify"
    (specify / "extension-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": "program-kit",
                        "url": f"{base}/extensions.json",
                        "priority": 10,
                        "install_allowed": True,
                        "description": "Program Kit upgrade regression",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (specify / "workflow-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": "program-kit",
                        "url": f"{base}/workflows.json",
                        "priority": 1,
                        "install_allowed": True,
                        "description": "Program Kit upgrade regression",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (specify / "preset-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": "program-kit",
                        "url": f"{base}/presets.json",
                        "priority": 10,
                        "install_allowed": True,
                        "description": "Program Kit upgrade regression",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (specify / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "catalogs": [
                    {
                        "id": "program-kit",
                        "url": f"{base}/bundles.json",
                        "priority": 10,
                        "install_policy": "install-allowed",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def previous_stable(root: Path, current_version: str) -> tuple[str, str]:
    current = tuple(int(part) for part in current_version.split("."))
    result = subprocess.run(
        ["git", "tag", "--list", "v*.*.*"],
        cwd=root,
        text=True,
        check=True,
        capture_output=True,
    )
    candidates: list[tuple[tuple[int, int, int], str]] = []
    for tag in result.stdout.splitlines():
        match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag.strip())
        if match is None:
            continue
        parsed = tuple(int(part) for part in match.groups())
        if parsed < current:
            candidates.append((parsed, tag.strip()))
    if not candidates:
        raise RuntimeError(f"No stable tag precedes v{current_version}")
    version, tag = max(candidates)
    return ".".join(str(part) for part in version), tag


def manifest_version(path: Path, section: str) -> str:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value[section]["version"]


def installed_versions(project: Path) -> dict[str, str]:
    specify = project / ".specify"
    records = json.loads((specify / "bundle-records.json").read_text(encoding="utf-8"))
    bundle = next(record for record in records["bundles"] if record["bundle_id"] == "program-kit")
    extension_record = next(
        component
        for component in bundle["contributed_components"]
        if component["kind"] == "extensions"
        and component["id"] == "program-kit-governance"
    )
    dotnet_extension_record = next(
        component
        for component in bundle["contributed_components"]
        if component["kind"] == "extensions"
        and component["id"] == "program-kit-dotnet"
    ) if any(
        component["kind"] == "extensions" and component["id"] == "program-kit-dotnet"
        for component in bundle["contributed_components"]
    ) else None
    building_block_record = next(
        component
        for component in bundle["contributed_components"]
        if component["kind"] == "extensions"
        and component["id"] == "program-kit-building-blocks"
    ) if any(
        component["kind"] == "extensions" and component["id"] == "program-kit-building-blocks"
        for component in bundle["contributed_components"]
    ) else None
    versions = {
        "extension": manifest_version(
            specify / "extensions/program-kit-governance/extension.yml", "extension"
        ),
        "preset": manifest_version(specify / "presets/program-kit-governance-preset/preset.yml", "preset"),
        "bundle record": bundle["version"],
        "bundle extension record": extension_record["version"],
    }
    workflow = specify / 'workflows/program-kit-bootstrap/workflow.yml'
    if workflow.is_file():
        registry = json.loads((specify / 'workflows/workflow-registry.json').read_text(encoding='utf-8'))
        versions['workflow'] = manifest_version(workflow, 'workflow')
        versions['workflow registry'] = registry['workflows']['program-kit-bootstrap']['version']
    if dotnet_extension_record is not None:
        versions["dotnet extension"] = manifest_version(
            specify / "extensions/program-kit-dotnet/extension.yml", "extension"
        )
        versions["bundle .NET extension record"] = dotnet_extension_record["version"]
    if building_block_record is not None:
        versions["building-block extension"] = manifest_version(
            specify / "extensions/program-kit-building-blocks/extension.yml", "extension"
        )
        versions["bundle building-block extension record"] = building_block_record["version"]
    return versions


def installed_component_bytes(project: Path) -> dict[str, str]:
    """Bind rejection to installed/native bytes, excluding transient catalog caches."""
    files = set()
    for name in ('.specify/extensions', '.specify/presets', '.specify/workflows',
                 '.specify/templates', '.specify/scripts', '.codex', 'eng', 'src'):
        files.update(path for path in (project / name).rglob('*') if path.is_file()
                     and '__pycache__' not in path.parts)
    # Spec Kit 1.1.3 keeps hooks/installed extension configuration and agent
    # integration state beside bundle ownership at the .specify root. Hidden
    # extension/preset .registry files and the workflow registry are in the trees above.
    files.update(path for path in (project / '.specify').iterdir() if path.is_file())
    return {path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(files)}


def main() -> int:
    parser = argparse.ArgumentParser(description='Upgrade the actual previous public release through the candidate packaged sequential updater.')
    parser.add_argument('--candidate-dir', type=Path, help='Actual local release-builder archives; otherwise use public release bytes')
    parser.add_argument('--previous-dir', type=Path, help='Cached immutable previous-release archives instead of public catalogs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    current = (root / 'VERSION').read_text(encoding='utf-8').strip()
    previous, tag = previous_stable(root, current)
    with previous_release_catalogs(root, tag, previous, args.previous_dir.resolve() if args.previous_dir else None) as catalogs, tempfile.TemporaryDirectory(prefix='program-kit-public-upgrade-') as temporary:
        workspace = Path(temporary)
        project = workspace / 'consumer app'; project.mkdir()
        run('specify', 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools', cwd=project)
        replace_catalogs(project, catalogs)
        # Reproduce actual historical initializer behavior and its native registrations.
        run('specify', 'workflow', 'add', 'program-kit-bootstrap', cwd=project)
        run('specify', 'bundle', 'install', 'program-kit', '--integration', 'codex', cwd=project)
        if set(installed_versions(project).values()) != {previous}:
            raise AssertionError('Prior public component versions are incoherent')
        from validate_public_delivery import prepare_prior_consumer
        class Preparation:
            def run(self, _name, command, target):
                run(*map(str, command), cwd=target)
        prepare_prior_consumer(Preparation(), project)
        authored = {'consumer-notes.txt': b'Keep the consumer decision.\n',
            '.specify/workflows/runs/historical-failed/state.json': b'{"status":"failed","synthetic":true}\n',
            '.specify/workflows/runs/historical-failed/workflow.yml': (project / '.specify/workflows/program-kit-bootstrap/workflow.yml').read_bytes()}
        for relative, raw in authored.items():
            path = project / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        name = f'program-kit-tooling-{current}.zip'
        if args.candidate_dir:
            archive = args.candidate_dir.resolve() / name
        else:
            import urllib.request
            base = f'https://github.com/orbyss-io/program-kit/releases/download/v{current}/'
            with urllib.request.urlopen(base + 'SHA256SUMS', timeout=30) as response:
                sums = dict((line.split(maxsplit=1)[1].lstrip('*'), line.split(maxsplit=1)[0]) for line in response.read().decode().splitlines())
            with urllib.request.urlopen(base + name, timeout=60) as response:
                raw = response.read()
            if hashlib.sha256(raw).hexdigest() != sums.get(name):
                raise AssertionError('Public tooling differs from the published checksum')
            archive = workspace / name; archive.write_bytes(raw)
        from validate_package_smoke import extract
        release = workspace / 'candidate'; extract(archive, release)
        run(sys.executable, str(release / 'scripts/upgrade_program_kit.py'), '--release-root', str(release),
            '--target', str(project), '--integration', 'codex', cwd=project)
        if set(installed_versions(project).values()) != {current}:
            raise AssertionError('Packaged updater did not converge all current component versions')
        if (project / '.specify/workflows/program-kit-bootstrap').exists():
            raise AssertionError('Retired workflow is still actively installed')
        for relative, raw in authored.items():
            if (project / relative).read_bytes() != raw:
                raise AssertionError('Upgrade changed historical/authored bytes: ' + relative)
        run(sys.executable, str(project / '.specify/extensions/program-kit-governance/scripts/governance_state.py'), 'validate-installation', cwd=project)
        record = next(row for row in json.loads((project / '.specify/bundle-records.json').read_text())['bundles'] if row['bundle_id'] == 'program-kit')
        if len(record['required_components']) != 4 or any(row['kind'] == 'workflows' for row in record['required_components']):
            raise AssertionError('Current native bundle retained retired workflow ownership')
    print(f'Public v{previous} to v{current} packaged upgrade and preserved history passed.')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

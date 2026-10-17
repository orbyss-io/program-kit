from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_policy_spec = importlib.util.spec_from_file_location('program_kit_device_policy', Path(__file__).with_name('device_toolchain.py'))
device = importlib.util.module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(device)


def version(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> str | None:
    try:
        result = subprocess.run(
            command + ["--version"],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip().splitlines()[0].removeprefix("v")


def executable(value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_file():
        return candidate.resolve()
    resolved = shutil.which(value)
    return Path(resolved).resolve() if resolved else None


def resolve_node(repository: Path, required: str, requested: str, manager: str) -> tuple[Path | None, str | None]:
    # Read only the active persistent selection. Manager exec/run can download tools or
    # hide a stale default, so neither manager caches nor PROGRAMKIT_* overrides are used.
    node = executable(requested)
    if requested != 'node' and node != executable('node'):
        node = executable('node')  # Explicit paths cannot hide the active device default.
    if node and not device.shared(node, repository):
        return None, None
    actual = version([str(node)], repository) if node else None
    return (node if actual == required else None), actual


def npm_candidates(node: Path, requested: str, repository: Path | None = None, required: str = '') -> list[list[str]]:
    active = executable('npm.cmd' if os.name == 'nt' else 'npm')
    selected = active  # A requested path cannot hide the current shared device selection.
    if not selected or (repository is not None and not device.shared(selected, repository)):
        return []
    return [[str(node), str(selected)] if selected.suffix.casefold() == '.js' else [str(selected)]]


def resolve_npm(repository: Path, node: Path, required: str, requested: str, environment=None) -> tuple[list[str] | None, str | None]:
    candidates = npm_candidates(node, requested, repository, required)
    command = candidates[0] if candidates else None
    actual = version(command, repository, environment) if command else None
    return (command if actual == required else None), actual


def require_writable_cache(cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    descriptor = -1
    probe: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".program-kit-write-probe-", dir=cache)
        probe = Path(name)
        os.close(descriptor)
        descriptor = -1
    except OSError as error:
        raise ValueError(f"PKT014 npm cache is not writable: {cache}: {error}") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if probe is not None:
            try:
                probe.unlink()
            except OSError:
                pass
    return cache


def cache_directory(repository: Path) -> Path:
    configured = os.environ.get("PROGRAMKIT_NPM_CACHE")
    cache = Path(configured).expanduser() if configured else repository / "artifacts/cache/npm"
    if not cache.is_absolute():
        cache = repository / cache
    return require_writable_cache(cache.resolve())


def trust_environment(
    repository: Path,
    cache: Path,
    selected_mode: str | None = None,
    selected_extra_ca: str | None = None,
) -> tuple[dict[str, str], str, str]:
    if os.environ.get("NPM_CONFIG_STRICT_SSL", "").casefold() == "false":
        raise ValueError("PKT015 NPM_CONFIG_STRICT_SSL=false is forbidden; configure system trust or an organization CA.")
    trust_mode = (
        selected_mode
        if selected_mode is not None
        else os.environ.get("PROGRAMKIT_NODE_TRUST_MODE", "system" if os.name == "nt" else "bundled")
    ).casefold()
    if trust_mode not in {"bundled", "system"}:
        raise ValueError("PKT015 PROGRAMKIT_NODE_TRUST_MODE must be bundled or system.")
    environment = os.environ.copy()
    environment["NPM_CONFIG_CACHE"] = str(cache)
    environment["NPM_CONFIG_STRICT_SSL"] = "true"
    if trust_mode == "system":
        existing = environment.get("NODE_OPTIONS", "").strip()
        if "--use-system-ca" not in existing.split():
            environment["NODE_OPTIONS"] = (existing + " --use-system-ca").strip()
    extra_ca = (
        selected_extra_ca
        if selected_extra_ca is not None
        else os.environ.get("PROGRAMKIT_NODE_EXTRA_CA_CERTS", "")
    ).strip()
    if extra_ca:
        path = Path(extra_ca)
        if not path.is_absolute():
            path = repository / path
        path = path.resolve()
        if not path.is_file():
            raise ValueError(f"PKT015 configured organization CA file is missing: {path}")
        environment["NODE_EXTRA_CA_CERTS"] = str(path)
        extra_ca = str(path)
    return environment, trust_mode, extra_ca


def node_npm_recovery(repository: Path, reason: str, required=None, installed=None, commands=None) -> str:
    """Read-only paired diagnosis; all actual device preparation stays user-owned."""
    if required is None:
        required = {}
        for name, filename in (('node', '.nvmrc'), ('npm', '.npm-version')):
            pin = repository / filename
            required[name] = pin.read_text(encoding='utf-8').strip().removeprefix('v') if pin.is_file() else None
    if not all(isinstance(required.get(name), str) and required[name] for name in ('node', 'npm')):
        return reason + '\nBoth authoritative .nvmrc and .npm-version pins are required; do not infer them from stale command evidence.'
    if installed is None:
        node, nv = resolve_node(repository, required['node'], 'node', 'auto')
        npm, pv = resolve_npm(repository, node, required['npm'], '') if node else (None, None)
        installed = {'node': nv, 'npm': pv}
        commands = {'node': [str(node)] if node else [], 'npm': npm or []}
    commands = commands or {}
    lines = [reason,
        f"Recover the selected pair together: node={required['node']} (.nvmrc), npm={required['npm']} (.npm-version).",
        'First select the required shared Node. Then inspect npm from that selection; bundled npm may differ from the independent npm pin.',
        'Apply npm preparation only after Node selection is correct. Preserve the existing manager, ownership and shared prefix.']
    mismatches = []
    for name in ('node', 'npm'):
        if installed.get(name) == required[name]:
            continue
        command = commands.get(name) or []
        executable_path = command[0] if isinstance(command, list) and command else command if isinstance(command, str) else None
        mismatches.append(device.render(device.diagnostic(name, required[name],
            str(repository / ('.nvmrc' if name == 'node' else '.npm-version')),
            installed.get(name), executable_path, repository)))
    lines.extend(mismatches or ['The observed active pair matches both pins; the recorded paths still require fresh evidence.'])
    lines.extend(['In a fresh user shell verify node --version, npm --version and npm lifecycle child Node selection together.',
        'Only after both pins and persistent paths are valid, run eng/toolchain.py with the verified shared Python; then renew/restage affected evidence through its normal owner. No installation or evidence renewal was performed by this diagnosis.'])
    return '\n\n'.join(lines)


def context(repository: Path, evidence_path: Path) -> tuple[list[str], dict[str, str]]:
    device.require_python(repository)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    required = evidence.get("required", {})
    for name, filename in (('node', '.nvmrc'), ('npm', '.npm-version')):
        pin = repository / filename
        if pin.is_file() and pin.read_text(encoding='utf-8').strip().removeprefix('v') != required.get(name):
            raise ValueError('PKT016 toolchain evidence differs from authoritative pin: ' + str(pin))
    resolved = evidence.get("resolved", {})
    commands = evidence.get("commands", {})
    npm = commands.get("npm") if isinstance(commands, dict) else None
    if (
        evidence.get("satisfied") is not True
        or not isinstance(npm, list)
        or not npm
        or resolved.get("node") != required.get("node")
        or resolved.get("npm") != required.get("npm")
    ):
        raise ValueError(
            "PKT016 exact Node/npm command evidence is missing or stale; run eng/toolchain.py first."
        )
    if any(not isinstance(item, str) or not item for item in npm):
        raise ValueError("PKT016 recorded npm command is invalid.")
    for index in range(min(2, len(npm))):
        if index == 1 and Path(npm[index]).suffix.casefold() != ".js":
            continue
        if not Path(npm[index]).is_file():
            raise ValueError(node_npm_recovery(repository, f"PKT016 recorded npm command path is missing: {npm[index]}"))
    node_command = commands.get("node") if isinstance(commands, dict) else None
    if not isinstance(node_command, list) or len(node_command) != 1 or not Path(node_command[0]).is_file():
        raise ValueError(node_npm_recovery(repository, "PKT016 recorded Node command is invalid or missing."))
    active_node, actual_node = resolve_node(repository, required.get('node'), 'node', 'auto')
    # npm lifecycle commands resolve node through a child shell even when the
    # recorded executable itself can run with an oversized Windows PATH.
    child_environment = os.environ.copy()
    if os.name == 'nt' and active_node:
        from windows_workflow_path import prepare_path, WindowsPathError
        try:
            child_environment['PATH'] = prepare_path(child_environment.get('PATH', ''), str(active_node))
        except WindowsPathError as error:
            raise ValueError('PKT018 npm child PATH cannot fit safely; reduce redundant device PATH entries in your terminal. ' + str(error)) from error
    active_npm, actual_npm = resolve_npm(repository, active_node, required.get('npm'), '', child_environment) if active_node else (None, None)
    if active_node is None or [str(active_node)] != node_command or active_npm != npm:
        raise ValueError(node_npm_recovery(repository, 'PKT017 device selection changed or PATH is stale; re-run eng/toolchain.py. ' + device.REFRESH,
            required=required, installed={'node': actual_node, 'npm': actual_npm},
            commands={'node': [str(active_node)] if active_node else [], 'npm': active_npm or []}))
    if actual_node != required.get('node') or actual_npm != required.get('npm'):
        raise ValueError(node_npm_recovery(repository, 'PKT017 exact active device Node/npm versions no longer match evidence. ' + device.REFRESH,
            required=required, installed={'node': actual_node, 'npm': actual_npm},
            commands={'node': node_command, 'npm': npm}))
    recorded_environment = evidence.get("environment", {})
    cache_value = recorded_environment.get("npmCache") if isinstance(recorded_environment, dict) else None
    if not isinstance(cache_value, str) or not cache_value:
        raise ValueError("PKT016 recorded npm cache is missing.")
    cache = Path(cache_value)
    require_writable_cache(cache)
    environment, _, _ = trust_environment(
        repository,
        cache,
        str(recorded_environment.get("trustMode", "")),
        str(recorded_environment.get("extraCaCertificates", "")),
    )
    if os.name == 'nt':
        environment['PATH'] = child_environment['PATH']
    return list(npm), environment


def run_npm(
    repository: Path,
    evidence_path: Path,
    arguments: list[str],
    cwd: Path,
    timeout: int,
    capture_stdout: bool = False,
) -> subprocess.CompletedProcess[str]:
    npm, environment = context(repository, evidence_path)
    command = npm + ["--strict-ssl=true"] + arguments
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE if capture_stdout else None,
        stderr=None,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run npm through Program Kit's exact resolved Node runtime.")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--evidence", default="artifacts/program-kit/toolchain.json")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("command", choices=("npm",))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        repository = Path(args.repository).resolve()
        evidence = Path(args.evidence)
        if not evidence.is_absolute():
            evidence = repository / evidence
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        result = run_npm(repository, evidence, arguments, Path.cwd(), args.timeout_seconds)
        return result.returncode
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

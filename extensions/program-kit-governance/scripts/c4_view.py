from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import quote, urlsplit


# Dynamic architecture-map loading must not create __pycache__ in the consumer repository.
sys.dont_write_bytecode = True


ARCHITECTURE_MAP = Path("docs/architecture/architecture-map.json")
WORKSPACE_DSL = Path("docs/architecture/workspace.dsl")
BOOTSTRAP_INTAKE = Path("docs/architecture/bootstrap-intake.json")
PROJECT_INTENT = Path("docs/architecture/project-intent.md")
PROFILE = Path(__file__).resolve().parents[1] / "references/c4-viewer-tool.json"
STATE_ENVIRONMENT = "PROGRAM_KIT_C4_STATE_ROOT"
WAR_ENVIRONMENT = "PROGRAM_KIT_STRUCTURIZR_WAR"
DIRECTIVE = re.compile(r'^\s*!(docs|adrs)\s+("(?:[^"\\]|\\.)+")\s*$', re.MULTILINE)
OPERATION_DEADLINE: ContextVar[float | None] = ContextVar("c4_operation_deadline", default=None)
START_TIMEOUT = 120
INSPECT_TIMEOUT = 30
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class C4ViewError(RuntimeError):
    pass


@contextmanager
def operation_budget(seconds: float):
    deadline = time.monotonic() + seconds
    outer = OPERATION_DEADLINE.get()
    token = OPERATION_DEADLINE.set(min(deadline, outer) if outer is not None else deadline)
    try:
        yield
    finally:
        OPERATION_DEADLINE.reset(token)


def remaining_timeout(maximum: float) -> float:
    deadline = OPERATION_DEADLINE.get()
    remaining = maximum if deadline is None else min(maximum, deadline - time.monotonic())
    if remaining <= 0:
        raise C4ViewError("C4 viewing time limit reached; stop and report this blocker without retrying")
    return remaining


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise C4ViewError(f"Missing {label}: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise C4ViewError(f"Cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise C4ViewError(f"{label} must be a JSON object: {path}")
    return value


def load_profile() -> dict:
    profile = load_json(PROFILE, "managed C4 viewer profile")
    selected = profile.get("selected")
    required = {
        "product",
        "command",
        "version",
        "docker_image",
        "docker_digest",
        "java_war",
        "java_war_url",
        "java_minimum",
        "default_port",
    }
    if (
        profile.get("schema_version") != "1.0"
        or not isinstance(selected, dict)
        or set(selected) != required
        or selected.get("command") != "local"
        or selected.get("docker_image") != f"structurizr/structurizr:{selected.get('version')}"
    ):
        raise C4ViewError(f"Managed C4 viewer profile has an invalid pin contract: {PROFILE}")
    return profile


def architecture_module():
    path = Path(__file__).with_name("architecture_map.py")
    spec = importlib.util.spec_from_file_location("program_kit_c4_architecture_map", path)
    if spec is None or spec.loader is None:
        raise C4ViewError(f"Cannot load architecture-map support: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bootstrap_intake_module():
    path = Path(__file__).with_name("bootstrap_intake.py")
    spec = importlib.util.spec_from_file_location("program_kit_c4_bootstrap_intake", path)
    if spec is None or spec.loader is None:
        raise C4ViewError(f"Cannot load bootstrap-intake support: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_project_root(value: str | Path) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise C4ViewError(f"Project root is not a directory: {root}")
    return root


def _artifact_record(intake: dict, key: str, expected: Path) -> dict:
    artifacts = intake.get("artifacts")
    record = artifacts.get(key) if isinstance(artifacts, dict) else None
    if (
        not isinstance(record, dict)
        or set(record) != {"path", "sha256", "bytes"}
        or record.get("path") != expected.as_posix()
        or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("sha256", "")))
        or not isinstance(record.get("bytes"), int)
    ):
        raise C4ViewError(
            f"Bootstrap intake has no valid registered {key} hash for {expected.as_posix()}"
        )
    return record


def validate_projection(project_root: Path) -> dict:
    map_path = project_root / ARCHITECTURE_MAP
    dsl_path = project_root / WORKSPACE_DSL
    intake_path = project_root / BOOTSTRAP_INTAKE
    if not map_path.is_file():
        raise C4ViewError(f"Canonical architecture map is missing: {ARCHITECTURE_MAP.as_posix()}")
    if not dsl_path.is_file():
        raise C4ViewError(
            f"C4 projection is missing: {WORKSPACE_DSL.as_posix()}. Regenerate it from the canonical map."
        )

    architecture = architecture_module()
    try:
        model = architecture.load_object(map_path)
        architecture.validate_model(model, project_root)
    except (architecture.ArchitectureMapError, OSError, UnicodeError) as exc:
        raise C4ViewError(f"Canonical architecture map is invalid or has stale source hashes: {exc}") from exc
    try:
        actual_text = dsl_path.read_text(encoding="utf-8")
        architecture.StructurizrDslImporter().import_path(dsl_path, model)
    except (architecture.ArchitectureMapError, OSError, UnicodeError) as exc:
        raise C4ViewError(f"Structurizr DSL projection is malformed: {exc}") from exc
    expected_text = architecture.StructurizrDslExporter().export(model)
    normalize = lambda value: value.replace("\r\n", "\n").replace("\r", "\n")
    if normalize(actual_text) != normalize(expected_text):
        raise C4ViewError(
            "C4 projection is stale relative to docs/architecture/architecture-map.json; "
            "regenerate workspace.dsl from the canonical map before review"
        )

    intake = load_json(intake_path, "bootstrap intake")
    if intake.get("schema_version") != "1.1":
        raise C4ViewError("Bootstrap intake must use the current schema_version 1.1")
    intake_status = intake.get("status")
    if intake_status not in {"draft", "confirmed"}:
        raise C4ViewError(
            f"Bootstrap intake status must be draft or confirmed: {BOOTSTRAP_INTAKE.as_posix()}"
        )
    map_record = _artifact_record(intake, "architecture_map", ARCHITECTURE_MAP)
    dsl_record = _artifact_record(intake, "c4_projection", WORKSPACE_DSL)
    map_hash = sha256_file(map_path)
    dsl_hash = sha256_file(dsl_path)
    map_match = map_record["sha256"] == map_hash and map_record["bytes"] == map_path.stat().st_size
    dsl_match = dsl_record["sha256"] == dsl_hash and dsl_record["bytes"] == dsl_path.stat().st_size
    if intake_status == "draft":
        intent_path = project_root / PROJECT_INTENT
        intent_record = _artifact_record(intake, "project_intent", PROJECT_INTENT)
        if not intent_path.is_file():
            raise C4ViewError(f"Draft intake artifact is missing: {PROJECT_INTENT.as_posix()}")
        intent_match = (
            intent_record["sha256"] == sha256_file(intent_path)
            and intent_record["bytes"] == intent_path.stat().st_size
        )
        mismatched = [
            path.as_posix()
            for path, matches in (
                (PROJECT_INTENT, intent_match),
                (ARCHITECTURE_MAP, map_match),
                (WORKSPACE_DSL, dsl_match),
            )
            if not matches
        ]
        if mismatched:
            raise C4ViewError(
                "Draft bootstrap intake hashes do not match current artifacts: "
                + ", ".join(mismatched)
            )
        binding = "draft-intake"
        review_mode = "draft-intake-review"
    else:
        if map_match != dsl_match:
            changed = WORKSPACE_DSL if map_match else ARCHITECTURE_MAP
            raise C4ViewError(
                f"Registered intake hashes show partial architecture drift at {changed.as_posix()}; "
                "refresh the generated pair and its governance evidence before review"
            )
        binding = "confirmed-intake" if map_match else "evolved-together-from-confirmed-intake"
        review_mode = "confirmed-baseline-review"
    intake_support = bootstrap_intake_module()
    try:
        intake_support.validate_intake(
            project_root,
            BOOTSTRAP_INTAKE,
            allow_architecture_evolution=intake_status == "confirmed",
            allowed_statuses={intake_status},
        )
    except (intake_support.IntakeError, OSError, UnicodeError) as exc:
        raise C4ViewError(f"Bootstrap intake is invalid for visual review: {exc}") from exc
    view_keys = [view["key"] for view in model["views"]]
    return {
        "project_root": str(project_root),
        "canonical_map": ARCHITECTURE_MAP.as_posix(),
        "projection": WORKSPACE_DSL.as_posix(),
        "map_sha256": map_hash,
        "projection_sha256": dsl_hash,
        "projection_current": True,
        "projection_parsed": True,
        "intake_status": intake_status,
        "intake_binding": binding,
        "review_mode": review_mode,
        "confirmation_performed": False,
        "architecture_acceptance_performed": False,
        "registered_map_sha256": map_record["sha256"],
        "registered_projection_sha256": dsl_record["sha256"],
        "view_keys": view_keys,
        "primary_view_key": view_keys[0],
    }


def diagram_url(port: int, view_key: str) -> str:
    return f"http://localhost:{port}/workspace/1/diagrams#{quote(view_key, safe='')}"


def run_capture(arguments: Sequence[str], timeout: float = 10) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(arguments),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=remaining_timeout(timeout),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(list(arguments), 127, "", str(exc))


def java_major(output: str) -> int | None:
    match = re.search(r'(?:version\s+"|openjdk\s+)(?:1\.)?(\d+)(?:[._"]|\s)', output, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def default_war_path(profile: dict) -> Path:
    selected = profile["selected"]
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        cache = Path(os.environ["LOCALAPPDATA"]) / "ProgramKit" / "tools"
    else:
        cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "program-kit" / "tools"
    return cache / "structurizr" / selected["version"] / selected["java_war"]


def discover_runtimes(profile: dict, war: str | None = None) -> dict:
    selected = profile["selected"]
    docker_path = shutil.which("docker")
    docker = {
        "installed": docker_path is not None,
        "path": docker_path,
        "daemon_available": False,
        "image": selected["docker_image"],
        "image_local": False,
        "diagnostic": "Docker is not installed",
    }
    if docker_path:
        version = run_capture((docker_path, "version", "--format", "{{.Server.Version}}"))
        docker["daemon_available"] = version.returncode == 0 and bool(version.stdout.strip())
        docker["diagnostic"] = (
            f"Docker server {version.stdout.strip()}" if docker["daemon_available"] else
            (version.stderr.strip() or "Docker is installed but its daemon is unavailable")
        )
        if docker["daemon_available"]:
            image = run_capture((docker_path, "image", "inspect", selected["docker_image"], "--format", "{{json .RepoDigests}}"))
            docker["image_local"] = (
                image.returncode == 0 and selected["docker_digest"] in image.stdout
            )
            if not docker["image_local"]:
                if image.returncode == 0:
                    docker["diagnostic"] = (
                        f"Local {selected['docker_image']} does not match tested digest "
                        f"{selected['docker_digest']}; explicit authorization is required before refreshing it"
                    )
                else:
                    docker["diagnostic"] = (
                        f"Pinned image is not local; explicit authorization is required before: "
                        f"docker pull {selected['docker_image']}"
                    )

    java_path = shutil.which("java")
    java = {
        "installed": java_path is not None,
        "path": java_path,
        "major": None,
        "supported": False,
        "war": None,
        "war_local": False,
        "diagnostic": "Java is not installed",
    }
    candidates: list[Path] = []
    if war:
        candidates.append(Path(war).expanduser())
    if os.environ.get(WAR_ENVIRONMENT):
        candidates.append(Path(os.environ[WAR_ENVIRONMENT]).expanduser())
    candidates.append(default_war_path(profile))
    existing = next((path.resolve() for path in candidates if path.is_file()), None)
    if java_path:
        result = run_capture((java_path, "-version"))
        major = java_major(result.stdout + "\n" + result.stderr)
        java["major"] = major
        java["supported"] = major is not None and major >= selected["java_minimum"]
        java["war"] = str(existing) if existing else str(candidates[0])
        java["war_local"] = existing is not None
        if not java["supported"]:
            java["diagnostic"] = (
                f"Java {major or 'unknown'} is available; Structurizr {selected['version']} requires "
                f"Java {selected['java_minimum']} or newer"
            )
        elif not existing:
            java["diagnostic"] = (
                f"Pinned WAR is not local; explicit authorization is required before downloading "
                f"{selected['java_war_url']} to {default_war_path(profile)}"
            )
        else:
            java["diagnostic"] = f"Supported Java {major} and pinned WAR are available"
    return {"docker": docker, "java": java}


def port_available(port: int, host: str = "127.0.0.1") -> bool:
    if not 1 <= port <= 65535:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def select_port(preferred: int, attempts: int = 100) -> int:
    for port in range(preferred, min(65536, preferred + attempts)):
        if port_available(port):
            return port
    raise C4ViewError(f"No free localhost port found from {preferred} through {preferred + attempts - 1}")


def session_identifier(project_root: Path) -> str:
    identity = str(project_root.resolve())
    if os.name == "nt":
        identity = identity.casefold()
    return sha256_bytes(identity.encode("utf-8"))[:12]


def state_root() -> Path:
    configured = os.environ.get(STATE_ENVIRONMENT)
    return Path(configured).resolve() if configured else Path(tempfile.gettempdir()).resolve() / "program-kit-c4-view"


def session_directory(project_root: Path) -> Path:
    return state_root() / session_identifier(project_root)


def _safe_session_path(path: Path) -> Path:
    base = state_root().resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(base)
    except ValueError as exc:
        raise C4ViewError(f"Viewer state path escaped its temporary root: {resolved}") from exc
    if len(relative.parts) < 1:
        raise C4ViewError(f"Refusing to operate on the viewer state root: {resolved}")
    return resolved


def render_command(arguments: Sequence[str], platform: str | None = None) -> str:
    platform = os.name if platform is None else platform
    return subprocess.list2cmdline(list(arguments)) if platform == "nt" else shlex.join(arguments)


def build_docker_command(
    docker: str, image: str, data_directory: Path, name: str, port: int
) -> list[str]:
    return [
        docker,
        "run",
        "--detach",
        "--pull=never",
        "--name",
        name,
        "--label",
        "program-kit.c4-viewer=true",
        "--publish",
        f"127.0.0.1:{port}:{port}",
        "--env",
        f"PORT={port}",
        "--volume",
        f"{os.fspath(data_directory)}:/usr/local/structurizr",
        image,
        "local",
    ]


def build_java_command(java: str, war: Path, data_directory: Path, port: int) -> list[str]:
    return [
        java,
        "-Dserver.address=127.0.0.1",
        f"-Dserver.port={port}",
        "-jar",
        os.fspath(war),
        "local",
        os.fspath(data_directory),
    ]


def _directive_paths(project_root: Path, text: str) -> list[tuple[Path, Path]]:
    paths: list[tuple[Path, Path]] = []
    for match in DIRECTIVE.finditer(text):
        try:
            raw = json.loads(match.group(2))
        except json.JSONDecodeError as exc:
            raise C4ViewError(f"Invalid {match.group(1)} path in workspace.dsl: {match.group(2)}") from exc
        relative = Path(raw)
        if relative.is_absolute():
            raise C4ViewError(f"Structurizr {match.group(1)} path must be repository-relative: {raw}")
        source = (project_root / relative).resolve()
        try:
            source.relative_to(project_root)
        except ValueError as exc:
            raise C4ViewError(f"Structurizr {match.group(1)} path escapes the repository: {raw}") from exc
        if not source.exists():
            raise C4ViewError(f"Structurizr {match.group(1)} input is missing: {raw}")
        paths.append((source, relative))
    return paths


def stage_projection(project_root: Path, target: Path) -> None:
    remaining_timeout(START_TIMEOUT)
    target = _safe_session_path(target)
    target.mkdir(parents=True, exist_ok=False)
    dsl = project_root / WORKSPACE_DSL
    shutil.copy2(dsl, target / "workspace.dsl")
    text = dsl.read_text(encoding="utf-8")
    for source, relative in _directive_paths(project_root, text):
        remaining_timeout(START_TIMEOUT)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)
    remaining_timeout(START_TIMEOUT)


def _state_file(project_root: Path) -> Path:
    return session_directory(project_root) / "state.json"


def load_state(project_root: Path) -> dict | None:
    path = _state_file(project_root)
    if not path.is_file():
        return None
    return load_json(path, "C4 viewer state")


def process_alive(pid: int) -> bool:
    if not isinstance(pid, int) or pid < 1:
        return False
    if os.name == "nt":
        # os.kill(pid, 0) is a conventional POSIX liveness probe, but signal 0
        # overlaps CTRL_C_EVENT on Windows. Using it can interrupt the console
        # process group that owns the caller (including PowerShell or Codex).
        # Query the process handle instead; this has no signalling side effect.
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        error_access_denied = 5
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL

        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            # Access denied still proves that the PID names an existing process.
            return ctypes.get_last_error() == error_access_denied
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def session_active(state: dict, runtimes: dict | None = None) -> bool:
    runtime = state.get("runtime")
    if runtime == "java":
        return process_alive(state.get("pid"))
    if runtime == "docker":
        docker = (runtimes or {}).get("docker", {})
        executable = docker.get("path") or shutil.which("docker")
        if not executable or not docker.get("daemon_available", True):
            return False
        result = run_capture((executable, "container", "inspect", state.get("container", ""), "--format", "{{.State.Running}}"))
        return result.returncode == 0 and result.stdout.strip().lower() == "true"
    return False


def write_state(project_root: Path, state: dict) -> None:
    path = _safe_session_path(_state_file(project_root))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def cleanup_directory(project_root: Path) -> None:
    directory = _safe_session_path(session_directory(project_root))
    if directory.exists():
        shutil.rmtree(directory)


def _stop_windows_process(pid: int) -> None:
    """Wait for the recorded process handle, including final log-handle teardown."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    # SYNCHRONIZE, PROCESS_QUERY_LIMITED_INFORMATION, PROCESS_TERMINATE.
    handle = kernel32.OpenProcess(0x00101001, False, pid)
    if not handle:
        if ctypes.get_last_error() == 87:  # ERROR_INVALID_PARAMETER: PID already gone.
            return
        raise C4ViewError("Cannot open the recorded Java C4 viewer; temporary state was preserved")
    try:
        result = kernel32.WaitForSingleObject(handle, 0)
        if result == 0:  # WAIT_OBJECT_0: already fully terminated.
            return
        if result != 258:  # WAIT_TIMEOUT: still running.
            raise C4ViewError("Cannot wait for the recorded Java C4 viewer; temporary state was preserved")
        if not kernel32.TerminateProcess(handle, int(signal.SIGTERM)):
            # The process may have exited between the initial wait and termination.
            if kernel32.WaitForSingleObject(handle, 0) == 0:
                return
            raise C4ViewError("Could not stop the recorded Java C4 viewer; temporary state was preserved")
        result = kernel32.WaitForSingleObject(handle, max(1, int(remaining_timeout(5) * 1000)))
        if result == 258:
            raise C4ViewError("Java C4 viewer did not stop; temporary state was preserved")
        if result != 0:
            raise C4ViewError("Cannot wait for the recorded Java C4 viewer; temporary state was preserved")
    finally:
        kernel32.CloseHandle(handle)


def stop_java_process(pid: int) -> None:
    if type(pid) is not int or pid < 1:
        raise C4ViewError("Recorded Java C4 viewer has no valid PID; temporary state was preserved")
    if os.name == "nt":
        # GetExitCodeProcess is a liveness query, not a completion wait. Windows
        # TerminateProcess is asynchronous; only the signaled handle admits cleanup.
        _stop_windows_process(pid)
    elif process_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as exc:
            raise C4ViewError(
                "Could not stop the recorded Java C4 viewer; temporary state was preserved"
            ) from exc


def stop_session(project_root: Path, runtimes: dict | None = None, *, cleanup: bool = True) -> bool:
    state = load_state(project_root)
    if state is None:
        if cleanup:
            cleanup_directory(project_root)
        return False
    if state.get("runtime") == "docker":
        docker = (runtimes or {}).get("docker", {})
        executable = docker.get("path") or shutil.which("docker")
        if not executable or not docker.get("daemon_available", True):
            raise C4ViewError(
                "Cannot reach Docker to stop the recorded C4 viewer; temporary state was preserved"
            )
        result = run_capture(
            (executable, "container", "rm", "--force", state.get("container", "")), timeout=20
        )
        if result.returncode != 0 and "No such container" not in result.stderr:
            raise C4ViewError(
                "Docker did not remove the recorded C4 viewer; temporary state was preserved: "
                + (result.stderr.strip() or result.stdout.strip())
            )
    elif state.get("runtime") == "java":
        stop_java_process(state.get("pid"))
    if cleanup:
        cleanup_directory(project_root)
    return True


def read_response(response, deadline: float) -> bytes:
    chunks = []
    size = 0
    while True:
        remaining_timeout(deadline - time.monotonic())
        # read1 avoids waiting to fill a large buffer while a server trickles bytes.
        chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - size))
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise C4ViewError("Structurizr response exceeds the bounded viewer response size")


def wait_ready(
    url: str, active: Callable[[], bool], timeout: float = 45, *, view_key: str | None = None
) -> None:
    """Check the actual diagrams page and parsed workspace, never only the home page."""
    with operation_budget(timeout):
        _wait_ready(url, active, timeout, view_key=view_key)


def _wait_ready(
    url: str, active: Callable[[], bool], timeout: float, *, view_key: str | None
) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + remaining_timeout(timeout)
    last_error = "no response"
    while time.monotonic() < deadline:
        remaining_timeout(timeout)
        if not active():
            raise C4ViewError("Structurizr stopped before the localhost viewer became ready")
        try:
            with opener.open(url, timeout=remaining_timeout(min(1, deadline - time.monotonic()))) as response:
                if response.status != 200:
                    raise C4ViewError(f"Diagram page returned HTTP {response.status}: {url}")
                if view_key is not None:
                    page = read_response(response, deadline)
                    if not re.search(rb'id=[\"\']diagram[\"\']', page):
                        raise C4ViewError(f"Structurizr returned no diagram canvas at {url}")
            if view_key is not None:
                address = urlsplit(url)
                workspace_url = f"{address.scheme}://{address.netloc}/api/workspace/1"
                with opener.open(workspace_url, timeout=remaining_timeout(min(1, deadline - time.monotonic()))) as response:
                    raw = read_response(response, deadline)
                    if response.status != 200:
                        raise C4ViewError("Structurizr workspace response is unavailable or too large")
                try:
                    workspace = json.loads(raw)
                except (ValueError, UnicodeError) as exc:
                    raise C4ViewError("Structurizr returned invalid workspace JSON") from exc
                views = workspace.get("views") if isinstance(workspace, dict) else None
                candidates = [view for group in (views or {}).values() if isinstance(group, list)
                              for view in group if isinstance(view, dict)] if isinstance(views, dict) else []
                if not any(view.get("key") == view_key for view in candidates):
                    raise C4ViewError(f"Structurizr did not load the requested diagram: {view_key}")
            return
        except urllib.error.HTTPError as exc:
            raise C4ViewError(f"Structurizr diagram/workspace request failed: HTTP {exc.code} at {exc.url}") from exc
        except C4ViewError:
            raise
        except Exception as exc:  # localhost readiness has platform-specific failure types
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, PermissionError) or getattr(reason, "winerror", None) in {5, 10013}:
                raise C4ViewError(
                    "Localhost access is denied by this execution environment; use an authorized "
                    "local terminal or supported permission mechanism, then stop if access remains blocked"
                ) from exc
            last_error = str(exc)
        time.sleep(min(0.25, max(0, deadline - time.monotonic())))
    raise C4ViewError(f"Structurizr did not become ready at {url}: {last_error}")


def open_browser_url(url: str) -> bool:
    # A browser handler can hang. Isolate it in a bounded non-agent child process.
    try:
        result = subprocess.run(
            # Avoid a Windows venv forwarding launcher whose child would outlive its PID.
            (getattr(sys, "_base_executable", sys.executable), "-c", "import sys, webbrowser; "
             "sys.exit(0 if webbrowser.open(sys.argv[1]) else 1)", url),
            # A launched GUI may inherit pipes and keep communicate() blocked after exit.
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=remaining_timeout(5), check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def preserve_failure(project_root: Path, error: BaseException, state: dict | None) -> Path:
    directory = _safe_session_path(session_directory(project_root))
    evidence = _safe_session_path(state_root() / "failures" /
                                 f"{session_identifier(project_root)}-{time.time_ns()}")
    evidence.mkdir(parents=True)
    for log in directory.glob("*.log"):
        shutil.copy2(log, evidence / log.name)
    (evidence / "failure.json").write_text(json.dumps({
        "error": str(error), "runtime": (state or {}).get("runtime"),
        "url": (state or {}).get("url"), "visual_review_performed": False,
    }, indent=2) + "\n", encoding="utf-8")
    return evidence


def choose_runtime(runtimes: dict, requested: str) -> str:
    docker_ready = runtimes["docker"]["daemon_available"] and runtimes["docker"]["image_local"]
    java_ready = runtimes["java"]["supported"] and runtimes["java"]["war_local"]
    if requested in {"auto", "docker"} and docker_ready:
        return "docker"
    if requested in {"auto", "java"} and java_ready:
        return "java"
    diagnostics = [runtimes["docker"]["diagnostic"], runtimes["java"]["diagnostic"]]
    if requested != "auto":
        diagnostics.insert(0, f"Requested {requested} runtime is unavailable")
    raise C4ViewError("No supported local Structurizr runtime is ready. " + " | ".join(diagnostics))


def reuse_session(state: dict, validation: dict, open_browser: bool) -> dict:
    if state.get("projection_sha256") != validation["projection_sha256"]:
        raise C4ViewError(
            "A viewer for an older projection is already running; stop it before starting the current projection"
        )
    state["reused"] = True
    state["url"] = diagram_url(state["port"], validation["primary_view_key"])
    state["intake_status"] = validation["intake_status"]
    state["review_mode"] = validation["review_mode"]
    state["confirmation_performed"] = False
    state["architecture_acceptance_performed"] = False
    wait_ready(state["url"], lambda: session_active(state), timeout=5,
               view_key=validation["primary_view_key"])
    state["diagram_available"] = True
    state["visual_review_performed"] = False
    state["browser_opened"] = open_browser_url(state["url"]) if open_browser else False
    return state


def start_session(
    project_root: Path,
    requested_runtime: str,
    requested_port: int | None,
    war: str | None,
    open_browser: bool,
    detach: bool,
    *, timeout: float = START_TIMEOUT,
) -> dict:
    if not 0 < timeout <= START_TIMEOUT:
        raise C4ViewError(f"Startup timeout must be greater than zero and at most {START_TIMEOUT} seconds")
    with operation_budget(timeout):
        return _start_session(project_root, requested_runtime, requested_port, war, open_browser, detach)


def _start_session(
    project_root: Path, requested_runtime: str, requested_port: int | None,
    war: str | None, open_browser: bool, detach: bool,
) -> dict:
    profile = load_profile()
    validation = validate_projection(project_root)
    remaining_timeout(START_TIMEOUT)
    existing = load_state(project_root)
    if existing and existing.get("runtime") == "java" and session_active(existing):
        return reuse_session(existing, validation, open_browser)

    runtimes = discover_runtimes(profile, war)
    if (
        existing
        and existing.get("runtime") == "docker"
        and not runtimes["docker"]["daemon_available"]
    ):
        raise C4ViewError(
            "A Docker-backed C4 viewer is recorded, but Docker is inaccessible; "
            "the session state was preserved so it can be stopped safely"
        )
    if existing and session_active(existing, runtimes):
        return reuse_session(existing, validation, open_browser)
    if existing:
        cleanup_directory(project_root)

    runtime = choose_runtime(runtimes, requested_runtime)
    preferred = requested_port or profile["selected"]["default_port"]
    port = select_port(preferred)
    directory = _safe_session_path(session_directory(project_root))
    directory.mkdir(parents=True, exist_ok=False)
    data_directory = directory / "data"
    state = None
    process = None
    try:
        stage_projection(project_root, data_directory)
        identifier = session_identifier(project_root)
        url = diagram_url(port, validation["primary_view_key"])
        state = {
            "schema_version": "1.0",
            "project_root": str(project_root),
            "runtime": runtime,
            "port": port,
            "url": url,
            "health_url": url,
            "primary_view_key": validation["primary_view_key"],
            "projection_sha256": validation["projection_sha256"],
            "intake_status": validation["intake_status"],
            "review_mode": validation["review_mode"],
            "confirmation_performed": False,
            "architecture_acceptance_performed": False,
            "data_directory": str(data_directory),
            "reused": False,
        }
        if runtime == "docker":
            docker = runtimes["docker"]["path"]
            # A failed launch must never clean up an unrelated container with the same name.
            name = f"program-kit-c4-{identifier}-{time.time_ns()}"
            command = build_docker_command(
                docker, profile["selected"]["docker_image"], data_directory, name, port
            )
            state.update({"container": name, "command": command})
            write_state(project_root, state)
            result = run_capture(command, timeout=45)
            (directory / "structurizr.stdout.log").write_text(result.stdout, encoding="utf-8")
            (directory / "structurizr.stderr.log").write_text(result.stderr, encoding="utf-8")
            if result.returncode != 0:
                raise C4ViewError(f"Structurizr Docker startup failed: {result.stderr.strip() or result.stdout.strip()}")
            state.update({"container": name, "container_id": result.stdout.strip(), "command": command})
        else:
            java = runtimes["java"]["path"]
            war_path = Path(runtimes["java"]["war"])
            command = build_java_command(java, war_path, data_directory, port)
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            with (directory / "structurizr.stdout.log").open("w", encoding="utf-8") as stdout, \
                    (directory / "structurizr.stderr.log").open("w", encoding="utf-8") as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, creationflags=flags)
            state.update({"pid": process.pid, "command": command})
        write_state(project_root, state)
        wait_ready(url, lambda: session_active(state, runtimes), view_key=validation["primary_view_key"])
        state["diagram_available"] = True
        state["visual_review_performed"] = False
        state["browser_opened"] = open_browser_url(url) if open_browser else False
        write_state(project_root, state)
        if not detach:
            announce_session(state)
            # Foreground mode belongs to a human terminal; only startup is bounded.
            token = OPERATION_DEADLINE.set(None)
            try:
                while session_active(state, runtimes):
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                try:
                    stop_session(project_root, runtimes, cleanup=False)
                    if process is not None:
                        process.wait(timeout=remaining_timeout(5))
                    cleanup_directory(project_root)
                finally:
                    OPERATION_DEADLINE.reset(token)
            state["stopped"] = True
        return state
    except BaseException as startup_error:
        # Leave time for bounded diagnostics and cleanup after the startup budget expires.
        token = OPERATION_DEADLINE.set(None)
        cleanup_error = None
        evidence_error = None
        evidence = directory
        try:
            with operation_budget(30):
                try:
                    if state and state.get("runtime") == "docker":
                        logs = run_capture((runtimes["docker"]["path"], "logs", "--tail", "200",
                                            state["container"]), timeout=5)
                        (directory / "structurizr.docker.log").write_text(
                            logs.stdout + "\n" + logs.stderr, encoding="utf-8")
                except (C4ViewError, OSError) as exc:
                    evidence_error = exc
                try:
                    if process is not None:
                        # Persisting state can fail after launch. The Popen handle still
                        # owns this child and does not depend on a readable state file.
                        if process.poll() is None:
                            process.terminate()
                        process.wait(timeout=remaining_timeout(5))
                    stop_session(project_root, runtimes, cleanup=False)
                except (C4ViewError, OSError, subprocess.TimeoutExpired) as exc:
                    cleanup_error = exc
                try:
                    evidence = preserve_failure(project_root, startup_error, state)
                except (C4ViewError, OSError) as exc:
                    evidence_error = exc
                if cleanup_error is None and evidence_error is None:
                    try:
                        cleanup_directory(project_root)
                    except (C4ViewError, OSError) as exc:
                        cleanup_error = exc
        finally:
            OPERATION_DEADLINE.reset(token)
        if isinstance(startup_error, (KeyboardInterrupt, SystemExit)):
            raise
        message = f"{startup_error}; diagnostics preserved at {evidence}"
        if cleanup_error is not None:
            message += f"; cleanup failed and session state was preserved: {cleanup_error}"
        if evidence_error is not None:
            message += f"; diagnostic capture incomplete and original session files retained: {evidence_error}"
        raise C4ViewError(message) from startup_error


def inspection(project_root: Path, war: str | None = None, preferred_port: int | None = None) -> dict:
    with operation_budget(INSPECT_TIMEOUT):
        return _inspection(project_root, war, preferred_port)


def _inspection(project_root: Path, war: str | None, preferred_port: int | None) -> dict:
    profile = load_profile()
    result = validate_projection(project_root)
    remaining_timeout(INSPECT_TIMEOUT)
    runtimes = discover_runtimes(profile, war)
    existing = load_state(project_root)
    active = existing if existing and session_active(existing, runtimes) else None
    port = active["port"] if active else select_port(preferred_port or profile["selected"]["default_port"])
    remaining_timeout(INSPECT_TIMEOUT)
    result.update(
        {
            "profile": profile["profile_id"],
            "structurizr_version": profile["selected"]["version"],
            "port": port,
            "runtimes": runtimes,
            "viewer_ready": (
                runtimes["docker"]["daemon_available"] and runtimes["docker"]["image_local"]
            ) or (runtimes["java"]["supported"] and runtimes["java"]["war_local"]),
            "active_session": active,
            "repository_writes": False,
            "external_network_calls": False,
            "confirmation_performed": False,
            "architecture_acceptance_performed": False,
            "startup_timeout_seconds": START_TIMEOUT,
            "visual_review_performed": False,
        }
    )
    return result


def announce_session(payload: dict) -> None:
    print(f"Structurizr Local diagram is available at {payload['url']}", flush=True)
    if not payload.get("browser_opened"):
        print("Browser was not opened automatically. Open the URL above in your local browser.", flush=True)
    print(f"Read-only review mode: {payload['review_mode']}")
    print("Viewing did not confirm the intake or accept the architecture.")
    print("Diagram availability was checked; visual review still requires opening it in a browser.")
    print("The first diagram opens directly; use the left thumbnail rail to switch views.")
    print("A magnifier on an element opens a linked detail view; no magnifier means the "
          "architecture map defines no deeper C4 view. Use +/- to zoom the canvas.")
    print("Stop and remove temporary viewer state with:")
    command = render_command((sys.executable, str(Path(__file__).resolve()), "stop",
                              "--project-root", payload["project_root"]))
    print(("& " if os.name == "nt" else "") + command)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Validate and view Program Kit's generated C4 projection.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "start", "stop"):
        command = subparsers.add_parser(name)
        command.add_argument("--project-root", default=".")
    inspect_parser = subparsers.choices["inspect"]
    inspect_parser.add_argument("--war")
    inspect_parser.add_argument("--port", type=int)
    inspect_parser.add_argument("--json", action="store_true")
    start_parser = subparsers.choices["start"]
    start_parser.add_argument("--war")
    start_parser.add_argument("--port", type=int)
    start_parser.add_argument("--runtime", choices=("auto", "docker", "java"), default="auto")
    start_parser.add_argument("--open", action="store_true")
    start_parser.add_argument("--detach", action="store_true")
    start_parser.add_argument("--timeout", type=int, default=START_TIMEOUT,
                              help="Startup budget in seconds (1-120); excludes bounded failure cleanup")
    args = parser.parse_args()
    try:
        root = canonical_project_root(args.project_root)
        if args.command == "inspect":
            payload = inspection(root, args.war, args.port)
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(f"C4 projection is current and parseable: {payload['projection']}")
                print(f"Review mode: {payload['review_mode']}")
                print("Viewing does not confirm the intake or accept the architecture.")
                print(f"Managed Structurizr version: {payload['structurizr_version']}")
                print(f"Viewer ready: {str(payload['viewer_ready']).lower()}; selected port: {payload['port']}")
                if not payload["viewer_ready"]:
                    for runtime in payload["runtimes"].values():
                        print(runtime["diagnostic"])
        elif args.command == "start":
            print("Checking the C4 projection and local viewer prerequisites...", file=sys.stderr, flush=True)
            payload = start_session(root, args.runtime, args.port, args.war, args.open, args.detach,
                                    timeout=args.timeout)
            if payload.get("stopped"):
                print("Structurizr Local stopped and temporary viewer state removed.")
            else:
                announce_session(payload)
        else:
            stopped = stop_session(root, discover_runtimes(load_profile()))
            print("Structurizr Local stopped and temporary viewer state removed." if stopped else "No active C4 viewer session was recorded.")
    except (C4ViewError, OSError, UnicodeError, ValueError) as exc:
        print(f"Program Kit C4 viewer failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

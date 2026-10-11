from __future__ import annotations

import hashlib
import importlib.util
import json
import io
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import redirect_stdout
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model(intent: Path, documentation: Path) -> dict:
    common = {
        "ownership": "Project",
        "technology": "",
        "evidence": ["e-001"],
        "decision_refs": [],
        "tags": [],
        "properties": {},
        "perspectives": [],
        "url": "",
        "group": "",
        "archetype": "",
    }
    return {
        "schema_version": "1.0",
        "model_id": "review-system",
        "title": "Review system",
        "sources": [
            {
                "id": "project-intent",
                "path": "docs/architecture/project-intent.md",
                "sha256": digest(intent),
                "format": "program-kit-intent-markdown",
                "importer": {"id": "program-kit-intake", "version": "1.0"},
            }
        ],
        "decisions": [],
        "documentation": [
            {
                "id": "architecture-readme",
                "path": "docs/architecture/README.md",
                "sha256": digest(documentation),
                "scope": "Architecture review",
            }
        ],
        "constraints": [],
        "elements": [
            {
                "id": "reviewer",
                "type": "person",
                "name": "Reviewer",
                "description": "Reviews the architecture.",
                "status": "explicit",
                **{**common, "ownership": ""},
            },
            {
                "id": "review-system",
                "type": "software-system",
                "name": "Review system",
                "description": "Provides the review surface.",
                "status": "proposed",
                **common,
            },
            {
                "id": "review-context",
                "type": "bounded-context",
                "name": "Review context",
                "description": "Owns review behavior.",
                "status": "proposed",
                **common,
            },
        ],
        "relationships": [
            {
                "id": "reviews",
                "source": "reviewer",
                "target": "review-system",
                "description": "Reviews",
                "technology": "HTTPS",
                "status": "explicit",
                "evidence": ["e-001"],
                "decision_refs": [],
                "tags": [],
                "properties": {},
                "perspectives": [],
                "url": "",
            }
        ],
        "views": [
            {
                "key": "system-context",
                "type": "system-context",
                "title": "System Context",
                "description": "Review boundary",
                "scope": "review-system",
                "elements": ["reviewer", "review-system"],
                "relationships": ["reviews"],
                "decision_refs": [],
                "filters": [],
                "order": [],
                "layout": {"rankDirection": "lr"},
                "animations": [],
                "properties": {},
            },
            {
                "key": "domain-context",
                "type": "domain-context",
                "title": "Domain Context",
                "description": "Review domain",
                "scope": "",
                "elements": ["review-system", "review-context"],
                "relationships": [],
                "decision_refs": [],
                "filters": [],
                "order": [],
                "layout": {"rankDirection": "lr"},
                "animations": [],
                "properties": {},
            },
        ],
        "configuration": {
            "styles": [],
            "themes": [],
            "terminology": {},
            "branding": {},
            "properties": {},
        },
        "extensions": [],
    }


def create_project(
    root: Path,
    architecture,
    semantic,
    value: dict | None = None,
    status: str = "confirmed",
) -> dict:
    intent = root / "docs/architecture/project-intent.md"
    documentation = root / "docs/architecture/README.md"
    write(intent, "# Intent\n\nA reviewer inspects the system.\n")
    write(documentation, "# Architecture\n")
    value = value or semantic.semantic_model(intent)
    value["documentation"] = [
        {"id": "architecture-readme", "path": "docs/architecture/README.md",
         "sha256": digest(documentation), "scope": "Architecture review"}
    ]
    map_path = root / "docs/architecture/architecture-map.json"
    dsl_path = root / "docs/architecture/workspace.dsl"
    write(map_path, json.dumps(value, indent=2) + "\n")
    write(dsl_path, architecture.StructurizrDslExporter().export(value))
    intake = semantic.intake_for(root, value, status)
    write(root / "docs/architecture/bootstrap-intake.json", json.dumps(intake, indent=2) + "\n")
    return value


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in root.rglob("*")
        if path.is_file()
    }


def expect_failure(action, text: str) -> None:
    try:
        action()
    except Exception as exc:
        if text not in str(exc):
            raise AssertionError(f"Expected {text!r} in {exc!r}") from exc
        return
    raise AssertionError(f"Expected failure containing {text!r}")


def validate_readiness_and_budgets(viewer) -> None:
    """Exercise real HTTP responses; a home page or an error page is not a diagram."""
    behavior = {"page_status": 200, "canvas": True, "key": "system-context", "valid_json": True}
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            if self.path == "/":
                status, body = 200, b"Home page"
            elif self.path == "/workspace/1/diagrams":
                status = behavior["page_status"]
                body = b'<div id="diagram"></div>' if behavior["canvas"] else b"Workspace load failed"
            elif self.path == "/api/workspace/1":
                status = 200
                body = json.dumps({"views": {"systemContextViews": [
                    {"key": behavior["key"], "elements": [{"id": "1"}]}]}}).encode()
                if not behavior["valid_json"]:
                    body = b"Workspace parse error"
            else:
                status, body = 404, b"Not found"
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = viewer.diagram_url(server.server_port, "system-context")
    try:
        viewer.wait_ready(url, lambda: True, timeout=5, view_key="system-context")
        assert requests == ["/workspace/1/diagrams", "/api/workspace/1"], requests
        behavior["page_status"] = 500
        expect_failure(lambda: viewer.wait_ready(url, lambda: True, timeout=5,
                                                view_key="system-context"), "HTTP 500")
        behavior["page_status"] = 200
        behavior["canvas"] = False
        expect_failure(lambda: viewer.wait_ready(url, lambda: True, timeout=5,
                                                view_key="system-context"), "no diagram canvas")
        behavior["canvas"] = True
        behavior["key"] = "wrong-view"
        expect_failure(lambda: viewer.wait_ready(url, lambda: True, timeout=5,
                                                view_key="system-context"), "requested diagram")
        behavior["key"] = "system-context"
        behavior["valid_json"] = False
        expect_failure(lambda: viewer.wait_ready(url, lambda: True, timeout=5,
                                                view_key="system-context"), "invalid workspace JSON")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    with patch.object(viewer.urllib.request, "build_opener") as opener:
        opener.return_value.open.side_effect = urllib.error.URLError(PermissionError("sandbox denied"))
        expect_failure(lambda: viewer.wait_ready(url, lambda: True, timeout=5,
                                                view_key="system-context"), "Localhost access is denied")
        assert opener.return_value.open.call_count == 1
    with viewer.operation_budget(0):
        expect_failure(lambda: viewer.run_capture((sys.executable, "-V")), "time limit reached")
    begin = time.monotonic()
    timeout_processes = []
    real_popen = viewer.subprocess.Popen
    def capture_timeout_process(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        timeout_processes.append(process)
        return process
    with patch.object(viewer.subprocess, "Popen", side_effect=capture_timeout_process), \
            viewer.operation_budget(0.1):
        expired = viewer.run_capture((getattr(sys, "_base_executable", sys.executable),
                                      "-c", "import time; time.sleep(10)"))
    assert expired.returncode == 127 and time.monotonic() - begin < 3
    assert len(timeout_processes) == 1 and timeout_processes[0].returncode is not None
    with patch.object(viewer.subprocess, "run", side_effect=subprocess.TimeoutExpired("browser", 5)) as run:
        assert viewer.open_browser_url(url) is False
        assert run.call_args.kwargs["timeout"] == 5
        assert run.call_args.kwargs["stdout"] == subprocess.DEVNULL
        assert run.call_args.kwargs["stderr"] == subprocess.DEVNULL


def validate_windows_stop_contract(viewer) -> None:
    """The completion handle, not an exit-code probe, admits Windows cleanup."""
    import ctypes

    cases = (
        ("already-exited", 123, [0], True, 0, None),
        ("terminated", 123, [258, 0], True, 0, None),
        ("exit-raced-termination", 123, [258, 0], False, 5, None),
        ("timeout", 123, [258, 258], True, 0, "did not stop"),
        ("initial-wait-failed", 123, [0xFFFFFFFF], True, 0, "Cannot wait"),
        ("final-wait-failed", 123, [258, 0xFFFFFFFF], True, 0, "Cannot wait"),
        ("terminate-denied", 123, [258, 258], False, 5, "Could not stop"),
        ("open-denied", 0, [], True, 5, "Cannot open"),
        ("already-gone", 0, [], True, 87, None),
    )
    for name, handle, waits, terminate, error, failure in cases:
        api = Mock()
        api.OpenProcess.return_value = handle
        api.WaitForSingleObject.side_effect = waits
        api.TerminateProcess.return_value = terminate
        api.CloseHandle.return_value = True
        with patch.object(ctypes, "WinDLL", return_value=api, create=True), \
                patch.object(ctypes, "get_last_error", return_value=error, create=True), \
                patch.object(viewer.os, "kill", side_effect=AssertionError("No control signals")), \
                viewer.operation_budget(0.15):
            if failure:
                expect_failure(lambda: viewer._stop_windows_process(54321), failure)
            else:
                viewer._stop_windows_process(54321)
        api.OpenProcess.assert_called_once_with(0x00101001, False, 54321)
        assert api.CloseHandle.call_count == (1 if handle else 0), name
        if handle:
            api.CloseHandle.assert_called_once_with(handle)
        if name == "already-exited":
            api.TerminateProcess.assert_not_called()
        if name == "terminated":
            api.TerminateProcess.assert_called_once_with(handle, int(viewer.signal.SIGTERM))
            assert api.WaitForSingleObject.call_args_list[0].args == (handle, 0)
            assert 0 < api.WaitForSingleObject.call_args_list[1].args[1] <= 150
        if failure:
            with tempfile.TemporaryDirectory(prefix="Program Kit C4 incomplete stop ") as directory:
                project = Path(directory) / "consumer"
                project.mkdir()
                with patch.dict(os.environ, {viewer.STATE_ENVIRONMENT: str(Path(directory) / "state")}):
                    viewer.write_state(project, {"runtime": "java", "pid": 54321})
                    log = viewer.session_directory(project) / "structurizr.stderr.log"
                    write(log, "Retained diagnostic\n")
                    before = snapshot(viewer.session_directory(project))
                    with patch.object(viewer, "stop_java_process", side_effect=viewer.C4ViewError(failure)):
                        expect_failure(lambda: viewer.stop_session(project), failure)
                    assert snapshot(viewer.session_directory(project)) == before, name
    with patch.object(viewer, "_stop_windows_process") as stop, \
            patch.object(viewer.os, "kill", side_effect=AssertionError("Invalid PID must not signal")):
        for value in (None, True, False, 0, -1, "54321", 1.5):
            expect_failure(lambda: viewer.stop_java_process(value), "no valid PID")
        stop.assert_not_called()
    print("Windows Java stop: 9 handle outcomes, 7 invalid PID controls passed.")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    scripts = repository / "extensions/program-kit-governance/scripts"
    architecture = load_module(scripts / "architecture_map.py", "test_c4_architecture")
    viewer = load_module(scripts / "c4_view.py", "test_c4_viewer")
    semantic = load_module(repository / "tests/validate_bootstrap_semantics.py", "test_c4_semantic_fixture")

    viewer_skill = (
        repository
        / "extensions/program-kit-governance/commands/speckit.program-kit-governance.view-c4.md"
    ).read_text(encoding="utf-8")
    bootstrap_skill = (
        repository
        / "extensions/program-kit-governance/commands/speckit.program-kit-governance.bootstrap.md"
    ).read_text(encoding="utf-8")
    viewing_reference = (
        repository / "extensions/program-kit-governance/references/c4-viewing.md"
    ).read_text(encoding="utf-8")
    workflow = (repository / "workflows/program-kit-bootstrap/workflow.yml").read_text(
        encoding="utf-8"
    )
    intake_validator = (
        repository / "extensions/program-kit-governance/scripts/bootstrap_intake.py"
    ).read_text(encoding="utf-8")
    for text, marker in (
        (viewer_skill, "including informed review before bootstrap confirmation"),
        (viewer_skill, "never performs bootstrap approval"),
        (bootstrap_skill, "draft artifact hashes"),
        (viewing_reference, "Draft intake review is allowed before explicit confirmation"),
    ):
        if marker not in text:
            raise AssertionError(f"Bootstrap/viewer guidance lost the draft-review boundary: {marker}")
    if "validate-bootstrap-intake" not in workflow or 'intake.get("status") != "confirmed"' not in intake_validator:
        raise AssertionError("The outer bootstrap workflow no longer requires a confirmed intake")

    profile = viewer.load_profile()
    if profile["selected"]["version"] in {"", "latest"}:
        raise AssertionError("Structurizr viewer must use an exact managed version")
    if not profile["selected"]["docker_digest"].startswith("sha256:"):
        raise AssertionError("Structurizr viewer image has no tested registry digest")
    if not profile["selected"]["java_war_url"].endswith(f"/{profile['selected']['java_war']}"):
        raise AssertionError("Structurizr WAR retrieval does not bind the exact managed filename")
    if profile["selected"]["default_port"] != 8081:
        raise AssertionError("C4 viewer must avoid Program Kit's Keycloak port 8080")
    if viewer.java_major('openjdk version "21.0.8"') != 21:
        raise AssertionError("Java runtime parsing did not recognize Java 21")
    if viewer.java_major('java version "1.8.0_411"') != 8:
        raise AssertionError("Java runtime parsing did not recognize legacy Java 8")
    if not viewer.process_alive(os.getpid()):
        raise AssertionError("C4 viewer did not recognize its current process as active")
    validate_readiness_and_budgets(viewer)
    validate_windows_stop_contract(viewer)

    with tempfile.TemporaryDirectory(prefix="Program Kit C4 tests ") as directory:
        tests_root = Path(directory)
        os.environ[viewer.STATE_ENVIRONMENT] = str(tests_root / "viewer state")
        project = tests_root / "consumer repository with spaces"
        value = create_project(project, architecture, semantic, status="draft")

        valid = viewer.validate_projection(project)
        if (
            not valid["projection_current"]
            or valid["intake_binding"] != "draft-intake"
            or valid["review_mode"] != "draft-intake-review"
            or valid["intake_status"] != "draft"
        ):
            raise AssertionError(f"Current draft projection was not accepted for review: {valid}")
        if valid["confirmation_performed"] or valid["architecture_acceptance_performed"]:
            raise AssertionError("Draft viewing claimed confirmation or architecture acceptance")
        if valid["primary_view_key"] != "system-context":
            raise AssertionError(f"Viewer did not select the first generated diagram: {valid}")
        if viewer.diagram_url(8081, valid["primary_view_key"]) != (
            "http://localhost:8081/workspace/1/diagrams#system-context"
        ):
            raise AssertionError("Viewer did not build a direct, local diagram URL")

        before = snapshot(project)
        data = viewer.session_directory(project) / "data"
        data.parent.mkdir(parents=True)
        viewer.stage_projection(project, data)
        if not (data / "workspace.dsl").is_file() or not (data / "docs/architecture/README.md").is_file():
            raise AssertionError("Temporary viewer staging lost the DSL or its documentation input")
        if snapshot(project) != before:
            raise AssertionError("View-only staging changed the consumer repository")
        viewer.cleanup_directory(project)

        fake_runtimes = {
            "docker": {
                "installed": True,
                "path": "docker",
                "daemon_available": True,
                "image": profile["selected"]["docker_image"],
                "image_local": True,
                "diagnostic": "ready",
            },
            "java": {
                "installed": False,
                "path": None,
                "major": None,
                "supported": False,
                "war": None,
                "war_local": False,
                "diagnostic": "not used",
            },
        }
        opened: list[str] = []
        original_discovery = viewer.discover_runtimes
        original_capture = viewer.run_capture
        original_wait = viewer.wait_ready
        original_open = viewer.open_browser_url

        def fake_capture(arguments, timeout=10):
            command = list(arguments)
            if command[1:3] == ["container", "inspect"]:
                return subprocess.CompletedProcess(command, 0, "true\n", "")
            if command[1:4] == ["container", "rm", "--force"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            if command[1] == "logs":
                return subprocess.CompletedProcess(command, 0, "Specific DSL parser diagnosis\n", "")
            if command[1] == "run":
                return subprocess.CompletedProcess(command, 0, "draft-viewer-container\n", "")
            return subprocess.CompletedProcess(command, 1, "", "unexpected command")

        viewer.discover_runtimes = lambda profile, war=None: fake_runtimes
        viewer.run_capture = fake_capture
        viewer.wait_ready = lambda url, active, timeout=45, **kwargs: None
        viewer.open_browser_url = lambda url: opened.append(url) or True
        draft_before_start = snapshot(project)
        try:
            started = viewer.start_session(project, "auto", None, None, True, True)
            if started["review_mode"] != "draft-intake-review" or not opened:
                raise AssertionError("Current draft intake did not open in read-only review mode")
            assert started["diagram_available"] and started["browser_opened"]
            assert started["visual_review_performed"] is False
            assert started["health_url"] == started["url"]
            staged_workspace = Path(started["data_directory"]) / "workspace.json"
            write(staged_workspace, '{"layout":"viewer-only"}\n')
            if (project / "workspace.json").exists():
                raise AssertionError("Viewer workspace.json escaped into the consumer repository")
            viewer.stop_session(project, fake_runtimes)

            output = io.StringIO()
            with patch.object(viewer, "session_active", side_effect=KeyboardInterrupt), redirect_stdout(output):
                foreground = viewer.start_session(project, "auto", None, None, False, False)
            assert foreground["stopped"] and foreground["url"] in output.getvalue()
            assert str(project) in output.getvalue() and "--project-root" in output.getvalue()
            assert not viewer.session_directory(project).exists()
            viewer.open_browser_url = lambda url: False
            unavailable_browser = viewer.start_session(project, "auto", None, None, True, True)
            assert unavailable_browser["browser_opened"] is False
            assert viewer.load_state(project) is not None  # Manual URL remains usable.
            viewer.stop_session(project, fake_runtimes)

            def startup_failure(url, active, timeout=45, **kwargs):
                write(viewer.session_directory(project) / "structurizr.stderr.log", "Java fixture diagnosis\n")
                raise viewer.C4ViewError("Fixture startup failure")

            viewer.wait_ready = startup_failure
            expect_failure(lambda: viewer.start_session(project, "auto", None, None, False, True),
                           "diagnostics preserved at")
            failures = list((viewer.state_root() / "failures").glob("*/failure.json"))
            assert len(failures) == 1
            evidence = failures[0].parent
            assert "Specific DSL parser diagnosis" in (evidence / "structurizr.docker.log").read_text()
            assert "Java fixture diagnosis" in (evidence / "structurizr.stderr.log").read_text()
            assert not viewer.session_directory(project).exists()
            with patch.object(viewer, "stop_session", side_effect=viewer.C4ViewError("Cannot stop fixture")):
                expect_failure(lambda: viewer.start_session(project, "auto", None, None, False, True),
                               "cleanup failed and session state was preserved")
            assert viewer.load_state(project) is not None
            viewer.stop_session(project, fake_runtimes)

            java_runtimes = {
                "docker": {"daemon_available": False, "image_local": False},
                "java": {"path": sys.executable, "supported": True, "war_local": True,
                         "war": "fixture.war"},
            }
            viewer.discover_runtimes = lambda profile, war=None: java_runtimes

            # A failed Popen must close the parent's logs before preserving evidence.
            launch_streams = []
            def launch_failure(*args, **kwargs):
                launch_streams.extend((kwargs["stdout"], kwargs["stderr"]))
                kwargs["stderr"].write("Launch failure diagnostic\n")
                raise OSError("Java fixture could not launch")

            with patch.object(viewer.subprocess, "Popen", side_effect=launch_failure), \
                    patch.object(viewer, "stop_java_process") as stop:
                try:
                    viewer.start_session(project, "java", None, None, False, True)
                except viewer.C4ViewError as error:
                    launch_error = str(error)
                else:
                    raise AssertionError("Java fixture launch should fail")
                assert "diagnostics preserved at" in launch_error
                assert "cleanup failed" not in launch_error, launch_error
                assert "capture incomplete" not in launch_error, launch_error
                stop.assert_not_called()
            assert len(launch_streams) == 2 and all(stream.closed for stream in launch_streams)
            assert not viewer.session_directory(project).exists()
            launch_evidence = [path.parent for path in (viewer.state_root() / "failures").glob("*/failure.json")
                               if json.loads(path.read_text())["error"] == "Java fixture could not launch"]
            assert len(launch_evidence) == 1
            assert "Launch failure diagnostic" in (launch_evidence[0] / "structurizr.stderr.log").read_text()

            def java_startup_failure(url, active, timeout=45, **kwargs):
                deadline = time.monotonic() + 3
                log = viewer.session_directory(project) / "structurizr.stderr.log"
                while "Java stream diagnosis" not in log.read_text(encoding="utf-8"):
                    assert time.monotonic() < deadline, "Fixture child did not write its diagnostic"
                    time.sleep(0.02)
                raise viewer.C4ViewError("Java fixture failed to load workspace")

            viewer.wait_ready = java_startup_failure
            # Windows venv python.exe is a forwarding launcher; use the real interpreter
            # so this Java stand-in owns its own PID and log handles like java.exe.
            command = [getattr(sys, "_base_executable", sys.executable), "-c", "import sys,time; "
                       "print('Java stream diagnosis', file=sys.stderr, flush=True); time.sleep(30)"]
            owned_processes = []
            original_popen = viewer.subprocess.Popen
            original_preserve = viewer.preserve_failure
            def observe_popen(*args, **kwargs):
                process = original_popen(*args, **kwargs)
                owned_processes.append(process)
                return process
            def preserve_reaped(*args, **kwargs):
                assert owned_processes and all(process.returncode is not None for process in owned_processes)
                return original_preserve(*args, **kwargs)

            with patch.object(viewer, "build_java_command", return_value=command), \
                    patch.object(viewer.subprocess, "Popen", side_effect=observe_popen), \
                    patch.object(viewer, "preserve_failure", side_effect=preserve_reaped):
                try:
                    viewer.start_session(project, "java", None, None, False, True)
                except viewer.C4ViewError as error:
                    java_error = str(error)
                else:
                    raise AssertionError("Java fixture startup should fail")
                assert "diagnostics preserved at" in java_error, java_error
                assert "cleanup failed" not in java_error, java_error
                assert "capture incomplete" not in java_error, java_error
            java_evidence = [path.parent for path in (viewer.state_root() / "failures").glob("*/failure.json")
                             if json.loads(path.read_text())["runtime"] == "java"]
            assert len(java_evidence) == 2  # Launch failure and the actual child failure.
            java_evidence = [path for path in java_evidence
                             if json.loads((path / "failure.json").read_text())["error"] ==
                             "Java fixture failed to load workspace"]
            assert len(java_evidence) == 1
            assert "Java stream diagnosis" in (java_evidence[0] / "structurizr.stderr.log").read_text()
            assert not viewer.session_directory(project).exists(), java_error

            # A launched child remains owned even if persisting its PID fails.
            with patch.object(viewer, "build_java_command", return_value=command), \
                    patch.object(viewer.subprocess, "Popen", side_effect=observe_popen), \
                    patch.object(viewer, "write_state", side_effect=OSError("Fixture state persistence failed")), \
                    patch.object(viewer, "preserve_failure", side_effect=preserve_reaped):
                try:
                    viewer.start_session(project, "java", None, None, False, True)
                except viewer.C4ViewError as error:
                    state_error = str(error)
                else:
                    raise AssertionError("Java fixture state persistence should fail")
                assert "diagnostics preserved at" in state_error
                assert "cleanup failed" not in state_error, state_error
                assert "capture incomplete" not in state_error, state_error
            assert owned_processes[-1].returncode is not None
            assert not viewer.session_directory(project).exists()
            assert any(json.loads(path.read_text())["error"] == "Fixture state persistence failed"
                       for path in (viewer.state_root() / "failures").glob("*/failure.json"))

            if os.name == "nt":
                # Exercise the installed CPython cached-returncode wait semantics.
                # No real PID is used: the native helper's exact handle is controlled.
                import ctypes
                for outcome in ("signaled", "timeout"):
                    cached = object.__new__(subprocess.Popen)
                    cached._child_created = False
                    cached._handle = 123
                    cached.pid = 54321
                    cached.args = ["cached-returncode-fixture"]
                    cached.returncode = 15
                    api = Mock()
                    api.OpenProcess.return_value = 321
                    api.TerminateProcess.return_value = True
                    api.CloseHandle.return_value = True
                    waits = [258, 0 if outcome == "signaled" else 258]
                    events = []
                    def native_wait(handle, milliseconds):
                        events.append(("native-wait", handle, milliseconds))
                        return waits.pop(0)
                    api.WaitForSingleObject.side_effect = native_wait
                    original_cached_wait = cached.wait
                    def cached_wait(*args, **kwargs):
                        events.append(("popen-wait",))
                        return original_cached_wait(*args, **kwargs)
                    def cached_launch(*args, **kwargs):
                        kwargs["stderr"].write("Cached returncode diagnostic\n")
                        return cached
                    with patch.object(ctypes, "WinDLL", return_value=api), \
                            patch.object(viewer.subprocess, "Popen", side_effect=cached_launch), \
                            patch.object(cached, "wait", side_effect=cached_wait) as wait, \
                            patch.object(viewer.subprocess._winapi, "WaitForSingleObject") as cpython_wait, \
                            patch.object(viewer, "write_state", side_effect=OSError("Cached state persistence failed")):
                        try:
                            viewer.start_session(project, "java", None, None, False, True)
                        except viewer.C4ViewError as error:
                            cached_error = str(error)
                        else:
                            raise AssertionError("Cached-state fixture must fail startup")
                        assert "diagnostics preserved at" in cached_error
                        cpython_wait.assert_not_called()  # Actual wait() takes its cached branch.
                        if outcome == "signaled":
                            assert "cleanup failed" not in cached_error, cached_error
                            assert not viewer.session_directory(project).exists()
                            wait.assert_called_once()
                            assert [event[0] for event in events] == ["native-wait", "native-wait", "popen-wait"], (
                                "Cached returncode cleanup bypassed native handle completion", events)
                        else:
                            assert "cleanup failed" in cached_error and "did not stop" in cached_error
                            wait.assert_not_called()
                            log = viewer.session_directory(project) / "structurizr.stderr.log"
                            assert "Cached returncode diagnostic" in log.read_text()
                            assert [event[0] for event in events] == ["native-wait", "native-wait"]
                    assert not waits
                    api.CloseHandle.assert_called_once_with(321)
                    api.TerminateProcess.assert_called_once_with(321, int(viewer.signal.SIGTERM))
                    viewer.cleanup_directory(project)
                print("Windows cached-returncode: signaled native handle required; timeout diagnostics retained.")

            # Actual detached Java stand-ins must release inherited logs before cleanup.
            def java_ready(url, active, timeout=45, **kwargs):
                assert active()
                deadline = time.monotonic() + 3
                log = viewer.session_directory(project) / "structurizr.stderr.log"
                while "Java stream diagnosis" not in log.read_text(encoding="utf-8"):
                    assert time.monotonic() < deadline, "Fixture child did not start"
                    time.sleep(0.02)
            viewer.wait_ready = java_ready
            with patch.object(viewer, "build_java_command", return_value=command), \
                    patch.object(viewer.subprocess, "Popen", side_effect=observe_popen):
                for _ in range(3):
                    started = viewer.start_session(project, "java", None, None, False, True)
                    process = owned_processes[-1]
                    assert started["pid"] == process.pid and viewer.session_active(started)
                    assert viewer.stop_session(project)
                    process.wait(timeout=5)
                    assert not viewer.session_directory(project).exists()

            # An already-exited process still has a handle: stop waits without signalling.
            log_directory = viewer.session_directory(project)
            log_directory.mkdir()
            with (log_directory / "structurizr.stdout.log").open("w") as stdout, \
                    (log_directory / "structurizr.stderr.log").open("w") as stderr:
                exited = original_popen([command[0], "-c", "print('Already exited')"],
                                        stdout=stdout, stderr=stderr)
                assert exited.wait(timeout=5) == 0
            viewer.write_state(project, {"runtime": "java", "pid": exited.pid})
            assert viewer.stop_session(project)
            assert not viewer.session_directory(project).exists()
            print("Java lifecycle: launch failure, reaped startup/state failure, 3 detached stops, exited stop passed.")
        finally:
            viewer.discover_runtimes = original_discovery
            viewer.run_capture = original_capture
            viewer.wait_ready = original_wait
            viewer.open_browser_url = original_open
            if viewer.session_directory(project).exists():
                viewer.cleanup_directory(project)
        if snapshot(project) != draft_before_start:
            raise AssertionError("Opening and closing a draft viewer changed repository files")
        if json.loads((project / "docs/architecture/bootstrap-intake.json").read_text(encoding="utf-8"))["status"] != "draft":
            raise AssertionError("Viewing changed draft intake status")

        dsl_path = project / "docs/architecture/workspace.dsl"
        original_dsl = dsl_path.read_text(encoding="utf-8")
        intake_path = project / "docs/architecture/bootstrap-intake.json"
        registered = json.loads(intake_path.read_text(encoding="utf-8"))
        registered["artifacts"]["c4_projection"]["sha256"] = "0" * 64
        write(intake_path, json.dumps(registered, indent=2) + "\n")
        expect_failure(lambda: viewer.validate_projection(project), "Draft bootstrap intake hashes do not match")
        registered["artifacts"]["c4_projection"]["sha256"] = digest(dsl_path)
        write(intake_path, json.dumps(registered, indent=2) + "\n")

        for expected_style in ("background #2563EB", "ProgramKitStatus:proposed", "routing Orthogonal"):
            if expected_style not in original_dsl:
                raise AssertionError(f"Generated projection omitted review styling: {expected_style}")
        write(dsl_path, original_dsl + "// manual edit\n")
        expect_failure(lambda: viewer.validate_projection(project), "stale relative")
        write(dsl_path, "workspace {\n")
        expect_failure(lambda: viewer.validate_projection(project), "malformed")
        write(dsl_path, original_dsl)
        dsl_path.unlink()
        expect_failure(lambda: viewer.validate_projection(project), "C4 projection is missing")
        write(dsl_path, original_dsl)

        registered = json.loads(intake_path.read_text(encoding="utf-8"))
        write(intake_path, "{\n")
        expect_failure(lambda: viewer.validate_projection(project), "Cannot read bootstrap intake")
        write(intake_path, json.dumps(registered, indent=2) + "\n")
        registered["status"] = "pending"
        write(intake_path, json.dumps(registered, indent=2) + "\n")
        expect_failure(lambda: viewer.validate_projection(project), "status must be draft or confirmed")
        registered["status"] = "confirmed"
        write(intake_path, json.dumps(registered, indent=2) + "\n")
        confirmed = viewer.validate_projection(project)
        marker = project / '.specify/proxy-intake.json'
        write(marker, '{}')
        expect_failure(lambda: viewer.validate_projection(project), 'PROXY_INTAKE_NON_AUTHORIZING')
        marker.unlink()
        if confirmed["review_mode"] != "confirmed-baseline-review" or confirmed["intake_binding"] != "confirmed-intake":
            raise AssertionError(f"Confirmed intake review regressed: {confirmed}")

        value["title"] = "Evolved review system"
        write(project / "docs/architecture/architecture-map.json", json.dumps(value, indent=2) + "\n")
        write(dsl_path, architecture.StructurizrDslExporter().export(value))
        evolved = viewer.validate_projection(project)
        if evolved["intake_binding"] != "evolved-together-from-confirmed-intake":
            raise AssertionError("A current generated pair did not report its older intake binding")
        registered["artifacts"]["architecture_map"]["sha256"] = digest(project / "docs/architecture/architecture-map.json")
        registered["artifacts"]["architecture_map"]["bytes"] = (project / "docs/architecture/architecture-map.json").stat().st_size
        write(intake_path, json.dumps(registered, indent=2) + "\n")
        expect_failure(lambda: viewer.validate_projection(project), "partial architecture drift")

        create_project(project, architecture, semantic, semantic.semantic_model(project / "docs/architecture/project-intent.md"))
        state = {
            "schema_version": "1.0",
            "project_root": str(project),
            "runtime": "java",
            "pid": os.getpid(),
            "port": 8081,
            "url": "http://localhost:8081/",
            "projection_sha256": digest(project / "docs/architecture/workspace.dsl"),
            "data_directory": str(viewer.session_directory(project) / "data"),
        }
        viewer.write_state(project, state)
        active_inspection = viewer.inspection(project)
        if active_inspection["port"] != 8081 or not active_inspection["active_session"]:
            raise AssertionError("Inspection did not report the recorded active viewer and its port")
        with patch.object(viewer, "wait_ready") as ready:
            repeated = viewer.start_session(project, "auto", None, None, False, True)
            assert ready.call_args.kwargs["view_key"] == "system-context"
            assert ready.call_args.kwargs["timeout"] == 5
        with patch.object(viewer, "wait_ready", side_effect=viewer.C4ViewError("Recorded viewer unreachable")):
            expect_failure(lambda: viewer.start_session(project, "auto", None, None, False, True),
                           "Recorded viewer unreachable")
            assert viewer.load_state(project) is not None  # Never kill an unverified PID.
        if not repeated.get("reused") or repeated["pid"] != os.getpid():
            raise AssertionError("Repeated invocation did not reuse the collision-safe active session")
        viewer.cleanup_directory(project)

        calls: list[list[str]] = []
        viewer.write_state(
            project,
            {
                "schema_version": "1.0",
                "runtime": "docker",
                "container": f"program-kit-c4-{viewer.session_identifier(project)}",
            },
        )
        expect_failure(
            lambda: viewer.stop_session(
                project, {"docker": {"path": "docker", "daemon_available": False}}
            ),
            "temporary state was preserved",
        )
        if not viewer.session_directory(project).is_dir():
            raise AssertionError("Inaccessible Docker caused the recoverable session state to be deleted")
        original_capture = viewer.run_capture
        viewer.run_capture = lambda arguments, timeout=10: (
            calls.append(list(arguments))
            or subprocess.CompletedProcess(list(arguments), 0, "", "")
        )
        try:
            if not viewer.stop_session(project, {"docker": {"path": "docker", "daemon_available": True}}):
                raise AssertionError("Recorded viewer was not stopped")
        finally:
            viewer.run_capture = original_capture
        if not calls or calls[0][1:4] != ["container", "rm", "--force"]:
            raise AssertionError(f"Cleanup did not target the exact recorded container: {calls}")
        if viewer.session_directory(project).exists():
            raise AssertionError("Cleanup retained temporary viewer state")

        windows_data = Path("C:/Repositories/Program Kit review/viewer data")
        docker_command = viewer.build_docker_command(
            "docker.exe", profile["selected"]["docker_image"], windows_data, "program-kit-c4-abc", 8081
        )
        expected_mount = f"{os.fspath(windows_data)}:/usr/local/structurizr"
        assert "--pull=never" in docker_command and "--rm" not in docker_command
        if docker_command[-3] != expected_mount:
            raise AssertionError("Windows path with spaces was split or lost in Docker command construction")
        rendered_windows = viewer.render_command(docker_command, "nt")
        if '"' not in rendered_windows or "latest" in docker_command:
            raise AssertionError("Windows command diagnostics did not quote the spaced mount path")
        posix_command = viewer.build_java_command(
            "/usr/bin/java", PurePosixPath("/opt/Program Kit/structurizr.war"), PurePosixPath("/tmp/review packet"), 8082
        )
        if "/tmp/review packet" not in posix_command or "'/tmp/review packet'" not in viewer.render_command(posix_command, "posix"):
            raise AssertionError("POSIX path handling did not preserve a spaced argument")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            port = occupied.getsockname()[1]
            if port < 65535 and viewer.select_port(port, 2) != port + 1:
                raise AssertionError("Port selection did not avoid an occupied localhost port")
        if viewer.select_port(8081) == 8080:
            raise AssertionError("Port selection regressed to the Keycloak default")

        docker_missing = {
            "docker": {"daemon_available": True, "image_local": False, "diagnostic": "image missing"},
            "java": {"supported": False, "war_local": False, "diagnostic": "java unavailable"},
        }
        expect_failure(lambda: viewer.choose_runtime(docker_missing, "auto"), "image missing")
        java_ready = {
            "docker": {"daemon_available": False, "image_local": False, "diagnostic": "docker unavailable"},
            "java": {"supported": True, "war_local": True, "diagnostic": "java ready"},
        }
        if viewer.choose_runtime(java_ready, "auto") != "java":
            raise AssertionError("Supported local Java/WAR fallback was not selected")

        discovery_before = snapshot(project)
        original_which = viewer.shutil.which
        original_capture = viewer.run_capture
        observed: list[list[str]] = []
        viewer.shutil.which = lambda name: "docker" if name == "docker" else None
        viewer.run_capture = lambda arguments, timeout=10: (
            observed.append(list(arguments))
            or subprocess.CompletedProcess(
                list(arguments),
                0 if arguments[1] == "version" else 1,
                "29.0.1\n" if arguments[1] == "version" else "",
                "image absent" if arguments[1] != "version" else "",
            )
        )
        try:
            discovery = viewer.discover_runtimes(profile)
        finally:
            viewer.shutil.which = original_which
            viewer.run_capture = original_capture
        if discovery["docker"]["image_local"] or any("pull" in command for command in observed):
            raise AssertionError("Runtime discovery pulled or treated the missing pinned image as local")
        if snapshot(project) != discovery_before:
            raise AssertionError("Runtime discovery changed the consumer repository")
        del os.environ[viewer.STATE_ENVIRONMENT]

    print("C4 projection viewing validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

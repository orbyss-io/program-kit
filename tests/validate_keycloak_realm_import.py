from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "extensions/program-kit-dotnet/templates/dotnet"
sys.path.insert(0, str(ROOT / "extensions/program-kit-dotnet/scripts"))

import identity_fixture  # noqa: E402
import spa_profile  # noqa: E402


def image_reference() -> str:
    compose = (TEMPLATE / "web-profiles/common/deploy/compose.identity.yml").read_text(encoding="utf-8")
    match = re.search(r"^\s*image:\s*(\S+)\s*$", compose, re.MULTILINE)
    if not match or "@sha256:" not in match.group(1):
        raise AssertionError("The managed Keycloak smoke test requires one digest-pinned image")
    return match.group(1)


def rendered_realm(profile: str) -> bytes:
    source = (TEMPLATE / "web-profiles/common/deploy/keycloak/program-kit-realm.json").read_bytes()
    configuration = None
    if profile == "spa-pkce":
        configuration = spa_profile.validate_configuration(
            json.loads((TEMPLATE / "web-profiles/spa-pkce/.program-kit/spa-pkce.json").read_text(encoding="utf-8"))
        )
    return identity_fixture.render_realm(source, TEMPLATE, profile, configuration)


def wait_ready(name: str, timeout: int = 180) -> None:
    port_result = subprocess.run(
        ["docker", "port", name, "9000/tcp"], capture_output=True, text=True, check=True
    )
    port = port_result.stdout.strip().rsplit(":", 1)[-1]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health/ready", timeout=3) as response:
                if response.status == 200 and b'"status": "UP"' in response.read():
                    return
        except (OSError, urllib.error.URLError):
            pass
        state = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", name],
            capture_output=True,
            text=True,
            check=False,
        )
        if state.returncode != 0 or state.stdout.strip() != "true":
            logs = subprocess.run(["docker", "logs", name], capture_output=True, text=True, check=False)
            raise AssertionError(f"Keycloak exited before readiness:\n{logs.stdout}{logs.stderr}")
        time.sleep(3)
    logs = subprocess.run(["docker", "logs", name], capture_output=True, text=True, check=False)
    raise AssertionError(f"Keycloak did not become ready:\n{logs.stdout}{logs.stderr}")


def smoke(profile: str, root: Path) -> None:
    name = f"program-kit-keycloak-{profile}-{uuid.uuid4().hex[:8]}"
    realm = root / f"{profile}.json"
    realm.write_bytes(rendered_realm(profile))
    started = subprocess.run(
        [
            "docker", "run", "--detach", "--name", name,
            "--publish", "127.0.0.1::9000",
            "--env", "KC_BOOTSTRAP_ADMIN_USERNAME=fixture-admin",
            "--env", "KC_BOOTSTRAP_ADMIN_PASSWORD=ephemeral-smoke-only",
            "--env", "KC_HOSTNAME=http://localhost:8080",
            "--volume", f"{realm.resolve()}:/opt/keycloak/data/import/program-kit-realm.json:ro",
            image_reference(), "start-dev", "--import-realm", "--health-enabled=true",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if started.returncode != 0:
        raise AssertionError(f"Could not start pinned Keycloak for {profile}: {started.stderr}")
    try:
        wait_ready(name)
        logs = subprocess.run(["docker", "logs", name], capture_output=True, text=True, check=True)
        if "Unrecognized field" in logs.stdout + logs.stderr:
            raise AssertionError(f"Keycloak rejected the {profile} realm representation")
    finally:
        subprocess.run(["docker", "rm", "--force", name], check=False, capture_output=True)


def main() -> int:
    if shutil.which("docker") is None:
        raise AssertionError("Docker is required for the pinned Keycloak realm-import smoke test")
    with tempfile.TemporaryDirectory(prefix="program-kit-keycloak-import-") as value:
        for profile in ("bff-cookie", "spa-pkce"):
            smoke(profile, Path(value))
    print("Pinned Keycloak imports both generated web-profile realms and reaches readiness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

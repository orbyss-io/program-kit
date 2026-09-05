from __future__ import annotations

import json
import base64
import hashlib
import http.cookiejar
import http.cookies
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
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


def published_port(name: str, container_port: str) -> str:
    result = subprocess.run(
        ["docker", "port", name, container_port], capture_output=True, text=True, check=True
    )
    return result.stdout.strip().rsplit(":", 1)[-1]


def validate_split_authority_metadata(name: str) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{published_port(name, '8080/tcp')}"
        "/realms/program-kit/.well-known/openid-configuration",
        headers={"Host": "program-kit-identity:8080"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        metadata = json.loads(response.read())
    expected_public = "http://localhost:8080/realms/program-kit"
    expected_backchannel = "http://program-kit-identity:8080/realms/program-kit"
    expected = {
        "issuer": expected_public,
        "authorization_endpoint": f"{expected_public}/protocol/openid-connect/auth",
        "end_session_endpoint": f"{expected_public}/protocol/openid-connect/logout",
        "token_endpoint": f"{expected_backchannel}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{expected_backchannel}/protocol/openid-connect/userinfo",
        "jwks_uri": f"{expected_backchannel}/protocol/openid-connect/certs",
    }
    actual = {key: metadata.get(key) for key in expected}
    if actual != expected:
        raise AssertionError(
            "Keycloak did not preserve the public issuer/frontchannel and private server backchannel: "
            + json.dumps(actual, sort_keys=True)
        )


def validate_authorization_entry(name: str, profile: str) -> None:
    port = published_port(name, "8080/tcp")
    discovery = urllib.request.Request(
        f"http://127.0.0.1:{port}/realms/program-kit/.well-known/openid-configuration",
        headers={"Host": "program-kit-identity:8080"},
    )
    with urllib.request.urlopen(discovery, timeout=10) as response:
        metadata = json.loads(response.read())
    par_endpoint = metadata.get("pushed_authorization_request_endpoint")
    if not isinstance(par_endpoint, str):
        raise AssertionError(f"Fresh {profile} realm does not advertise PAR")
    parsed_par = urllib.parse.urlsplit(par_endpoint)
    client_id = "program-kit-bff" if profile == "bff-cookie" else "program-kit-spa"
    redirect_uri = (
        "http://localhost:5000/signin-oidc"
        if profile == "bff-cookie"
        else "http://localhost:5173/auth/callback"
    )
    scopes = (
        "openid profile offline_access program-kit-api"
        if profile == "bff-cookie"
        else "openid profile program-kit-api"
    )
    verifier = "program-kit-clean-import-par-verifier-0123456789abcdef"
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    form = {
        "client_id": client_id,
        "response_type": "code",
        "response_mode": "query",
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": "program-kit-import-state",
        "nonce": "program-kit-import-nonce",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if profile == "bff-cookie":
        form["client_secret"] = "local-program-kit-secret"
    par = urllib.request.Request(
        urllib.parse.urlunsplit(("http", f"127.0.0.1:{port}", parsed_par.path, parsed_par.query, "")),
        data=urllib.parse.urlencode(form).encode("ascii"),
        headers={
            "Host": "program-kit-identity:8080",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(par, timeout=10) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise AssertionError(
            f"Fresh {profile} realm rejected the managed PAR scope contract: "
            f"{error.code} {error.read().decode('utf-8', errors='replace')}"
        ) from error
    request_uri = payload.get("request_uri")
    if not isinstance(request_uri, str) or not request_uri:
        raise AssertionError(f"Fresh {profile} PAR response omitted request_uri: {payload}")
    query = urllib.parse.urlencode({"client_id": client_id, "request_uri": request_uri})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect()
    )
    next_url = f"http://localhost:{port}/realms/program-kit/protocol/openid-connect/auth?{query}"
    page = ""
    cookies: dict[str, str] = {}
    for _ in range(6):
        headers = {"Host": "localhost:8080"}
        if cookies:
            headers["Cookie"] = "; ".join(f"{key}={value}" for key, value in cookies.items())
        request = urllib.request.Request(next_url, headers=headers)
        try:
            with opener.open(request, timeout=10) as response:
                page = response.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as error:
            if error.code not in {301, 302, 303, 307, 308} or not error.headers.get("Location"):
                raise AssertionError(
                    f"Fresh {profile} PAR authorization entry failed at {error.url}: "
                    f"{error.code} {error.read().decode('utf-8', errors='replace')}"
                ) from error
            for value in error.headers.get_all("Set-Cookie", []):
                parsed_cookie = http.cookies.SimpleCookie()
                parsed_cookie.load(value)
                cookies.update((key, morsel.value) for key, morsel in parsed_cookie.items())
            redirected = urllib.parse.urljoin(next_url, error.headers["Location"])
            parsed = urllib.parse.urlsplit(redirected)
            next_url = urllib.parse.urlunsplit(
                ("http", f"localhost:{port}", parsed.path, parsed.query, "")
            )
    if 'name="username"' not in page:
        raise AssertionError(f"Fresh {profile} PAR did not reach the real Keycloak login form")


def smoke(profile: str, root: Path) -> None:
    name = f"program-kit-keycloak-{profile}-{uuid.uuid4().hex[:8]}"
    realm = root / f"{profile}.json"
    realm.write_bytes(rendered_realm(profile))
    started = subprocess.run(
        [
            "docker", "run", "--detach", "--name", name,
            "--publish", "127.0.0.1::8080",
            "--publish", "127.0.0.1::9000",
            "--env", "KC_BOOTSTRAP_ADMIN_USERNAME=fixture-admin",
            "--env", "KC_BOOTSTRAP_ADMIN_PASSWORD=ephemeral-smoke-only",
            "--env", "KC_HOSTNAME=http://localhost:8080",
            "--env", "KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true",
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
        combined_logs = logs.stdout + logs.stderr
        if "Unrecognized field" in combined_logs:
            raise AssertionError(f"Keycloak rejected the {profile} realm representation")
        if "referenced client scope" in combined_logs.casefold() and "does not exist" in combined_logs.casefold():
            raise AssertionError(f"Fresh {profile} realm ignored a referenced client scope:\n{combined_logs}")
        validate_split_authority_metadata(name)
        validate_authorization_entry(name, profile)
    finally:
        subprocess.run(["docker", "rm", "--force", name], check=False, capture_output=True)


def main() -> int:
    if shutil.which("docker") is None:
        raise AssertionError("Docker is required for the pinned Keycloak realm-import smoke test")
    with tempfile.TemporaryDirectory(prefix="program-kit-keycloak-import-") as value:
        for profile in ("bff-cookie", "spa-pkce"):
            smoke(profile, Path(value))
    print("Pinned Keycloak clean-imports both profiles and accepts their real PAR/login entry flows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

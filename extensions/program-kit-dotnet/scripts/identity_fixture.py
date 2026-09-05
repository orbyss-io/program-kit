from __future__ import annotations

import json
from pathlib import Path

import spa_profile


REALM_PATH = "deploy/keycloak/program-kit-realm.json"
PROFILE_CLIENT_PATH = "identity-client.json"


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def _client_ids(realm: dict) -> list[str]:
    clients = realm.get("clients")
    if not isinstance(clients, list) or not all(isinstance(client, dict) for client in clients):
        raise ValueError("PKW113 managed Keycloak realm clients must be objects")
    identifiers = [client.get("clientId") for client in clients]
    if not all(isinstance(identifier, str) and identifier for identifier in identifiers):
        raise ValueError("PKW113 every managed Keycloak client must have a non-empty clientId")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("PKW113 managed Keycloak client identifiers must be unique")
    return identifiers


def _profile_client(template_root: Path, web_profile: str) -> dict:
    path = template_root / "web-profiles" / web_profile / PROFILE_CLIENT_PATH
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"PKW113 expected one profile client object in {path}")
    return value


def render_realm(
    source: bytes,
    template_root: Path,
    web_profile: str,
    spa_configuration: dict | None,
) -> bytes:
    realm = json.loads(source.decode("utf-8"))
    identifiers = _client_ids(realm)
    if identifiers != ["program-kit-api"]:
        raise ValueError(
            "PKW113 the profile-neutral Keycloak realm must contain only the bearer-only API client"
        )
    realm["clients"].append(_profile_client(template_root, web_profile))
    rendered = json_bytes(realm)
    if web_profile == "spa-pkce":
        if spa_configuration is None:
            raise ValueError("PKW113 the SPA identity fixture requires its typed configuration")
        rendered = spa_profile.render_realm(rendered, spa_configuration)
    validate_realm(rendered, web_profile, spa_configuration)
    return rendered


def validate_realm(
    content: bytes,
    web_profile: str,
    spa_configuration: dict | None,
) -> None:
    realm = json.loads(content.decode("utf-8"))
    identifiers = _client_ids(realm)
    if web_profile == "bff-cookie":
        audience = "program-kit-api"
        selected = "program-kit-bff"
    elif web_profile == "spa-pkce" and spa_configuration is not None:
        audience = spa_configuration["audience"]
        selected = spa_configuration["clientId"]
    else:
        raise ValueError(f"PKW113 unsupported identity-fixture profile {web_profile!r}")
    expected = [audience, selected]
    if identifiers != expected:
        raise ValueError(
            "PKW113 the selected-profile Keycloak fixture must contain exactly the bearer-only "
            f"API client and the selected {web_profile} client; expected {expected!r}, got {identifiers!r}"
        )
    api = realm["clients"][0]
    if api.get("bearerOnly") is not True:
        raise ValueError("PKW113 the API audience must remain a bearer-only Keycloak client")
    profile_client = realm["clients"][1]
    if web_profile == "bff-cookie":
        if profile_client.get("publicClient") is not False or not profile_client.get("secret"):
            raise ValueError("PKW113 the selected BFF client must remain confidential")
    elif profile_client.get("publicClient") is not True or "secret" in profile_client:
        raise ValueError("PKW113 the selected SPA-PKCE client must remain public and secret-free")


def verify_repository(
    repository: Path,
    web_profile: str,
    spa_configuration: dict | None,
) -> None:
    validate_realm(
        (repository / REALM_PATH).read_bytes(),
        web_profile,
        spa_configuration,
    )

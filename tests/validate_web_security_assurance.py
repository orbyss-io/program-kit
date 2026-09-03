from __future__ import annotations

import json
from pathlib import Path


THREAT_MODEL_ID = "program-kit-web-threat-model-v1"
EVIDENCE_ID = "program-kit-web-security-evidence-v1"
PROFILES = {"bff-cookie-v1", "spa-pkce-v1"}
REQUIRED_SOURCES = {
    "SRC-IETF-RFC9700",
    "SRC-IETF-BROWSER-APPS",
    "SRC-OIDC-CORE",
    "SRC-OIDC-RP-LOGOUT",
    "SRC-OIDC-BACKCHANNEL-LOGOUT",
    "SRC-NIST-800-63B-4",
    "SRC-NIST-800-63C-4",
    "SRC-FKS-OAUTH",
    "SRC-FKS-OIDC",
    "SRC-PK-LOCAL-POLICY",
}
REQUIRED_CONTROLS = {f"WEB-C{number:02d}" for number in range(1, 14)}
REQUIRED_DEFAULTS = {f"WEB-D{number:02d}" for number in range(1, 9)}
REQUIRED_VERIFICATION = {f"WEB-V{number}" for number in range(1, 5)}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"Expected a JSON object in {path}")
    return value


def indexed(items: object, label: str) -> dict[str, dict]:
    if not isinstance(items, list) or not items:
        raise AssertionError(f"Security evidence has no {label}")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise AssertionError(f"Security evidence has an invalid {label} entry")
        item_id = item["id"]
        if item_id in result:
            raise AssertionError(f"Security evidence repeats {label} ID {item_id}")
        result[item_id] = item
    return result


def require_nonempty(item: dict, fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if field not in item or item[field] in (None, "", []):
            raise AssertionError(f"{label} has no {field}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    references = root / "extensions/program-kit-dotnet/references"
    evidence_path = references / "web-security-evidence.json"
    threat_model_path = references / "web-security-threat-model.md"
    evidence = load_object(evidence_path)

    if evidence.get("schemaVersion") != 1 or evidence.get("id") != EVIDENCE_ID:
        raise AssertionError("Security evidence identity or schema is invalid")
    if evidence.get("threatModel") != THREAT_MODEL_ID:
        raise AssertionError("Security evidence does not bind the expected threat model")
    if set(evidence.get("profileContracts", [])) != PROFILES:
        raise AssertionError("Security evidence does not cover both authenticated profiles")
    require_nonempty(evidence, ("lastReviewed", "owner", "claim"), "Security evidence")
    if "do not certify" not in evidence["claim"]:
        raise AssertionError("Security evidence must bound its assurance claim")

    source_classes = set(evidence.get("sourceClasses", []))
    sources = indexed(evidence.get("sources"), "source")
    if not REQUIRED_SOURCES.issubset(sources):
        raise AssertionError("Security evidence is missing required standards or research sources")
    for source_id, source in sources.items():
        require_nonempty(source, ("title", "class", "status", "url"), source_id)
        if source["class"] not in source_classes:
            raise AssertionError(f"{source_id} uses an undeclared source class")
        if source["class"] != "program-kit-policy" and not source["url"].startswith("https://"):
            raise AssertionError(f"{source_id} must use an HTTPS primary-source URL")
    browser_source = sources["SRC-IETF-BROWSER-APPS"]
    if browser_source["class"] != "ietf-working-group-draft" or "not a final RFC" not in browser_source["status"]:
        raise AssertionError("The browser-app guidance must remain honestly classified as a draft")
    if sources["SRC-PK-LOCAL-POLICY"]["class"] != "program-kit-policy":
        raise AssertionError("Program Kit policy must not be represented as external evidence")

    threats = indexed(evidence.get("threats"), "threat")
    controls = indexed(evidence.get("controls"), "control")
    if set(controls) != REQUIRED_CONTROLS:
        raise AssertionError("Security evidence control catalogue is incomplete or unexpectedly renumbered")
    mapped_threats: set[str] = set()
    for control_id, control in controls.items():
        require_nonempty(
            control,
            ("decision", "classification", "threats", "sources", "verification"),
            control_id,
        )
        unknown_threats = set(control["threats"]) - set(threats)
        unknown_sources = set(control["sources"]) - set(sources)
        if unknown_threats:
            raise AssertionError(f"{control_id} maps unknown threats: {sorted(unknown_threats)}")
        if unknown_sources:
            raise AssertionError(f"{control_id} maps unknown sources: {sorted(unknown_sources)}")
        mapped_threats.update(control["threats"])
    if mapped_threats != set(threats):
        raise AssertionError(f"Uncontrolled threats: {sorted(set(threats) - mapped_threats)}")

    defaults = indexed(evidence.get("configurableDefaults"), "configurable default")
    if set(defaults) != REQUIRED_DEFAULTS:
        raise AssertionError("Configurable-default evidence is incomplete or unexpectedly renumbered")
    for default_id, default in defaults.items():
        require_nonempty(
            default,
            ("setting", "default", "unit", "classification", "rationale", "overrideWhen", "requiredEvidence"),
            default_id,
        )
    indexed(evidence.get("residualRisks"), "residual risk")
    verification = indexed(evidence.get("verificationLevels"), "verification level")
    if set(verification) != REQUIRED_VERIFICATION:
        raise AssertionError("Security assurance levels are incomplete")
    review_triggers = indexed(evidence.get("reviewTriggers"), "review trigger")
    if len(review_triggers) < 5 or not any("Twelve months" in item["trigger"] for item in review_triggers.values()):
        raise AssertionError("Security evidence lacks the periodic review trigger")

    threat_model = threat_model_path.read_text(encoding="utf-8")
    for required in (
        THREAT_MODEL_ID,
        EVIDENCE_ID,
        "Attacker capabilities",
        "Trust boundaries",
        "Assumptions and out-of-scope risks",
        "do not prove absence of defects",
    ):
        if required not in threat_model:
            raise AssertionError(f"Threat model is missing {required!r}")
    for threat_id in threats:
        if threat_id not in threat_model:
            raise AssertionError(f"Threat model does not explain {threat_id}")

    for profile_directory, contract_id in (
        ("bff-cookie", "bff-cookie-v1"),
        ("spa-pkce", "spa-pkce-v1"),
    ):
        profile_root = root / "extensions/program-kit-dotnet/templates/dotnet/web-profiles" / profile_directory
        manifest = load_object(profile_root / "managed-files.json")
        files = {item["path"]: item for item in manifest["files"]}
        for destination, source in (
            (".program-kit/security/web-security-evidence.json", "web-security-evidence.json"),
            ("docs/architecture/program-kit/web-security-threat-model.md", "web-security-threat-model.md"),
        ):
            entry = files.get(destination)
            if not entry or entry.get("ownership") != "managed" or entry.get("source") != source:
                raise AssertionError(f"{profile_directory} does not ship managed {destination}")
        contract = load_object(profile_root / "eng/program-kit/web/web-contract.json")
        if contract.get("profile") != contract_id:
            raise AssertionError(f"Unexpected profile contract in {profile_directory}")
        if contract.get("assurance") != {
            "threatModel": THREAT_MODEL_ID,
            "evidenceProfile": EVIDENCE_ID,
        }:
            raise AssertionError(f"{profile_directory} does not bind exact assurance IDs")
        profile_record = load_object(profile_root / ".program-kit/web-profile.json")
        if profile_record.get("threatModel") != THREAT_MODEL_ID or profile_record.get("securityEvidence") != EVIDENCE_ID:
            raise AssertionError(f"{profile_directory} profile record does not bind exact assurance IDs")
        host_settings = load_object(profile_root / "hostsettings.json")["ProgramKit"]["Web"]
        if host_settings.get("PermissionClaim") != "permissions":
            raise AssertionError(f"{profile_directory} does not name the canonical permission claim")
        if host_settings.get("RolePermissions") != {} or host_settings.get("ScopePermissions") != {}:
            raise AssertionError(
                f"{profile_directory} must not invent application-specific provider mappings"
            )

    host_web_root = root / "src/dotnet/ProgramKit.Host/Web"
    host_web = "\n".join(path.read_text(encoding="utf-8") for path in host_web_root.glob("*.cs"))
    for required in (
        "PermissionClaimsTransformation",
        "PermissionPolicyProvider",
        'RequireClaim(webOptions.Value.PermissionClaim, permission)',
        "settings.RolePermissions",
        "settings.ScopePermissions",
        "permissions",
    ):
        if required not in host_web:
            raise AssertionError(f"ProgramKit.Host does not implement permission contract: {required}")
    web_profiles_root = root / "extensions/program-kit-dotnet/templates/dotnet/web-profiles"
    browser_contract = "\n".join(
        path.read_text(encoding="utf-8")
        for pattern in ("*.ts", "*.ps1")
        for path in web_profiles_root.rglob(pattern)
    )
    if "PROGRAMKIT_PERMISSION_PROBE_PATH" not in browser_contract or "PROGRAMKIT_ROLE_PROBE_PATH" in browser_contract:
        raise AssertionError("The browser contract must probe application permissions, not provider roles")

    adr = (root / "docs/decisions/0005-secure-web-boundary-profiles.md").read_text(encoding="utf-8")
    contract = (references / "secure-web-profiles.md").read_text(encoding="utf-8")
    for document_name, document in (("ADR 0005", adr), ("secure web contract", contract)):
        for required in (THREAT_MODEL_ID, EVIDENCE_ID):
            if required not in document:
                raise AssertionError(f"{document_name} does not reference {required}")
    if "not a final RFC" not in adr or "does not certify" not in adr:
        raise AssertionError("ADR 0005 overstates the strength of its security evidence")

    print("Web security assurance validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

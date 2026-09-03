from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

import spa_profile


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def extension_version(extension_root: Path) -> str:
    content = (extension_root / "extension.yml").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"([^"]+)"\s*$', content, re.MULTILINE)
    if match is None:
        raise ValueError("Could not read the Program Kit extension version.")
    return match.group(1)


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def consumer_nuget_routing_error(path: Path) -> str | None:
    """Validate the protected routes while allowing consumer-owned feed extensions."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        return f"cannot parse consumer-owned NuGet configuration: {exc}"

    sources = {
        source.attrib.get("key", ""): source.attrib.get("value", "")
        for source in root.findall("./packageSources/add")
    }
    required_sources = {
        "nuget.org": "https://api.nuget.org/v3/index.json",
        "CShells Preview": "https://f.feedz.io/valence-works/cshells/nuget/index.json",
        "Nuplane Preview": "https://f.feedz.io/valence-works/nuplane/nuget/index.json",
    }
    for source, url in required_sources.items():
        if sources.get(source) != url:
            return f"{source} must retain its approved package-source URL"

    mappings = {
        source.attrib.get("key", ""): {
            package.attrib.get("pattern", "") for package in source.findall("package")
        }
        for source in root.findall("./packageSourceMapping/packageSource")
    }
    expected = {
        "CShells Preview": {"CShells", "CShells.*"},
        "Nuplane Preview": {"Nuplane", "Nuplane.*"},
    }
    if "*" not in mappings.get("nuget.org", set()):
        return "nuget.org must retain the default '*' public-package route"
    for source, patterns in expected.items():
        if mappings.get(source) != patterns:
            return f"{source} must retain only the protected patterns {sorted(patterns)}"
    for source, patterns in mappings.items():
        if source != "nuget.org" and "*" in patterns:
            return f"{source} must use namespace-specific patterns rather than a second '*' route"
        protected = {"CShells", "CShells.*", "Nuplane", "Nuplane.*"}
        if source not in expected and patterns.intersection(protected):
            return f"{source} must not duplicate a protected CShells or Nuplane route"
    return None


def selected_web_profile(target: Path, requested: str) -> str:
    """Resolve an explicit profile or derive the secure default from reviewed bootstrap evidence."""
    if requested != "auto":
        return requested

    decision_path = target / "docs" / "architecture" / "bootstrap-decisions.json"
    if decision_path.is_file():
        decisions = load_json(decision_path, {})
        web = decisions.get("web")
        if isinstance(web, dict):
            selected = web.get("secure_profile")
            approved_profiles = {
                "none-v1": "none",
                "bff-cookie-v1": "bff-cookie",
                "spa-pkce-v1": "spa-pkce",
            }
            if selected in approved_profiles:
                return approved_profiles[selected]

    evidence_paths = [
        target / "docs" / "initial-design.md",
        target / "INITIAL_DESIGN.md",
        target / "initial_design.md",
    ]
    evidence = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in evidence_paths if path.is_file()
    )
    browser_markers = ("browser", "react", "single-page", "single page", "spa", "typescript")
    return "bff-cookie" if any(marker in evidence for marker in browser_markers) else "none"


def selected_dotnet_sdk(target: Path, managed_global_json: Path) -> tuple[str, str]:
    """Return the governed SDK version and its authority source."""
    managed = load_json(managed_global_json, {})
    managed_version = managed.get("sdk", {}).get("version")
    if not isinstance(managed_version, str) or not managed_version.strip():
        raise ValueError("The Program Kit managed global.json has no exact SDK version.")

    decision_path = target / "docs" / "architecture" / "bootstrap-decisions.json"
    if not decision_path.is_file():
        return managed_version, "program-kit-default"
    decisions = load_json(decision_path, {})
    toolchain = decisions.get("toolchain")
    if not isinstance(toolchain, dict) or toolchain.get("source") != "override":
        return managed_version, "program-kit-default"
    reason = toolchain.get("override_reason")
    pins = toolchain.get("pins")
    overrides = decisions.get("overrides")
    override_ids = {
        item.get("id") for item in overrides if isinstance(item, dict)
    } if isinstance(overrides, list) else set()
    selected = pins.get("dotnet-sdk") if isinstance(pins, dict) else None
    if (
        not isinstance(reason, str)
        or not reason.strip()
        or "managed-toolchain-version" not in override_ids
        or not isinstance(selected, str)
        or not selected.strip()
    ):
        raise ValueError(
            "The .NET SDK override is incomplete; record a non-empty reason, an exact dotnet-sdk "
            "pin, and the managed-toolchain-version override decision."
        )
    return selected.strip(), "override"


def desired_content(
    source: Path,
    relative: str,
    dotnet_sdk: str,
    web_profile: str,
    spa_configuration: dict | None,
) -> bytes:
    content = source.read_bytes()
    if relative == "global.json":
        value = load_json(source, {})
        sdk = value.get("sdk")
        if not isinstance(sdk, dict):
            raise ValueError("The Program Kit managed global.json has no sdk object.")
        sdk["version"] = dotnet_sdk
        return (json.dumps(value, indent=2) + "\n").encode("utf-8")
    if web_profile != "spa-pkce" or spa_configuration is None:
        return content
    renderers = {
        "hostsettings.json": spa_profile.render_hostsettings,
        ".program-kit/web-profile.json": spa_profile.render_profile,
        "deploy/keycloak/program-kit-realm.json": spa_profile.render_realm,
        "eng/program-kit/web/web-contract.json": spa_profile.render_web_contract,
    }
    renderer = renderers.get(relative)
    return renderer(content, spa_configuration) if renderer else content


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Synchronize the Program Kit .NET repository baseline.")
    parser.add_argument("--target", default=".", help="Consuming repository root")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    parser.add_argument(
        "--web-profile",
        choices=("auto", "none", "bff-cookie", "spa-pkce"),
        default="auto",
        help="Secure web boundary profile; auto adopts BFF for a detected browser UI",
    )
    parser.add_argument(
        "--profile-selected",
        action="store_true",
        help="Confirms that the consuming repository accepted the .NET technology profile",
    )
    parser.add_argument(
        "--host-runtime-accepted",
        action="store_true",
        help="Confirms that the approved bootstrap baseline or a later Accepted override selects ProgramKit.Host",
    )
    parser.add_argument(
        "--preview-sources-approved",
        action="store_true",
        help="Confirms explicit approval to add the Program Kit preview packages and NuGet sources",
    )
    parser.add_argument(
        "--persistence-profile",
        choices=("none", "ef-postgresql", "ef-sqlserver", "ef-sqlite"),
        default="none",
        help="Explicit governed persistence profile; none keeps all providers inactive",
    )
    args = parser.parse_args()

    if not args.profile_selected:
        print("Refusing to scaffold: the .NET technology profile was not explicitly selected.", file=sys.stderr)
        return 3
    if not args.check and not args.host_runtime_accepted:
        print(
            "Refusing to scaffold: the Program Kit host/runtime choice is not confirmed by the approved "
            "bootstrap baseline or a later Accepted override.",
            file=sys.stderr,
        )
        return 4
    if not args.check and not args.preview_sources_approved:
        print(
            "Refusing to scaffold: adding preview packages and NuGet sources was not explicitly approved.",
            file=sys.stderr,
        )
        return 5

    extension_root = Path(__file__).resolve().parents[1]
    template_root = extension_root / "templates" / "dotnet"
    template_manifest = load_json(template_root / "managed-files.json", {})
    entries = template_manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("The .NET template manifest has no files list.")
    obsolete_files = template_manifest.get("obsoleteFiles", [])
    if not isinstance(obsolete_files, list) or not all(isinstance(path, str) for path in obsolete_files):
        raise ValueError("The .NET template manifest has an invalid obsoleteFiles list.")

    target = Path(args.target).resolve()
    dotnet_sdk, dotnet_sdk_source = selected_dotnet_sdk(
        target, template_root / "files" / "global.json"
    )
    web_profile = selected_web_profile(target, args.web_profile)
    spa_configuration: dict | None = None
    if web_profile == "spa-pkce":
        configuration_source = target / spa_profile.CONFIGURATION_PATH
        if not configuration_source.is_file():
            configuration_source = (
                template_root / "web-profiles/spa-pkce" / spa_profile.CONFIGURATION_PATH
            )
        spa_configuration = spa_profile.validate_configuration(
            spa_profile.load_object(configuration_source)
        )
    print(f"selected .NET SDK: {dotnet_sdk} ({dotnet_sdk_source})")
    print(f"selected web profile: {web_profile}")
    print(f"selected persistence profile: {args.persistence_profile}")
    profile_manifest_path = template_root / "web-profiles" / web_profile / "managed-files.json"
    if profile_manifest_path.is_file():
        profile_manifest = load_json(profile_manifest_path, {})
        profile_entries = profile_manifest.get("files")
        if not isinstance(profile_entries, list):
            raise ValueError(f"The {web_profile} profile manifest has no files list.")
        profile_destinations = {entry["path"] for entry in profile_entries}
        entries = [entry for entry in entries if entry["path"] not in profile_destinations]
        entries.extend(profile_entries)
    if not args.check:
        target.mkdir(parents=True, exist_ok=True)
    state_path = target / ".program-kit" / "managed.json"
    state = load_json(state_path, {"schemaVersion": 1, "files": {}})
    old_files = state.get("files")
    if not isinstance(old_files, dict):
        raise ValueError(f"Invalid managed-file state in {state_path}")

    created: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []
    conflict_details: dict[str, str] = {}
    removed: list[str] = []
    next_files: dict[str, dict[str, str]] = {}

    for entry in entries:
        relative = entry["path"]
        ownership = entry["ownership"]
        source_root = template_root / entry.get("sourceRoot", "files")
        source = source_root / entry.get("source", relative)
        destination = target / relative
        desired = desired_content(source, relative, dotnet_sdk, web_profile, spa_configuration)
        desired_hash = sha256_bytes(desired)
        previous = old_files.get(relative)

        if not destination.exists():
            created.append(relative)
            if not args.check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(desired)
            current_hash = desired_hash
        else:
            current = destination.read_bytes()
            current_hash = sha256_bytes(current)
            if current_hash == desired_hash:
                unchanged.append(relative)
            elif (
                isinstance(previous, dict)
                and current_hash == previous.get("installedHash")
                and (ownership == "managed" or previous.get("ownership") == "managed")
            ):
                updated.append(relative)
                if not args.check:
                    destination.write_bytes(desired)
                current_hash = desired_hash
            elif ownership == "scaffold" and relative == "NuGet.config":
                routing_error = consumer_nuget_routing_error(destination)
                if routing_error is None:
                    unchanged.append(relative)
                else:
                    conflicts.append(relative)
                    conflict_details[relative] = routing_error
            elif ownership == "configuration":
                unchanged.append(relative)
            else:
                conflicts.append(relative)

        next_files[relative] = {
            "ownership": ownership,
            "templateHash": desired_hash,
            "installedHash": current_hash,
        }

    for relative in obsolete_files:
        destination = target / relative
        previous = old_files.get(relative)
        if not destination.exists():
            continue
        current_hash = sha256_bytes(destination.read_bytes())
        if isinstance(previous, dict) and current_hash == previous.get("installedHash"):
            removed.append(relative)
            if not args.check:
                destination.unlink()
        else:
            conflicts.append(relative)

    print(f"created: {len(created)}")
    for path in created:
        print(f"  + {path}")
    print(f"updated: {len(updated)}")
    for path in updated:
        print(f"  ~ {path}")
    print(f"unchanged: {len(unchanged)}")
    print(f"conflicts: {len(conflicts)}")
    for path in conflicts:
        detail = conflict_details.get(path)
        print(f"  ! {path}" + (f": {detail}" if detail else ""))
    print(f"removed obsolete managed files: {len(removed)}")
    for path in removed:
        print(f"  - {path}")

    if conflicts:
        print("Resolve conflicts explicitly; no conflicted file was overwritten.", file=sys.stderr)
        return 2

    if args.check:
        if created or updated or removed:
            return 1
        if web_profile == "spa-pkce" and spa_configuration is not None:
            spa_profile.verify_outputs(target, spa_configuration)
        return 0

    if web_profile == "spa-pkce" and spa_configuration is not None:
        spa_profile.verify_outputs(target, spa_configuration)

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "programKitVersion": extension_version(extension_root),
                "dotnetSdk": dotnet_sdk,
                "dotnetSdkSource": dotnet_sdk_source,
                "webProfile": web_profile,
                "webProfileContract": f"{web_profile}-v1",
                "webThreatModel": (
                    "program-kit-web-threat-model-v1" if web_profile != "none" else "none"
                ),
                "webSecurityEvidence": (
                    "program-kit-web-security-evidence-v1" if web_profile != "none" else "none"
                ),
                "persistenceProfile": args.persistence_profile,
                "files": next_files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

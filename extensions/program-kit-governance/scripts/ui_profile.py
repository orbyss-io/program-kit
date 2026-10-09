"""Deterministic, consumer-safe UI profile scaffolding and generation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

from ui_content import discovery, document, gallery, head
from ui_contracts import public, validate
from ui_tokens import LAYERS, compile_tokens
from ui_svg import icons, sanitize_svg
from ui_patterns import AUTH_STATES, auth_contract, auth_document, feedback_patterns, form_pattern, list_detail

TEMPLATES = Path(__file__).resolve().parents[1] / "templates/ui-experience"
SOURCE = ".program-kit/ui"
OUTPUT = "web/generated/program-kit"
STATE = f"{SOURCE}/outputs.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def safe_path(root: Path, relative: str) -> Path:
    """Resolve only literal repository-relative paths, rejecting linked ancestors and escapes."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
        raise ValueError("Unsafe generated path")
    candidate = root
    for part in path.parts:
        candidate = candidate / part
        if candidate.is_symlink() or candidate.is_junction():
            raise ValueError(f"Linked generation path is forbidden: {relative}")
    candidate.resolve().relative_to(root.resolve())
    return candidate


def read_json(path: Path) -> dict:
    def unique(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    result = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    return result


def explain(profile: dict, content: dict) -> dict:
    """Read-only view derived from existing inputs, not another decision register."""
    starter = read_json(TEMPLATES / 'profile.json')
    values = {
        'globalLayout': {'archetype': profile['archetype'], 'navigation': profile['navigation']},
        'pageLayout': {page['id']: page.get('layout', 'content') for page in content['pages']},
        'branding': profile['brand'],
        'theme': {'scheme': profile['scheme'], 'density': profile['density']},
        'components': {'presentation': profile.get('presentation', 'classic-v1')},
        'feedbackAndRecovery': 'field, operation and page; adapter-owned semantics',
        'motion': {'style': profile['motion'], 'reducedMotion': 'honor user preference'},
        'icons': profile['brand'].get('icons', {'bundle': 'lucide'}),
        'implementation': {'css': profile['css'], 'frontend': 'existing accepted consumer frontend'},
        'authentication': auth_contract() if profile.get('presentation') == 'modern-product-v1' else 'existing identity-theme bridge',
    }
    return {'profile': profile['profile'], 'presentation': profile.get('presentation', 'classic-v1'),
            'values': values, 'inputPaths': [f'{SOURCE}/profile.json', f'{SOURCE}/content.json'],
            'decisionProvenance': 'Read the existing bootstrap-decisions.json/project intent; matching a default does not prove human preference.',
            'matchesStarterDefault': {key: profile.get(key) == starter.get(key) for key in ('presentation', 'archetype', 'navigation', 'density', 'scheme', 'motion', 'css')},
            'generatedPaths': {'assets': f'{OUTPUT}/public/assets', 'integration': f'{OUTPUT}/integration', 'acceptance': f'{OUTPUT}/acceptance'},
            'override': 'Edit consumer inputs or the consumer CSS layer; build then check. Init never replaces inputs.',
            'adapters': {'native': 'reference renderer, deterministic/browser fixture coverage',
                         'tailwind': 'pinned semantic-token bridge and compiled browser comparison',
                         'existing-system': 'consumer-owned mapping; consumer acceptance required',
                         'Material or Bootstrap': 'design/component choices, no shipped dedicated adapter',
                         'Keycloak': 'inherited theme scaffold; real selected-provider acceptance required'},
            'phase': {'intake': 'experience intent and consequential recovery behavior',
                      'planning': 'affected compositions, field rules, states, error mapping and identity screen owners',
                      'implementation': 'focused changed state/journey tests',
                      'handoff': 'affected feature acceptance and human visual review'},
            'knowledge': ['ui-design-model.md', 'ui-feedback-and-recovery.md', 'ui-experience-v1.md', 'ui-evidence-v1.json']}


def outputs(profile: dict, content: dict) -> dict[str, bytes]:
    validate(profile, content)
    generated: dict[str, bytes] = {}
    resources = []
    def add_resource(route: str, file: str, text: str, kind: str, index: bool = False) -> None:
        data = text.encode("utf-8")
        generated[f"{OUTPUT}/public/{file}"] = data
        resources.append({"route": route, "file": "public/" + file, "contentType": kind,
                          "sha256": digest(data), "index": index, "visibility": "public"})
    tokens = compile_tokens(profile)
    analytics = profile.get("analytics", {"provider": "none"})
    generated[f"{OUTPUT}/integration/analytics.json"] = encoded({**analytics,
        "pages": [p["id"] for p in content["pages"] if public(p)] if analytics["provider"] != "none" else [],
        "events": analytics.get("events", []), "transportOwner": "consumer", "consentMode": "basic",
        "automaticActivation": False})
    if "svg" in profile["brand"].get("logo", {}):
        add_resource("/assets/brand-logo.svg", "assets/brand-logo.svg", sanitize_svg(profile["brand"]["logo"]["svg"], "pk-logo"), "image/svg+xml")
    icon_assets = icons(profile)
    for name, source in icon_assets.items():
        add_resource(f"/assets/icons/{name}.svg", f"assets/icons/{name}.svg", source, "image/svg+xml")
    selected_icons = profile["brand"].get("icons", {"bundle": "lucide"})
    if selected_icons["bundle"] != "none":
        license_text = (TEMPLATES / "icons/LICENSE.txt").read_text(encoding="utf-8") if selected_icons["bundle"] == "lucide" else selected_icons["license"] + "\nSource: " + selected_icons["source"]
        add_resource("/assets/icons/LICENSE.txt", "assets/icons/LICENSE.txt", license_text, "text/plain; charset=utf-8")
    for name in ("tokens.css",):
        add_resource("/assets/" + name, "assets/" + name, tokens.pop(name), "text/css; charset=utf-8")
    for name in ("layout.css", "interactions.mjs", "analytics.mjs"):
        source = 'layout-classic.css' if name == 'layout.css' and profile.get('presentation', 'classic-v1') == 'classic-v1' else name
        text = (TEMPLATES / source).read_text(encoding="utf-8")
        kind = "text/css; charset=utf-8" if name.endswith("css") else "text/javascript; charset=utf-8"
        add_resource("/assets/" + name, "assets/" + name, text, kind)
    for name, text in tokens.items():
        generated[f"{OUTPUT}/integration/{name}"] = text.encode("utf-8")
    if profile.get('presentation', 'classic-v1') == 'modern-product-v1':
        for name, text in {'form': form_pattern(), 'list-detail': list_detail(), 'feedback': feedback_patterns()}.items():
            generated[f'{OUTPUT}/integration/patterns/{name}.html'] = text.encode('utf-8')
        for state in AUTH_STATES:
            generated[f'{OUTPUT}/integration/auth/{state}.html'] = auth_document(profile, state).encode('utf-8')
        generated[f'{OUTPUT}/integration/auth/contract.json'] = encoded(auth_contract())
        generated[f'{OUTPUT}/integration/design-map.json'] = encoded(explain(profile, content))
        # Inherit provider behavior; the consumer adapter applies accepted screen styling.
        theme = f'{OUTPUT}/integration/auth/keycloak/login'
        generated[f'{theme}/theme.properties'] = b'parent=keycloak\nimport=common/keycloak\nstyles=css/login.css css/program-kit-brand.css\n'
        generated[f'{theme}/resources/css/program-kit-brand.css'] = tokens['keycloak-brand.css'].encode('utf-8')
        if 'svg' in profile['brand'].get('logo', {}):
            generated[f'{theme}/resources/img/brand-logo.svg'] = sanitize_svg(profile['brand']['logo']['svg'], 'pk-auth-logo').encode('utf-8')
    for page in content["pages"]:
        if not public(page):
            continue
        file = (page["path"].strip("/") + "/" if page["path"] != "/" else "") + "index.html"
        add_resource(page["path"], file, document(page, content, profile), "text/html; charset=utf-8", page["index"])
        generated[f"{OUTPUT}/integration/heads/{page['id']}.html"] = head(page, content, profile).encode("utf-8")
    for name, text in discovery(content, profile).items():
        kind = "application/xml; charset=utf-8" if name.endswith("xml") else "text/markdown; charset=utf-8" if name.endswith("md") or name == "llms.txt" else "text/plain; charset=utf-8"
        add_resource("/" + name, name, text, kind)
    # Gallery is local acceptance evidence, deliberately outside the public deployment tree.
    generated[f"{OUTPUT}/acceptance/gallery.html"] = gallery(profile).encode("utf-8")
    for archetype in ("journey", "product-shell", "workspace", "content-hub", "showcase"):
        example = copy.deepcopy(profile)
        example["archetype"] = archetype
        generated[f"{OUTPUT}/acceptance/archetypes/{archetype}.html"] = gallery(example).encode("utf-8")
    for source in sorted((TEMPLATES / "acceptance").iterdir()):
        if source.is_file() and source.name in {"package.json", "package-lock.json", ".npmrc", "analytics.test.mjs", "browser.mjs"}:
            generated[f"{OUTPUT}/acceptance/tests/{source.name}"] = source.read_bytes()
    tailwind_profile = {**profile, "css": "tailwind"}
    generated[f"{OUTPUT}/acceptance/tests/tailwind-theme.css"] = compile_tokens(tailwind_profile)["tailwind.css"].encode("utf-8")
    generated[f"{OUTPUT}/acceptance/tests/tailwind-input.css"] = (LAYERS + '@import "tailwindcss" source(none);\n@import "../../public/assets/tokens.css";\n@import "./tailwind-theme.css";\n@source inline("bg-primary text-on-primary rounded-brand font-sans");\n').encode("utf-8")
    generated[f"{OUTPUT}/publication.json"] = encoded({"version": "1.0", "resources": sorted(resources, key=lambda r: r["route"])})
    sizes = {"cssBytes": sum(len(data) for path, data in generated.items() if "/public/" in path and path.endswith(".css")),
             "jsBytes": sum(len(data) for path, data in generated.items() if "/public/" in path and path.endswith(".mjs")),
             "htmlBytes": max((len(data) for path, data in generated.items() if "/public/" in path and path.endswith(".html")), default=0)}
    for name, size in sizes.items():
        if size > profile["budgets"][name]:
            raise ValueError(f"Asset budget {name} exceeded: {size} > {profile['budgets'][name]}")
    generated[f"{OUTPUT}/acceptance/report.json"] = encoded({"profile": profile["profile"], "assetBytes": sizes,
        "presentation": profile.get('presentation', 'classic-v1'),
        "publicPages": sum(public(p) for p in content["pages"]), "privatePagesExcluded": sum(not public(p) for p in content["pages"]),
        "manualAcceptanceRequired": ["screen-reader and keyboard user journey", "actual branding and translations", "deployment authentication/CSP/WAF", "field Core Web Vitals where applicable"],
        "claims": "Generation and contract checks only; not WCAG conformance, search ranking or universal AI comprehension."})
    return generated


def synchronize(root: Path, expected: dict[str, bytes], check: bool) -> dict:
    state_path = safe_path(root, STATE)
    previous = read_json(state_path) if state_path.exists() else {"version": "1.0", "files": {}}
    if set(previous) != {"version", "files"} or previous["version"] != "1.0" or not isinstance(previous["files"], dict):
        raise ValueError("Invalid UI generation state")
    known = previous["files"]
    public_root = safe_path(root, OUTPUT + "/public")
    if public_root.exists():
        for candidate in public_root.rglob("*"):
            relative = candidate.relative_to(root).as_posix()
            safe_path(root, relative)
            if candidate.is_file() and relative not in expected and relative not in known:
                raise ValueError("Unowned public artifact could leak or drift: " + relative)
    for path, value in known.items():
        if not path.startswith(OUTPUT + "/") or not isinstance(value, str) or len(value) != 64:
            raise ValueError("Generation state contains an invalid owned file")
        safe_path(root, path)
    conflicts, changed = [], []
    for name in sorted(set(known) | set(expected)):
        destination = safe_path(root, name)
        if destination.exists() and not destination.is_file():
            raise ValueError(f"Expected a generated file: {name}")
        actual = destination.read_bytes() if destination.exists() else None
        wanted = expected.get(name)
        if actual != wanted:
            changed.append(name)
            if actual is not None and digest(actual) != known.get(name):
                conflicts.append(name)
    if conflicts:
        raise ValueError("Consumer edits conflict with generation; preserve/relocate them explicitly: " + ", ".join(conflicts))
    next_state = {"version": "1.0", "files": {name: digest(data) for name, data in sorted(expected.items())}}
    if check and (changed or previous != next_state):
        raise ValueError("Generated UI drift: run build and review outputs: " + ", ".join(changed))
    if not check:
        for name in changed:
            destination = safe_path(root, name)
            if name not in expected:
                destination.unlink()  # Only a previously owned, hash-matching generated file.
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(expected[name])
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_bytes(encoded(next_state))
    return {"files": len(expected), "changed": len(changed), "checked": check}


def execute(root: Path, command: str) -> dict:
    if command == "init":
        targets = {name: safe_path(root, f"{SOURCE}/{name}.json") for name in ("profile", "content")}
        # Preflight every target before creating anything.
        if any(path.exists() for path in targets.values()):
            raise ValueError("UI sources already exist; init never overwrites consumer inputs")
        for name, path in targets.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((TEMPLATES / f"{name}.json").read_bytes())
        return {"created": [str(path.relative_to(root)) for path in targets.values()]}
    profile = read_json(safe_path(root, f"{SOURCE}/profile.json"))
    content = read_json(safe_path(root, f"{SOURCE}/content.json"))
    if command == 'explain':
        validate(profile, content)
        return explain(profile, content)
    expected = outputs(profile, content)
    if command == "validate":
        return {"valid": True, "files": len(expected)}
    return synchronize(root, expected, command == "check")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "validate", "build", "check", "explain"))
    parser.add_argument("--target", default=".")
    args = parser.parse_args()
    try:
        print(json.dumps(execute(Path(args.target).resolve(), args.command)))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"PKUI001 {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

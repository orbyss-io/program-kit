"""Optional native toolkit refresh. Product authoring and application migration are separate."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

from product_version import parse, order

COMPONENTS = (("extensions", "program-kit-governance"), ("extensions", "program-kit-building-blocks"),
              ("extensions", "program-kit-dotnet"), ("presets", "program-kit-governance-preset"))
REONBOARD = ("PKU160 0.x to 1.0 preview requires deliberate re-onboarding in a fresh checkout. "
    "Keep the original repository and authored architecture, ADRs, specifications, application files and locks. "
    "Use those documents as intake inputs; no workflow state or approval authority is migrated. No files changed.")

class UpgradeError(ValueError):
    pass


def require(value, message):
    if not value:
        raise UpgradeError(message)


def manifest_version(path, label="component"):
    require(path.is_file(), "PKU101 missing " + label + ": " + str(path))
    match = re.search(r"^\s{2}version:\s*[\"']?([^\"'#\s]+)", path.read_text(encoding="utf-8"), re.M)
    require(match is not None, "PKU101 version missing from " + str(path))
    parse(match[1])
    return match[1]


def validate_release(release):
    version = (release / "VERSION").read_text(encoding="utf-8").strip()
    parse(version)
    require(manifest_version(release / "bundle.yml") == version, "PKU102 bundle version differs")
    for kind, identity in COMPONENTS:
        filename = "extension.yml" if kind == "extensions" else "preset.yml"
        require(manifest_version(release / kind / identity / filename) == version, "PKU102 component version differs: " + identity)
    return version


def contained(root, relative):
    path = root / relative
    require(not Path(relative).is_absolute() and path.resolve().is_relative_to(root), "PKU161 path escapes consumer")
    for item in (path, *path.parents):
        require(not item.is_symlink() and not getattr(item, "is_junction", lambda: False)(),
                "PKU161 aliased toolkit/input/output path requires owner reconciliation: " + str(item))
        if item == root:
            break
    return path


def source_files(directory):
    result = {}
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        require(not path.is_symlink() and not getattr(path, "is_junction", lambda: False)(), "PKU161 aliased component source")
        if path.is_file() and not {"__pycache__", ".dev-cache", ".composed"}.intersection(relative.parts):
            if len(relative.parts) == 1 and path.name.endswith(("-config.yml", "-config.local.yml")):
                continue  # Native configuration preservation owns these consumer files.
            result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight(target, release, previous):
    target, release = target.resolve(strict=True), release.resolve(strict=True)
    version = validate_release(release)
    installed = manifest_version(contained(target, ".specify/extensions/program-kit-governance/extension.yml"))
    require(parse(installed)[0] != 0, REONBOARD)
    require(previous is not None, "PKU161 supply --previous-release-root with the exact previous preview package sources; authored work is untouched")
    previous = previous.resolve(strict=True)
    require(validate_release(previous) == installed, "PKU161 previous release source differs from installed toolkit")
    require(order(version) >= order(installed), "PKU161 toolkit downgrade requires explicit owner reconciliation")
    record = json.loads(contained(target, ".specify/bundle-records.json").read_text(encoding="utf-8"))
    require(any(row.get("bundle_id") == "program-kit" for row in record.get("bundles", [])), "PKU161 missing native bundle ownership")
    for kind, identity in COMPONENTS:
        actual = contained(target, ".specify/" + kind + "/" + identity)
        require(source_files(actual) == source_files(previous / kind / identity),
                "PKU161 installed toolkit is customized or incomplete; preserve and reconcile: " + identity)
    # Native generation records protect rendered commands independently of their source.
    render = load_module(release / "extensions/program-kit-governance/scripts/render_profile.py", "preview_native_render")
    reader = render.Reader(target)
    require(reader.records, "PKU161 native output ownership is unknown; preserve customized outputs for owner reconciliation")
    outputs = {}
    for row in reader.records:
        for relative, digest in row["outputs"].items():
            outputs.setdefault(relative, digest)
    for relative, expected in outputs.items():
        path = contained(target, relative)
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                "PKU161 customized/missing native output; preserve and reconcile: " + relative)
    state = json.loads(contained(target, ".specify/integration.json").read_text(encoding="utf-8"))
    integration = state.get("default_integration") or state.get("integration")
    keys = state.get("installed_integrations", [integration])
    require(keys == [integration] and isinstance(integration, str),
            "PKU161 multiple/unknown native integrations require explicit native-owner refresh; no files changed")
    return {"fromVersion": installed, "toVersion": version, "integration": integration,
            "action": "refresh native toolkit only; preserve authored work and native dependency locks",
            "applicationMigrationPerformed": False, "productAcceptanceEstablished": False}


def refresh(target, release, previous, *, plan_only=False):
    target, release = target.resolve(strict=True), release.resolve(strict=True)
    plan = preflight(target, release, previous)
    if plan_only:
        return plan
    lock = contained(target, '.specify/program-kit-refresh.lock')
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise UpgradeError('PKU161 another toolkit refresh owns this checkout; preserve the lock and reconcile its owner before retry') from error
    os.close(descriptor)  # Presence is the claim; avoid an open handle across Windows rollback.
    try:
        # Admission must still hold after claiming this mutation, not just when
        # an earlier plan happened to be printed.
        plan = preflight(target, release, previous)
        return _refresh(target, release, plan)
    finally:
        lock.unlink()


def _refresh(target, release, plan):
    from specify_cli._assets import get_speckit_version
    from specify_cli.agents import CommandRegistrar
    from specify_cli import _get_skills_dir
    from specify_cli.presets import PresetManager
    # The updater's own selected device prerequisites never install software.
    policy = load_module(release / "extensions/program-kit-governance/scripts/program_kit_runtime/device_toolchain.py", "preview_devices")
    policy.contributor(target, python_only=True, exact_specify=False)
    registrar = CommandRegistrar(target)
    integration = plan["integration"]
    directories = {contained(target, ".specify"),
        _get_skills_dir(target, integration),
        registrar._resolve_agent_dir(integration, registrar.AGENT_CONFIGS[integration], target)}
    directories = sorted({contained(target, path.relative_to(target)) for path in directories}, key=lambda path: len(path.parts))
    directories = [path for i, path in enumerate(directories) if not any(path.is_relative_to(parent) for parent in directories[:i])]
    for directory in directories:
        if directory.exists():
            require(not any(path.is_symlink() or getattr(path, "is_junction", lambda: False)() for path in directory.rglob("*")),
                    "PKU161 aliased native output tree requires owner reconciliation")
    # A bounded local rollback protects native toolkit mutations. No authoring state is translated.
    with tempfile.TemporaryDirectory(prefix="program-kit-preview-refresh-") as temporary:
        backup = Path(temporary)
        existed = []
        for i, directory in enumerate(directories):
            existed.append(directory.exists())
            if directory.exists():
                shutil.copytree(directory, backup / str(i))
        try:
            installer = load_module(release / "scripts/install_local_extension.py", "preview_extension_copy")
            for kind, identity in COMPONENTS:
                if kind == "extensions":
                    installer.install(target, release / kind / identity, identity, force=True)
            render = load_module(release / "extensions/program-kit-governance/scripts/render_profile.py", "preview_render_capture")
            with render.capture(target, ["preset", "add"]):
                PresetManager(target).install_from_directory(release / "presets/program-kit-governance-preset", get_speckit_version(), force=True)
            bundles = load_module(release / 'scripts/record_local_bundle.py', 'preview_native_bundle')
            bundles.seal(target, release, integration)
        except BaseException:
            for i, directory in enumerate(directories):
                contained(target, directory.relative_to(target))
                if directory.exists():
                    shutil.rmtree(directory)
                if existed[i]:
                    shutil.copytree(backup / str(i), directory)
            raise
    return {**plan, "status": "native-toolkit-refreshed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--release-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--previous-release-root", type=Path)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(refresh(args.target, args.release_root, args.previous_release_root, plan_only=args.plan), indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

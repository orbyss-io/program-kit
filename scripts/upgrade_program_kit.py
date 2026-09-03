from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


COMPONENTS = (
    ("bundle", Path("bundle.yml")),
    ("governance extension", Path("extensions/program-kit-governance/extension.yml")),
    (".NET extension", Path("extensions/program-kit-dotnet/extension.yml")),
    ("governance preset", Path("presets/program-kit-governance-preset/preset.yml")),
    ("bootstrap workflow", Path("workflows/program-kit-bootstrap/workflow.yml")),
)


class UpgradeError(ValueError):
    pass


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def manifest_version(path: Path, label: str) -> str:
    if not path.is_file():
        raise UpgradeError(f"PKU101 {label} is missing: {path}")
    match = re.search(
        r"^\s{2}version:\s*[\"']?([^\"'#\s]+)",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise UpgradeError(f"PKU101 {label} has no version: {path}")
    return match.group(1)


def validate_release(release: Path) -> str:
    version_path = release / "VERSION"
    if not version_path.is_file():
        raise UpgradeError(f"PKU101 release VERSION is missing: {version_path}")
    expected = version_path.read_text(encoding="utf-8").strip()
    if not expected:
        raise UpgradeError("PKU101 release VERSION is empty")
    versions = {
        label: manifest_version(release / relative, label)
        for label, relative in COMPONENTS
    }
    mismatches = {label: version for label, version in versions.items() if version != expected}
    if mismatches:
        details = ", ".join(f"{label}={version}" for label, version in mismatches.items())
        raise UpgradeError(
            f"PKU102 release source is version-incoherent; VERSION={expected}, {details}"
        )
    return expected


def load_managed_profile(target: Path) -> tuple[str, str] | None:
    path = target / ".program-kit/managed.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU103 cannot read managed baseline state {path}: {error}") from error
    web = value.get("webProfile")
    persistence = value.get("persistenceProfile")
    if web not in {"none", "bff-cookie", "spa-pkce"} or persistence not in {
        "none", "ef-postgresql", "ef-sqlserver", "ef-sqlite",
    }:
        raise UpgradeError(
            "PKU103 existing managed baseline does not record supported web and persistence profiles"
        )
    return str(web), str(persistence)


def selected_integration(target: Path, requested: str) -> str:
    if requested != "auto":
        candidate = requested
    else:
        path = target / ".specify/integration.json"
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UpgradeError(f"PKU104 cannot resolve integration from {path}: {error}") from error
        candidate = state.get("default_integration") or state.get("integration")
    if not isinstance(candidate, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", candidate):
        raise UpgradeError(f"PKU104 unsupported integration identity: {candidate!r}")
    return candidate


def require_existing_bundle(target: Path) -> None:
    path = target / ".specify/bundle-records.json"
    try:
        records = json.loads(path.read_text(encoding="utf-8")).get("bundles")
    except (OSError, json.JSONDecodeError) as error:
        raise UpgradeError(f"PKU109 cannot read existing bundle records {path}: {error}") from error
    if not any(
        isinstance(record, dict) and record.get("bundle_id") == "program-kit"
        for record in records or []
    ):
        raise UpgradeError(
            "PKU109 target has no existing Program Kit bundle record; use Initialize-ProgramKit for a fresh install"
        )


def current_version(target: Path) -> str:
    manifest = target / ".specify/extensions/program-kit-governance/extension.yml"
    return manifest_version(manifest, "installed Program Kit Governance extension")


def run_step(command: list[str], target: Path, label: str, number: int, total: int) -> None:
    print(f"[{number}/{total}] {label}")
    result = subprocess.run(command, cwd=target, check=False)
    if result.returncode != 0:
        raise UpgradeError(
            f"PKU105 {label} failed with exit code {result.returncode}; "
            "the Program Kit installation must not be used until validate-installation passes"
        )


def acquire_lock(target: Path) -> tuple[int, Path]:
    path = target / ".specify/program-kit-upgrade.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise UpgradeError(
            f"PKU106 another Program Kit component mutation may be active: {path}"
        ) from error
    os.write(descriptor, f"pid={os.getpid()}\n".encode("utf-8"))
    return descriptor, path


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(
        description="Upgrade every Program Kit component sequentially from one local release."
    )
    parser.add_argument("--release-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--target", default=".")
    parser.add_argument("--integration", default="auto")
    parser.add_argument("--specify-command", default="specify", help=argparse.SUPPRESS)
    args = parser.parse_args()
    descriptor: int | None = None
    lock_path: Path | None = None
    try:
        release = Path(args.release_root).resolve()
        target = Path(args.target).resolve()
        version = validate_release(release)
        if not (target / ".specify").is_dir():
            raise UpgradeError(f"PKU107 target is not an initialized Spec Kit project: {target}")
        require_existing_bundle(target)
        previous_version = current_version(target)
        profile = load_managed_profile(target)
        has_bootstrap_decisions = (target / "docs/architecture/bootstrap-decisions.json").is_file()
        integration = selected_integration(target, args.integration)
        specify = shutil.which(args.specify_command)
        if not specify:
            raise UpgradeError(f"PKU108 Spec Kit CLI is unavailable: {args.specify_command}")
        descriptor, lock_path = acquire_lock(target)
        steps = [
            ([specify, "bundle", "install", str(release / "bundle.yml"), "--offline", "--integration", integration], "Resolve bundle composition record"),
            ([specify, "workflow", "add", str(release / "workflows/program-kit-bootstrap"), "--dev"], "Install bootstrap workflow"),
            ([specify, "extension", "add", str(release / "extensions/program-kit-governance"), "--dev", "--force"], "Install governance extension"),
            ([specify, "extension", "add", str(release / "extensions/program-kit-dotnet"), "--dev", "--force"], "Install .NET extension"),
            ([specify, "preset", "remove", "program-kit-governance-preset"], "Remove prior governance preset"),
            ([specify, "preset", "add", "--dev", str(release / "presets/program-kit-governance-preset")], "Install governance preset"),
        ]
        total = len(steps) + (2 if profile else 0) + 1 + (1 if has_bootstrap_decisions else 0)
        for number, (command, label) in enumerate(steps, 1):
            run_step(command, target, label, number, total)
        next_step = len(steps) + 1
        if profile:
            web, persistence = profile
            sync = target / ".specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py"
            write = [
                sys.executable, str(sync), "--target", str(target), "--profile-selected",
                "--host-runtime-accepted", "--preview-sources-approved",
                "--persistence-profile", persistence, "--web-profile", web,
            ]
            check = [
                sys.executable, str(sync), "--target", str(target), "--profile-selected",
                "--persistence-profile", persistence, "--web-profile", web, "--check",
            ]
            run_step(write, target, "Resynchronize managed .NET baseline", next_step, total)
            run_step(check, target, "Verify managed .NET baseline convergence", next_step + 1, total)
            next_step += 2
        validator = target / ".specify/extensions/program-kit-governance/scripts/governance_state.py"
        run_step(
            [sys.executable, str(validator), "validate-installation"],
            target,
            "Validate cross-component version coherence",
            next_step,
            total,
        )
        if has_bootstrap_decisions:
            run_step(
                [
                    sys.executable, str(validator), "record-upgrade",
                    "--previous-version", previous_version,
                    "--target-version", version,
                ],
                target,
                "Record accepted governed upgrade",
                next_step + 1,
                total,
            )
        print(
            f"Program Kit v{version} upgrade completed: workflow, extensions, preset, bundle record, "
            "managed baseline, and governed version authority are coherent."
        )
        return 0
    except (OSError, UpgradeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if lock_path is not None:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())

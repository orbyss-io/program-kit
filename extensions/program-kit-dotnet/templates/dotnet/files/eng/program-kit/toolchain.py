from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def required_versions(repository: Path) -> dict[str, str]:
    global_json = json.loads((repository / "global.json").read_text(encoding="utf-8"))
    dotnet = global_json.get("sdk", {}).get("version")
    node = (repository / ".nvmrc").read_text(encoding="utf-8").strip().removeprefix("v")
    if not isinstance(dotnet, str) or not dotnet or not node:
        raise ValueError("PKT001 managed global.json or .nvmrc has no exact toolchain version.")
    return {"dotnet": dotnet, "node": node}


def run_version(command: list[str]) -> str | None:
    if shutil.which(command[0]) is None:
        return None
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
    if result.returncode != 0:
        return None
    return result.stdout.strip().splitlines()[0].removeprefix("v")


def installed_versions(dotnet_command: str = "dotnet", node_command: str = "node") -> dict[str, str | None]:
    return {
        "dotnet": run_version([dotnet_command, "--version"]),
        "node": run_version([node_command, "--version"]),
    }


def write_evidence(path: Path | None, required: dict, installed: dict, resolved: bool) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"schemaVersion": 1, "required": required, "resolved": installed, "satisfied": resolved},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def mismatch(required: dict[str, str], installed: dict[str, str | None]) -> list[str]:
    return [name for name, version in required.items() if installed.get(name) != version]


def install_dotnet(version: str, installer: str) -> None:
    if not installer:
        raise ValueError(
            "PKT004 no approved .NET installer is available. Obtain Microsoft's dotnet-install script, "
            "review it, and pass --dotnet-installer; Program Kit will use side-by-side installation."
        )
    path = Path(installer).resolve()
    if not path.is_file():
        raise ValueError(f"PKT005 .NET installer is unavailable: {path}")
    if path.suffix.lower() == ".ps1":
        command = ["powershell", "-NoProfile", "-File", str(path), "-Version", version]
    else:
        command = [str(path), "--version", version]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise ValueError("PKT006 approved .NET side-by-side installation failed (offline or installer error).")


def node_manager(selected: str) -> str | None:
    names = [selected] if selected != "auto" else ["fnm", "nvm", "volta"]
    return next((name for name in names if shutil.which(name)), None)


def install_node(version: str, selected: str) -> None:
    manager = node_manager(selected)
    if manager is None:
        raise ValueError(
            "PKT007 no selected Node version manager is available. Install or select fnm, nvm, or volta; "
            "Program Kit does not replace the user's manager."
        )
    command = [manager, "install", version if manager != "volta" else f"node@{version}"]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise ValueError("PKT008 approved Node installation failed (offline or manager error).")


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(description="Check and approval-gate Program Kit toolchain remediation.")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--evidence", default=".program-kit/evidence/toolchain.json")
    parser.add_argument("--remediate", action="store_true")
    parser.add_argument("--approve", action="store_true", help="Explicit non-interactive approval for system/network changes")
    parser.add_argument("--decline", action="store_true")
    parser.add_argument("--dotnet-installer", default="")
    parser.add_argument("--node-manager", choices=("auto", "fnm", "nvm", "volta"), default="auto")
    parser.add_argument("--dotnet-command", default="dotnet", help=argparse.SUPPRESS)
    parser.add_argument("--node-command", default="node", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        repository = Path(args.repository).resolve()
        evidence = Path(args.evidence)
        if not evidence.is_absolute():
            evidence = repository / evidence
        required = required_versions(repository)
        installed = installed_versions(args.dotnet_command, args.node_command)
        missing = mismatch(required, installed)
        if not missing:
            write_evidence(evidence, required, installed, True)
            print("PKT000 exact managed toolchain versions are satisfied")
            return 0
        print(
            "PKT002 toolchain mismatch: "
            + ", ".join(f"{name} required={required[name]} resolved={installed[name] or 'missing'}" for name in missing),
            file=sys.stderr,
        )
        write_evidence(evidence, required, installed, False)
        if not args.remediate:
            print("Repository writes: evidence only. Proposed system changes and network downloads require approval.", file=sys.stderr)
            return 2
        if args.decline:
            print("PKT003 remediation declined; no installer was run.", file=sys.stderr)
            return 3
        approved = args.approve
        if not approved:
            approved = input("Install the exact missing SDK/Node versions side-by-side? [y/N] ").strip().lower() == "y"
        if not approved:
            print("PKT003 remediation declined; no installer was run.", file=sys.stderr)
            return 3
        if "dotnet" in missing:
            install_dotnet(required["dotnet"], args.dotnet_installer)
        if "node" in missing:
            install_node(required["node"], args.node_manager)
        resolved = installed_versions(args.dotnet_command, args.node_command)
        remaining = mismatch(required, resolved)
        write_evidence(evidence, required, resolved, not remaining)
        if remaining:
            raise ValueError("PKT009 installation completed, but exact version checks still fail: " + ", ".join(remaining))
        print("PKT010 approved toolchain remediation completed and was re-verified")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())

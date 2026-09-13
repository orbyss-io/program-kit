"""Plan and execute offline repository setup through ordered, reviewable adapters."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import shutil
from contextlib import contextmanager
from pathlib import Path

import package_execution
import sync_readiness
from lifecycle_state import lifecycle_sha256


PHASES = ("bootstrap", "planning", "after-plan", "implementation-setup", "implementation", "upgrade")


def load(path: Path, default=None):
    if not path.is_file() and default is not None:
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def write(path: Path, value: dict) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if path.is_file() and path.read_bytes() == payload:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def contained(repository: Path, relative: str) -> Path:
    path = (repository / relative).resolve()
    if not path.is_relative_to(repository.resolve()):
        raise ValueError(f"PKS001 setup path escapes repository: {relative}")
    return path


def provider(name: str):
    path = package_execution.extension_root() / name
    spec = importlib.util.spec_from_file_location("sync_" + path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"PKS001 adapter is unavailable: {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(repository: Path, command: list[str], allowed=(0,)) -> subprocess.CompletedProcess:
    result = subprocess.run(command, cwd=repository, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    if result.returncode not in allowed:
        raise ValueError(f"PKS002 adapter failed ({result.returncode}): {result.stdout.strip()} {result.stderr.strip()}")
    return result


def version() -> str:
    manifest = Path(__file__).resolve().parents[1] / "extension.yml"
    match = re.search(r'^\s{2}version:\s*"([^"]+)"', manifest.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise ValueError("PKS001 coordinator manifest has no version")
    return match.group(1)


def context(repository: Path, phase: str, feature: str | None) -> dict:
    if feature is None:
        feature = load(repository / ".specify/feature.json", {}).get("feature_directory")
    if feature:
        feature = contained(repository, feature).relative_to(repository).as_posix()
    decisions = load(repository / "docs/architecture/bootstrap-decisions.json", {})
    managed = load(repository / ".program-kit/managed.json", {})
    selected = decisions.get("selected_profiles", [])
    dotnet = bool(managed) or ("dotnet" in selected and phase != "upgrade")
    if dotnet and phase != "upgrade" and decisions.get("dotnet", {}).get("program_kit_host_opt_out") is True:
        raise ValueError("PKS003 the accepted host opt-out needs an alternative engineering adapter; Foundation scaffolding is not authorized")
    ownership = load(contained(repository, feature) / "artifact-ownership.json", {}) if feature else {}
    javascript = dotnet or bool(set(selected) & {"typescript-web", "typescript-vite", "browser-web"}) or "typescript-vite" in ownership.get("profiles", [])
    template = package_execution.extension_root() / "program-kit-dotnet/templates/dotnet/files"
    pins = {"node": (template / ".nvmrc").read_text().strip(), "npm": (template / ".npm-version").read_text().strip()} if javascript else {}
    toolchain = decisions.get("toolchain", {})
    if toolchain.get("source") == "override":
        overrides = {item.get("id") for item in decisions.get("overrides", []) if isinstance(item, dict)}
        if "managed-toolchain-version" not in overrides or not toolchain.get("override_reason", "").strip():
            raise ValueError("PKS003 toolchain override lacks approved rationale")
        pins.update({key: value for key, value in toolchain.get("pins", {}).items() if key in pins})
    if any(not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value) for value in pins.values()):
        raise ValueError("PKS003 setup needs exact approved toolchain versions")
    inputs = ["docs/architecture/bootstrap-decisions.json", "docs/architecture/architecture-map.json",
              "docs/architecture/building-block-selection.json", ".specify/governance/bootstrap-approval.json",
              ".specify/memory/constitution-ratification.json"]
    governance = provider('program-kit-governance/scripts/governance_state.py')
    configuration = [governance._load_configuration(contained(repository, path.as_posix()))
                     for path in (governance.CONFIGURATION, governance.LOCAL_CONFIGURATION)]
    for section, key, default in (('constitution','document',governance.CONSTITUTION),
                                  ('constitution','ratification',governance.RATIFICATION),
                                  ('architecture','decisions',governance.DECISIONS)):
        value = default.as_posix()
        for document in configuration:
            if isinstance(document.get(section), dict):
                value = document[section].get(key, value)
        configured = governance._configured_relative_path(value, f'{section}.{key}')
        inputs.append((configured / 'bootstrap-baseline.md').as_posix() if key == 'decisions' else configured.as_posix())
    inputs.extend(path.as_posix() for path in (governance.CONFIGURATION, governance.LOCAL_CONFIGURATION, governance.ASSESSMENT_APPROVAL))
    if feature:
        inputs.extend(f"{feature}/{name}" for name in ("spec.md", "plan.md", "artifact-ownership.json", "tasks.md"))
    web = managed.get("webProfile", "auto") if phase == "upgrade" else "auto"
    persistence = managed.get("persistenceProfile", "none")
    selection = load(repository / "docs/architecture/building-block-selection.json", {})
    targets = [{"id": item["id"], "path": item["path"], "kind": item["kind"],
                "state": "materialized" if contained(repository, item["path"]).is_file() else "planned"}
               for item in selection.get("targets", [])]
    return {"schemaVersion": 1, "programKitVersion": version(), "phase": phase, "feature": feature,
            "dotnet": dotnet, "javascript": javascript, "webProfile": web, "persistenceProfile": persistence,
            "toolchainPins": pins, "targets": targets,
            "authorityInputs": {relative: lifecycle_sha256(contained(repository, relative)) if contained(repository, relative).is_file() else None for relative in inputs},
            "providerInputs": provider_inputs()}


def provider_inputs() -> dict:
    root = package_execution.extension_root()
    result = {}
    for name in ('program-kit-governance', 'program-kit-dotnet', 'program-kit-building-blocks'):
        for path in sorted((root / name).rglob('*')):
            if path.is_file() and not set(path.relative_to(root).parts) & {'__pycache__', '.specify-dev', 'node_modules', '.git', 'bin', 'obj'} and path.suffix not in {'.pyc','.pyo'}:
                result[path.relative_to(root).as_posix()] = digest(path)
    return result


def dotnet_command(repository: Path, setup: dict) -> list[str]:
    return [sys.executable, str(package_execution.extension_root() / "program-kit-dotnet/scripts/dotnet_sync.py"),
            "--target", str(repository), "--profile-selected", "--web-profile", setup["webProfile"],
            "--persistence-profile", setup["persistenceProfile"]]


def toolchain_current(repository: Path, pins: dict) -> bool:
    evidence = load(repository / ".program-kit/evidence/toolchain.json", {})
    if evidence.get("satisfied") is not True or any(evidence.get("required", {}).get(key) != value for key, value in pins.items()):
        return False
    cache = evidence.get("environment", {}).get("npmCache")
    if not cache or not Path(cache).resolve().is_relative_to(repository.resolve()):
        return False
    runtime = package_execution.javascript_runtime()
    required = dict(pins)
    if (repository / "global.json").is_file():
        required["dotnet"] = load(repository / "global.json")["sdk"]["version"]
    environment = os.environ.copy()
    node = evidence.get("commands", {}).get("node", [])
    if node:
        environment["PATH"] = str(Path(node[0]).parent) + os.pathsep + environment.get("PATH", "")
    for key, expected in required.items():
        command = evidence.get("commands", {}).get(key)
        if not command or not Path(command[0]).is_file() or runtime.version(command, repository, environment) != expected:
            return False
    return True


def describe(repository: Path, phase: str, feature: str | None = None) -> dict:
    setup = context(repository, phase, feature)
    operations = []
    if setup["dotnet"] and phase != "bootstrap":
        result = run(repository, dotnet_command(repository, setup) + ["--check", "--json"], (0, 1))
        planned = json.loads(result.stdout)
        operations.append({"id": "engineering-baseline", "adapter": "dotnet", "plan": planned,
                           "required": result.returncode == 1, "network": False})
    if setup["javascript"] and phase not in {"bootstrap", "upgrade"}:
        evidence = repository / ".program-kit/evidence/toolchain.json"
        current = load(evidence, {})
        required = not toolchain_current(repository, setup["toolchainPins"])
        if setup["dotnet"]:
            expected_dotnet = load(repository / "global.json", {}).get("sdk", {}).get("version")
            required = required or not expected_dotnet or current.get("required", {}).get("dotnet") != expected_dotnet
        operations.append({"id": "toolchain", "adapter": "javascript", "pins": setup["toolchainPins"], "required": required, "network": False})
    selection = repository / "docs/architecture/building-block-selection.json"
    lock_path = repository / ".program-kit/building-blocks.lock.json"
    if selection.is_file() and phase in {"implementation-setup", "implementation", "upgrade"}:
        blocks = provider("program-kit-building-blocks/scripts/building_blocks.py")
        catalog = package_execution.extension_root() / "program-kit-building-blocks/references/orbyss-building-blocks.json"
        full = blocks.resolve(repository, selection, catalog, version())
        scoped = blocks.materialized_plan(repository, full)
        if scoped["targets"] and (phase != "upgrade" or lock_path.is_file()):
            operations.append({"id": "building-blocks", "adapter": "building-blocks", "plan": scoped,
                               "required": load(lock_path, {}) != scoped, "network": False})
    # Bind the reviewed plan to inputs and exact adapter plans. Readiness does not mean that a
    # planning-time candidate graph has already installed application dependencies.
    plan = {"schemaVersion": 1, "context": setup, "operations": operations,
            "deferredTargets": [item for item in setup["targets"] if item["state"] == "planned"],
            "packageNetwork": "explicit-separate-operation"}
    plan["planDigest"] = package_execution.canonical_hash(plan)
    return plan


def audit_toolchain(repository: Path, pins: dict) -> None:
    """Resolve only the toolchains required by this setup or compatibility scope."""
    runtime = package_execution.javascript_runtime()
    proof = {'schemaVersion': 2, 'required': dict(pins), 'resolved': {}, 'commands': {}, 'satisfied': True}
    if 'node' in pins or 'npm' in pins:
        if not all(key in pins for key in ('node', 'npm')):
            raise ValueError('PKS004 JavaScript requires both Node and npm pins')
        node, node_version = runtime.resolve_node(repository, pins['node'], 'node', 'auto')
        npm, npm_version = runtime.resolve_npm(repository, node, pins['npm'], '') if node else (None, None)
        cache = runtime.cache_directory(repository)
        _, trust, extra_ca = runtime.trust_environment(repository, cache)
        proof.update(resolved={'node': node_version, 'npm': npm_version},
                     commands={'node': [str(node)] if node else [], 'npm': npm or []},
                     environment={'npmCache': str(cache), 'trustMode': trust, 'extraCaCertificates': extra_ca, 'strictSsl': True},
                     satisfied=bool(node and npm))
    sdk = pins.get('dotnet') or (load(repository / 'global.json')['sdk']['version'] if (repository / 'global.json').is_file() else None)
    if sdk:
        executable = shutil.which('dotnet')
        command = [executable] if executable else []
        actual = runtime.version(command, repository) if command else None
        proof['required']['dotnet'] = sdk
        proof['resolved']['dotnet'] = actual
        proof['commands']['dotnet'] = command
        proof['satisfied'] = proof['satisfied'] and sdk == actual
    write(repository / '.program-kit/evidence/toolchain.json', proof)
    if not proof['satisfied']:
        raise ValueError(f"PKS004 exact toolchain unavailable: required={pins}, resolved={proof['resolved']}; install the approved versions, then resume sync")


@contextmanager
def mutation_lock(repository: Path):
    path = repository / ".program-kit/sync/mutation.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError("PKS006 another sync is active; retry after it finishes") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def apply(repository: Path, plan: dict, *, validate_authority: bool = True) -> dict:
    with mutation_lock(repository):
        return _apply(repository, plan, validate_authority=validate_authority)


def _apply(repository: Path, plan: dict, *, validate_authority: bool = True) -> dict:
    setup = plan["context"]
    unsigned = dict(plan)
    unsigned.pop("planDigest", None)
    if package_execution.canonical_hash(unsigned) != plan["planDigest"]:
        raise ValueError("PKS005 stored plan was modified")
    now = context(repository, setup["phase"], setup["feature"])
    if any(now[key] != setup[key] for key in ("authorityInputs", "providerInputs", "toolchainPins")):
        raise ValueError("PKS005 authority or provider inputs changed; review a new plan")
    if validate_authority and setup["phase"] != "upgrade":
        governance = Path(__file__).with_name("governance_state.py")
        run(repository, [sys.executable, str(governance), "validate-setup-authority"])
        decisions = load(repository / "docs/architecture/bootstrap-decisions.json", {})
        if setup["dotnet"] and not any(item.get("id") == "orbyss-building-block-dependencies" for item in decisions.get("acknowledgements", [])):
            raise ValueError("PKS003 accepted building-block source acknowledgement is missing")
        if not (repository / ".specify/governance/bootstrap-approval.json").is_file():
            raise ValueError("PKS003 bootstrap acceptance is required before setup")
    receipt_path = repository / ".program-kit/sync/receipt.json"
    previous = load(receipt_path, {})
    current = describe(repository, setup["phase"], setup["feature"])
    if not any(item["required"] for item in current["operations"]) and previous.get("context") == now and previous.get("status") == "offline-synchronized":
        for operation in current["operations"]:
            if operation["adapter"] == "javascript":
                package_execution.javascript_runtime().context(repository, repository / ".program-kit/evidence/toolchain.json")
            elif operation["adapter"] == "building-blocks":
                provider("program-kit-building-blocks/scripts/building_blocks.py").check_materialization(repository, load(repository / ".program-kit/building-blocks.lock.json"))
        return {**previous, "readiness": readiness(repository, setup["phase"], setup["feature"], validate_authority=False), "reused": True}
    write(repository / f".program-kit/sync/plans/{plan['planDigest']}.json", plan)
    receipt = {"schemaVersion": 1, "reviewedPlanDigest": plan["planDigest"], "context": setup, "operations": [], "status": "running"}
    write(repository / ".program-kit/sync/context.json", setup)
    write(receipt_path, receipt)
    for operation in plan["operations"]:
        record = {"id": operation["id"], "status": "current"}
        try:
            if operation["adapter"] == "dotnet":
                current = run(repository, dotnet_command(repository, setup) + ["--check", "--json"], (0, 1))
                if current.returncode == 1:
                    # A changed consumer file or adapter input cannot acquire approval from an old plan.
                    if json.loads(current.stdout)["planDigest"] != operation["plan"]["planDigest"]:
                        raise ValueError("PKS005 engineering plan changed; review sync again")
                    run(repository, dotnet_command(repository, setup) + ["--foundation-host-accepted", "--building-block-sources-approved", "--plan-digest", operation["plan"]["planDigest"]])
                    record["status"] = "applied"
            elif operation["adapter"] == "javascript":
                path = repository / ".program-kit/evidence/toolchain.json"
                if next(item for item in describe(repository, setup["phase"], setup["feature"])["operations"] if item["id"] == "toolchain")["required"]:
                    audit_toolchain(repository, operation["pins"])
                    record["status"] = "applied"
                else:
                    package_execution.javascript_runtime().context(repository, path)
                record["evidenceSha256"] = digest(path)
            elif operation["adapter"] == "building-blocks":
                blocks = provider("program-kit-building-blocks/scripts/building_blocks.py")
                lock_path = repository / ".program-kit/building-blocks.lock.json"
                if operation["required"]:
                    catalog_path = package_execution.extension_root() / "program-kit-building-blocks/references/orbyss-building-blocks.json"
                    computed = blocks.materialized_plan(repository, blocks.resolve(repository, repository / "docs/architecture/building-block-selection.json", catalog_path, version()))
                    if computed != operation["plan"]:
                        raise ValueError("PKS005 building-block target scope changed; review sync again")
                    if load(lock_path, {}) != computed:
                        blocks.apply_materialization(repository, lock_path, computed, load(catalog_path))
                    record["status"] = "applied"
                blocks.check_materialization(repository, load(lock_path))
            receipt["operations"].append(record)
            write(receipt_path, receipt)
        except Exception:
            record["status"] = "failed"
            receipt["operations"].append(record)
            receipt["status"] = "incomplete"
            write(receipt_path, receipt)
            raise
    if setup["phase"] in {"implementation-setup", "implementation", "upgrade"}:
        materialized = load(repository / ".program-kit/building-blocks.lock.json", {})
        dependency_plan = sync_readiness.dependencies(repository, setup, materialized)
        if setup["phase"] == "upgrade":
            previous_dependencies = load(repository / ".program-kit/sync/dependencies.json", {})
            paths = {target["path"] for target in dependency_plan["targets"]}
            dependency_plan["targets"].extend(target for target in previous_dependencies.get("targets", []) if target["path"] not in paths and contained(repository, target["path"]).is_file())
            dependency_plan.pop("planDigest", None)
            dependency_plan["planDigest"] = package_execution.canonical_hash(dependency_plan)
        write(repository / ".program-kit/sync/dependencies.json", dependency_plan)
    receipt["context"] = context(repository, setup["phase"], setup["feature"])
    write(repository / ".program-kit/sync/context.json", receipt["context"])
    receipt["status"] = "offline-synchronized"
    receipt["readiness"] = readiness(repository, setup["phase"], setup["feature"], validate_authority=False)
    write(receipt_path, receipt)
    return receipt


def readiness(repository: Path, phase: str, feature: str | None = None, *, validate_authority: bool = True) -> dict:
    plan = describe(repository, phase, feature)
    restore = provider("program-kit-building-blocks/scripts/restore_dependencies.py")
    problems = sync_readiness.blockers(repository, plan["context"], plan["operations"], restore)
    if validate_authority and phase not in {'bootstrap', 'upgrade'}:
        try:
            run(repository, [sys.executable, str(Path(__file__).with_name('governance_state.py')), 'validate-setup-authority'])
        except ValueError as error:
            problems.append(f'PKS015 setup authority is not current: {error}')
    pending = []
    if phase == "upgrade":
        dependencies = load(repository / ".program-kit/sync/dependencies.json", {})
        if dependencies.get("targets"):
            try:
                restore.verify_evidence(repository, dependencies, load(repository / ".program-kit/evidence/building-block-restore.json", {}))
            except (OSError, ValueError, RuntimeError) as error:
                pending.append(str(error))
    return {"phase": phase, "ready": not problems, "readinessScope": "offline-setup" if phase == "upgrade" else phase,
            "blockers": problems, "pendingPackageVerification": pending, "deferredTargets": plan["deferredTargets"]}


def upgrade(repository: Path) -> dict:
    """The release-owned upgrader already validated admission and component mutation authority."""
    return apply(repository, describe(repository, "upgrade"), validate_authority=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "apply", "resume", "check", "recover", "request-renew", "request-locked"))
    parser.add_argument("--repository", default=".")
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--feature-dir")
    parser.add_argument("--plan-digest")
    args = parser.parse_args()
    try:
        repository = Path(args.repository).resolve()
        if args.operation.startswith("request-"):
            restore = provider("program-kit-building-blocks/scripts/restore_dependencies.py")
            lock_path = repository / ".program-kit/sync/dependencies.json"
            request = restore.restore_request(repository, lock_path, load(lock_path), args.operation.removeprefix("request-"))
            write(repository / ".program-kit/evidence/building-block-restore-request.json", request)
            print(json.dumps(request, indent=2))
            return 0
        if args.operation == "recover":
            with mutation_lock(repository):
                setup = context(repository, args.phase, args.feature_dir)
                if setup["dotnet"]:
                    run(repository, dotnet_command(repository, setup) + ["--recover", "--check"], (0, 1))
                provider("program-kit-building-blocks/scripts/building_blocks.py").recover_materialization(repository)
            print("Recovered adapter transactions. Resume the reviewed plan if its authority inputs remain current.")
            return 0
        if args.operation == "resume":
            if not args.plan_digest or not re.fullmatch(r"[0-9a-f]{64}", args.plan_digest):
                raise ValueError("PKS005 resume requires the exact reviewed plan digest")
            plan = load(repository / f".program-kit/sync/plans/{args.plan_digest}.json")
            if plan["context"]["phase"] != args.phase:
                raise ValueError("PKS005 resume phase differs from the reviewed plan")
            print(json.dumps(apply(repository, plan), indent=2))
            return 0
        plan = describe(repository, args.phase, args.feature_dir)
        if args.operation == "apply":
            if args.plan_digest != plan["planDigest"]:
                raise ValueError("PKS005 reviewed sync plan is missing or changed; run plan and review its digest")
            print(json.dumps(apply(repository, plan), indent=2))
        elif args.operation == "plan":
            print(json.dumps(plan, indent=2))
        else:
            report = readiness(repository, args.phase, args.feature_dir)
            print(json.dumps(report, indent=2))
            return 0 if report["ready"] else 1
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

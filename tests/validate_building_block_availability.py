from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"
SCRIPT = ROOT / "extensions/program-kit-building-blocks/scripts/public_availability.py"
RESTORE_SCRIPT = ROOT / "extensions/program-kit-building-blocks/scripts/restore_dependencies.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("program_kit_public_availability", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Response:
    def __init__(self, value: object, headers: dict[str, str] | None = None):
        self.payload = json.dumps(value).encode("utf-8")
        self.headers = headers or {}

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def main() -> int:
    module = load_module(SCRIPT)
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    all_keys = module.selected_keys(catalog, None)
    if len(all_keys) != 63:
        raise AssertionError("Catalog-wide public gate must cover all 63 artifacts")
    selected_lock = {
        "inputs": {"catalog": {"id": catalog["catalogId"]}},
        "targets": [
            {
                "packages": [
                    {
                        "packageKey": "nuget:Orbyss.Foundation.Tasks",
                        "version": catalog["packages"]["nuget:Orbyss.Foundation.Tasks"]["version"],
                    }
                ]
            }
        ],
    }
    if module.selected_keys(catalog, selected_lock) != ["nuget:Orbyss.Foundation.Tasks"]:
        raise AssertionError("Consumer public gate did not reduce to the selected lock closure")

    package = catalog["packages"]["nuget:Orbyss.Foundation.Tasks"]

    def nuget_open(url, timeout=0):
        if "flatcontainer" in str(url):
            return Response({"versions": [package["version"]]})
        return Response(
            {
                "items": [
                    {
                        "items": [
                            {"catalogEntry": {"version": package["version"], "listed": True}}
                        ]
                    }
                ]
            }
        )

    if module.verify_nuget(package, nuget_open)["status"] != "listed-restorable":
        raise AssertionError("NuGet availability requires both listed and restorable metadata")

    npm_package = catalog["packages"]["npm:@orbyss-io/forms-contracts"]
    npm_source = catalog["sources"][npm_package["source"]]
    credential = npm_source["authentication"]["credentialEnvironment"]
    old_credential = os.environ.get(credential)
    old_npm = os.environ.get("PROGRAMKIT_NPM_EXECUTABLE")
    os.environ[credential] = "test-token-never-logged"
    os.environ["PROGRAMKIT_NPM_EXECUTABLE"] = sys.executable
    try:
        def npm_run(args, **_kwargs):
            if Path(args[0]).resolve() != Path(sys.executable).resolve():
                raise AssertionError("npm availability ignored its explicit executable")
            return subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({"version": npm_package["version"], "dist.tarball": "https://example.invalid/forms.tgz"}),
                stderr="",
            )

        if module.verify_npm(npm_package, npm_source, npm_run)["status"] != "metadata-tarball":
            raise AssertionError("npm availability did not require metadata and a tarball")
    finally:
        if old_credential is None:
            os.environ.pop(credential, None)
        else:
            os.environ[credential] = old_credential
        if old_npm is None:
            os.environ.pop("PROGRAMKIT_NPM_EXECUTABLE", None)
        else:
            os.environ["PROGRAMKIT_NPM_EXECUTABLE"] = old_npm

    os.environ["PROGRAMKIT_NPM_EXECUTABLE"] = str(ROOT / "missing-npm-command")
    try:
        try:
            module.npm_executable()
        except module.AvailabilityError as error:
            if "PKB614" not in str(error):
                raise AssertionError(f"Missing npm diagnostic lost its code: {error}") from error
        else:
            raise AssertionError("Missing npm executable did not fail closed")
    finally:
        if old_npm is None:
            os.environ.pop("PROGRAMKIT_NPM_EXECUTABLE", None)
        else:
            os.environ["PROGRAMKIT_NPM_EXECUTABLE"] = old_npm

    host = catalog["packages"]["oci:ghcr.io/orbyss-io/foundation-host"]
    digest = "sha256:" + "a" * 64
    if module.verify_oci(host, catalog["sources"][host["source"]], lambda *_args, **_kwargs: Response({}, {"Docker-Content-Digest": digest}))["reference"] != f"{host['packageId']}@{digest}":
        raise AssertionError("OCI availability did not capture an immutable manifest digest")

    restore = load_module(RESTORE_SCRIPT)
    with tempfile.TemporaryDirectory(prefix="program-kit-restore-plan-") as value:
        repository = Path(value)
        for relative, content in {
            "src/App/App.csproj": "<Project />\n",
            "web/package.json": '{"name":"web"}\n',
            ".config/dotnet-tools.json": '{"version":1,"isRoot":true,"tools":{}}\n',
        }.items():
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        restore_lock = {
            "targets": [
                {"path": "src/App/App.csproj", "packages": [{"materializationKind": "nuget-project"}]},
                {"path": "web/package.json", "packages": [{"materializationKind": "npm-dependency"}]},
                {"path": ".config/dotnet-tools.json", "packages": [{"materializationKind": "dotnet-tool"}]},
            ]
        }
        renew = restore.restore_commands(repository, restore_lock, "renew")
        locked = restore.restore_commands(repository, restore_lock, "locked")
        if not any("--force-evaluate" in item["args"] for item in renew if item["ecosystem"] == "nuget"):
            raise AssertionError("Native lock renewal omitted explicit NuGet reevaluation")
        if not any("--locked-mode" in item["args"] for item in locked if item["ecosystem"] == "nuget"):
            raise AssertionError("Locked verification omitted NuGet locked mode")
        if not any(item["args"][1] == "ci" for item in locked if item["ecosystem"] == "npm"):
            raise AssertionError("Locked verification must use npm ci")

    print("Availability gates, credential-safe probes, and explicit native restore modes passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

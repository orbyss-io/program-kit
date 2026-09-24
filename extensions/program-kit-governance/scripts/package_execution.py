"""One exact-runtime, registry-aware execution context for npm package operations."""
from __future__ import annotations

import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit


def extension_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def javascript_runtime():
    # This provider is shipped even in JavaScript-only bundles. No .NET baseline must be applied.
    source = extension_root() / "program-kit-dotnet/templates/dotnet/files/.program-kit/eng/js_toolchain.py"
    spec = importlib.util.spec_from_file_location("program_kit_package_runtime", source)
    if spec is None or spec.loader is None:
        raise ValueError("PKP001 shared JavaScript runtime provider is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def routes(packages: list[str], catalog: dict | None = None) -> list[dict]:
    if catalog is None:
        catalog = json.loads((extension_root() / "program-kit-building-blocks/references/orbyss-building-blocks.json").read_text(encoding="utf-8"))
    result = {}
    for package in packages:
        if not re.fullmatch(r"(?:@[a-z0-9_.-]+/)?[a-z0-9_.-]+", package):
            raise ValueError(f"PKP002 invalid npm package name: {package!r}")
        matched = [(key, value) for key, value in catalog["sources"].items()
                   if value.get("ecosystem") == "npm" and any(fnmatch.fnmatchcase(package, pattern) for pattern in value["patterns"])]
        if len(matched) > 1:
            raise ValueError(f"PKP002 ambiguous registry routing for {package}")
        source_id, source = matched[0] if matched else ("npm-public", {"url": "https://registry.npmjs.org", "authentication": {"required": False}})
        url = urlsplit(source["url"])
        if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError(f"PKP002 invalid secure registry URL for {source_id}")
        authentication = source.get("authentication", {})
        credential = authentication.get("credentialEnvironment") if authentication.get("required") else None
        if authentication.get("required") and (not isinstance(credential, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", credential)):
            raise ValueError(f"PKP002 missing credential reference for {source_id}")
        scope = package.split("/")[0] if package.startswith("@") else None
        key = scope or "default"
        route = {"source": source_id, "scope": scope, "registry": source["url"].rstrip("/") + "/", "credentialEnvironment": credential}
        if key in result and result[key] != route:
            raise ValueError(f"PKP002 contradictory registry routes for {key}")
        result[key] = route
    return sorted(result.values(), key=lambda route: route["scope"] or "")


def classify_failure(output: str) -> str:
    value = output.upper()
    if any(code in value for code in ("SELF_SIGNED_CERT", "UNABLE_TO_VERIFY", "CERT_HAS_EXPIRED", "UNABLE_TO_GET_ISSUER_CERT", "PKT015")):
        return "trust"
    if any(code in value for code in ("E401", "ENEEDAUTH", "E403")):
        return "access-denied"
    if any(code in value for code in ("E404", "ETARGET")):
        return "package-unavailable"
    if any(code in value for code in ("ERESOLVE", "EBADENGINE", "EBADPLATFORM")):
        return "incompatible-graph"
    if any(code in value for code in ("ENOTFOUND", "EAI_AGAIN", "ETIMEDOUT", "ECONNRESET", "ECONNREFUSED")):
        return "network"
    return "execution"


def redact(output: str, references: list[dict]) -> str:
    for route in references:
        credential = os.environ.get(route.get("credentialEnvironment") or "", "")
        if credential:
            output = output.replace(credential, "[REDACTED]")
    output = re.sub(r"(?i)(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", output)
    return output


def toolchain_digest(evidence: Path) -> str:
    record = json.loads(evidence.read_text(encoding="utf-8"))
    environment = record.get("environment", {})
    # Cache relocation changes where bytes are stored, not which dependency graph was proved.
    return canonical_hash({key: record.get(key) for key in ("required", "resolved", "commands", "satisfied")} |
                          {"trustMode": environment.get("trustMode")})


def context_proof(repository: Path, evidence: Path, packages: list[str]) -> dict:
    """Describe routing/trust inputs without requiring credentials or writing a cache probe."""
    toolchain = json.loads(evidence.read_text(encoding="utf-8"))
    extra_ca = toolchain.get("environment", {}).get("extraCaCertificates", "") or os.environ.get("NODE_EXTRA_CA_CERTS", "")
    proof = {"toolchainSha256": toolchain_digest(evidence),
             "routes": routes(packages), "strictSsl": True,
             "extraCaSha256": hashlib.sha256(Path(extra_ca).read_bytes()).hexdigest() if extra_ca else None}
    proof["contextDigest"] = canonical_hash(proof)
    return proof


@contextmanager
def execution_context(repository: Path, evidence: Path, packages: list[str], *, catalog: dict | None = None):
    selected_routes = routes(packages, catalog)
    for route in selected_routes:
        reference = route["credentialEnvironment"]
        if reference and not os.environ.get(reference):
            raise ValueError(f"PKP003 missing-access: {route['source']} requires environment reference {reference}")
    npm, environment = javascript_runtime().context(repository, evidence)
    # A temporary user config travels with isolated graph/metadata and in-place restore alike.
    # Store interpolation references only; neither this config nor receipts contain secret values.
    with tempfile.TemporaryDirectory(prefix="program-kit-package-context-") as directory:
        config = Path(directory) / "routing.npmrc"
        lines = ["registry=https://registry.npmjs.org/", "strict-ssl=true", "legacy-peer-deps=false", "force=false"]
        for route in selected_routes:
            prefix = route["scope"] + ":" if route["scope"] else ""
            lines.append(prefix + "registry=" + route["registry"])
            if route["credentialEnvironment"]:
                url = urlsplit(route["registry"])
                lines.append(f"//{url.netloc}{url.path}:_authToken=${{{route['credentialEnvironment']}}}")
        config.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        for key in list(environment):
            if key.casefold() in {"npm_config_userconfig", "npm_config_registry", "npm_config_force", "npm_config_legacy_peer_deps", "npm_config_strict_ssl"}:
                environment.pop(key)
        environment["NPM_CONFIG_USERCONFIG"] = str(config)
        environment["NPM_CONFIG_STRICT_SSL"] = "true"
        proof = {"toolchainSha256": toolchain_digest(evidence), "routes": selected_routes,
                 "strictSsl": True, "extraCaSha256": hashlib.sha256(Path(environment["NODE_EXTRA_CA_CERTS"]).read_bytes()).hexdigest()
                 if environment.get("NODE_EXTRA_CA_CERTS") else None}
        proof["contextDigest"] = canonical_hash(proof)
        yield npm, environment, proof


def execute(repository: Path, evidence: Path, packages: list[str], arguments: list[str], cwd: Path, timeout: int) -> tuple[subprocess.CompletedProcess, dict]:
    with execution_context(repository, evidence, packages) as (npm, environment, proof):
        default_registry = next((route["registry"] for route in proof["routes"] if route["scope"] is None), "https://registry.npmjs.org/")
        registry_arguments = [f"--registry={default_registry}"]
        registry_arguments.extend(f"--{route['scope']}:registry={route['registry']}" for route in proof["routes"] if route["scope"])
        forbidden = ("--force", "--legacy-peer-deps", "--strict-ssl=false", "--ignore-scripts=false")
        if any(argument == key or argument.startswith(key + "=") for argument in arguments for key in forbidden):
            raise ValueError("PKP006 package operations cannot bypass strict resolution, scripts or TLS policy")
        strict_arguments = ["--force=false", "--legacy-peer-deps=false", "--strict-peer-deps=true", "--engine-strict=true", "--ignore-scripts=true"]
        result = subprocess.run([*npm, "--strict-ssl=true", *registry_arguments, *strict_arguments, *arguments], cwd=cwd, env=environment,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        result.stdout = redact(result.stdout, proof["routes"])
        result.stderr = redact(result.stderr, proof["routes"])
        proof["failureCategory"] = None if result.returncode == 0 else classify_failure(result.stdout + "\n" + result.stderr)
        return result, proof

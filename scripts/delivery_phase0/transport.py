"""Explicit, non-retrying API transport for authorized disposable probes.

Credentials are obtained from existing CLI facilities and never serialized. HTTP
errors expose status/type only. TLS uses the host trust store, including Windows.
"""
from __future__ import annotations

import json
import os
import shutil
import ssl
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    def __init__(self, status, codes=()):
        self.status, self.codes = status, tuple(codes)
        super().__init__(f"Provider request failed: status={status}, codes={self.codes}")


class Transport:
    def __init__(self, provider):
        self.provider = provider
        self.context = ssl.create_default_context()
        roots = ""
        if hasattr(ssl, "enum_certificates"):
            roots = "".join(ssl.DER_cert_to_PEM_cert(cert)
                            for cert, encoding, trust in ssl.enum_certificates("ROOT")
                            if encoding == "x509_asn" and
                            (trust is True or "1.3.6.1.5.5.7.3.1" in trust))
            self.context.load_verify_locations(cadata=roots)
        if provider == "github":
            command = [shutil.which("gh"), "auth", "token", "--hostname", "github.com"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        elif provider == "azure":
            path = None
            try:
                env = dict(os.environ)
                if roots:
                    with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", suffix=".pem", delete=False) as bundle:
                        path = bundle.name
                        bundle.write(roots)
                    env["REQUESTS_CA_BUNDLE"] = path
                result = subprocess.run([
                    shutil.which("az"), "account", "get-access-token", "--resource",
                    "499b84ac-1321-427f-aa17-267ca6975798", "--query", "accessToken", "-o", "tsv",
                ], env=env, capture_output=True, text=True, timeout=60)
            finally:
                if path:
                    os.remove(path)
        else:
            raise ValueError("Unsupported provider")
        if result.returncode or not result.stdout.strip():
            raise RuntimeError(f"{provider} CLI credential acquisition failed; sign in interactively")
        self._token = result.stdout.strip()

    def request(self, method, path, body=None, content_type="application/json", api_version="7.1"):
        # Fixed origin prevents forwarding credentials to caller-supplied hosts.
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Expected provider-relative API path")
        origin = "https://api.github.com" if self.provider == "github" else "https://dev.azure.com/Unfussiness"
        if self.provider == "azure":
            path += ("&" if "?" in path else "?") + "api-version=" + api_version
        headers = {"Authorization": "Bearer " + self._token, "Content-Type": content_type,
                   "Accept": "application/json", "User-Agent": "ProgramKit-Delivery-Phase0",
                   "Cache-Control": "no-cache"}
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(origin + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, context=self.context, timeout=40) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read())
            except (ValueError, UnicodeError):
                payload = {}
            raise ApiError(exc.code, [payload.get("typeKey", "http_error")]) from None

    def graphql(self, query, variables=None):
        result = self.request("POST", "/graphql", {"query": query, "variables": variables or {}})
        if result.get("errors"):
            raise ApiError(200, [e.get("type", "graphql_error") for e in result["errors"]])
        return result["data"]

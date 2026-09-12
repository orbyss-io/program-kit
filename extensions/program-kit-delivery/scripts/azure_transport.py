"""Azure DevOps Services transport using an existing human Azure CLI session.

No credential persistence, redirects or automatic mutation retries. Tokens are acquired
only for explicit connected operations; offline delivery commands never import this module.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


class AzureError(ValueError):
    def __init__(self, code, status=None):
        self.code, self.status = code, status
        super().__init__(f'PKD_AZURE {code}' + (f' (HTTP {status})' if status else ''))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AzureTransport:
    def __init__(self, organization):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,49}', organization):
            raise AzureError('invalid organization name')
        self.organization = organization
        self._token = None
        self.context = ssl.create_default_context()
        self.roots = ''
        if hasattr(ssl, 'enum_certificates'):
            self.roots = ''.join(ssl.DER_cert_to_PEM_cert(cert) for cert, encoding, trust
                in ssl.enum_certificates('ROOT') if encoding == 'x509_asn'
                and (trust is True or '1.3.6.1.5.5.7.3.1' in trust))
            if self.roots:
                self.context.load_verify_locations(cadata=self.roots)
        self.opener = build_opener(NoRedirect(), HTTPSHandler(context=self.context))

    def authenticate(self):
        executable = shutil.which('az')
        if not executable:
            raise AzureError('Azure CLI missing; install it and sign in interactively')
        env = dict(os.environ)
        bundle = None
        try:
            if self.roots:
                with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', suffix='.pem', delete=False) as stream:
                    bundle = Path(stream.name)
                    stream.write(self.roots)
                env['REQUESTS_CA_BUNDLE'] = str(bundle)
            account = subprocess.run([executable, 'account', 'show', '--query', 'user.type', '-o', 'tsv'],
                capture_output=True, text=True, timeout=60, env=env)
            if account.returncode or account.stdout.strip().lower() != 'user':
                raise AzureError('a human Azure CLI login is required; service identities are not supported in Phase 2')
            token = subprocess.run([executable, 'account', 'get-access-token', '--resource',
                '499b84ac-1321-427f-aa17-267ca6975798', '--query', 'accessToken', '-o', 'tsv'],
                capture_output=True, text=True, timeout=60, env=env)
            if token.returncode or not token.stdout.strip():
                raise AzureError('Azure CLI sign-in must be renewed interactively')
            self._token = token.stdout.strip()
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AzureError('credential facility unavailable') from None
        finally:
            if bundle:
                bundle.unlink(missing_ok=True)

    def request(self, method, path, body=None, *, query=None, version='7.1', graph=False, patch=False):
        parts = urlsplit(path)
        if not path.startswith('/') or path.startswith('//') or parts.scheme or parts.netloc or parts.query or parts.fragment:
            raise AzureError('expected an organization-relative API path without query')
        if '\\' in path or any(segment in ('.', '..') for segment in path.split('/')) or '%' in path:
            raise AzureError('API paths must be unencoded and cannot traverse')
        if not self._token:
            self.authenticate()
        host = 'vssps.dev.azure.com' if graph else 'dev.azure.com'
        url = f'https://{host}/{self.organization}' + quote(path, safe='/$:')
        url += '?' + urlencode({'api-version': version, **(query or {})})
        headers = {'Authorization': 'Bearer ' + self._token, 'Accept': 'application/json',
                   'Content-Type': 'application/json-patch+json' if patch else 'application/json',
                   'User-Agent': 'ProgramKit-Delivery', 'Cache-Control': 'no-cache'}
        payload = json.dumps(body, allow_nan=False).encode() if body is not None else None
        try:
            with self.opener.open(Request(url, data=payload, method=method, headers=headers), timeout=40) as response:
                raw = response.read()
                value = json.loads(raw) if raw else None
                return value, dict(response.headers.items())
        except HTTPError as error:
            # Do not include response bodies/URLs: they can contain human text or credentials.
            try:
                failure = json.loads(error.read())
                kind = failure.get('typeKey', 'request-rejected')
                if not isinstance(kind, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,120}', kind):
                    kind = 'request-rejected'
            except (ValueError, OSError):
                kind = 'request-rejected'
            raise AzureError(kind + '; observe before retrying a mutation', error.code) from None
        except (OSError, URLError, ValueError):
            raise AzureError('response unavailable or invalid; mutation outcome may be unknown') from None

    def call(self, method, path, body=None, **kwargs):
        return self.request(method, path, body, **kwargs)[0]

    def list(self, path, *, query=None, version='7.1', graph=False):
        items, seen, token = [], set(), None
        while True:
            parameters = dict(query or {})
            if token:
                parameters['continuationToken'] = token
            value, headers = self.request('GET', path, query=parameters, version=version, graph=graph)
            if not isinstance(value, dict) or not isinstance(value.get('value'), list):
                raise AzureError('incomplete list response')
            items.extend(value['value'])
            token = next((v for k, v in headers.items() if k.lower() == 'x-ms-continuationtoken'), None)
            if not token:
                return items
            if token in seen:
                raise AzureError('repeated pagination token; observation incomplete')
            seen.add(token)

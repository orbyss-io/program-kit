"""Maintained test-only process/provider mechanics; application semantics stay in tests."""
from __future__ import annotations

from contextlib import closing
import hashlib
import http.client
import http.server
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import socket
import threading
import time
import uuid
from urllib.parse import urlsplit

from foundation_process import run


def require(condition, message):
    if not condition:
        raise ValueError(message)


def captured(command, cwd, directory, *, timeout=120, environment=None, secret_values=()):
    """Retain both drained streams, redacted even on failure or interruption."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    paths = [directory / 'stdout.log', directory / 'stderr.log']
    result = {'status': 'running', 'cleanupComplete': False, 'logsDrained': False,
              'supervisor': 'maintained compatibility_process.run',
              'cleanupProtocol': 'Windows Job accounting and process handles' if os.name == 'nt' else 'owned process group termination',
              'streamProtocol': 'direct owned files closed after descendant termination'}
    started = time.monotonic()
    try:
        with paths[0].open('wb') as out, paths[1].open('wb') as err:
            result['exitCode'] = run(command, cwd, out, err, timeout, env=environment)
        result.update(status='completed' if result['exitCode'] == 0 else 'failed',
                      cleanupComplete=True, logsDrained=True)
        return result
    except KeyboardInterrupt:
        result['status'] = 'interrupted'
        raise
    except BaseException:
        result['status'] = 'failed'
        raise
    finally:
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        result['streams'] = {}
        for path in paths:
            if path.is_file():
                raw = path.read_bytes()
                clean, count = raw, 0
                for value in secret_values:
                    if value:
                        encoded = value.encode('utf-8')
                        count += clean.count(encoded)
                        clean = clean.replace(encoded, b'[REDACTED]')
                path.write_bytes(clean)
                result['streams'][path.name] = {'rawSha256': hashlib.sha256(raw).hexdigest(),
                    'sha256': hashlib.sha256(clean).hexdigest(), 'redactionCount': count}
        (directory / 'process.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


def poll(probe, *, timeout=45, interval=.1):
    """Use a bounded readiness predicate; return observed elapsed time."""
    require(0 < timeout <= 300 and 0 < interval <= 10, 'Invalid readiness budget')
    started = time.monotonic()
    while True:
        if probe():
            return round(time.monotonic() - started, 3)
        if time.monotonic() - started >= timeout:
            raise ValueError('Service readiness budget expired')
        time.sleep(min(interval, max(0, timeout - (time.monotonic() - started))))


class ResponseLossProxy:
    """Test-only loopback HTTP response-loss seam, shared with product recovery cases.

    Consume the actual upstream response, then close the downstream connection.
    No rollback/replay claim follows: the application owns effect/recovery assertions.
    Request headers, bodies and upstream response bytes are never retained.
    """
    def __init__(self, upstream, *, timeout=5):
        target = urlsplit(upstream)
        require(target.scheme == 'http' and target.hostname and not target.username and not target.password
                and target.path in ('', '/') and not target.query and not target.fragment,
                'Response-loss fixture requires a plain loopback HTTP origin')
        require(target.hostname == 'localhost' or ipaddress.ip_address(target.hostname).is_loopback,
                'Response-loss fixture cannot route to a live deployment')
        require(0 < timeout <= 30, 'Invalid response-loss budget')
        self.consumed = 0
        owner = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.forward()
            def do_POST(self):
                self.forward()
            do_PUT = do_POST
            do_PATCH = do_POST
            do_DELETE = do_POST
            def forward(self):
                started = time.monotonic()
                self.connection.settimeout(timeout)
                require(self.path.startswith('/') and not self.path.startswith('//'), 'Expected local request path')
                length = int(self.headers.get('Content-Length', '0'))
                require(0 <= length <= 2 * 1024 * 1024 and not self.headers.get('Transfer-Encoding'),
                        'Response-loss fixture admits bounded content-length requests only')
                body = self.rfile.read(length) if length else None
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in ('host', 'connection', 'transfer-encoding')}
                with closing(http.client.HTTPConnection(target.hostname, target.port or 80, timeout=timeout)) as connection:
                    connection.request(self.command, self.path, body=body, headers=headers)
                    response = connection.getresponse()
                    while response.read(65536):
                        require(time.monotonic() - started < timeout, 'Response-loss fixture upstream budget expired')
                owner.consumed += 1
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
            def log_message(self, *_):
                pass  # Request data can contain secrets; never emit it.
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = False
        self.thread = threading.Thread(target=self.server.serve_forever, name='foundation-response-loss')
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        require(not self.thread.is_alive(), 'Response-loss fixture did not drain')


class PostgreSqlFixture:
    """Own one pinned disposable database, preserving its data across owned restarts.

    Credentials never enter command arguments or retained evidence. Anonymous volumes
    belong to the unique container and are removed at disposal; host bind mounts are
    prohibited. This fixture establishes transport behavior, never product semantics.
    """
    label = 'org.program-kit.foundation-fixture'

    def __init__(self, image, evidence_directory):
        require(isinstance(image, str) and re.fullmatch(r'postgres@sha256:[a-f0-9]{64}', image),
                'PostgreSQL fixture requires an immutable image digest')
        self.image = image
        self.directory = Path(evidence_directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.name = 'pk-foundation-' + uuid.uuid4().hex
        self.password = secrets.token_urlsafe(32)
        self.requested = False
        self.identity = None
        self.port = None
        self.counter = 0
        self.cleanup = {'requested': False, 'identityVerified': False, 'removed': False}

    def command(self, arguments, *, allowed=(0,), timeout=60):
        self.counter += 1
        directory = self.directory / f'command-{self.counter:03d}'
        environment = dict(os.environ, POSTGRES_PASSWORD=self.password)
        result = captured(['docker', *arguments], self.directory, directory,
                          timeout=timeout, environment=environment, secret_values=(self.password,))
        require(result.get('exitCode') in allowed and result['cleanupComplete'] and result['logsDrained'],
                'Owned PostgreSQL command failed; inspect ' + str(directory))
        return result['exitCode'], (directory / 'stdout.log').read_text(encoding='utf-8').strip()

    def inspect(self):
        _, value = self.command(['inspect', self.name])
        rows = json.loads(value)
        require(len(rows) == 1, 'Owned PostgreSQL inspection is ambiguous')
        row = rows[0]
        require(row.get('Name') == '/' + self.name and
                row.get('Config', {}).get('Labels', {}).get(self.label) == self.name and
                row.get('Config', {}).get('Image') == self.image and
                (self.identity is None or row.get('Id') == self.identity),
                'Refused PostgreSQL operation against foreign container identity')
        require(all(mount.get('Type') != 'bind' for mount in row.get('Mounts', [])),
                'Disposable PostgreSQL cannot mount a consumer directory')
        self.identity = row['Id']
        self.cleanup['identityVerified'] = True
        return row

    def start(self):
        self.command(['image', 'inspect', self.image])
        self.requested = self.cleanup['requested'] = True
        self.command(['run', '--detach', '--pull=never', '--name', self.name,
                      '--label', self.label + '=' + self.name, '--publish', '127.0.0.1::5432',
                      '--env', 'POSTGRES_USER=fixture', '--env', 'POSTGRES_DB=foundation_fixture',
                      '--env', 'POSTGRES_PASSWORD', self.image])
        self.inspect()
        self.wait_ready()
        return self

    def wait_ready(self):
        _, address = self.command(['port', self.name, '5432/tcp'])
        match = re.fullmatch(r'127\.0\.0\.1:(\d+)', address)
        require(match is not None, 'Owned PostgreSQL must expose exactly one loopback binding')
        self.port = int(match[1])
        return poll(lambda: self.command(['exec', self.name, 'pg_isready', '-U', 'fixture',
                    '-d', 'foundation_fixture'], allowed=(0, 1, 2), timeout=5)[0] == 0)

    def connection(self):
        require(self.port is not None, 'Start owned PostgreSQL before requesting connection')
        return f'Host=127.0.0.1;Port={self.port};Database=foundation_fixture;Username=fixture;Password={self.password};Timeout=5'

    def stop(self):
        self.inspect()
        self.command(['stop', '--time', '5', self.name])

    def restart(self):
        self.inspect()
        self.command(['restart', '--time', '5', self.name])
        return self.wait_ready()  # Reacquire the actual mapped port after restart.

    def close(self):
        try:
            if self.requested:
                code, _ = self.command(['inspect', self.name], allowed=(0, 1))
                if code == 0:
                    self.inspect()
                    self.command(['rm', '--force', '--volumes', self.name])
                _, remaining = self.command(['ps', '--all', '--quiet', '--filter', 'name=^/' + self.name + '$'])
                self.cleanup['removed'] = not remaining
                require(self.cleanup['removed'], 'Owned PostgreSQL removal was not confirmed')
        finally:
            (self.directory / 'cleanup.json').write_text(json.dumps(self.cleanup, indent=2) + '\n', encoding='utf-8')

    def __enter__(self):
        try:
            return self.start()
        except BaseException:
            self.close()
            raise

    def __exit__(self, *_):
        self.close()

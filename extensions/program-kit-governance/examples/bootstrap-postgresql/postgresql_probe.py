"""Isolated real PostgreSQL mechanism; shared coordinator owns package restoration."""
import json
import os
from pathlib import Path
import re
import secrets
import sys
import time
import uuid
import xml.etree.ElementTree as ET

from bounded_process import run


def main():
    root = Path.cwd()
    inputs = json.loads((root / 'runtime-inputs.json').read_text())
    tools = json.loads((root / '.program-kit/evidence/toolchain.json').read_text())['commands']
    suite = ET.Element('testsuite', name='ProgramKitPostgreSqlCompatibility')
    name = 'pk-postgres-' + uuid.uuid4().hex
    password = secrets.token_hex(24)
    counter = 0
    created = False
    old = {key: os.environ.get(key) for key in ('POSTGRES_PASSWORD', 'PROGRAM_KIT_PROBE_CONNECTION')}

    def command(args, timeout=90, allowed=(0,)):
        nonlocal counter
        counter += 1
        stdout, stderr = root / f'command-{counter}.out', root / f'command-{counter}.err'
        with stdout.open('wb') as out, stderr.open('wb') as err:
            code = run(args, root, out, err, timeout)
        output = stdout.read_text(encoding='utf-8', errors='replace')
        if code not in allowed:
            detail = (output + stderr.read_text(encoding='utf-8', errors='replace'))[-4096:]
            raise RuntimeError(f'PostgreSQL command {counter} exit {code}: ' + detail.replace(password, '[REDACTED]'))
        return code, output.strip()

    def connect():
        _, address = command(['docker', 'port', name, '5432/tcp'])
        match = re.fullmatch(r'127\.0\.0\.1:(\d+)', address)
        if not match:
            raise RuntimeError('PostgreSQL proof requires an isolated loopback port')
        os.environ['PROGRAM_KIT_PROBE_CONNECTION'] = f'Host=127.0.0.1;Port={match[1]};Database=probe;Username=probe;Password={password};Timeout=10'
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            code, _ = command(['docker', 'exec', name, 'pg_isready', '-h', '127.0.0.1', '-U', 'probe', '-d', 'probe'], allowed=(0, 1, 2))
            if code == 0:
                return
            time.sleep(.25)
        raise RuntimeError('PostgreSQL readiness timed out')

    def exercise(phase):
        result = root / (phase + '.xml')
        try:
            command([*tools['dotnet'], str(root / 'bin/Debug/net10.0/Probe.dll'), phase, str(result)], timeout=120)
        finally:
            if result.is_file():
                cases = ET.fromstring(result.read_text(encoding='utf-8').replace(password, '[REDACTED]'))
                suite.extend(cases)
                for case in cases.iter('testcase'):
                    for failure in case.findall('failure'):
                        detail = (failure.get('message', '') + '\n' + (failure.text or ''))[-4096:]
                        print(f"{case.get('classname')}.{case.get('name')}: {detail}", file=sys.stderr)

    try:
        command(['docker', 'image', 'inspect', inputs['image']])
        command([*tools['dotnet'], 'build', 'Probe.csproj', '--no-restore', '--nologo', '-p:UseSharedCompilation=false'], timeout=120)
        os.environ['POSTGRES_PASSWORD'] = password
        created = True
        command(['docker', 'run', '-d', '--pull=never', '--name', name, '-p', '127.0.0.1::5432',
                 '-e', 'POSTGRES_PASSWORD', '-e', 'POSTGRES_USER=probe', '-e', 'POSTGRES_DB=probe', inputs['image']])
        connect()
        _, version = command(['docker', 'exec', name, 'postgres', '--version'])
        if not re.search(r'\b' + re.escape(inputs['version']) + r'\b', version):
            raise RuntimeError('Running PostgreSQL version differs from managed profile')
        ET.SubElement(suite, 'testcase', classname='PostgreSql', name='exact_server')
        exercise('exercise')
        command(['docker', 'restart', name]); connect(); exercise('restart')
        return 0
    except Exception as error:
        reason = str(error).replace(password, '[REDACTED]')
        ET.SubElement(ET.SubElement(suite, 'testcase', classname='PostgreSql', name='execution'), 'failure', message=reason)
        print(reason, file=sys.stderr)
        return 1
    finally:
        try:
            if created:
                command(['docker', 'rm', '-f', '-v', name])
        finally:
            for key, value in old.items():
                if value is None: os.environ.pop(key, None)
                else: os.environ[key] = value
            ET.ElementTree(suite).write(root / 'compatibility-results.xml', encoding='utf-8', xml_declaration=True)

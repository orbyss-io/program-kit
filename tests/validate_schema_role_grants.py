"""Deployment administrator and application-role separation in an owned PostgreSQL fixture."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = ROOT / 'artifacts/tests/schema-role-grants' / uuid.uuid4().hex
    evidence.mkdir(parents=True)
    selected = json.loads((ROOT / 'extensions/program-kit-dotnet/references/persistence-runtimes.json').read_text())['profiles']['ef-postgresql']
    image = selected['image']
    assert '@sha256:' in image
    container = 'pk-schema-grants-' + uuid.uuid4().hex
    password = secrets.token_hex(24)
    environment = {**os.environ, 'POSTGRES_PASSWORD': password}
    operations = []
    created = False

    def run(arguments, input=None, allowed=(0,)):
        result = subprocess.run(['docker', *arguments], input=input, capture_output=True, text=True,
                                env=environment, timeout=90)
        log = (result.stdout + result.stderr).replace(password, '[REDACTED]')
        (evidence / (str(len(operations)) + '.log')).write_text(log, encoding='utf-8')
        operations.append({'operation': arguments[0], 'exitCode': result.returncode})
        if result.returncode not in allowed:
            raise RuntimeError('Inspect ' + str(evidence))
        return result.returncode, log

    def sql(statement, succeeds=True):
        code, output = run(['exec', '-i', container, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1'],
                           statement, (0,) if succeeds else (3,))
        if not succeeds:
            assert 'permission denied' in output
        return output

    try:
        run(['pull', image])
        run(['run', '-d', '--pull=never', '--name', container, '--label', 'program-kit.fixture=schema-role-grants',
             '-e', 'POSTGRES_PASSWORD', image])
        created = True
        deadline = time.monotonic() + 45
        while True:
            code, _ = run(['exec', container, 'pg_isready', '-U', 'postgres'], allowed=(0, 1, 2))
            if not code:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned PostgreSQL fixture did not become ready')
            time.sleep(.25)
        # Only the deployment administrator creates this synthetic journal/schema.
        sql('CREATE ROLE managed_app; CREATE SCHEMA deployment; '
            'CREATE TABLE deployment.journal(version text); '
            "INSERT INTO deployment.journal VALUES ('accepted'); "
            'CREATE TABLE deployment.unrelated(secret text);')
        sql('SET ROLE managed_app; SELECT version FROM deployment.journal;', succeeds=False)
        sql('GRANT USAGE ON SCHEMA deployment TO managed_app;')
        sql('SET ROLE managed_app; SELECT version FROM deployment.journal;', succeeds=False)
        sql('GRANT SELECT ON TABLE deployment.journal TO managed_app;')
        assert 'accepted' in sql('SET ROLE managed_app; SELECT version FROM deployment.journal;')
        sql('SET ROLE managed_app; SELECT secret FROM deployment.unrelated;', succeeds=False)
    finally:
        if created:
            run(['rm', '-f', '-v', container])
        (evidence / 'operations.json').write_text(json.dumps(operations, indent=2))
    (evidence / 'result.json').write_text(json.dumps({'status': 'passed', 'image': image,
        'schemaUsageRequired': True, 'journalSelectRequired': True, 'exactRoleReadAdmitted': True,
        'unrelatedTableStillDenied': True, 'cleanupComplete': True,
        'scope': 'Synthetic deployment guidance; no consumer schema, startup creation or reset.'}, indent=2))
    print('Exact application-role grant regression passed: ' + str(evidence))


if __name__ == '__main__':
    main()

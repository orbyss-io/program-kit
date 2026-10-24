"""Postpublication public initializer + one previous-release upgrade, no agents.

This is a separate delivery-surface check. It runs only after approved publication,
uses the actual public URLs, and never rebuilds or changes the published payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request

from owned_fixture import FixtureDirectory
from validate_package_smoke import extract
from validate_public_upgrade import installed_versions, replace_catalogs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from live.v2.supervisor import run_supervised
from release_candidate import policy, read, require, source, verify_payload, write


class PublicDelivery:
    def __init__(self, diagnostics, budget=120):
        self.diagnostics = diagnostics
        self.started = time.monotonic()
        self.budget = budget
        self.operations = []
        diagnostics.mkdir(parents=True, exist_ok=True)

    def remaining(self):
        remaining = self.budget - (time.monotonic() - self.started)
        require(remaining > 0, 'Public installation/upgrade exceeded its runtime budget')
        return remaining

    def run(self, name, command, cwd):
        started = time.monotonic()
        print('Public delivery: ' + name, flush=True)
        output = self.diagnostics / name
        result = run_supervised([str(x) for x in command], cwd=cwd, environment=os.environ.copy(),
                                evidence_directory=output, timeout_seconds=max(1,int(self.remaining())),
                                secrets=[os.environ[key] for key in ('GH_TOKEN','GITHUB_TOKEN') if os.environ.get(key)])
        self.operations.append({'name':name,'seconds':time.monotonic()-started,'exitCode':result.exitCode,
                                'timedOut':result.timedOut,'cleanupComplete':result.cleanupComplete,'logsDrained':result.logsDrained})
        require(result.exitCode == 0 and not result.timedOut and result.cleanupComplete and result.logsDrained,
                f'Public {name} failed or timed out; inspect retained diagnostics')
        self.remaining()
        return (output / result.stdout.path).read_text(encoding='utf-8')

    def download(self, url, destination, expected):
        require(url.startswith('https://github.com/' + policy()['repository'] + '/releases/download/'),
                'Public package URL must belong to this repository release')
        with urllib.request.urlopen(url, timeout=min(30,self.remaining())) as response:
            data = response.read(expected['size'] + 1)
        require(len(data) == expected['size'] and hashlib.sha256(data).hexdigest() == expected['sha256'],
                'Public download differs from inspected package: ' + destination.name)
        destination.write_bytes(data)
        self.remaining()


def previous_release(releases, current):
    current_tuple = tuple(map(int,current.split('.')))
    matches = [r for r in releases if not r['draft'] and not r['prerelease'] and
               re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+',r['tag_name']) and
               tuple(map(int,r['tag_name'][1:].split('.'))) < current_tuple]
    require(matches, 'No prior stable public release available for upgrade smoke')
    return max(matches,key=lambda r:tuple(map(int,r['tag_name'][1:].split('.'))))['tag_name']


def prepare_prior_consumer(session, project):
    """Complete the prior initializer's documented post-bundle preparation.

    These are the prior package's installed entrypoints. A bare native bundle
    installation has neither the UTF-8 transformation nor a schema-tool baseline
    and is not the initialized consumer whose upgrade we claim to exercise.
    """
    scripts = project / '.specify/extensions/program-kit-governance/scripts'
    session.run('prepare-prior-utf8', [sys.executable, scripts / 'ensure_utf8.py', '--target', '.'], project)
    session.run('prepare-prior-schema', [sys.executable, scripts / 'schema_runtime.py', 'setup'], project)
    session.run('record-prior-schema', [sys.executable, scripts / 'schema_runtime.py', 'record-copy'], project)
    session.run('check-prior-schema', [sys.executable, scripts / 'schema_runtime.py', 'check-copy'], project)
    session.run('prior-installation-check', [sys.executable, scripts / 'governance_state.py', 'validate-installation'], project)


def journey(session, workspace, promotion, previous):
    version = promotion['source']['version']
    tag = 'v' + version
    by_name = {r['name']:r for r in promotion['assets']}
    base = 'https://github.com/' + policy()['repository'] + '/releases/download/' + tag + '/'
    clean = workspace / 'public clean consumer'
    clean.mkdir()
    initializer = f'Initialize-ProgramKit-{version}.sh'
    session.download(base+initializer,clean/initializer,by_name[initializer])
    session.run('initialize-git',['git','init'],clean)
    # No agent-context variables are removed. The real initializer preserves its
    # user-terminal boundary; CI is a non-agent process with actual prerequisites.
    session.run('public-initializer',['bash',clean/initializer,'copilot'],clean)
    require(set(installed_versions(clean).values()) == {version}, 'Public initializer installed incoherent component versions')
    governance = clean/'.specify/extensions/program-kit-governance/scripts/governance_state.py'
    session.run('public-installation-check',[sys.executable,governance,'validate-installation'],clean)

    upgrade = workspace / 'public prior consumer'
    upgrade.mkdir()
    session.run('initialize-prior',['specify','init','.','--force','--non-interactive',
                                  '--integration','copilot','--script','py','--ignore-agent-tools'],upgrade)
    replace_catalogs(upgrade,'https://raw.githubusercontent.com/' + policy()['repository'] + '/' + previous + '/catalogs')
    session.run('install-prior-workflow',['specify','workflow','add','program-kit-bootstrap'],upgrade)
    session.run('install-prior-bundle',['specify','bundle','install','program-kit','--integration','copilot'],upgrade)
    require(set(installed_versions(upgrade).values()) == {previous[1:]}, 'Prior public consumer baseline is incoherent')
    prepare_prior_consumer(session, upgrade)
    authored = upgrade/'authored-consumer.txt'
    authored.write_text('Consumer-owned content must survive the public upgrade.\n',encoding='utf-8')
    before = authored.read_bytes()
    bundle = f'program-kit-tooling-{version}.zip'
    session.download(base+bundle,workspace/bundle,by_name[bundle])
    release = workspace/'public downloaded release'
    extract(workspace/bundle,release)
    session.run('public-upgrade',[sys.executable,release/'scripts/upgrade_program_kit.py',
                '--release-root',release,'--target',upgrade,'--integration','copilot'],upgrade)
    require(authored.read_bytes() == before, 'Public upgrade changed consumer-owned content')
    require(set(installed_versions(upgrade).values()) == {version}, 'Public upgrade did not converge all component versions')
    session.run('public-upgrade-check',[sys.executable,upgrade/'.specify/extensions/program-kit-governance/scripts/governance_state.py',
                                      'validate-installation'],upgrade)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True,help='Already inspected promotion directory')
    parser.add_argument('--budget-seconds',type=int,default=120)
    args = parser.parse_args()
    require(not any(os.environ.get(key) for key in ('CODEX_SESSION_ID','CODEX_THREAD_ID','CODEX_INTERNAL_ORIGINATOR_OVERRIDE')),
            'Run public delivery only in release CI or a normal human-owned terminal; never strip agent-context variables')
    require(args.budget_seconds > 0,'Public delivery budget must be positive')
    directory = args.directory.resolve()
    promotion = read(directory/'promotion.json')
    require(promotion['source'] == source(),'Public delivery source differs from inspected candidate')
    verify_payload(read(directory/'payload/candidate-payload.json'),directory/'payload',source())
    diagnostics = ROOT/'artifacts/public-delivery'
    session = PublicDelivery(diagnostics,args.budget_seconds)
    outcome = 'failed'
    try:
        releases = session.run('lookup-previous-release',['gh','api',f'repos/{policy()["repository"]}/releases?per_page=100'],ROOT)
        previous = previous_release(json.loads(releases),promotion['source']['version'])
        with FixtureDirectory() as temporary:
            journey(session,Path(temporary),promotion,previous)
        outcome = 'passed'
    finally:
        write(diagnostics/'result.json',{'status':outcome,'source':promotion['source'],'seconds':time.monotonic()-session.started,
              'budgetSeconds':args.budget_seconds,'operations':session.operations,
              'scope':'public initializer and one supported previous-version upgrade; no application or agent acceptance'})
    print('Public installation/upgrade passed.')
    return 0


if __name__ == '__main__': raise SystemExit(main())

"""Selection lifecycle cases for the real sequential upgrade validator."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import validate_building_blocks as blocks_test


def validate_0127_upgrade(installed: Path, upgrade_test) -> None:
    """Install the actual historical components; no metadata is injected."""
    release = upgrade_test.ROOT
    updater = upgrade_test.load_updater()
    with tempfile.TemporaryDirectory(prefix='program-kit-0127-upgrade-') as temporary:
        scratch = Path(temporary)
        archive = scratch / 'old.zip'
        upgrade_test.require_success(upgrade_test.run(
            'git', 'archive', '--format=zip', '--output', str(archive), 'v0.12.7', cwd=release),
            'historical 0.12.7 source fixture')
        old = scratch / 'release'
        with zipfile.ZipFile(archive) as source:
            source.extractall(old)
        target = scratch / 'consumer'
        shutil.copytree(installed, target)
        for kind, name in (('workflow', 'program-kit-bootstrap'),
                           ('extension', 'program-kit-governance'),
                           ('extension', 'program-kit-building-blocks'),
                           ('extension', 'program-kit-dotnet'),
                           ('preset', 'program-kit-governance-preset')):
            if kind == 'preset':
                upgrade_test.require_success(upgrade_test.run('specify', kind, 'remove', name, cwd=target), 'remove fixture preset')
            source = str(old / (kind + 's') / name)
            command = (['specify', kind, 'add', '--dev', source] if kind == 'preset'
                       else ['specify', kind, 'add', source, '--dev'])
            if kind == 'extension': command.append('--force')
            upgrade_test.require_success(upgrade_test.run(*command, cwd=target), 'install historical ' + name)
        upgrade_test.require_success(upgrade_test.run(
            sys.executable, str(release / 'scripts/record_local_bundle.py'), '--release-root', str(old),
            '--target', str(target), '--integration', 'codex', cwd=target), 'seal historical bundle')
        runtime = updater.load_release_module(release / 'extensions/program-kit-governance/scripts/schema_runtime.py', 'historical_upgrade_runtime')
        runtime.record_copy(target)
        blocks = blocks_test.load_module(target / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py')
        registry = blocks.profile_registry()
        assert (registry / 'index.json').is_file()
        assert not (registry / 'engineering-contracts.json').exists()
        catalog = blocks.new_project_catalog()
        assert catalog['families']['foundation']['releaseVersion'] == '0.2.4'
        selection_path, architecture_path = blocks_test.accepted_fixture(blocks, target, catalog)
        selection = blocks.load_json(selection_path)
        (target / selection['targets'][0]['path']).unlink()
        adr = target / 'docs/architecture/decisions/selection.md'
        adr.parent.mkdir(parents=True)
        adr.write_text('# Selection\n\nStatus: Accepted\n', encoding='utf-8')
        architecture = blocks.load_json(architecture_path)
        architecture['elements'] = [{'id': 'feature', 'ownership': 'Feature team', 'decision_refs': ['use-building-blocks']}]
        architecture['decisions'][0].update(path=adr.relative_to(target).as_posix(), sha256=blocks.raw_sha256(adr))
        for item in selection['targets']:
            item['placement'] = {'state': 'planned', 'owner': 'feature', 'decisionIds': ['use-building-blocks'], 'rationale': 'Accepted placement.'}
        blocks_test.write_json(selection_path, selection)
        blocks_test.write_json(architecture_path, architecture)
        blocks_test.refresh_registration(selection_path, architecture_path)
        candidate = target / 'captured-catalog.json'
        blocks_test.write_json(candidate, catalog)
        blocks.preserve_dependency_profile(target, selection, candidate)
        candidate.unlink()
        record_path = target / '.program-kit/dependency-profile.json'
        record = blocks.load_json(record_path)
        index = blocks.load_json(registry / 'index.json')
        record['newProjectQualification'] = {'profile': index['default'], 'entrySha256': blocks.canonical_sha256(index['profiles'][index['default']])}
        blocks_test.write_json(record_path, record)
        intake = target / 'docs/architecture/bootstrap-intake.json'
        blocks_test.write_json(intake, {'status': 'Confirmed', 'fixture': 'accepted 0.12.7 consumer intake'})
        history = target / '.specify/workflows/runs/completed/history.json'
        blocks_test.write_json(history, {'status': 'completed', 'steps': ['complete-bootstrap'], 'programKitVersion': '0.12.7'})
        constitution = target / '.specify/memory/constitution.md'
        immutable = {path: path.read_bytes() for path in
                     (selection_path, architecture_path, adr, record_path, intake, history, constitution,
                      target / record['catalogPath'], target / record['profilePath'])}
        command = (sys.executable, str(upgrade_test.UPDATER), '--release-root', str(release),
                   '--target', str(target), '--integration', 'codex', '--offline')
        # Missing/corrupt accepted authority must fail before component installation.
        snapshot = target / record['catalogPath']
        for contents in (None, b'{}'):
            if contents is None: snapshot.unlink()
            else: snapshot.write_bytes(contents)
            before = {path: path.read_bytes() for path in target.rglob('*')
                      if path.is_file() and '__pycache__' not in path.parts}
            failed = upgrade_test.run(*command, cwd=target)
            diagnostic = 'PKU101' if contents is None else 'PKB111'
            assert failed.returncode == 2 and diagnostic in failed.stderr, failed.stdout + failed.stderr
            assert before == {path: path.read_bytes() for path in target.rglob('*')
                              if path.is_file() and '__pycache__' not in path.parts}
            assert updater.current_version(target) == '0.12.7'
            assert not (registry / 'engineering-contracts.json').exists()
            snapshot.write_bytes(immutable[snapshot])
        result = upgrade_test.run(*command, cwd=target)
        upgrade_test.require_offline_setup(result, 'direct qualified 0.12.7 upgrade')
        assert 'Validate cross-component version coherence' in result.stdout
        assert 'Optional software update review:' in result.stdout
        assert 'review all repository software' in result.stdout
        assert 'dependency_profiles.py list' in result.stdout
        expected = (release / 'VERSION').read_text().strip()
        assert updater.current_version(target) == expected
        assert (registry / 'engineering-contracts.json').is_file()
        assert blocks.load_json(target / '.specify/bundle-records.json')['bundles'][0]['version'] == expected
        assert all(path.read_bytes() == content for path, content in immutable.items()), 'Upgrade changed accepted consumer authority/history'
        current = blocks_test.load_module(target / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py')
        effective = current.effective_dependency_context(target)
        assert effective['catalog'] == catalog and effective['qualification'] == record['newProjectQualification']
        print('Historical 0.12.7 qualified consumer upgraded coherently with unchanged pins, intake, constitution and bootstrap history.')


def validate_selection_upgrades(installed: Path, upgrade_test) -> None:
    validate_0127_upgrade(installed, upgrade_test)
    updater = upgrade_test.load_updater()
    blocks = blocks_test.load_module(blocks_test.RESOLVER)
    catalog = blocks.load_json(blocks_test.CATALOG)
    release = upgrade_test.ROOT
    with tempfile.TemporaryDirectory(prefix="program-kit-selection-upgrade-") as temporary:
        target = Path(temporary) / "planned"
        shutil.copytree(installed, target)
        assert updater.building_block_upgrade_state(target, release) is None
        selection_path, architecture_path = blocks_test.accepted_fixture(blocks, target, catalog)
        selection = blocks.load_json(selection_path)
        project = target / selection["targets"][0]["path"]
        project_bytes = project.read_bytes()
        project.unlink()
        adr = target / "docs/architecture/decisions/selection.md"
        adr.parent.mkdir(parents=True)
        adr.write_text("# Selection\n\nStatus: Accepted\n", encoding="utf-8")
        architecture = blocks.load_json(architecture_path)
        architecture["elements"] = [{"id": "feature", "ownership": "Feature team", "decision_refs": ["use-building-blocks"]}]
        architecture["decisions"][0].update(path=adr.relative_to(target).as_posix(), sha256=blocks.raw_sha256(adr))
        for item in selection["targets"]:
            item["placement"] = {"state": "planned", "owner": "feature", "decisionIds": ["use-building-blocks"], "rationale": "Accepted greenfield placement."}
        blocks_test.write_json(selection_path, selection)
        blocks_test.write_json(architecture_path, architecture)
        blocks_test.refresh_registration(selection_path, architecture_path)
        lock_path = target / "eng/building-blocks.lock.json"
        assert updater.building_block_upgrade_state(target, release) == "planned"
        immutable = {path: path.read_bytes() for path in (selection_path, architecture_path, adr)}

        def rejected(fragment):
            before = {path: upgrade_test.sha256(path) for path in target.rglob("*") if path.is_file()}
            try:
                updater.building_block_upgrade_state(target, release)
            except updater.UpgradeError as error:
                assert fragment in str(error), str(error)
            else:
                raise AssertionError(f"Expected {fragment}")
            assert before == {path: upgrade_test.sha256(path) for path in target.rglob("*") if path.is_file()}

        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text('{}', encoding='utf-8')
        rejected("stale or corrupt")
        lock_path.unlink()
        project.write_bytes(project_bytes)
        rejected("PKU116")
        project.unlink()
        output = blocks.resolve(target, selection_path, blocks_test.CATALOG, updater.current_version(target))["managedOutputs"][0]
        leftover = target / output["path"]
        leftover.parent.mkdir(parents=True, exist_ok=True)
        leftover.write_text("leftover materialization", encoding="utf-8")
        rejected("PKU116")
        leftover.unlink()
        journal = blocks.transaction_root(target) / "interrupted/journal.json"
        journal.parent.mkdir(parents=True)
        journal.write_text('{}', encoding='utf-8')
        rejected("unfinished")
        shutil.rmtree(journal.parent)
        for change in ("Draft", "missing-placement", "catalog", "authority"):
            value = copy.deepcopy(selection)
            if change == "Draft":
                value["status"] = "Draft"
            elif change == "missing-placement":
                value["targets"][0].pop("placement")
            elif change == "catalog":
                value["catalog"]["resolutionSha256"] = "0" * 64
            else:
                value["authority"]["decisionIds"] = ["absent"]
            blocks_test.write_json(selection_path, value)
            blocks_test.refresh_registration(selection_path, architecture_path)
            rejected("PKU116")
            for path, data in immutable.items():
                path.write_bytes(data)
        changed_release = Path(temporary) / "changed-release"
        shutil.copytree(release / "extensions/program-kit-building-blocks", changed_release / "extensions/program-kit-building-blocks")
        for name in ('VERSION', 'bundle.yml'):
            shutil.copyfile(release / name, changed_release / name)
        changed_catalog = copy.deepcopy(catalog)
        changed_catalog["resolutionRevision"] += 1
        blocks_test.write_json(changed_release / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json", changed_catalog)
        assert updater.building_block_upgrade_state(target, changed_release) == 'planned'
        assert selection_path.read_bytes() == immutable[selection_path], 'Program Kit upgrade rewrote accepted dependency choices'
        unowned = target / "unowned/package.json"
        unowned.parent.mkdir()
        npm = next(p for p in catalog["packages"].values() if p["ecosystem"] == "npm")
        blocks_test.write_json(unowned, {"dependencies": {npm["packageId"]: npm["version"]}})
        rejected("PKB405")
        unowned.unlink()

        # Clone the same old installation, materialize legitimately, then upgrade
        # both lifecycle states through the actual installer, not mocked steps.
        applied = Path(temporary) / "materialized"
        shutil.copytree(target, applied)
        applied_selection = applied / selection_path.relative_to(target)
        (applied / project.relative_to(target)).write_bytes(project_bytes)
        old_plan = blocks.resolve(applied, applied_selection, blocks_test.CATALOG, updater.current_version(applied))
        applied_lock = applied / lock_path.relative_to(target)
        blocks.apply_materialization(applied, applied_lock, old_plan, catalog)
        assert updater.building_block_upgrade_state(applied, release) == "materialized"
        lock_bytes = applied_lock.read_bytes()
        stale = json.loads(lock_bytes)
        stale['inputs']['selection']['canonicalSha256'] = '0' * 64
        bad_locks = (None, b'{invalid', b'{}', json.dumps(stale).encode('utf-8'))
        for bad in bad_locks:
            if bad is None:
                applied_lock.unlink()
            else:
                applied_lock.write_bytes(bad)
            try:
                updater.building_block_upgrade_state(applied, release)
            except (updater.UpgradeError, json.JSONDecodeError):
                pass
            else:
                raise AssertionError("Missing/corrupt applied lock was accepted")
            applied_lock.write_bytes(lock_bytes)
        applied_project = applied / project.relative_to(target)
        applied_bytes = applied_project.read_bytes()
        applied_project.write_bytes(project_bytes)
        try:
            updater.building_block_upgrade_state(applied, release)
        except updater.UpgradeError as error:
            assert 'PKB403' in str(error)
        else:
            raise AssertionError('Materialization drift was accepted')
        applied_project.write_bytes(applied_bytes)
        for root in (target, applied):
            result = upgrade_test.run(sys.executable, str(upgrade_test.UPDATER), "--release-root", str(release),
                                      "--target", str(root), "--integration", "codex", "--offline", cwd=root)
            upgrade_test.require_offline_setup(result, "accepted selection sequential upgrade")
            for path, data in immutable.items():
                assert (root / path.relative_to(target)).read_bytes() == data
        assert not lock_path.exists()
        assert all(not (target / item["path"]).exists() for item in selection["targets"])
        assert updater.building_block_upgrade_state(target, release) == "planned"
        assert updater.building_block_upgrade_state(applied, release) == "materialized"
        assert applied_lock.read_bytes() != lock_bytes, "Applied provenance did not advance"
        print("Accepted planned-only and materialized sequential upgrades passed; invalid states failed before mutation.")

"""Selection lifecycle cases for the real sequential upgrade validator."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

import validate_building_blocks as blocks_test


def validate_selection_upgrades(installed: Path, upgrade_test) -> None:
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
        lock_path = target / ".program-kit/building-blocks.lock.json"
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
        changed_catalog = copy.deepcopy(catalog)
        changed_catalog["resolutionRevision"] += 1
        blocks_test.write_json(changed_release / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json", changed_catalog)
        try:
            updater.building_block_upgrade_state(target, changed_release)
        except updater.UpgradeError as error:
            assert "resolution-affecting" in str(error)
        else:
            raise AssertionError("Changed release catalog was accepted without renewed selection authority")
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
                                      "--target", str(root), "--integration", "codex", cwd=root)
            upgrade_test.require_success(result, "accepted selection sequential upgrade")
            for path, data in immutable.items():
                assert (root / path.relative_to(target)).read_bytes() == data
        assert not lock_path.exists()
        assert all(not (target / item["path"]).exists() for item in selection["targets"])
        assert updater.building_block_upgrade_state(target, release) == "planned"
        assert updater.building_block_upgrade_state(applied, release) == "materialized"
        assert applied_lock.read_bytes() != lock_bytes, "Applied provenance did not advance"
        print("Accepted planned-only and materialized sequential upgrades passed; invalid states failed before mutation.")

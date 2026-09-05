from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path, PurePosixPath


class ReconciliationError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ReconciliationError(f"Unsafe reconciliation path: {value}")
    return path.as_posix()


def atomic_write(path: Path, content: bytes, suffix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{suffix}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def write_journal(path: Path, value: dict) -> None:
    atomic_write(
        path,
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "journal",
    )


def _current_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.is_file() else None


def rollback_transaction(target: Path, transaction: Path, journal: dict) -> None:
    actions = journal.get("actions")
    if not isinstance(actions, list):
        raise ReconciliationError(f"Invalid reconciliation journal: {transaction}")
    backup_root = transaction / "backup"
    conflicts: list[str] = []
    for action in reversed(actions):
        relative = safe_relative(str(action.get("path", "")))
        destination = target / relative
        backup = backup_root / relative
        current_hash = _current_hash(destination)
        original_hash = action.get("originalHash")
        desired_hash = action.get("desiredHash")
        allowed = {value for value in (original_hash, desired_hash) if isinstance(value, str)}
        if current_hash is not None and current_hash not in allowed:
            conflicts.append(relative)
            continue
        if backup.is_file():
            atomic_write(destination, backup.read_bytes(), transaction.name)
        elif current_hash is not None:
            destination.unlink()

    state_path = target / ".program-kit/managed.json"
    state_backup = backup_root / ".program-kit/managed.json"
    state_current = _current_hash(state_path)
    old_state_hash = journal.get("oldStateHash")
    new_state_hash = journal.get("newStateHash")
    allowed_state = {
        value for value in (old_state_hash, new_state_hash) if isinstance(value, str)
    }
    if state_current is not None and state_current not in allowed_state:
        conflicts.append(".program-kit/managed.json")
    elif state_backup.is_file():
        atomic_write(state_path, state_backup.read_bytes(), transaction.name)
    elif state_current is not None:
        state_path.unlink()

    if conflicts:
        raise ReconciliationError(
            "Recovery preserved externally changed paths: " + ", ".join(sorted(conflicts))
        )
    shutil.rmtree(transaction)


def pending_transactions(target: Path) -> list[Path]:
    root = target / ".program-kit/transactions"
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())


def recover_transactions(target: Path) -> list[str]:
    recovered: list[str] = []
    for transaction in pending_transactions(target):
        journal_path = transaction / "journal.json"
        if not journal_path.is_file():
            shutil.rmtree(transaction)
            recovered.append(transaction.name)
            continue
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal.get("status") == "committed":
            shutil.rmtree(transaction)
        else:
            rollback_transaction(target, transaction, journal)
        recovered.append(transaction.name)
    return recovered


def apply_plan(target: Path, actions: list[dict], next_state: bytes) -> str:
    transaction_id = uuid.uuid4().hex
    transaction = target / ".program-kit/transactions" / transaction_id
    stage_root = transaction / "stage"
    backup_root = transaction / "backup"
    transaction.mkdir(parents=True)

    state_path = target / ".program-kit/managed.json"
    old_state = state_path.read_bytes() if state_path.is_file() else None
    serialized_actions: list[dict] = []
    for action in actions:
        relative = safe_relative(action["path"])
        destination = target / relative
        original = destination.read_bytes() if destination.is_file() else None
        desired = action.get("content")
        if desired is not None and not isinstance(desired, bytes):
            raise ReconciliationError(f"Invalid desired bytes for {relative}")
        if original is not None:
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(original)
        if desired is not None:
            stage = stage_root / relative
            stage.parent.mkdir(parents=True, exist_ok=True)
            stage.write_bytes(desired)
        serialized_actions.append(
            {
                "path": relative,
                "kind": action["kind"],
                "originalHash": sha256_bytes(original) if original is not None else None,
                "desiredHash": sha256_bytes(desired) if desired is not None else None,
            }
        )
    if old_state is not None:
        state_backup = backup_root / ".program-kit/managed.json"
        state_backup.parent.mkdir(parents=True, exist_ok=True)
        state_backup.write_bytes(old_state)

    journal = {
        "schemaVersion": 1,
        "transactionId": transaction_id,
        "status": "staged",
        "actions": serialized_actions,
        "oldStateHash": sha256_bytes(old_state) if old_state is not None else None,
        "newStateHash": sha256_bytes(next_state),
    }
    journal_path = transaction / "journal.json"
    write_journal(journal_path, journal)

    fail_after_text = os.environ.get("PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION", "")
    fail_after = int(fail_after_text) if fail_after_text.isdigit() else None
    try:
        journal["status"] = "committing"
        write_journal(journal_path, journal)
        for index, action in enumerate(serialized_actions, 1):
            relative = action["path"]
            destination = target / relative
            if action["kind"] == "remove":
                if destination.is_file():
                    destination.unlink()
            else:
                atomic_write(destination, (stage_root / relative).read_bytes(), transaction_id)
            if fail_after == index:
                raise OSError(f"Injected reconciliation interruption after action {index}")
        atomic_write(state_path, next_state, transaction_id)
        journal["status"] = "committed"
        write_journal(journal_path, journal)
    except Exception:
        rollback_transaction(target, transaction, journal)
        raise
    shutil.rmtree(transaction)
    return transaction_id

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class LiveContractError(RuntimeError):
    """Raised when governed live-acceptance input is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return sha256_bytes(canonical_json(value))


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LiveContractError(f"LIVE_CONTRACT_INVALID_JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise LiveContractError(f"LIVE_CONTRACT_OBJECT_REQUIRED: {path}")
    return value


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or any(part in ("", ".") for part in path.parts):
        raise LiveContractError(f"LIVE_UNSAFE_RELATIVE_PATH: {value!r}")
    return path


def file_inventory(root: Path, excluded_parts: set[str] | None = None) -> list[dict[str, object]]:
    excluded = excluded_parts or {".git", "node_modules", "bin", "obj", "dist", "cache", "__pycache__"}
    records: list[dict[str, object]] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts):
            continue
        if path.is_symlink():
            raise LiveContractError(f"LIVE_CHECKPOINT_SYMLINK_FORBIDDEN: {relative.as_posix()}")
        if not path.is_file():
            continue
        records.append({"path": relative.as_posix(), "sha256": sha256_file(path), "size": path.stat().st_size})
    return sorted(records, key=lambda item: str(item["path"]).casefold())


def _resolve_ref(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    reference = schema.get("$ref")
    if reference is None:
        return schema
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise LiveContractError(f"LIVE_SCHEMA_UNSUPPORTED_REF: {reference!r}")
    current: Any = root
    for part in reference[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise LiveContractError(f"LIVE_SCHEMA_MISSING_REF: {reference}")
        current = current[part]
    if not isinstance(current, dict):
        raise LiveContractError(f"LIVE_SCHEMA_INVALID_REF: {reference}")
    return current


def validate(instance: object, schema: dict[str, Any], path: str = "$", root: dict[str, Any] | None = None) -> None:
    """Validate the deliberately small JSON-Schema subset used by live evidence."""
    root = root or schema
    schema = _resolve_ref(schema, root)
    if "allOf" in schema:
        for child in schema["allOf"]:
            validate(instance, child, path, root)
    if "oneOf" in schema:
        matches = 0
        for child in schema["oneOf"]:
            try:
                validate(instance, child, path, root)
                matches += 1
            except LiveContractError:
                pass
        if matches != 1:
            raise LiveContractError(f"LIVE_SCHEMA_ONE_OF: {path} matched {matches} branches")
    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        checks = {
            "object": lambda value: isinstance(value, dict),
            "array": lambda value: isinstance(value, list),
            "string": lambda value: isinstance(value, str),
            "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
            "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": lambda value: isinstance(value, bool),
            "null": lambda value: value is None,
        }
        if not any(checks[name](instance) for name in names):
            raise LiveContractError(f"LIVE_SCHEMA_TYPE: {path} must be {names}")
    if "const" in schema and instance != schema["const"]:
        raise LiveContractError(f"LIVE_SCHEMA_CONST: {path}")
    if "enum" in schema and instance not in schema["enum"]:
        raise LiveContractError(f"LIVE_SCHEMA_ENUM: {path}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            raise LiveContractError(f"LIVE_SCHEMA_MIN_LENGTH: {path}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            raise LiveContractError(f"LIVE_SCHEMA_PATTERN: {path}")
    if isinstance(instance, (int, float)) and "minimum" in schema and instance < schema["minimum"]:
        raise LiveContractError(f"LIVE_SCHEMA_MINIMUM: {path}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            raise LiveContractError(f"LIVE_SCHEMA_MIN_ITEMS: {path}")
        if schema.get("uniqueItems") and len({canonical_json(value) for value in instance}) != len(instance):
            raise LiveContractError(f"LIVE_SCHEMA_UNIQUE_ITEMS: {path}")
        child_schema = schema.get("items")
        if isinstance(child_schema, dict):
            for index, child in enumerate(instance):
                validate(child, child_schema, f"{path}[{index}]", root)
    if isinstance(instance, dict):
        missing = [name for name in schema.get("required", []) if name not in instance]
        if missing:
            raise LiveContractError(f"LIVE_SCHEMA_REQUIRED: {path} missing {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                raise LiveContractError(f"LIVE_SCHEMA_ADDITIONAL_PROPERTIES: {path} has {extras}")
        for name, child in instance.items():
            if name in properties:
                validate(child, properties[name], f"{path}.{name}", root)


def validate_file(instance_path: Path, schema_path: Path) -> dict[str, Any]:
    instance = load_object(instance_path)
    schema = load_object(schema_path)
    validate(instance, schema)
    return instance

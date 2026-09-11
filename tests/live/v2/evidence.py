from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from .common import LiveContractError, atomic_write_json, canonical_sha256, sha256_bytes, sha256_file, utc_now


class EvidenceStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.objects = self.root / "objects" / "sha256"
        self.runs = self.root / "runs"
        self.checkpoints = self.root / "checkpoints"
        self.authorizations = self.root / "authorizations"

    def initialize(self) -> None:
        for path in (self.objects, self.runs, self.checkpoints, self.authorizations):
            path.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, payload: bytes) -> dict[str, object]:
        digest = sha256_bytes(payload)
        destination = self.objects / digest
        if destination.exists():
            if sha256_file(destination) != digest:
                raise LiveContractError(f"LIVE_EVIDENCE_OBJECT_CORRUPT: {digest}")
        else:
            temporary = destination.with_name(destination.name + f".{os.getpid()}.tmp")
            temporary.write_bytes(payload)
            if sha256_file(temporary) != digest:
                temporary.unlink(missing_ok=True)
                raise LiveContractError("LIVE_EVIDENCE_WRITE_HASH_MISMATCH")
            try:
                temporary.rename(destination)
            except FileExistsError:
                temporary.unlink(missing_ok=True)
        return {"sha256": digest, "size": len(payload)}

    def put_file(self, source: Path) -> dict[str, object]:
        digest = sha256_file(source)
        destination = self.objects / digest
        if destination.exists():
            if sha256_file(destination) != digest:
                raise LiveContractError(f"LIVE_EVIDENCE_OBJECT_CORRUPT: {digest}")
        else:
            temporary = destination.with_name(destination.name + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
            try:
                shutil.copyfile(source, temporary)
                if sha256_file(temporary) != digest:
                    raise LiveContractError("LIVE_EVIDENCE_COPY_HASH_MISMATCH")
                try:
                    temporary.rename(destination)
                except FileExistsError:
                    if sha256_file(destination) != digest:
                        raise LiveContractError(f"LIVE_EVIDENCE_OBJECT_CORRUPT: {digest}")
            finally:
                temporary.unlink(missing_ok=True)
            if sha256_file(destination) != digest:
                raise LiveContractError("LIVE_EVIDENCE_COPY_HASH_MISMATCH")
        return {"sha256": digest, "size": source.stat().st_size}

    def write_run_manifest(self, run_id: str, manifest: dict[str, object]) -> Path:
        manifest = {**manifest, "sealedAt": utc_now()}
        manifest["manifestSha256"] = canonical_sha256(manifest)
        destination = self.runs / run_id / "manifest.json"
        if destination.exists():
            raise LiveContractError(f"LIVE_EVIDENCE_RUN_ALREADY_SEALED: {run_id}")
        atomic_write_json(destination, manifest)
        return destination

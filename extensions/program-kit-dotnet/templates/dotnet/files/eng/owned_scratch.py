"""Short, owned local staging with explicit operation/cleanup failure semantics.

Scratch is disposable. This module must never clean durable witnesses or accept an
arbitrary deletion target. Network scratch roots are unsupported: their directory
identity and cleanup semantics have not been qualified.
"""
from __future__ import annotations

import json
import ntpath
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import uuid


def windows_extended_path(value: str) -> str:
    """Convert an absolute drive/UNC path; reject device namespaces and relatives."""
    if value.startswith('\\\\.\\'):
        raise ValueError('PKR015 device paths are not staging paths')
    if value.startswith('\\\\?\\'):
        if value.startswith('\\\\?\\UNC\\'):
            value = '\\\\' + value[8:]
        elif len(value) >= 7 and value[5:7] == ':\\' and value[4].isalpha():
            value = value[4:]
        else:
            raise ValueError('PKR015 unsupported extended path namespace')
    value = ntpath.normpath(value)
    drive, tail = ntpath.splitdrive(value)
    if drive.startswith('\\\\'):
        if len(drive[2:].split('\\')) != 2 or not all(drive[2:].split('\\')):
            raise ValueError('PKR015 an absolute UNC server/share is required')
        return '\\\\?\\UNC\\' + value[2:]
    if len(drive) != 2 or drive[1] != ':' or not tail.startswith('\\'):
        raise ValueError('PKR015 an absolute drive path is required')
    return '\\\\?\\' + value


def filesystem_path(path: Path) -> str:
    return windows_extended_path(str(path)) if os.name == 'nt' else str(path)


def native_path(path: Path) -> str:
    """NuGet/configuration paths use native drive/UNC syntax, never a device URI."""
    value = str(path)
    if os.name == 'nt' and value.startswith('\\\\?\\'):
        return '\\\\' + value[8:] if value.startswith('\\\\?\\UNC\\') else value[4:]
    return value


def directory_identity(path: Path):
    info = os.lstat(filesystem_path(path))
    if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
            or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)):
        raise ValueError('PKR015 scratch directories must not be links or reparse points: ' + str(path))
    if not info.st_ino:
        raise ValueError('PKR015 filesystem does not expose a stable scratch directory identity')
    return info.st_dev, info.st_ino


class ScratchCleanupError(RuntimeError):
    def __init__(self, record):
        self.record = record
        super().__init__('PKR015 owned scratch cleanup failed; residual=' + record['scratch']
                         + '; cleanup=' + record['cleanupError'])


class OwnedScratch:
    def __init__(self, repository: Path, purpose: str):
        repository = Path(repository)
        if not repository.is_absolute():
            raise ValueError('PKR015 staging requires an absolute repository path')
        self.repository = repository.resolve(strict=True)
        if os.name == 'nt' and native_path(self.repository).startswith('\\\\'):
            raise ValueError('PKR015 network/UNC scratch roots are unsupported; use a local drive checkout')
        if purpose not in {'selected-roots', 'release-bundle', 'validation-fixture'}:
            raise ValueError('PKR015 unknown owned staging purpose')
        self.purpose = purpose
        self.path = None
        self._created_path = None
        self.identities = {}

    def __enter__(self):
        # Check each owned parent before traversing it; resolving first would hide
        # a junction pointing at a sibling or an unrelated data directory.
        artifacts = self.repository / 'artifacts'
        parent = artifacts / 's'
        for directory in (self.repository, artifacts, parent):
            directory.mkdir(exist_ok=True)
            self.identities[directory] = directory_identity(directory)
        self.path = Path(tempfile.mkdtemp(prefix='', dir=filesystem_path(parent)))
        # Keep ordinary public paths; only filesystem operations use extended form.
        if os.name == 'nt':
            self.path = parent / self.path.name
        self.identities[self.path] = directory_identity(self.path)
        self._created_path = self.path
        try:
            self._verify()
        except Exception as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise
        return self.path

    def _verify(self):
        if (self.path is None or self.path != self._created_path
                or self.path.parent != self.repository / 'artifacts/s'):
            raise ValueError('PKR015 deletion target is not this exact owned scratch root')
        for directory, identity in self.identities.items():
            if directory_identity(directory) != identity:
                raise ValueError('PKR015 scratch directory identity changed; refusing cleanup: ' + str(directory))

    def _remove(self):
        self._verify()
        shutil.rmtree(filesystem_path(self.path))

    def __exit__(self, error_type, operation_error, traceback):
        try:
            self._remove()
        except Exception as cleanup_error:
            record = {'schemaVersion': 1, 'status': 'cleanup-failed', 'purpose': self.purpose,
                      'scratch': str(self.path), 'ownedIdentity': self.identities.get(self.path),
                      'operationError': None if operation_error is None else repr(operation_error),
                      'cleanupError': repr(cleanup_error), 'cleanupCompleted': False}
            # stderr belongs to the maintained command's preserved stream. Failure
            # reporting never follows a possibly substituted artifacts parent.
            try:
                print(json.dumps(record), file=sys.stderr, flush=True)
            except Exception:
                pass
            failure = ScratchCleanupError(record)
            if operation_error is not None:
                operation_error.add_note(str(failure))
                operation_error.programkit_cleanup_failure = record
                return False  # Preserve the original operation and its traceback.
            raise failure from cleanup_error
        return False


def owned_scratch(repository: Path, purpose: str):
    return OwnedScratch(repository, purpose)

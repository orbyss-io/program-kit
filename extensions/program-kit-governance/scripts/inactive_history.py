"""Explicit, read-only reconciliation of withdrawn application authority for upgrades.

This narrow route admits tooling refresh only. It cannot accept a design, repair a
materialized application, change dependency selections or rewrite historical proof.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SELECTION = 'docs/architecture/building-block-selection.json'
LOCK = 'eng/building-blocks.lock.json'
COMPOSITION = 'eng/foundation-composition.json'
PROFILE = '.program-kit/dependency-profile.json'


def require(condition, message):
    if not condition:
        raise ValueError('PKU149 ' + message)


def inside(root, relative):
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative
            and not relative.startswith('/') and '..' not in relative.split('/'), 'unsafe inactive-history path')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()) and
            not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *[p for p in path.parents if p != root and p.is_relative_to(root)])),
            'linked inactive-history input requires owner reconciliation')
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def read(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate inactive-history field')
        value[key] = item
    return value


def validate(root, declaration, expected, blocks):
    raise ValueError('PKU149 The 0.x inactive-history upgrade route is retired. Preserve the original '
                     'repository, history and locks; re-onboard into a fresh preview installation. '
                     'No historical workflow authority is converted and no files changed.')


def arguments(binding):
    return ['--inactive-history', binding['declaration'], '--inactive-history-sha256', binding['declarationSha256']] if binding else []

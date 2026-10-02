"""Publish validated bytes without carrying private staging ACLs into a workspace."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import uuid


def ensure_workspace_owner(path: Path, root: Path) -> None:
    """Grant only the workspace owner's SID read/write on this owned output.

    Inheritance alone can carry OWNER RIGHTS rather than the human owner's SID;
    a sandbox-created file then belongs to a different owner. Never reset a
    directory ACL or grant access to broad user groups.
    """
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    pointer = ctypes.c_void_p
    class Trustee(ctypes.Structure):
        _fields_ = [('multiple', pointer), ('operation', ctypes.c_int), ('form', ctypes.c_int),
                    ('kind', ctypes.c_int), ('name', pointer)]
    class Entry(ctypes.Structure):
        _fields_ = [('permissions', ctypes.c_uint32), ('mode', ctypes.c_int),
                    ('inheritance', ctypes.c_uint32), ('trustee', Trustee)]
    get = api.GetNamedSecurityInfoW
    get.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_uint32,
                   pointer, pointer, pointer, pointer, pointer]
    get.restype = ctypes.c_uint32
    merge = api.SetEntriesInAclW
    merge.argtypes = [ctypes.c_uint32, ctypes.POINTER(Entry), pointer, ctypes.POINTER(pointer)]
    merge.restype = ctypes.c_uint32
    set_info = api.SetNamedSecurityInfoW
    set_info.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_uint32,
                        pointer, pointer, pointer, pointer]
    set_info.restype = ctypes.c_uint32
    kernel.LocalFree.argtypes = [pointer]
    kernel.LocalFree.restype = pointer
    owner, root_descriptor, dacl, descriptor, merged = (pointer() for _ in range(5))
    try:
        code = get(str(root), 1, 1, ctypes.byref(owner), None, None, None, ctypes.byref(root_descriptor))
        if code:
            raise ctypes.WinError(code)
        code = get(str(path), 1, 4, None, None, ctypes.byref(dacl), None, ctypes.byref(descriptor))
        if code:
            raise ctypes.WinError(code)
        if not dacl:
            raise OSError('Refusing to alter an unrestricted/null destination DACL')
        entry = Entry(0x12019F, 1, 0, Trustee(None, 0, 0, 1, owner))  # FILE_GENERIC_READ | WRITE, GRANT_ACCESS, SID.
        code = merge(1, ctypes.byref(entry), dacl, ctypes.byref(merged))
        if code:
            raise ctypes.WinError(code)
        code = set_info(str(path), 1, 4, None, None, merged, None)
        if code:
            raise ctypes.WinError(code)
    finally:
        for allocation in (merged, descriptor, root_descriptor):
            if allocation:
                kernel.LocalFree(allocation)


def replace_bytes(target: Path, content: bytes, owner_root: Path | None = None) -> None:
    # open('xb') uses ordinary file creation permissions, unlike mkstemp and
    # Windows 3.13+ TemporaryDirectory's protected owner-only security descriptor.
    # A sibling inherits the destination directory's ACL, not the staging ACL.
    sibling = target.with_name(f'.{target.name}.{uuid.uuid4().hex}.tmp')
    try:
        with sibling.open('xb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name == 'nt' and target.exists():
            if owner_root:
                ensure_workspace_owner(target, owner_root)
            # ReplaceFile preserves the existing destination's DACL and metadata.
            # Fail closed if permissions cannot be preserved; no ignore-ACL flag.
            replace = ctypes.WinDLL('kernel32', use_last_error=True).ReplaceFileW
            replace.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                                ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
            replace.restype = ctypes.c_int
            if not replace(str(target), str(sibling), None, 0, None, None):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            if os.name == 'nt' and owner_root:
                ensure_workspace_owner(sibling, owner_root)
            if target.exists():
                os.chmod(sibling, target.stat().st_mode & 0o777)
            os.replace(sibling, target)
    finally:
        sibling.unlink(missing_ok=True)

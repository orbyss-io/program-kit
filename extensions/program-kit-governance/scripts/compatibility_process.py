"""Bounded recipe process tree; never launches an agent or changes machine configuration."""
from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import time


if os.name == 'nt':
    from ctypes import wintypes

    class Limits(ctypes.Structure):
        _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                    ('flags', wintypes.DWORD), ('min_working', ctypes.c_size_t),
                    ('max_working', ctypes.c_size_t), ('active_limit', wintypes.DWORD),
                    ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD), ('scheduling', wintypes.DWORD)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [('basic', Limits), ('io', ctypes.c_ulonglong * 6),
                    ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                    ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]

    class Accounting(ctypes.Structure):
        _fields_ = [('times', ctypes.c_longlong * 4), ('faults', wintypes.DWORD),
                    ('total', wintypes.DWORD), ('active', wintypes.DWORD), ('terminated', wintypes.DWORD)]

    class ProcessIds(ctypes.Structure):
        _fields_ = [('assigned', wintypes.DWORD), ('count', wintypes.DWORD), ('ids', ctypes.c_size_t * 512)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    ntdll = ctypes.WinDLL('ntdll')
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    ntdll.NtResumeProcess.restype = wintypes.LONG


def run(command, cwd, stdout, stderr, timeout):
    """Return exit status after terminating descendants; output goes to owned files."""
    job = None
    process = None
    try:
        if os.name == 'nt':
            job = kernel.CreateJobObjectW(None, None)
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise OSError('Cannot create bounded compatibility Job Object')
            kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW | 0x4}  # CREATE_SUSPENDED
        else:
            kwargs = {'start_new_session': True}
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr, **kwargs)
        if os.name == 'nt':
            if not kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)):
                raise OSError('Cannot assign compatibility recipe to its Job Object')
            if ntdll.NtResumeProcess(wintypes.HANDLE(process._handle)) != 0:
                raise OSError('Cannot resume compatibility recipe')
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124
    finally:
        # No PID liveness/signalling probes. Close every owned descendant, including
        # children left behind by a recipe that exited successfully.
        if os.name == 'nt' and job:
            handles = []
            try:
                ids = ProcessIds()
                if not kernel.QueryInformationJobObject(job, 3, ctypes.byref(ids), ctypes.sizeof(ids), None):
                    raise OSError('Cannot enumerate compatibility process handles for cleanup')
                for identity in ids.ids[:ids.count]:
                    handle = kernel.OpenProcess(0x100000, False, identity)  # SYNCHRONIZE only
                    if handle:
                        handles.append(handle)
                if not kernel.TerminateJobObject(job, 1):
                    raise OSError('Cannot terminate compatibility process tree')
                deadline = time.monotonic() + 5
                while True:
                    accounting = Accounting()
                    if not kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                        raise OSError('Cannot verify compatibility descendant cleanup')
                    if accounting.active == 0:
                        break
                    if time.monotonic() >= deadline:
                        raise OSError('Compatibility descendants did not terminate')
                    time.sleep(0.01)
                for handle in handles:
                    remaining = max(1, int((deadline - time.monotonic()) * 1000))
                    if kernel.WaitForSingleObject(handle, remaining) != 0:
                        raise OSError('Compatibility process handles did not finish cleanup')
            finally:
                for handle in handles:
                    kernel.CloseHandle(handle)
                kernel.CloseHandle(job)
        elif process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)

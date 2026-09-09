from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO

from .common import LiveContractError, sha256_file, utc_now
from .redaction import RedactionSummary, StreamingRedactor


@dataclass
class CapturedLog:
    path: str
    sha256: str
    size: int
    originalSha256: str
    redactionCount: int
    redactionRuleset: str


@dataclass
class ProcessResult:
    pid: int
    exitCode: int | None
    startedAt: str
    finishedAt: str
    timedOut: bool
    operatorCancellationRecorded: bool
    forcedDescendantCleanup: bool
    cleanupComplete: bool
    logsDrained: bool
    stdout: CapturedLog
    stderr: CapturedLog

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class _CaptureThread(threading.Thread):
    def __init__(self, stream: BinaryIO, destination: Path, secrets: list[str]):
        super().__init__(daemon=True)
        self.stream = stream
        self.destination = destination
        self.redactor = StreamingRedactor(secrets)
        self.summary: RedactionSummary | None = None
        self.error: BaseException | None = None

    def run(self) -> None:
        try:
            self.destination.parent.mkdir(parents=True, exist_ok=True)
            with self.destination.open("wb") as output:
                for chunk in iter(lambda: self.stream.read(65536), b""):
                    redacted = self.redactor.feed(chunk)
                    if redacted:
                        output.write(redacted)
                final, self.summary = self.redactor.finish()
                output.write(final)
                output.flush()
                os.fsync(output.fileno())
        except BaseException as error:
            self.error = error
        finally:
            self.stream.close()


if os.name == "nt":
    from ctypes import wintypes

    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    CREATE_SUSPENDED = 0x00000004
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    JobObjectBasicAccountingInformation = 1
    JobObjectExtendedLimitInformation = 9

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.SetThreadExecutionState.argtypes = [wintypes.DWORD]
    _kernel32.SetThreadExecutionState.restype = wintypes.DWORD
    _ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    _ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    _ntdll.NtResumeProcess.restype = wintypes.LONG


class _ProcessTree:
    def __init__(self):
        self.job: int | None = None

    def popen_kwargs(self) -> dict[str, object]:
        if os.name == "nt":
            return {"creationflags": subprocess.CREATE_NO_WINDOW | CREATE_SUSPENDED}
        return {"start_new_session": True}

    def attach(self, process: subprocess.Popen[bytes]) -> None:
        if os.name != "nt":
            return
        job = _kernel32.CreateJobObjectW(None, None)
        if not job:
            process.terminate()
            raise LiveContractError(f"LIVE_JOB_CREATE_FAILED: {ctypes.get_last_error()}")
        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _kernel32.SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(limits), ctypes.sizeof(limits)):
            _kernel32.CloseHandle(job)
            process.terminate()
            raise LiveContractError(f"LIVE_JOB_CONFIGURE_FAILED: {ctypes.get_last_error()}")
        if not _kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)):
            _kernel32.CloseHandle(job)
            process.terminate()
            raise LiveContractError(f"LIVE_JOB_ASSIGN_FAILED: {ctypes.get_last_error()}")
        self.job = job
        resume_status = _ntdll.NtResumeProcess(wintypes.HANDLE(process._handle))
        if resume_status != 0:
            _kernel32.TerminateJobObject(job, 1)
            self.close()
            raise LiveContractError(f"LIVE_PROCESS_RESUME_FAILED: NTSTATUS {resume_status:#x}")

    def active_processes(self) -> int | None:
        if os.name != "nt" or self.job is None:
            return None
        accounting = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
        if not _kernel32.QueryInformationJobObject(
            self.job,
            JobObjectBasicAccountingInformation,
            ctypes.byref(accounting),
            ctypes.sizeof(accounting),
            None,
        ):
            return None
        return int(accounting.ActiveProcesses)

    def terminate(self, process: subprocess.Popen[bytes]) -> None:
        if os.name == "nt" and self.job is not None:
            _kernel32.TerminateJobObject(self.job, 1)
        elif process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)

    def force(self, process: subprocess.Popen[bytes]) -> None:
        if os.name == "nt" and self.job is not None:
            _kernel32.TerminateJobObject(self.job, 1)
        elif process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)

    def close(self) -> None:
        if os.name == "nt" and self.job is not None:
            _kernel32.CloseHandle(self.job)
            self.job = None


class _SystemAwakeLease:
    def acquire(self) -> None:
        if os.name != "nt":
            return
        if not _kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED):
            raise LiveContractError(f"LIVE_SYSTEM_AWAKE_LEASE_FAILED: {ctypes.get_last_error()}")

    def release(self) -> None:
        if os.name == "nt":
            _kernel32.SetThreadExecutionState(ES_CONTINUOUS)


def _log_record(path: Path, summary: RedactionSummary) -> CapturedLog:
    return CapturedLog(
        path=path.name,
        sha256=sha256_file(path),
        size=path.stat().st_size,
        originalSha256=summary.original_sha256,
        redactionCount=summary.redaction_count,
        redactionRuleset=summary.ruleset,
    )


def run_supervised(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    evidence_directory: Path,
    timeout_seconds: int,
    secrets: list[str] | None = None,
) -> ProcessResult:
    if timeout_seconds < 1:
        raise LiveContractError("LIVE_SUPERVISOR_INVALID_TIMEOUT")
    evidence_directory.mkdir(parents=True, exist_ok=True)
    stdout_path = evidence_directory / "workflow.stdout.log"
    stderr_path = evidence_directory / "workflow.stderr.log"
    started = utc_now()
    awake = _SystemAwakeLease()
    awake.acquire()
    try:
        tree = _ProcessTree()
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **tree.popen_kwargs(),
        )
        tree.attach(process)
        assert process.stdout is not None and process.stderr is not None
        stdout_capture = _CaptureThread(process.stdout, stdout_path, secrets or [])
        stderr_capture = _CaptureThread(process.stderr, stderr_path, secrets or [])
        stdout_capture.start()
        stderr_capture.start()
        timed_out = False
        operator_cancelled = False
        forced_descendants = False
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            tree.terminate(process)
        except KeyboardInterrupt:
            operator_cancelled = True
            tree.terminate(process)
        finally:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                tree.force(process)
                forced_descendants = True
                process.wait(timeout=10)
            active = tree.active_processes()
            if active not in (None, 0):
                tree.force(process)
                forced_descendants = True
                time.sleep(0.1)
            stdout_capture.join(timeout=10)
            stderr_capture.join(timeout=10)
            logs_drained = not stdout_capture.is_alive() and not stderr_capture.is_alive()
            cleanup_complete = process.poll() is not None and logs_drained
            tree.close()
        for capture in (stdout_capture, stderr_capture):
            if capture.error is not None:
                raise LiveContractError(f"LIVE_LOG_CAPTURE_FAILED: {capture.error}") from capture.error
            if capture.summary is None:
                raise LiveContractError("LIVE_LOG_CAPTURE_INCOMPLETE")
        return ProcessResult(
            pid=process.pid,
            exitCode=process.returncode,
            startedAt=started,
            finishedAt=utc_now(),
            timedOut=timed_out,
            operatorCancellationRecorded=operator_cancelled,
            forcedDescendantCleanup=forced_descendants,
            cleanupComplete=cleanup_complete,
            logsDrained=logs_drained,
            stdout=_log_record(stdout_path, stdout_capture.summary),
            stderr=_log_record(stderr_path, stderr_capture.summary),
        )
    finally:
        awake.release()

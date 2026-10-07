"""External process evidence only. Never signals a process or opens A's EventStore."""
from datetime import datetime, timezone
import os
import threading

import psutil


class StreamCapture:
    """Full output on disk; at most 8192 characters retained per stream in RAM."""
    def __init__(self, path, tail_chars=8192):
        self.path = path
        self.limit = tail_chars
        self.tail = ''
        self.error = None
        self.lock = threading.Lock()
        self.file = path.open('a', encoding='utf-8', errors='replace')

    def append(self, text):
        with self.lock:
            self.tail = (self.tail + text[-self.limit:])[-self.limit:]
            try:
                self.file.write(text)
                self.file.flush()
            except OSError as error:
                self.error = repr(error)

    def snapshot(self):
        with self.lock:
            return {'path': str(self.path), 'tail': self.tail, 'capture_error': self.error}

    def close(self):
        with self.lock:
            if not self.file.closed:
                self.file.close()


class ProcessProbe:
    """Read-only retained Windows handle, including non-child Bridge/worker exits.

    POSIX cannot recover an arbitrary grandchild's exit code after its parent
    reaps it. That case remains explicitly unknown, never synthesized as zero.
    """
    def __init__(self, process, role, popen=None):
        self.process, self.pid, self.role = process, process.pid, role
        self.popen = popen
        self.recorded = False
        self.handle = None
        self.capture_error = None
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            self.api = ctypes.WinDLL('kernel32', use_last_error=True)
            self.api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            self.api.OpenProcess.restype = wintypes.HANDLE
            self.api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            self.api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            self.api.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
            self.api.CloseHandle.argtypes = [wintypes.HANDLE]
            self.handle = self.api.OpenProcess(0x00100000 | 0x1000, False, self.pid)
            if not self.handle:
                self.capture_error = 'OpenProcess error ' + str(ctypes.get_last_error())

    def poll(self):
        if self.recorded:
            return None
        code, exit_time, source = None, None, None
        if self.handle:
            if self.api.WaitForSingleObject(self.handle, 0) != 0:
                return None
            import ctypes
            from ctypes import wintypes
            status = wintypes.DWORD()
            if self.api.GetExitCodeProcess(self.handle, ctypes.byref(status)):
                code, source = status.value, 'retained_windows_handle'
            times = [wintypes.FILETIME() for _ in range(4)]
            if self.api.GetProcessTimes(self.handle, *(ctypes.byref(t) for t in times)):
                ticks = (times[1].dwHighDateTime << 32) | times[1].dwLowDateTime
                if ticks:
                    exit_time = datetime.fromtimestamp(ticks / 10**7 - 11644473600,
                                                       timezone.utc).isoformat()
        elif self.popen is not None:
            code = self.popen.poll()
            if code is None:
                return None
            source = 'parent_Popen'
        else:
            try:
                if not hasattr(self.process, 'is_running'):
                    self.process = psutil.Process(self.pid)
                if self.process.is_running() and self.process.status() != psutil.STATUS_ZOMBIE:
                    return None
                code = self.process.wait(timeout=0)
                source = 'psutil_wait' if code is not None else 'exit_code_unavailable'
            except psutil.TimeoutExpired:
                return None
            except psutil.NoSuchProcess:
                source = 'process_disappeared_exit_code_unavailable'
            except psutil.AccessDenied as error:
                self.capture_error = repr(error)
                return None  # AccessDenied does not prove exit.
        self.recorded = True
        self.close()
        return {'role': self.role, 'pid': self.pid, 'exit_code': code,
                'exit_time': exit_time, 'exit_time_kind': 'kernel' if exit_time else 'unknown',
                'exit_code_source': source, 'probe_error': self.capture_error,
                'exit_class': 'NORMAL_EXIT' if code == 0 else
                              'ABNORMAL_EXIT' if code is not None else 'EXIT_REASON_UNKNOWN'}

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None

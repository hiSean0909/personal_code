"""Prevent duplicate application instances within the Windows desktop session."""

import ctypes
from ctypes import wintypes


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
INSTANCE_NAME = "Local\\QuickTranslator"


def acquire_instance():
    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, False, INSTANCE_NAME)
    error = ctypes.get_last_error()
    if not handle:
        raise ctypes.WinError(error)
    if error == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None
    return handle


def release_instance(handle):
    kernel32.CloseHandle(handle)

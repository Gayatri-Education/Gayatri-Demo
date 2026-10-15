"""Gayatri AI Platform — Anti-Tampering, Anti-Debugging & Runtime Integrity Protection."""
from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger("gayatri.core.tamper")


def is_debugger_present() -> bool:
    """Detects active Python and Win32 debuggers or instrumentation hooks."""
    # 1. Python trace / debugger hook (pdb, pydevd, ptvsd)
    if sys.gettrace() is not None:
        return True

    # 2. Windows Native API Debugger Detection
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            if k32.IsDebuggerPresent():
                return True
            is_remote = ctypes.c_bool(False)
            if k32.CheckRemoteDebuggerPresent(k32.GetCurrentProcess(), ctypes.byref(is_remote)) and is_remote.value:
                return True
        except Exception:
            pass

    return False


def verify_environment_integrity() -> bool:
    """Verifies that runtime environment does not have unauthorized injection variables."""
    suspicious_env_vars = [
        "PYTHONINSPECT",
        "PYTHONBREAKPOINT",
        "PYDEVD_LOAD_VALUES_ASYNC",
    ]
    for var in suspicious_env_vars:
        val = os.environ.get(var, "")
        if val and val != "0":
            return False
    return True


def enforce_runtime_security() -> bool:
    """Enforces anti-tamper and anti-debugging protection in production distributions.
    
    Returns True if clean, or aborts/returns False if tampering or debugging detected.
    """
    # Only enforce strict termination when running packaged / frozen distribution
    is_frozen = getattr(sys, "frozen", False)
    allow_debug = os.environ.get("GAYATRI_ALLOW_DEBUG") == "1"

    if is_frozen and not allow_debug:
        if is_debugger_present() or not verify_environment_integrity():
            logger.critical("Security Violation: Unauthorized debugging or environment manipulation detected.")
            sys.exit(0)
    return True


def sanitize_runtime_arguments() -> None:
    """Removes unauthorized command-line switches such as Chromium remote debugging flags."""
    forbidden_prefixes = ("--remote-debugging-port", "--js-flags", "--enable-logging")
    sanitized = []
    for arg in sys.argv:
        if any(arg.lower().startswith(prefix) for prefix in forbidden_prefixes):
            logger.warning("Stripped unauthorized execution parameter: %s", arg)
            continue
        sanitized.append(arg)
    sys.argv[:] = sanitized

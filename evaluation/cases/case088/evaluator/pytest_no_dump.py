"""Run official pytest nodes without producing host-side Linux/WSL core dumps."""
import ctypes
import resource
import sys

import pytest

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(4, 0, 0, 0, 0) != 0 or libc.prctl(3, 0, 0, 0, 0) != 0:
    raise RuntimeError("Could not disable process dumpability")
sys.exit(pytest.main(sys.argv[1:]))

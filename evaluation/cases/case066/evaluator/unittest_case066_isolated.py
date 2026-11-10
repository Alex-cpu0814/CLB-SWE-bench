"""Run original legacy unittest cases in fresh processes without changing tests."""
import ctypes
import importlib.util
import json
import pathlib
import resource
import signal
import subprocess
import sys
import unittest

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(4, 0, 0, 0, 0) != 0 or libc.prctl(3, 0, 0, 0, 0) != 0:
    raise RuntimeError('Could not disable dumpability')

def load(node):
    file, cls, method = node.split('::')
    source = pathlib.Path(file)
    spec = importlib.util.spec_from_file_location('official_' + source.stem, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = getattr(module, cls)(method)
    assert isinstance(case, unittest.TestCase)
    return unittest.TestSuite([case])

if '--worker' in sys.argv:
    node = sys.argv[-1]
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(load(node))
    assert result.testsRun == 1
    status = 'SKIPPED' if result.skipped else ('PASSED' if result.wasSuccessful() else 'FAILED')
    print(node + ' ' + status, flush=True)
    sys.exit(0 if result.wasSuccessful() else 1)

nodes = [arg for arg in sys.argv[1:] if arg.startswith('Tests/') and '::' in arg]
assert nodes
if '--collect-only' in sys.argv:
    for node in nodes:
        assert load(node).countTestCases() == 1
        print(node + ' COLLECTED', flush=True)
    sys.exit(0)
failed = False
for node in nodes:
    print('ISOLATED_NODE_BEGIN ' + node, flush=True)
    process = subprocess.run([sys.executable, __file__, '--worker', node], timeout=120)
    result = {'node': node, 'returncode': process.returncode, 'signal': signal.Signals(-process.returncode).name if process.returncode < 0 else None}
    print('ISOLATED_NODE_RESULT ' + json.dumps(result), flush=True)
    if process.returncode < 0:
        print(node + ' FAILED', flush=True)
    elif process.returncode not in (0, 1):
        raise RuntimeError('Unexpected unittest exit: ' + json.dumps(result))
    failed = failed or process.returncode != 0
sys.exit(1 if failed else 0)

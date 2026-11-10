"""Execute original Pillow tester functions, count their assertions, preserve output."""
import ctypes
import importlib.util
import json
import pathlib
import resource
import signal
import subprocess
import sys
import traceback

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(4, 0, 0, 0, 0) != 0 or libc.prctl(3, 0, 0, 0, 0) != 0:
    raise RuntimeError('Could not disable dumpability')

def load(node):
    file, function = node.split('::')
    source = pathlib.Path(file)
    spec = importlib.util.spec_from_file_location('official_' + source.stem, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, getattr(module, function)

if '--worker' in sys.argv:
    node = sys.argv[-1]
    module, function = load(node)
    import tester
    tester._target = module
    tester.run = None  # execute selected function here, avoid atexit rerunning all nodes
    tester._tests = []
    tester.success.count = tester.failure.count = 0
    try:
        function()
        for delayed, args in tester._tests:
            delayed(*args)
    except BaseException:
        traceback.print_exc(file=sys.stdout)
        tester.failure.count += 1
    counts = {'node': node, 'assertions_passed': tester.success.count,
              'assertions_failed': tester.failure.count}
    print('OFFICIAL_TESTER_COUNTS ' + json.dumps(counts), flush=True)
    passed = tester.success.count > 0 and tester.failure.count == 0
    print(node + (' PASSED' if passed else ' FAILED'), flush=True)
    sys.exit(0 if passed else 1)

nodes = [arg for arg in sys.argv[1:] if arg.startswith('Tests/') and '::' in arg]
assert nodes
if '--collect-only' in sys.argv:
    import tester
    tester.run = None
    for node in nodes:
        assert callable(load(node)[1])
        print(node + ' COLLECTED', flush=True)
    sys.exit(0)
failed = False
for node in nodes:
    print('ISOLATED_NODE_BEGIN ' + node, flush=True)
    process = subprocess.run([sys.executable, __file__, '--worker', node], timeout=120)
    result = {'node': node, 'returncode': process.returncode,
              'signal': signal.Signals(-process.returncode).name if process.returncode < 0 else None}
    print('ISOLATED_NODE_RESULT ' + json.dumps(result), flush=True)
    if process.returncode < 0:
        print(node + ' FAILED', flush=True)
    elif process.returncode not in (0, 1):
        raise RuntimeError('Unexpected official tester exit: ' + json.dumps(result))
    failed = failed or process.returncode != 0
sys.exit(1 if failed else 0)

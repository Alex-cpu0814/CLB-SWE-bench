"""Run unchanged official nodes in separate processes, preserving native crash evidence."""
import ctypes
import json
import resource
import signal
import subprocess
import sys

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(4, 0, 0, 0, 0) != 0 or libc.prctl(3, 0, 0, 0, 0) != 0:
    raise RuntimeError('Could not disable process dumpability')
args = sys.argv[1:]
nodes = [x for x in args if x.startswith('Tests/') and '::' in x]
options = [x for x in args if x not in nodes]
if '--collect-only' in args:
    sys.exit(subprocess.call([sys.executable, '/benchmark/pytest_no_dump.py'] + args))
failed = False
for node in nodes:
    print('ISOLATED_NODE_BEGIN ' + node, flush=True)
    result = subprocess.run([sys.executable, '/benchmark/pytest_no_dump.py'] + options + [node])
    details = {'node': node, 'returncode': result.returncode, 'signal': signal.Signals(-result.returncode).name if result.returncode < 0 else None}
    print('ISOLATED_NODE_RESULT ' + json.dumps(details), flush=True)
    if result.returncode < 0:
        print(node + ' FAILED (official test process terminated by ' + details['signal'] + ')', flush=True)
    elif result.returncode != 0 and result.returncode != 1:
        raise RuntimeError('Unexpected pytest process exit: ' + json.dumps(details))
    failed = failed or result.returncode != 0
sys.exit(1 if failed else 0)

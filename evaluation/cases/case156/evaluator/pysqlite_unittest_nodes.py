"""Execute complete upstream unittest cases without rewriting their bodies (Python2 compatible)."""
from __future__ import print_function
import ctypes
import importlib
import resource
import sys
import unittest

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(4, 0, 0, 0, 0) != 0 or libc.prctl(3, 0, 0, 0, 0) != 0:
    raise RuntimeError('Could not disable process dumpability')
collect = '--collect-only' in sys.argv[1:]
nodes = [n for n in sys.argv[1:] if n != '--collect-only']
if not nodes or len(nodes) != len(set(nodes)):
    raise ValueError('Unique original unittest node IDs required')
suite = unittest.TestSuite()
node_by_test = {}
for node in nodes:
    path, cls, method = node.split('::')
    if not path.startswith('lib/test/') or not path.endswith('.py') or not method.startswith('Check'):
        raise ValueError('Expected original pysqlite Check method')
    module = importlib.import_module('pysqlite2.test.' + path[len('lib/test/'):-3])
    if not module.__file__.startswith('/testbed/build/lib.linux-x86_64-2.7/pysqlite2/test/'):
        raise RuntimeError('Unexpected original module path')
    case = getattr(module, cls)(method)
    node_by_test[case.id()] = node
    suite.addTest(case)
if collect:
    for node in nodes:
        print(node)
    sys.exit(0)

class CanonicalResult(unittest.TextTestResult):
    def record(self, case, status):
        print(node_by_test[case.id()] + ' ' + status)
        sys.stdout.flush()
    def addSuccess(self, case):
        unittest.TextTestResult.addSuccess(self, case)
        self.record(case, 'PASSED')
    def addFailure(self, case, err):
        unittest.TextTestResult.addFailure(self, case, err)
        self.record(case, 'FAILED')
    def addError(self, case, err):
        unittest.TextTestResult.addError(self, case, err)
        self.record(case, 'ERROR')
    def addSkip(self, case, reason):
        unittest.TextTestResult.addSkip(self, case, reason)
        self.record(case, 'SKIPPED')

result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=CanonicalResult).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)

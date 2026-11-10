"""Run complete original unittest methods and preserve actual native child results."""
from __future__ import print_function
import glob,imp,json,os,re,subprocess,sys,unittest
child_mode='--child' in sys.argv[1:];collect='--collect-only' in sys.argv[1:]
nodes=[x for x in sys.argv[1:]if x not in ['--child','--collect-only']]
if not nodes or len(nodes)!=len(set(nodes)):raise ValueError('Unique original unittest IDs required')
for node in nodes:
 if not re.match(r'^src/test/python/[A-Za-z0-9_]+\.py::[A-Za-z0-9_]+::test_[A-Za-z0-9_]+$',node):raise ValueError('Original jpy unittest node required')
if not child_mode:
 command=[sys.executable,os.path.abspath(__file__),'--child']+(['--collect-only']if collect else[])+nodes
 child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1,universal_newlines=True)
 starts=[];terminals={}
 for line in child.stdout:
  sys.stdout.write(line);sys.stdout.flush()
  fields=line.rstrip('\n').rsplit(' ',1)
  if len(fields)==2 and fields[0]in nodes:
   if fields[1]=='STARTED':starts.append(fields[0])
   elif fields[1]in ['PASSED','FAILED','ERROR','SKIPPED']:terminals[fields[0]]=fields[1]
 code=child.wait();shell_code=code if code>=0 else 128-code
 for report in sorted(glob.glob('/testbed/hs_err_pid*.log')):
  print('__JVM_FATAL_REPORT_BEGIN__ '+report)
  with open(report)as f:sys.stdout.write(f.read())
  print('__JVM_FATAL_REPORT_END__ '+report)
 if not collect:print('__NATIVE_PROCESS_RESULT__ '+json.dumps({'command':command,'requested_nodes':nodes,'observed_starts':starts,'terminal_statuses':terminals,'returncode':code,'signal':{-11:'SIGSEGV',-6:'SIGABRT'}.get(code),'shell_exit_code':shell_code,'executed':True}))
 sys.exit(shell_code)

import ctypes,resource
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(4,0,0,0,0)!=0 or libc.prctl(3,0,0,0,0)!=0:raise RuntimeError('Could not set process core/dumpability metadata')
suite=unittest.TestSuite();mapping={};modules={}
for node in nodes:
 path,cls,method=node.split('::');source=os.path.realpath('/testbed/'+path)
 if not source.startswith('/testbed/src/test/python/')or not os.path.isfile(source):raise ValueError('Unexpected upstream test path')
 if path not in modules:
  sys.path.insert(0,os.path.dirname(source));modules[path]=imp.load_source(os.path.basename(path)[:-3],source)
 test=getattr(modules[path],cls)(method);mapping[test.id()]=node;suite.addTest(test)
if collect:
 for node in nodes:print(node)
 sys.exit(0)
class CanonicalResult(unittest.TextTestResult):
 def startTest(self,test):
  print(mapping[test.id()]+' STARTED');sys.stdout.flush();unittest.TextTestResult.startTest(self,test)
 def record(self,test,status):print(mapping[test.id()]+' '+status);sys.stdout.flush()
 def addSuccess(self,test):unittest.TextTestResult.addSuccess(self,test);self.record(test,'PASSED')
 def addFailure(self,test,err):unittest.TextTestResult.addFailure(self,test,err);self.record(test,'FAILED')
 def addError(self,test,err):unittest.TextTestResult.addError(self,test,err);self.record(test,'ERROR')
 def addSkip(self,test,reason):unittest.TextTestResult.addSkip(self,test,reason);self.record(test,'SKIPPED')
result=unittest.TextTestRunner(stream=sys.stdout,verbosity=2,resultclass=CanonicalResult).run(suite)
sys.exit(0 if result.wasSuccessful()else 1)

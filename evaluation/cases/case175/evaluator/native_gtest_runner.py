"""Run complete upstream native GoogleTest cases; preserve real native exits/statuses."""
import argparse,hashlib,json,os,pathlib,re,signal,subprocess,sys
parser=argparse.ArgumentParser();parser.add_argument('--binary',required=True);parser.add_argument('--collect-only',action='store_true');parser.add_argument('nodes',nargs='+');args=parser.parse_args()
if len(args.nodes)!=len(set(args.nodes)):raise ValueError('Unique original nodes required')
mapping={}
for node in args.nodes:
 source,name=node.split('::',1)
 if not source.startswith('test/')or not source.endswith('.cpp')or not re.fullmatch(r'[A-Za-z0-9_]+\.[A-Za-z0-9_]+',name):raise ValueError('Original C++ GoogleTest node required')
 mapping[name]=node
binary=pathlib.Path(args.binary).resolve()
if not str(binary).startswith('/testbed/build/')or not binary.is_file():raise ValueError('Unexpected native test binary')
native_filter=':'.join(mapping)
if args.collect_only:
 command=[str(binary),'--gtest_color=no','--gtest_filter='+native_filter,'--gtest_list_tests'];r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 print('__NATIVE_DISCOVERY__ '+json.dumps({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
 if r.returncode:sys.exit(r.returncode if r.returncode>0 else 128-r.returncode)
 suite=None;found=[]
 for line in r.stdout.splitlines():
  if line and not line[0].isspace()and line.endswith('.'):suite=line.strip()
  elif suite and line.startswith('  '):
   name=suite+line.strip().split(' ',1)[0]
   if name in mapping:found.append(mapping[name])
 if set(found)!=set(args.nodes)or len(found)!=len(args.nodes):raise RuntimeError('Original binary discovery mismatch')
 for node in found:print(node)
 sys.exit(0)
guard=pathlib.Path('/benchmark/native_no_core.c');guard_library='/tmp/benchmark_no_core.so'
subprocess.check_call(['cc','-shared','-fPIC','-O2',str(guard),'-o',guard_library])
environment=os.environ.copy();environment['LD_PRELOAD']=guard_library
print('__NATIVE_GTEST_WRAPPER__ '+json.dumps({'guard_source_sha256':hashlib.sha256(guard.read_bytes()).hexdigest(),'guard_scope':'Process dumpability/resource metadata only; no interposed functions, allocator, signal handler or test modification','core_pattern':pathlib.Path('/proc/sys/kernel/core_pattern').read_text().strip()}),flush=True)
command=[str(binary),'--gtest_color=no','--gtest_filter='+native_filter];child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,env=environment)
active=set();starts=[];terminals={}
for line in child.stdout:
 sys.stdout.write(line)
 start=re.match(r'^\[\s*RUN\s*\]\s+(\S+)\s*$',line)
 if start and start.group(1)in mapping:
  name=start.group(1);active.add(name);starts.append(mapping[name]);print(mapping[name]+' STARTED',flush=True)
 terminal=re.match(r'^\[\s*(OK|FAILED|SKIPPED)\s*\]\s+(\S+)(?:\s+.*)?$',line)
 if terminal and terminal.group(2)in active:
  kind,name=terminal.groups();status={'OK':'PASSED','FAILED':'FAILED','SKIPPED':'SKIPPED'}[kind];active.remove(name);terminals[mapping[name]]=status;print(mapping[name]+' '+status,flush=True)
 sys.stdout.flush()
returncode=child.wait();shell_exit=returncode if returncode>=0 else 128-returncode
record={'command':command,'requested_nodes':args.nodes,'observed_starts':starts,'terminal_statuses':terminals,'returncode':returncode,'signal':signal.Signals(-returncode).name if returncode<0 else None,'shell_exit_code':shell_exit,'executed':True}
print('__NATIVE_PROCESS_RESULT__ '+json.dumps(record),flush=True)
sys.exit(shell_exit)

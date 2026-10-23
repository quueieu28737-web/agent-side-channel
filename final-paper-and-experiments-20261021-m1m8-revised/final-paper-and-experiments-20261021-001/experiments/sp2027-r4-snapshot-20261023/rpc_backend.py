"""Persistent supported Codex app-server transport, fresh ephemeral thread per call.

The server process is shared; model contexts are never shared. No host environment
is exposed to the model. All retail actions are returned as structured text.
"""
import atexit
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import tomllib
from common import *

class RPCError(RuntimeError):pass

class Server:
    def __init__(self):
        self.lock=threading.Lock();self.seq=0;self.pending={};self.events={}
        self.tmp=tempfile.TemporaryDirectory(prefix='luna-retail-rpc-',ignore_cleanup_errors=True)
        self.stderr=open(Path(self.tmp.name)/'server.stderr','w',encoding='utf-8')
        self.config={'model_reasoning_effort':'low','web_search':'disabled','project_doc_max_bytes':0,
            'features.shell_tool':False,'features.multi_agent':False,'features.apps':False,'features.plugins':False,
            'features.skip_host_skill_discovery':True,'features.memories':False,'features.shell_snapshot':False,
            'features.hooks':False,'suppress_unstable_features_warning':True}
        cfg=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'config.toml'
        if cfg.exists():
            # Read server NAMES only to disable configured connectors. No credential values are copied.
            names=tomllib.loads(cfg.read_text(encoding='utf-8')).get('mcp_servers',{})
            for name in names:self.config[f'mcp_servers.{name}.enabled']=False
        command=[shutil.which('codex'),'app-server','--stdio']
        for key,val in self.config.items():command+=['-c',key+'='+json.dumps(val)]
        self.proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,
            text=True,encoding='utf-8',bufsize=1,cwd=self.tmp.name,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        threading.Thread(target=self.reader,daemon=True).start()
        self.rpc('initialize',{'clientInfo':{'name':'luna_retail_benchmark','version':'1.0'},
            'capabilities':{'experimentalApi':True}})
        self.send({'method':'initialized','params':{}})
        atexit.register(self.close)

    def send(self,obj):
        with self.lock:
            self.proc.stdin.write(json.dumps(obj,ensure_ascii=False)+'\n');self.proc.stdin.flush()

    def reader(self):
        try:
            for line in self.proc.stdout:
                try:e=json.loads(line)
                except ValueError:continue
                if 'id' in e and 'method' not in e:
                    if e['id'] in self.pending:self.pending[e['id']].put(e)
                    continue
                if 'id' in e:
                    # No dynamic or host tool request is part of this interface.
                    self.send({'id':e['id'],'error':{'code':-32601,'message':'Host tools disabled by experiment'}})
                params=e.get('params',{});tid=params.get('threadId') or params.get('thread',{}).get('id')
                if tid in self.events:self.events[tid].put(e)
        finally:
            for q in self.pending.values():q.put({'error':{'message':'App-server exited'}})
            for q in self.events.values():q.put({'method':'transport/closed'})

    def rpc(self,method,params,timeout=120):
        with self.lock:
            self.seq+=1;ident=self.seq;q=queue.Queue();self.pending[ident]=q
        self.send({'id':ident,'method':method,'params':params})
        try:reply=q.get(timeout=timeout)
        except queue.Empty as e:raise RPCError('RPC timeout: '+method) from e
        finally:self.pending.pop(ident,None)
        if 'error' in reply:raise RPCError(str(reply['error']))
        return reply['result']

    def infer(self,prompt,attempt,timeout=180):
        started=time.monotonic()
        params={'model':MODEL,'modelProvider':'openai','allowProviderModelFallback':False,
            'ephemeral':True,'cwd':self.tmp.name,'environments':[],
            'approvalPolicy':'never','sandbox':'read-only','dynamicTools':[],
            'baseInstructions':(HERE/'model_instructions.txt').read_text(encoding='utf-8'),
            'developerInstructions':'Return one structured retail decision only. No external environment is available.',
            'config':self.config}
        write(attempt/'thread_request.json',params)
        r=self.rpc('thread/start',params);write(attempt/'thread_response.json',r)
        if r['model']!=MODEL or r['modelProvider']!='openai':raise RPCError('Model/provider mismatch')
        if r.get('instructionSources'):raise RPCError('Unexpected instruction source: '+str(r['instructionSources']))
        tid=r['thread']['id'];q=queue.Queue();self.events[tid]=q
        usage={};answer=None;turnid=None
        try:
            turn=self.rpc('turn/start',{'threadId':tid,'model':MODEL,'effort':'low','environments':[],
                'input':[{'type':'text','text':prompt}],'outputSchema':read(HERE/'action.schema.json')})
            turnid=turn['turn']['id']
            with (attempt/'events.jsonl').open('w',encoding='utf-8',newline='\n') as f:
                deadline=time.monotonic()+timeout
                while True:
                    try:e=q.get(timeout=max(.01,deadline-time.monotonic()))
                    except queue.Empty as exc:raise RPCError('Model turn timeout') from exc
                    f.write(json.dumps(e,ensure_ascii=False)+'\n');f.flush()
                    method=e.get('method');p=e.get('params',{})
                    if method=='transport/closed':raise RPCError('Transport closed')
                    if method=='thread/tokenUsage/updated':
                        u=p['tokenUsage']['total']
                        usage={a:u.get(b,0) for a,b in [('input_tokens','inputTokens'),('cached_input_tokens','cachedInputTokens'),
                            ('output_tokens','outputTokens'),('reasoning_output_tokens','reasoningOutputTokens')]}
                    if method in ('item/started','item/completed'):
                        item=p.get('item',{});kind=item.get('type')
                        if kind not in ('userMessage','agentMessage','reasoning'):
                            raise RPCError('Unexpected host tool/item: '+str(kind))
                        if method=='item/completed' and kind=='agentMessage':answer=item.get('text')
                    if method=='item/tool/call':raise RPCError('Unexpected host tool call')
                    if method=='turn/completed':
                        if p['turn']['status']!='completed':raise RPCError('Failed turn: '+str(p['turn']))
                        break
            if answer is None:raise RPCError('No final answer')
            parsed=json.loads(answer);write(attempt/'answer.json',parsed)
            return {'answer':parsed,'usage':usage,'elapsed_seconds':time.monotonic()-started,
                'requested_model':MODEL,'reported_model':r['model'],'interface':'codex-app-server',
                'reasoning_effort':'low','instruction_sources':r.get('instructionSources',[])}
        finally:
            if turnid:
                try:self.rpc('turn/interrupt',{'threadId':tid,'turnId':turnid},timeout=10)
                except Exception:pass
            try:self.rpc('thread/unsubscribe',{'threadId':tid},timeout=10)
            except Exception:pass
            self.events.pop(tid,None)

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:self.proc.kill()
        self.stderr.close()
        self.tmp.cleanup()

_server=None
_lock=threading.Lock()
def server():
    global _server
    with _lock:
        if _server is None:_server=Server()
    return _server

if __name__=='__main__':
    import sys
    dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=True)
    for i in range(2):
        d=dest/str(i);d.mkdir(exist_ok=True)
        print(json.dumps(server().infer('Return action respond, arguments_json {}, and content LUNA_READY.',d)),flush=True)

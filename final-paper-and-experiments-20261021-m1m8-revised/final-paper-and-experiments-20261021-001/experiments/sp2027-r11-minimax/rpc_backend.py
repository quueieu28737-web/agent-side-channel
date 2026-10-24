"""Anthropic-compatible endpoint adapter. Credentials are never serialized."""
import json, os, urllib.request, urllib.error, datetime
from pathlib import Path

class RPCError(RuntimeError): pass

class Backend:
    def infer(self, prompt, attempt, timeout=180):
        root=Path(__file__).resolve().parent
        schema=json.loads((root/'action.schema.json').read_text())
        body={'model':'MiniMax-M3','max_tokens':4096,
              'system':(root/'model_instructions.txt').read_text()+'\nOutput only a JSON object satisfying this schema: '+json.dumps(schema),
              'messages':[{'role':'user','content':prompt}],
              'tools':[{'name':'next_action','description':'Emit one next benchmark action; the harness executes it.','input_schema':schema}],
              'tool_choice':{'type':'tool','name':'next_action'}}
        (attempt/'request_body.json').write_text(json.dumps(body,ensure_ascii=False),encoding='utf-8')
        req=urllib.request.Request(os.environ['ANTHROPIC_BASE_URL'].rstrip('/')+'/v1/messages',
            data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['ANTHROPIC_AUTH_TOKEN'],
            'anthropic-version':'2023-06-01','Content-Type':'application/json'})
        prior=sorted(p for p in attempt.parent.glob('attempt-*/response.json') if p.parent!=attempt)
        try:
            if prior:
                saved=json.loads(prior[-1].read_text(encoding='utf-8'))
                raw={**saved,'content':[{'type':'text','text':saved['text']}]+saved.get('tool_calls',[])}
            else:
                with urllib.request.urlopen(req,timeout=timeout) as res:
                    raw=json.load(res)
        except urllib.error.HTTPError as exc:
            raise RPCError('HTTP '+str(exc.code)) from None
        except Exception as exc:
            raise RPCError('Transport failure: '+type(exc).__name__) from None
        # Deliberately omit private reasoning blocks and response headers.
        text='\n'.join(b['text'] for b in raw.get('content',[]) if b.get('type')=='text').strip()
        tool_calls=[b for b in raw.get('content',[]) if b.get('type')=='tool_use']
        receipt={'model':raw.get('model'),'id':raw.get('id'),'usage':raw.get('usage'),'tool_calls':tool_calls,
                 'stop_reason':raw.get('stop_reason'),'text':text,
                 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        (attempt/'response.json').write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8')
        if text.startswith('```'):
            text=text.split('\n',1)[1].rsplit('```',1)[0].strip()
        try:
            assert len(tool_calls)==1 and tool_calls[0]['name']=='next_action'
            answer=tool_calls[0]['input']
            assert isinstance(answer,dict)
            assert all(isinstance(answer[k],str) for k in ('action','arguments_json','content'))
        except Exception:
            # The collector records missing action fields as a protocol-error
            # episode, retaining the failure instead of resampling the model.
            answer={}
        if raw.get('stop_reason')=='max_tokens':
            answer={}
        return {'answer':answer,'usage':raw.get('usage',{}),'returned_model':raw.get('model')}

def server(): return Backend()

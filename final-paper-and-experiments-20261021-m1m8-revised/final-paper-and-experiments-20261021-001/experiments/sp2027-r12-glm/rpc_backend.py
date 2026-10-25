"""GLM OpenAI-compatible native tool adapter; authenticated TLS required."""
import json,os,ssl,urllib.request,urllib.error,datetime
from pathlib import Path

class RPCError(RuntimeError):pass

class Backend:
    def infer(self,prompt,attempt,timeout=180):
        root=Path(__file__).resolve().parent
        schema=json.loads((root/'action.schema.json').read_text())
        body={'model':'glm-5.3-flash','max_tokens':16384,'parallel_tool_calls':False,
            'messages':[{'role':'system','content':(root/'model_instructions.txt').read_text()+'\nOutput one action satisfying this schema: '+json.dumps(schema)},
                        {'role':'user','content':prompt}],
            'tools':[{'type':'function','function':{'name':'next_action','description':'Emit one next benchmark action; the harness executes it.','parameters':schema}}],
            'tool_choice':{'type':'function','function':{'name':'next_action'}}}
        (attempt/'request_body.json').write_text(json.dumps(body,ensure_ascii=False),encoding='utf-8')
        prior=sorted(p for p in attempt.parent.glob('attempt-*/response.json') if p.parent!=attempt)
        if prior:
            receipt=json.loads(prior[-1].read_text(encoding='utf-8'))
        else:
            context=ssl.create_default_context(cafile=os.environ.get('GLM_CA_BUNDLE') or None)
            req=urllib.request.Request(os.environ['GLM_BASE_URL'].rstrip('/')+'/chat/completions',
                data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GLM_API_KEY'],'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req,timeout=timeout,context=context) as res:raw=json.load(res)
            except urllib.error.HTTPError as exc:raise RPCError('HTTP '+str(exc.code)) from None
            except Exception as exc:raise RPCError('Transport failure: '+type(exc).__name__) from None
            choice=(raw.get('choices') or [{}])[0];msg=choice.get('message',{});calls=[]
            for call in msg.get('tool_calls') or []:
                f=call.get('function',{})
                try:args=json.loads(f.get('arguments',''))
                except (ValueError,TypeError):args=None
                calls.append({'type':'tool_use','id':call.get('id'),'name':f.get('name'),'input':args,'arguments_raw':f.get('arguments')})
            usage=raw.get('usage',{})
            receipt={'model':raw.get('model'),'id':raw.get('id'),'tool_calls':calls,'text':msg.get('content') or '',
                'provider_usage':usage,'usage':{'input_tokens':usage.get('prompt_tokens',0),'output_tokens':usage.get('completion_tokens',0)},
                'stop_reason':choice.get('finish_reason'),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        # No authorization headers or private reasoning are persisted.
        (attempt/'response.json').write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8')
        try:
            calls=receipt['tool_calls'];assert len(calls)==1 and calls[0]['name']=='next_action'
            answer=calls[0]['input'];assert isinstance(answer,dict)
            assert all(isinstance(answer[k],str) for k in ('action','arguments_json','content'))
            assert receipt['stop_reason']!='length'
        except Exception:
            answer={}
        error = None
        if receipt['stop_reason']=='length': error='output_token_limit'
        elif len(receipt['tool_calls'])!=1: error='tool_call_count:'+str(len(receipt['tool_calls']))
        elif not answer: error='invalid_action_schema'
        return {'protocol_error':error,'answer':answer,'usage':receipt['usage'],'returned_model':receipt['model']}

def server():return Backend()

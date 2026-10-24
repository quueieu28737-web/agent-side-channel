"""Read-only feasibility inventory; no captures, attacker fitting, scoring, or LLM calls."""
import ast,json,hashlib,re
from pathlib import Path
from collections import Counter,defaultdict
H=Path(__file__).resolve().parent;E=H.parent;V=E/'tau-cover-bridge/vendor';R4=E/'sp2027-r4-snapshot-20261023';FULL=E/'sp2027-r4-full-20261023'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=V/'tau_bench__envs__retail__tasks_test.py';tree=ast.parse(source.read_text());expr=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='TASKS_TEST' for x in n.targets))
tasks=[]
for tid,node in enumerate(expr.elts):
 kw={k.arg:k.value for k in node.keywords};actions=[]
 for a in kw['actions'].elts:
  q={k.arg:k.value for k in a.keywords};actions.append(dict(name=ast.literal_eval(q['name']),kwargs=ast.literal_eval(q['kwargs'])))
 tasks.append(dict(task=tid,user=ast.literal_eval(kw['user_id']),instruction=ast.literal_eval(kw['instruction']),actions=actions))
orders=read(V/'tau_bench__envs__retail__data__orders.json');products=read(V/'tau_bench__envs__retail__data__products.json');users=read(V/'tau_bench__envs__retail__data__users.json');split=read(R4/'split.json');ids=split['train']+split['test'];assert len(set(ids))==115
WRITES={'cancel_pending_order','modify_pending_order_address','modify_pending_order_items','modify_pending_order_payment','modify_user_address','return_delivered_order_items','exchange_delivered_order_items'}
episodes=[];paths=[]
for arm in ['baseline','rules']:
 for tid in ids:
  for rep in [0,1,2]:
   rel=Path('runs')/arm/f'task-{tid:03d}-repeat-{rep}'/'episode.json';p=R4/rel
   if not p.exists():p=FULL/'delta'/rel
   e=read(p);assert e['task']==tid and e['user']==tasks[tid]['user'];episodes.append({k:e[k] for k in ['task','user','prompt','repeat','has_cancel','has_return']}|{'calls':[{k:c[k] for k in ['name','kwargs','err'] if k in c} for c in e['calls']]});paths.append(p)
assert len(episodes)==690
write(H/'episode_metadata.json',episodes)
instances=[];strata=defaultdict(list)
for t in tasks:
 writes=[a for a in t['actions'] if a['name'] in WRITES];verbs=sorted({a['name'] for a in writes})
 t['write_verbs']=verbs;t['gold_write_calls']=len(writes)
 for j,a in enumerate(writes):
  oid=a['kwargs'].get('order_id');order=orders.get(oid);items=[];scope='unavailable'
  if order:
   if 'item_ids' in a['kwargs']:
    selected=set(a['kwargs']['item_ids']);items=[i for i in order['items'] if i['item_id'] in selected];scope='selected_initial_order_items' if not (selected-{i['item_id'] for i in items}) else 'selected_items_not_all_in_initial_order'
   else:items=order['items'];scope='entire_initial_order'
  row=dict(task=t['task'],user=t['user'],verb=a['name'],gold_write_index=j,order_id=oid,only_gold_write_verb=len(verbs)==1,single_gold_write_call=len(writes)==1,kwargs=a['kwargs'],item_scope=scope,product_names=sorted({i['name'] for i in items}),product_ids=sorted({i['product_id'] for i in items}),item_ids=sorted({i['item_id'] for i in items}),selected_item_count=len(items),order_item_count=len(order['items']) if order else None,order_status=order.get('status') if order else None,order_total=sum(i['price'] for i in order['items']) if order else None,selected_total=sum(i['price'] for i in items) if items else None,order_state=order.get('address',{}).get('state') if order else None,payment_types=sorted({x.get('payment_method_id','').split('_')[0] for x in order.get('payment_history',[])}) if order else [],missing_selected_item_ids=sorted(set(a['kwargs'].get('item_ids',[]))-{i['item_id'] for i in items}) if order else sorted(a['kwargs'].get('item_ids',[])))
  instances.append(row);strata[a['name']].append(row)
summary=[]
for verb,rr in strata.items():
 strict=[r for r in rr if r['single_gold_write_call']];es=[e for e in episodes if e['task'] in {r['task'] for r in strict}];matched=[e for e in es if len([c for c in e['calls'] if c['name'] in WRITES])==1 and next(c for c in e['calls'] if c['name'] in WRITES)['name']==verb]
 summary.append(dict(verb=verb,gold_action_instances=len(rr),tasks=len({r['task'] for r in rr}),customers=len({r['user'] for r in rr}),single_gold_write_tasks=len(strict),single_gold_write_customers=len({r['user'] for r in strict}),single_gold_order_instances=len({(r['user'],r['order_id']) for r in strict if r['order_id']}),eligible_original_episodes=len(es),actual_single_same_verb_episodes=len(matched),actual_single_same_verb_tasks=len({e['task'] for e in matched}),actual_single_same_verb_customers=len({e['user'] for e in matched})))
write(H/'source_inventory.json',dict(status='feasibility only; no attacker fitted or predictions read',episodes=690,tasks=115,customers=len({e['user'] for e in episodes}),label_definition='collect.py:124-128 uses reference task.actions names, not observed episode.calls; action-class labels are not non-action sensitive attributes.',native_product_names=sorted({p['name'] for p in products.values()}),order_fields=sorted({k for x in orders.values() for k in x}),user_fields=sorted({k for x in users.values() for k in x}),strata=summary,source_sha256={str(p.relative_to(E)):sha(p) for p in [source,V/'tau_bench__envs__retail__data__orders.json',V/'tau_bench__envs__retail__data__products.json',V/'tau_bench__envs__retail__data__users.json',R4/'collect.py',R4/'split.json']}))
write(H/'gold_attribute_instances.json',instances);write(H/'task_action_inventory.json',tasks)
print(json.dumps(read(H/'source_inventory.json'),indent=2))


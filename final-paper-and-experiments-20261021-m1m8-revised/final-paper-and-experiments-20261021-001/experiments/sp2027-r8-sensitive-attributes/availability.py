"""Attribute/stratum counts only. Never reads traffic lengths, predictions, or attacker scores."""
import json,hashlib
from pathlib import Path
from collections import defaultdict,Counter
H=Path(__file__).resolve().parent;E=H.parent;V=E/'tau-cover-bridge/vendor'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
rows=read(H/'episode_metadata.json');gold=read(H/'gold_attribute_instances.json');orders=read(V/'tau_bench__envs__retail__data__orders.json');products=read(V/'tau_bench__envs__retail__data__products.json')
DIGITAL={'Action Camera','Bluetooth Speaker','Digital Camera','E-Reader','Gaming Mouse','Headphones','Indoor Security Camera','Laptop','Mechanical Keyboard','Portable Charger','Smart Thermostat','Smart Watch','Smartphone','Tablet','Wireless Earbuds'}
WRITES={'cancel_pending_order','modify_pending_order_address','modify_pending_order_items','modify_pending_order_payment','modify_user_address','return_delivered_order_items','exchange_delivered_order_items'}
instances=[];excluded=Counter()
for e in rows:
 for i,c in enumerate(e['calls']):
  if c['name'] not in WRITES:continue
  kw=c.get('kwargs',{});oid=kw.get('order_id');o=orders.get(oid)
  if not o:excluded[c['name']+':no_initial_order']+=1;continue
  if o['user_id']!=e['user']:excluded[c['name']+':other_customer_order']+=1;continue
  ids=kw.get('item_ids');items=[x for x in o['items'] if x['item_id'] in set(ids)] if ids else o['items']
  if ids and set(ids)-{x['item_id'] for x in items}:excluded[c['name']+':unresolved_selected_item']+=1;continue
  if ids is not None and not ids:excluded[c['name']+':empty_item_list']+=1;continue
  names=sorted({x['name'] for x in items});pid=sorted({x['product_id'] for x in items});itemids=sorted({x['item_id'] for x in items})
  single=ids is not None and len(ids)==1 and len(itemids)==1
  instances.append(dict(episode=f"{e['prompt']}-t{e['task']:03d}-r{e['repeat']}",task=e['task'],prompt=e['prompt'],repeat=e['repeat'],user=e['user'],call_index=i,verb=c['name'],order_id=oid,item_ids=itemids,product_names=names,product_ids=pid,request_item_list_length=len(ids) if ids is not None else None,single_requested_item=single,call_error=bool(c.get('err')),selected_has_digital_device=int(bool(set(names)&DIGITAL)),order_has_digital_device=int(any(x['name'] in DIGITAL for x in o['items'])),order_item_rows=len(o['items']),order_distinct_items=len({x['item_id'] for x in o['items']}),order_multi_item=int(len(o['items'])>1),order_status=o['status'],state=o.get('address',{}).get('state'),selected_total=sum(x['price'] for x in items)))
def summary(rr,label):
 pos={r['user'] for r in rr if r[label]==1};neg={r['user'] for r in rr if r[label]==0}
 sig=lambda r:(r['user'],r['verb'],r['order_id'],tuple(r['item_ids']))
 return dict(call_rows=len(rr),episodes=len({r['episode'] for r in rr}),tasks=len({r['task'] for r in rr}),customers=len(pos|neg),positive_customers=len(pos),negative_customers=len(neg),mixed_customers=len(pos&neg),positive_only_customers=len(pos-neg),negative_only_customers=len(neg-pos),orders=len({(r['user'],r['order_id']) for r in rr}),distinct_action_instances=len({sig(r) for r in rr}),positive_action_instances=len({sig(r) for r in rr if r[label]}),negative_action_instances=len({sig(r) for r in rr if not r[label]}),native_product_types=dict(Counter(n for r in {sig(r):r for r in rr}.values() for n in r['product_names'])),error_rows=sum(r['call_error'] for r in rr))
reports=[]
for verb in sorted({r['verb'] for r in instances}):
 for scope in ['all_resolved_order_calls','single_requested_item']:
  rr=[r for r in instances if r['verb']==verb and (scope=='all_resolved_order_calls' or r['single_requested_item'])]
  for label in ['selected_has_digital_device','order_has_digital_device','order_multi_item']:
   reports.append(dict(verb=verb,scope=scope,label=label,**summary(rr,label)))
write(H/'actual_attribute_instances.json',instances);write(H/'attribute_availability.json',dict(status='design-only counts, no traffic-length distributions, models or prediction results accessed',category_mapping=dict(label='selected_has_digital_device',native_field='initial order item.name, cross-referenced product_id to catalog product.name',positive_names=sorted(DIGITAL),negative='all other native product names; synthetic posthoc semantic grouping, not a benchmark-native taxonomy'),excluded_actual_write_calls=dict(excluded),reports=reports))
for r in reports:
 if r['label']=='selected_has_digital_device':print(r['verb'],r['scope'],'rows',r['call_rows'],'task',r['tasks'],'cust',r['customers'],'pos/neg/mixed',r['positive_customers'],r['negative_customers'],r['mixed_customers'],'uniqueinstances',r['distinct_action_instances'])
print('EXCLUDED',dict(excluded))

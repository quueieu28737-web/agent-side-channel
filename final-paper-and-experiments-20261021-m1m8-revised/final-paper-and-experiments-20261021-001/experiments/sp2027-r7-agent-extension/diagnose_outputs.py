from common import *
import time

def main():
 rows=[]
 for file in ['D2_predictions.json','network_predictions.json']:
  for r in read(HERE/file):
   scores=r['scores'];pred=r['predictions'];entry={k:r[k] for k in ['target','view','prompt','attacker']}
   if 'condition' in r:entry['condition']=r['condition']
   entry.update({'source':file,'test_rows':len(scores),'score_min':min(scores),'score_max':max(scores),'constant_score':max(scores)-min(scores)<=1e-12,'constant_prediction':len(set(pred))==1})
   rows.append(entry)
 summary={}
 for name in sorted(set(r['attacker'] for r in rows)):
  group=[r for r in rows if r['attacker']==name];summary[name]={'models':len(group),'constant_score_models':sum(r['constant_score'] for r in group),'constant_score_fraction':sum(r['constant_score'] for r in group)/len(group),'constant_prediction_models':sum(r['constant_prediction'] for r in group)}
 write(HERE/'constant_output_diagnostic.json',{'tolerance':1e-12,'per_model':rows,'summary':summary,'defaults':read(HERE/'gboost_default_diagnostic.json'),'interpretation':'Fixed inherited gboost underpowered with 29 training rows; constant output must not be interpreted as no leakage. No hyperparameters changed.'})
 print(summary)
if __name__=='__main__':
 while not ((HERE/'D2_predictions.json').exists() and (HERE/'network_predictions.json').exists()):time.sleep(20)
 main()

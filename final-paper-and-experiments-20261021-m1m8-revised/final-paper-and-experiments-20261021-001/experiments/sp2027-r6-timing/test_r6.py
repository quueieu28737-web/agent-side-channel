"""Focused correctness checks explicitly authorized as part of experiment verification."""
import unittest
import numpy as np
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from features import features, cutpoint
from analyze import weights, metric_draws
from transport import encode, decode, CELL, PAYLOAD
from experiment import Cover
from r6common import inputs

class Checks(unittest.TestCase):
    def test_views(self):
        r=[[1,100,0],[-1,200,1000000],[1,90,3000000],[-1,150,5000000]]
        changed_time=[[d,n,t*17] for d,n,t in r]
        changed_size=[[d,n*7,t] for d,n,t in r]
        self.assertEqual(features(r,'size_order'),features(changed_time,'size_order'))
        self.assertEqual(features(r,'timing_direction'),features(changed_size,'timing_direction'))
        self.assertNotEqual(features(r,'joint'),features(changed_time,'joint'))
    def test_encoding(self):
        obj={'id':1,'text':'real observation'}
        for cap in (0,4,512):
            frame=encode(obj,cap)
            self.assertEqual(int.from_bytes(frame[:4],'big'),len(frame)-4)
            self.assertEqual(decode(frame[4:]),obj)
        self.assertEqual(PAYLOAD+4,CELL)
    def test_metrics(self):
        y=np.array([0,1,0,1,1,0]);p=np.array([0,0,1,1,1,0]);s=np.array([.1,.2,.4,.8,.9,.4])
        w=weights(['a','b','c','d','e','f'],20)
        ba,au=metric_draws(y,s,p,w)
        self.assertAlmostEqual(ba[0],balanced_accuracy_score(y,p))
        self.assertAlmostEqual(au[0],roc_auc_score(y,s))
        for i in range(1,len(w)):
            if w[i,y==0].sum() and w[i,y==1].sum():
                self.assertAlmostEqual(ba[i],balanced_accuracy_score(y,p,sample_weight=w[i]))
                self.assertAlmostEqual(au[i],roc_auc_score(y,s,sample_weight=w[i]))
    def test_cut(self):
        self.assertEqual(cutpoint([.01,.01,.99,.99]),2)
    def test_split_and_prefix(self):
        rows,split,cal=inputs()
        tr=[e for e in rows if e['task'] in split['train']];te=[e for e in rows if e['task'] in split['test']]
        self.assertEqual((len(tr),len(te)),(414,276))
        self.assertFalse(set(e['user'] for e in tr)&set(e['user'] for e in te))
        e=tr[0];a,b=Cover(e,cal),Cover(e,cal)
        for c in e['calls'][:3]:
            self.assertEqual(a.before(),b.before());a.observe(c['name']);b.observe(c['name'])
        self.assertEqual(a.deficits(),b.deficits())

if __name__=='__main__':unittest.main()

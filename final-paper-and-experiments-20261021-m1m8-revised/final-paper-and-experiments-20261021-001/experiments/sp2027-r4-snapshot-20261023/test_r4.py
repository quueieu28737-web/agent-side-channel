"""Local unit checks only; these fixtures are never scientific observations."""
import copy
import unittest
from common import *
from defense import cover_episode,fit_calibration
from evaluate import count_rule,scalar_summary
import numpy as np

class R4Tests(unittest.TestCase):
    def test_group_split(self):
        s=read(HERE/'split.json');_,_,_,tasks=load()
        self.assertEqual(set(s['train'])|set(s['test']),set(range(len(tasks))))
        self.assertFalse(set(s['train'])&set(s['test']))
        self.assertFalse({tasks[i].user_id for i in s['train']}&{tasks[i].user_id for i in s['test']})
    def test_calibration_rejects_test_rows(self):
        tid=read(HERE/'split.json')['test'][0]
        with self.assertRaises(AssertionError):fit_calibration([{'task':tid}],None,{}, {})
    def test_threshold_is_training_only(self):
        _,p,a=count_rule([0,1,2,3],np.array([0,0,1,1]),[0,4])
        _,q,b=count_rule([0,1,2,3],np.array([0,0,1,1]),[0,400000])
        self.assertEqual(a,b);self.assertEqual(a,2)
        self.assertEqual(p.tolist(),q.tolist())
    def test_real_overflow_is_not_dropped(self):
        e={'task':0,'repeat':0,'prompt':'baseline','user':'heldout',
           'calls':[{'name':'unknown_test_verb','req':9,'resp':2,'err':False}]*3}
        cal={'template':{},'donors':{},'shape_emit_probability':.6}
        before=copy.deepcopy(cal)
        calls,flags=cover_episode(e,cal,{}, {'orders':{},'users':{},'products':{}})
        self.assertEqual(len(calls),3);self.assertTrue(flags['template_overflow'])
        self.assertEqual(cal,before)
    def test_bootstrap_clusters_repeats(self):
        a=scalar_summary([0,1],[{'task':0},{'task':1}])
        b=scalar_summary([0,0,0,1,1,1],[{'task':i//3} for i in range(6)])
        self.assertEqual(a,b)
    def test_prompt_has_no_reference_program(self):
        self.assertNotIn('task.actions',RULES);self.assertNotIn('task.outputs',RULES)
        self.assertIn('Do not add unrelated calls',RULES)

if __name__=='__main__':unittest.main()

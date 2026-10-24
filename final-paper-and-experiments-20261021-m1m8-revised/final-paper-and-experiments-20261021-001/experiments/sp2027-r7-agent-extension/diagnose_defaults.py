from common import *
import evaluate_d2 as d2
import datetime
m=d2.ev.MODELS['gboost']();params=m.get_params()
write(HERE/'gboost_default_diagnostic.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_model_class':type(m).__name__,'params':params,'training_rows_per_prompt':29,'minimum_rows_for_two_leaves':2*params['min_samples_leaf'],'expected_limit':'29 rows is less than 2*20=40; unchanged inherited defaults prevent a split. Actual constant-output fractions will be checked from retained predictions after fixed analysis.','model_changed':False})
print(read(HERE/'gboost_default_diagnostic.json'))

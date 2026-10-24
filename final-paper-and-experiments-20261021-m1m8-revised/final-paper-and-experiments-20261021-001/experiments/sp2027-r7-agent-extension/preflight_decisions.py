from common import *
import verify_decisions as vd
import traceback
try:
 vd.verify(HERE,HERE/'preflight_unexpected_complete.json')
except AssertionError:
 frames=traceback.extract_tb(sys.exc_info()[2]);last=frames[-1]
 expected=last.line=='assert len(rows)==150'
 write(HERE/'decision_preflight.json',{'expected_incomplete_only':expected,'last_check':last.line,'exception':traceback.format_exc().replace(str(Path.home()),'<USER_HOME>'),'complete':False})
 print(read(HERE/'decision_preflight.json'))

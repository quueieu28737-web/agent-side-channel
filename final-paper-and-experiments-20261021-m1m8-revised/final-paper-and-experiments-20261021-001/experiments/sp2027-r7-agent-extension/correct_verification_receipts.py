"""Add explicit dispatch-vs-executed counters; preserve original frozen-verifier receipts."""
from common import *

def main():
 for source,alignment,dest in [('formal_validation.json','decision_alignment.json','formal_validation_corrected.json'),('public_validation.json','public_decision_alignment.json','public_validation_corrected.json')]:
  if not (HERE/source).exists() or not (HERE/alignment).exists():continue
  old=read(HERE/source);a=read(HERE/alignment)
  assert old['real_tool_calls']==a['tool_dispatch_attempts'] and old['model_calls']==a['model_calls']
  new=dict(old,real_tool_calls=a['real_tool_calls'],tool_dispatch_attempts=a['tool_dispatch_attempts'],unknown_tool_attempts=a['unknown_tool_attempts'],legacy_receipt=source,legacy_receipt_sha256=sha(HERE/source),decision_alignment=alignment,decision_alignment_sha256=sha(HERE/alignment),correction='Original frozen verifier labelled all dispatch attempts real_tool_calls. This derived receipt counts only known simulator-tool invocations as real; original receipt and scientific outputs are unchanged.')
  write(HERE/dest,new)
 print('STRICT_TOOL_COUNTER_RECEIPTS_READY')
if __name__=='__main__':main()

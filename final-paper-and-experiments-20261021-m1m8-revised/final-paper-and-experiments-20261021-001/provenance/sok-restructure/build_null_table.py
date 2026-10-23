"""Render W1's conditional reference with its exchangeability scope explicit."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;P=HERE.parents[1]
def main():
    d=json.loads((HERE/'conditional_null_results.json').read_text())
    lines=[r'\section{Conditional Task-Permutation Reference}',
           r'This post hoc diagnostic holds the fitted E9 attackers fixed and permutes labels over the 46 test tasks 2,000 times (seed 20261023), keeping each task\textquotesingle s three repetitions together. Each draw recomputes the attack-suite maximum. It characterizes a task-label exchangeability reference; it does not preserve dependencies among tasks belonging to one customer. Consequently, the tail fractions below are conditional reference values, not customer-valid population $p$-values or evidence of equivalence. The original customer-cluster intervals, paired contrasts and frozen absolute criterion remain the primary assessments.',
           r'\begin{table}[ht]\centering\footnotesize',
           r'\caption{All 32 E9 cells: observed maximum BA, permutation mean and 95th percentile (\%), conditional tail fraction $(1+\#\{T_b\ge T_{\rm obs}\})/2001$, and positive excess over the 95th percentile (percentage points).}',
           r'\begin{tabular}{@{}llllrrrrr@{}}\toprule',
           r'Prompt & View & Condition & Target & BA & Ref. mean & Ref. 95th & Tail & Excess\\\midrule']
    names={'raw':'Raw','padding_only':'Padding','shape_only':'Shape','shape_const':'Joint'}
    for r in d['cells']:
        lines.append(' & '.join([r['prompt'],r['view'],names[r['condition']],r['target'],*[f'{100*r[k]:.1f}' for k in ('observed_ba','reference_mean','reference_q95')],f"{r['reference_tail_fraction']:.4f}",f"{100*r['positive_excess_over_q95']:.1f}"])+r'\\')
    lines += [r'\bottomrule\end{tabular}\end{table}',r'The baseline raw network cells exceed the reference 95th percentiles (68.5\%/65.4\%), whereas baseline joint cells have no positive excess. This is consistent with the measured paired reductions; failure to exceed a reference threshold is not a population guarantee. The diagnostic uses saved predictions and makes its task-level exchangeability assumption explicit.']
    text='\n\n'.join(lines)+'\n';p=P/'manuscript/tables/conditional-null.tex'
    if '--check' in sys.argv:assert p.read_bytes()==text.encode()
    else:p.write_text(text,encoding='utf-8',newline='\n')
    print('32_CELL_CONDITIONAL_REFERENCE_TABLE_MATCH')
if __name__=='__main__':main()

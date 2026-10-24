"""Emit a LaTeX tabular fragment from exact detailed results; never edits manuscript.
Usage: python table.py --prompt baseline > main_table.tex
       python table.py --prompt all > all_results_table.tex
"""
import json,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--prompt',choices=['rules','baseline','all'],default='baseline');a=p.parse_args()
 d=json.loads((HERE/'detailed_results.json').read_text());res=d['results'];paired=d['paired_contrasts'];labels={'undefended':'Undefended','jointconstant':'Joint constant','jointbucket1024':'Joint bucket 1024'}
 print(r'\begin{tabular}{lllrrrrrl}')
 print(r'\toprule')
 print(r'Target & Prompt & Defense & BA [95\% CI] & AUROC & $\Delta$BA [95\% CI] & Wire $\times$ & Calls $\times$ & Winner \\')
 print(r'\midrule')
 for target in ['cancel','return']:
  for arm in ['baseline','rules']:
   if a.prompt!='all' and arm!=a.prompt:continue
   for cond in ['undefended','jointconstant','jointbucket1024']:
    r=next(r for r in res if (r['target'],r['prompt'],r['condition'])==(target,arm,cond));delta='--'
    if cond!='undefended':
     c=next(c for c in paired if (c['target'],c['prompt'],c['contrast'])==(target,arm,'undefended minus '+cond));delta=f"{c['ba_decrease']:.3f} [{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}]"
    ba=f"{r['suite_ba']:.3f} [{r['suite_ba_ci95'][0]:.3f}, {r['suite_ba_ci95'][1]:.3f}]";winner=r['best_attacker'].replace('_',r'\_')
    print(f"{target.title()} & {arm} & {labels[cond]} & {ba} & {r['suite_auroc']:.3f} & {delta} & {r['bytes_ratio']:.2f} & {r['calls_ratio']:.2f} & {winner} "+r'\\')
 print(r'\bottomrule');print(r'\end{tabular}')
 print('% Posthoc original 690 Sol episodes, R5 customer five-fold OOF, train-only defense calibration and attacks.')
 print('% '+str(len(res[0]['attackers']))+' attacks in the union; all legacy network extended attacks plus fixed CNN and k-FP-style learner.')
 print('% 2000 paired customer-cluster bootstrap draws; max over full suite reselected on each draw; conditional on fitted attacks.')
 print('% Delta BA = undefended minus defended. Direction and length only; timing channel identically zero.')
if __name__=='__main__':main()


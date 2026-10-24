"""Emit main two-row or complete S21 LaTeX tabular to stdout; no manuscript writes."""
import json,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 a=argparse.ArgumentParser();a.add_argument('--detail',action='store_true');a.add_argument('--prompt',choices=['baseline','rules'],default='baseline');args=a.parse_args();d=json.loads((HERE/'detailed_results.json').read_text());res=d['results']
 def fmt(r):return f"{r['suite_ba']:.3f} [{r['suite_ba_ci95'][0]:.3f}, {r['suite_ba_ci95'][1]:.3f}]"
 if not args.detail:
  print(r'\begin{tabular}{lccc}');print(r'\toprule');print(r'Target & Full trace & Reads only (oracle) & Writes only (oracle) \\');print(r'\midrule')
  for target in ['cancel','return']:
   cells=[next(r for r in res if (r['target'],r['prompt'],r['view'])==(target,args.prompt,v)) for v in ['full','no_writes','writes_only']];print(target.title()+' & '+' & '.join(map(fmt,cells))+r' \\')
 else:
  print(r'\begin{tabular}{lllrrl}');print(r'\toprule');print(r'Target & Prompt & Oracle view & BA [95\% CI] & AUROC [95\% CI] & BA winner \\');print(r'\midrule')
  for r in res:
   auc=f"{r['suite_auroc']:.3f} [{r['suite_auroc_ci95'][0]:.3f}, {r['suite_auroc_ci95'][1]:.3f}]";winner=r['best_attacker'].replace('_',r'\_');view=r['view'].replace('_',r'\_');print(f"{r['target'].title()} & {r['prompt']} & {view} & {fmt(r)} & {auc} & {winner}"+r' \\')
 print(r'\bottomrule');print(r'\end{tabular}')
 print('% Posthoc original 690 Sol episodes; original R5 customer 5-fold OOF; union of all 9 legacy attacks plus CNN and k-FP-style (11 total).')
 print('% BA confidence intervals: 2000 customer-cluster bootstrap draws, 11-attack maximum reselected each draw; conditional on fitted attacks.')
 print('% Oracle uses true write-call identities to retain or remove exchanges. Direction/length only, timing identically zero. Full OOF reused from verified R7 crossfit.')
if __name__=='__main__':main()

"""Generate the R5 LaTeX tables (main Table 13, Supplement S15) from saved JSON."""
import r5lib as L

MS = L.HERE.parent.parent / 'manuscript' / 'tables'
NAMES = {'r4': 'R4 point (all tools, constant)', 'r4_bucket': 'All tools, 1024-B buckets',
         'r4_cap80': 'All tools, constant, q80 cap', 'writes': 'Writes only, constant',
         'writes_cap80': 'Writes only, constant, q80 cap', 'writes_bucket': 'Writes only, 1024-B buckets'}

SHORT = {'r4': 'E9 point (constant)', 'r4_bucket': '1024-B buckets', 'writes': 'Writes-only cover'}


def pct(x):
    return f'{100 * x:.1f}'


def ci(v):
    return f'[{pct(v[0])}, {pct(v[1])}]'


def main():
    e10 = L.read(L.HERE / 'e10_crossfit_results.json')
    e11 = L.read(L.HERE / 'e11_heldout_results.json'); sel = L.read(L.HERE / 'e11_selection.json')
    e12 = L.read(L.HERE / 'e12_localization_results.json')
    R = {(r['config'], r['target'], r['view'], r['prompt'], r['condition']): r for r in e10['results']}
    H = {(r['config'], r['target'], r['view'], r['prompt'], r['condition']): r for r in e11['results']}
    G = {(r['observer'], r['prompt'], r['target'], r['view']): r for r in e12['results']}
    pos = R['r4', 'cancel', 'network', 'baseline', 'raw']; posr = R['r4', 'return', 'network', 'baseline', 'raw']
    rows = []
    def line(label, r1, r2, bytes_=True):
        b = f"{r1['bytes_ratio']:.1f}/{r1['calls_ratio']:.1f}" if bytes_ else '--'
        return f"{label} & {pct(r1['core_ba'])} {ci(r1['core_ba_ci95'])} & {pct(r2['core_ba'])} {ci(r2['core_ba_ci95'])} & {b}\\\\"
    rows.append('\\multicolumn{4}{@{}l}{\\emph{E10: cross-fitted, ' + f"{2 * pos['episodes']} episodes, {pos['customers']} customers" + '}}\\\\')
    rows.append(line('Undefended', pos, posr))
    for c in ('r4', 'r4_bucket', 'writes'):
        rows.append(line(SHORT[c], R[c, 'cancel', 'network', 'baseline', 'shape_const'], R[c, 'return', 'network', 'baseline', 'shape_const']))
    rows.append(line('Rules + buckets', R['r4_bucket', 'cancel', 'network', 'rules', 'shape_const'], R['r4_bucket', 'return', 'network', 'rules', 'shape_const']))
    ch = sel['chosen']
    rows.append('\\midrule\\multicolumn{4}{@{}l}{\\emph{E11: chosen on training folds; frozen ' + f"{H['r4', 'cancel', 'network', 'baseline', 'shape_const']['episodes'] // 3}" + '-task test}}\\\\')
    for c in dict.fromkeys(['r4', ch]):
        lab = ('Selected: ' + SHORT[c]) if c == ch else 'E9 point'
        rows.append(line(lab, H[c, 'cancel', 'network', 'baseline', 'shape_const'], H[c, 'return', 'network', 'baseline', 'shape_const']))
    rows.append('\\midrule\\multicolumn{4}{@{}l}{\\emph{E12: undefended observer ablation, cross-fitted}}\\\\')
    for o, lab in (('no_writes', 'Writes removed'), ('writes_only', 'Writes only')):
        rows.append(line(lab, G[o, 'baseline', 'cancel', 'network'], G[o, 'baseline', 'return', 'network'], bytes_=False))
    main_tab = ('\\begin{table}[t]\\centering\\scriptsize\\setlength{\\tabcolsep}{2.5pt}\n'
                '\\caption{E10--E12: network-view maximum BA (\\%) over the fixed suite with customer-cluster 95\\% intervals. '
                f"Cross-fitting raises positive customers to {pos['positive_customers']} (cancel) and {posr['positive_customers']} (return). "
                'Baseline prompt unless stated; bytes/calls relative to raw transport. Writes: state-changing calls.}\\label{tab:r5}\n'
                '\\begin{tabular}{@{}lrrr@{}}\\toprule\nConfiguration & Cancel BA & Return BA & B$\\times$/C$\\times$\\\\\\midrule\n'
                + '\n'.join(rows) + '\n\\bottomrule\\end{tabular}\\end{table}\n')
    (MS / 'r5-main.tex').write_text(main_tab, encoding='utf-8', newline='\n')

    # Supplement: every configuration, both prompts, core and extended suites.
    sup = ['\\begin{table*}[ht]\\centering\\footnotesize\\setlength{\\tabcolsep}{3pt}',
           '\\caption{E10 cross-fitted network view: all configurations and prompts. Core = R4 suite; Ext. adds random forest, $k$-NN and a forest size decoder. SA-AUC: sign-agnostic AUROC $\\max(A,1-A)$.}',
           '\\begin{tabular}{@{}llrrrrrrr@{}}\\toprule',
           'Configuration & Prompt & Cancel core [CI] & Ext. & SA-AUC & Return core [CI] & Ext. & SA-AUC & Bytes$\\times$/Calls$\\times$\\\\\\midrule']
    for c in L.read(L.HERE / 'e10_crossfit_results.json')['calibrations']:
        for arm in L.PROMPTS:
            for cond in ('padding_only', 'shape_const') if c == 'r4' else ('shape_const',):
                a = R[c, 'cancel', 'network', arm, cond]; b = R[c, 'return', 'network', arm, cond]
                lab = NAMES[c] + (' (padding only)' if cond == 'padding_only' else '')
                sup.append(f"{lab} & {arm} & {pct(a['core_ba'])} {ci(a['core_ba_ci95'])} & {pct(a['ext_ba'])} & {a['sign_agnostic_auroc']:.2f} & "
                           f"{pct(b['core_ba'])} {ci(b['core_ba_ci95'])} & {pct(b['ext_ba'])} & {b['sign_agnostic_auroc']:.2f} & "
                           f"{a['bytes_ratio']:.1f}/{a['calls_ratio']:.1f}\\\\")
    sup += ['\\bottomrule\\end{tabular}\\end{table*}', '']
    sup += ['\\begin{table}[ht]\\centering\\small',
            '\\caption{E11 inner (training-fold) selection statistics. Eligible: all four inner network BAs $\\le 60\\%$.}',
            '\\begin{tabular}{@{}lrrrrrr@{}}\\toprule', 'Configuration & C/base & R/base & C/rules & R/rules & Bytes$\\times$ & Eligible\\\\\\midrule']
    for r in sel['inner']:
        v = r['inner_network_core_ba']
        sup.append(f"{NAMES[r['config']]} & {pct(v['cancel/baseline'])} & {pct(v['return/baseline'])} & {pct(v['cancel/rules'])} & "
                   f"{pct(v['return/rules'])} & {r['inner_bytes_ratio']:.1f} & {'yes' if r['eligible'] else 'no'}\\\\")
    sup += ['\\bottomrule\\end{tabular}\\end{table}', '']
    sup += ['\\begin{table}[ht]\\centering\\small',
            '\\caption{E12 observer ablation on undefended traces, cross-fitted (core-suite BA, \\%).}',
            '\\begin{tabular}{@{}lllrr@{}}\\toprule', 'Observer & Prompt & View & Cancel & Return\\\\\\midrule']
    for o in ('full', 'no_writes', 'writes_only'):
        for arm in L.PROMPTS:
            for view in ('dispatch', 'network'):
                sup.append(f"{o.replace('_', ' ')} & {arm} & {view} & {pct(G[o, arm, 'cancel', view]['core_ba'])} & {pct(G[o, arm, 'return', view]['core_ba'])}\\\\")
    sup += ['\\bottomrule\\end{tabular}\\end{table}', '']
    hz = {h['prompt']: h for h in e12['homogenization']}
    sup.append('\\noindent Rules-prompt homogenization: distinct read-only call sequences fall from '
               f"{hz['baseline']['distinct_read_sequences']} to {hz['rules']['distinct_read_sequences']} "
               f"(entropy {hz['baseline']['read_sequence_entropy_bits']:.2f} to {hz['rules']['read_sequence_entropy_bits']:.2f} bits), "
               f"whereas state-changing sequences stay at {hz['baseline']['distinct_write_sequences']} versus {hz['rules']['distinct_write_sequences']} "
               f"({hz['baseline']['write_sequence_entropy_bits']:.2f} versus {hz['rules']['write_sequence_entropy_bits']:.2f} bits).\\par")
    (MS / 'r5-supp.tex').write_text('\n'.join(sup) + '\n', encoding='utf-8', newline='\n')
    print('tables written')


if __name__ == '__main__':
    main()

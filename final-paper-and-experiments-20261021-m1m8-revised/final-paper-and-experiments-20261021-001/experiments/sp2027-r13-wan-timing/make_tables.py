"""Generate LaTeX and Markdown tables comparing Loopback (E13) vs WAN 20ms vs WAN 50ms."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R6 = HERE.parent / 'sp2027-r6-timing'

def load_data():
    r6_data = json.load(open(R6 / 'results.json'))
    wan_data = json.load(open(HERE / 'results_all.json'))
    return r6_data, wan_data

def make_flush_table(r6, wan):
    # Loopback flush detector metrics from R6
    r6_flush = r6['detectors']['shadow_serial-flush']
    r6_pt = r6_flush['ba']['point'] * 100
    r6_ci = [r6_flush['ba']['ci95'][0] * 100, r6_flush['ba']['ci95'][1] * 100]
    r6_auc = r6_flush['auroc']

    # WAN 20ms
    w20_det = wan['wan_20ms']['detectors']
    w20_tf_pt = w20_det['shadow_serial-flush-transfer']['ba']['point'] * 100
    w20_tf_ci = [w20_det['shadow_serial-flush-transfer']['ba']['ci95'][0] * 100, w20_det['shadow_serial-flush-transfer']['ba']['ci95'][1] * 100]
    w20_tf_auc = w20_det['shadow_serial-flush-transfer']['auroc']
    w20_ad_pt = w20_det['shadow_serial-flush-adapted']['ba']['point'] * 100
    w20_ad_ci = [w20_det['shadow_serial-flush-adapted']['ba']['ci95'][0] * 100, w20_det['shadow_serial-flush-adapted']['ba']['ci95'][1] * 100]
    w20_ad_auc = w20_det['shadow_serial-flush-adapted']['auroc']

    # WAN 50ms
    w50_det = wan['wan_50ms']['detectors']
    w50_tf_pt = w50_det['shadow_serial-flush-transfer']['ba']['point'] * 100
    w50_tf_ci = [w50_det['shadow_serial-flush-transfer']['ba']['ci95'][0] * 100, w50_det['shadow_serial-flush-transfer']['ba']['ci95'][1] * 100]
    w50_tf_auc = w50_det['shadow_serial-flush-transfer']['auroc']
    w50_ad_pt = w50_det['shadow_serial-flush-adapted']['ba']['point'] * 100
    w50_ad_ci = [w50_det['shadow_serial-flush-adapted']['ba']['ci95'][0] * 100, w50_det['shadow_serial-flush-adapted']['ba']['ci95'][1] * 100]
    w50_ad_auc = w50_det['shadow_serial-flush-adapted']['auroc']

    tex = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Serial shadow cover flush-phase detection across network conditions (15,278 records from 276 test episodes). Direct transfer applies the frozen loopback detector $D_{\text{loop}}$; Adapted fits 5-fold customer-grouped models on the WAN workload.}",
        r"\label{tab:wan-flush-comparison}",
        r"\small",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"\textbf{Network Condition} & \textbf{Model} & \textbf{Flush Point BA} & \textbf{95\% CI} & \textbf{AUROC} \\",
        r"\midrule",
        f"Loopback (0 ms, 0 ms jitter) & Frozen $D_{{\\text{{loop}}}}$ & {r6_pt:.1f}\\% & [{r6_ci[0]:.1f}, {r6_ci[1]:.1f}] & {r6_auc:.3f} \\\\",
        r"\midrule",
        f"WAN Mild (20 ms, 5 ms jitter) & Transfer $D_{{\\text{{loop}}}}$ & {w20_tf_pt:.1f}\\% & [{w20_tf_ci[0]:.1f}, {w20_tf_ci[1]:.1f}] & {w20_tf_auc:.3f} \\\\",
        f"& Adapted $D_{{\\text{{WAN}}}}$ & {w20_ad_pt:.1f}\\% & [{w20_ad_ci[0]:.1f}, {w20_ad_ci[1]:.1f}] & {w20_ad_auc:.3f} \\\\",
        r"\midrule",
        f"WAN Realistic (50 ms, 10 ms jitter) & Transfer $D_{{\\text{{loop}}}}$ & {w50_tf_pt:.1f}\\% & [{w50_tf_ci[0]:.1f}, {w50_tf_ci[1]:.1f}] & {w50_tf_auc:.3f} \\\\",
        f"& Adapted $D_{{\\text{{WAN}}}}$ & {w50_ad_pt:.1f}\\% & [{w50_ad_ci[0]:.1f}, {w50_ad_ci[1]:.1f}] & {w50_ad_auc:.3f} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}"
    ]
    return "\n".join(tex)

def make_controls_table(r6, wan):
    tex = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Timing defenses under loopback versus WAN conditions (276 test episodes). Full-suite intent Balanced Accuracy (BA) reported for cancellation / return. Incomplete/exhausted reflects sessions failing to complete all real calls within the fixed horizon.}",
        r"\label{tab:wan-controls-comparison}",
        r"\small",
        r"\begin{tabular}{lcccccc}",
        r"\toprule",
        r"\textbf{Condition} & \textbf{Network Environment} & \textbf{Full-Suite BA} & \textbf{Real p95 ms} & \textbf{Dur p95 ms} & \textbf{Byte Mult.} & \textbf{Status / Exh.} \\",
        r"\midrule"
    ]

    cond_labels = {
        'raw': 'Raw transport',
        'padding': 'Per-call constant framing',
        'shadow_serial': 'Serial shadow cover',
        'tunnel_2ms': 'Full tunnel (2 ms cell)'
    }

    for cond, label in cond_labels.items():
        # Loopback
        r6_res_base = r6['resources'].get(f'baseline|{cond}', {})
        r6_res_rules = r6['resources'].get(f'rules|{cond}', {})
        r6_c_ba = r6['cells'][f'baseline|{cond}|suite|cancel']['ba']['point'] * 100
        r6_r_ba = r6['cells'][f'baseline|{cond}|suite|return']['ba']['point'] * 100
        r6_real_p95 = r6_res_base['last_real_response_ms']['p95'] if r6_res_base.get('last_real_response_ms') else 0.0
        r6_dur_p95 = r6_res_base['traffic_finish_ms']['p95'] if r6_res_base.get('traffic_finish_ms') else 0.0
        r6_bytes = r6_res_base.get('wire_ratio', 1.0)
        tot_sess = r6_res_base.get('sessions', 138) + r6_res_rules.get('sessions', 138)
        tot_fail = r6_res_base.get('failures', 0) + r6_res_rules.get('failures', 0)
        r6_status = f"{tot_sess - tot_fail}/{tot_sess}"

        # WAN 20ms
        w20 = wan['wan_20ms']
        w20_res = w20['resources'][cond]
        w20_c_ba = w20['cells'].get(f'baseline|{cond}|suite|cancel', {}).get('ba', {}).get('point', 0.0) * 100
        w20_r_ba = w20['cells'].get(f'baseline|{cond}|suite|return', {}).get('ba', {}).get('point', 0.0) * 100
        w20_status = f"{w20_res['complete_sessions']}/{w20_res['total_sessions']}"

        # WAN 50ms
        w50 = wan['wan_50ms']
        w50_res = w50['resources'][cond]
        w50_c_ba = w50['cells'].get(f'baseline|{cond}|suite|cancel', {}).get('ba', {}).get('point', 0.0) * 100
        w50_r_ba = w50['cells'].get(f'baseline|{cond}|suite|return', {}).get('ba', {}).get('point', 0.0) * 100
        w50_status = f"{w50_res['complete_sessions']}/{w50_res['total_sessions']}"

        tex.append(f"{label} & Loopback (0 ms, 0 ms jit.) & {r6_c_ba:.1f}\\% / {r6_r_ba:.1f}\\% & {r6_real_p95:.1f} & {r6_dur_p95:.1f} & {r6_bytes:.1f}$\\times$ & {r6_status} \\\\")
        tex.append(f"& WAN Mild (20 ms, 5 ms jit.) & {w20_c_ba:.1f}\\% / {w20_r_ba:.1f}\\% & {w20_res['real_chain_p95_ms']:.1f} & {w20_res['duration_p95_ms']:.1f} & {w20_res['byte_multiplier']:.1f}$\\times$ & {w20_status} \\\\")
        tex.append(f"& WAN Real. (50 ms, 10 ms jit.) & {w50_c_ba:.1f}\\% / {w50_r_ba:.1f}\\% & {w50_res['real_chain_p95_ms']:.1f} & {w50_res['duration_p95_ms']:.1f} & {w50_res['byte_multiplier']:.1f}$\\times$ & {w50_status} \\\\")
        tex.append(r"\midrule")

    tex[-1] = r"\bottomrule"
    tex.extend([
        r"\end{tabular}",
        r"\end{table*}"
    ])
    return "\n".join(tex)

def main():
    r6, wan = load_data()
    flush_tex = make_flush_table(r6, wan)
    controls_tex = make_controls_table(r6, wan)

    with open(HERE / 'tab_wan_flush.tex', 'w') as f:
        f.write(flush_tex)
    with open(HERE / 'tab_wan_controls.tex', 'w') as f:
        f.write(controls_tex)

    print("LaTeX tables written to tab_wan_flush.tex and tab_wan_controls.tex.")

if __name__ == '__main__':
    main()

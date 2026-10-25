# R19 targeted primary-source follow-up

These checks support specific record-local decisions. They do not claim a new independent full-paper recoding of all 82 families. Original archived source hashes are retained alongside every record.

| Source | Locator | Decision |
|---|---|---|
| [SparLeak v1](https://arxiv.org/html/2609.38830v1) | §7.5, Table 4; §7.4 | Model × perturbation-intensity cells pair attack success and ROUGE, meeting component utility R8. Change P → B. Spy overhead in §7.4 is attack cost, not defense cost; R9 remains U. |
| [CachePrune v1](https://arxiv.org/html/2605.23640v1) | §5.1–5.6, Tables 1–2; contrast §5.7 | Direct and contextual recovery rows use the same secure selective-sharing configuration. Local quality and serving-cost experiments supply a configuration-level join. Count two records but one shared configuration; do not claim identical sampled requests. Exclude the privacy-disabled §5.7 cache-hit comparison from secure-condition cost/utility evidence. |
| [OTRO v1](https://arxiv.org/html/2606.17358v1) | §VII-C and §VII-E | Measured unpadded TTFT and derived epoch-padding cost are distinct operating points. The padding increment is omitted from the unpadded TTFT figures; retain separate records and mark padded cost partial rather than borrowing unpadded measured latency. |

The all-39 audit inherits the scope and version locators of `combined_result_records.json`. It explicitly separates contextual controls, component-cost-only records, protected inference, configuration-linked utility and source binding that remains unresolved. `build_audit.py` contains each current judgment and rationale; the 528 earlier pair judgments are preserved exactly, with 31 additional related-pair judgments identified as the R19 extension.

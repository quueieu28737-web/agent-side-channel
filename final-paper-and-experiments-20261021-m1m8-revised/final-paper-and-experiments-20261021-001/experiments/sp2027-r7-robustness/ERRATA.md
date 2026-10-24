# Frozen-protocol clarifications

The original `PROTOCOL.md` and its SHA256 remain unchanged. These corrections do not alter training, predictions, thresholds or measured captures.

1. **Power-planning grid:** the frozen description says 5–250 positive customers. The implemented, reported sensitivity includes 400 as an additional grid point. The 400 and >400 entries are therefore a post hoc extension of the planning range. This is a prospective-design sensitivity on assumed Bernoulli populations, not newly collected customers or an empirical certification of power. All grid points are retained in `power.json`; the main defense analysis was not selected using this planning calculation.
2. **Offline payload preservation:** adapters operate on capture metadata, not decrypted application payloads. Fragment IDs track the size, direction, order and release time implied by each input record. The checks establish conservation of this abstract fragment sequence and byte accounting. They do not compare payload contents or execute the transformed traffic through a real network. E13's separately measured response/state checks remain actual execution checks.

The implementation notes and current manuscript use these corrected meanings. The original protocol wording remains available for audit.

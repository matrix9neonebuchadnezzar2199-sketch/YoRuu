# ADR-001: Principal concept design rollup (ch10/13/16/18/22)

**Status**: Accepted (2026-05-28)  
**Implementation note (M5.1, 2026-05-28)**: Canonical chapters were updated during M4.3 (`fca1306`, `cbe24f3`). Rolling drafts are archived under `docs/design/archive/principal-rollout-2026-05-28/`.

## Context

- **H-1 accounting**: `balance` = free funds; `principal` = cumulative deposits − withdrawals; `total_assets` = balance + locked.
- **INV-D-06 v2**: `balance + Σ(open) ≈ principal + Σ(closed pnl)`.
- **New**: INV-D-07/08/09, `principal_transactions`, SSE `principal_changed`, REST/CLI principal, FX display API.

## Decision

1. Roll `ch10_v1.2`, `ch13_v1.0.5`, `ch16_v1.0.3`, `ch18_v1.1.1`, `ch22_v1.0.5` **rolling drafts** into canonical chapters (completed M4.3):
   - `docs/design/10_functions_data_model.md`
   - `docs/design/13_paper_execution.md`
   - `docs/design/16_invariants.md`
   - `docs/design/18_error_handling.md`
   - `docs/design/22_config_spec.md`
2. Move superseded `*_ROLLING_DRAFT.md` files to  
   **`docs/design/archive/principal-rollout-2026-05-28/`** (completed PHASE 5 M5.1).
3. Keep cross-references in `INDEX.md` and `00_ROADMAP.md` pointing to canonical chapters only.

## Consequences

- **Positive**: Single SSOT per topic; reviewers read one file per chapter.
- **Negative**: Large diff in design docs during M4.3; archive preserves history.
- **Implementation**: Aligned in `src/yoruu/` (M4.4–M4.5).

## Alternatives considered

- Leave drafts as SSOT indefinitely — rejected (dual maintenance).
- Per-chapter ADRs — rejected (principal spans all five chapters).

## References

- [`PHASE4_EXIT_DECLARATION.md`](../design/PHASE4_EXIT_DECLARATION.md)
- [`PRINCIPAL_CONCEPT_V1_DRAFT.md`](../design/PRINCIPAL_CONCEPT_V1_DRAFT.md)
- Archive README: [`../design/archive/principal-rollout-2026-05-28/README.md`](../design/archive/principal-rollout-2026-05-28/README.md)

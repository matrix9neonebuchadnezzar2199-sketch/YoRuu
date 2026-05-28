# ADR-001: Principal concept design rollup (ch10/13/16/18/22)

**Status**: Accepted (2026-05-28)  
**Context**: PHASE 4 M4.3 produced rolling drafts; implementation (M4.4–M4.7) is complete.  
**Decision**: Merge approved rolling content into canonical design chapters in one changeset.

## Context

- **H-1 accounting**: `balance` = free funds; `principal` = cumulative deposits − withdrawals; `total_assets` = balance + locked.
- **INV-D-06 v2**: `balance + Σ(open) ≈ principal + Σ(closed pnl)`.
- **New**: INV-D-07/08/09, `principal_transactions`, SSE `principal_changed`, REST/CLI principal, FX display API.

## Decision

1. Roll `ch10_v1.2`, `ch13_v1.0.5`, `ch16_v1.0.3`, `ch18_v1.1.1`, `ch22_v1.0.5` **rolling drafts** into:
   - `10_functions_data_model.md`
   - `13_paper_execution.md`
   - `16_invariants.md` (or equivalent filename in repo)
   - `18_api_errors.md`
   - `22_configuration.md`
2. Move superseded `*_ROLLING_DRAFT.md` files to `docs/design/archive/`.
3. Keep cross-references in `INDEX.md` and `00_ROADMAP.md` pointing to canonical chapters only.

## Consequences

- **Positive**: Single SSOT per topic; reviewers read one file per chapter.
- **Negative**: Large diff in design docs; requires careful diff review.
- **Implementation**: Already aligned in `src/yoruu/` (M4.4–M4.5).

## Alternatives considered

- Leave drafts as SSOT indefinitely — rejected (dual maintenance).
- Per-chapter ADRs — rejected (principal spans all five chapters).

## References

- [`PHASE4_EXIT_DECLARATION.md`](../design/PHASE4_EXIT_DECLARATION.md)
- [`PRINCIPAL_CONCEPT_V1_DRAFT.md`](../design/PRINCIPAL_CONCEPT_V1_DRAFT.md)

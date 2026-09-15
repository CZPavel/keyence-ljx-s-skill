# ADR 0003: Family-aware no silent propagation

## Context
LJ-X8000, LJ-X8000A and LJ-S8000 can differ.

## Decision
Do not reuse a family fact unless canonical family evidence allows it.

## Consequences
`NOT_VERIFIED` is surfaced as uncertainty rather than treated as support.

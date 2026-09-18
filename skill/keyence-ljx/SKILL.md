---
name: keyence-ljx
description: Source-grounded assistance for KEYENCE LJ-X/LJ-S laser profiler commissioning, PC/PLC communication, commands, signals, profiles, programs, head selection, and measurement setup. Use for LJ-X8000, LJ-X8000A, or LJ-S8000 questions; do not assume facts transfer between families.
---

# KEYENCE LJ-X / LJ-S

Use this skill for technical support, integration, configuration, and measurement-program questions about KEYENCE LJ-X/LJ-S controllers and heads.

## Route first

1. Infer the controller family from the model. If the answer can differ and it remains unknown, ask one focused family question.
2. Determine mode and head only when relevant.
3. From any working directory, set `$skillRoot = Join-Path $env:USERPROFILE '.codex\skills\keyence-ljx'` and resolve the intent with `python "$skillRoot\tools\run.py" skill_lookup intent <intent> --controller <family> --json`.
4. Inspect the returned canonical file and apply its family/mode/status fields.
5. Use a workflow before isolated facts for commissioning, triggering, profiles, program changes, and recovery.

Read [control.md](references/control.md) for commands/signals and [measurement.md](references/measurement.md) for tools and corrections. Use [evidence_policy.md](references/evidence_policy.md) whenever a fact is incomplete or an action changes controller state.

## Family and evidence rules

- `LJ-X8000` facts do not apply to `LJ-X8000A` or `LJ-S8000` unless the family delta explicitly permits reuse.
- Prefer `OFFICIAL_EXACT`, then `OFFICIAL_CONTEXTUAL`; label `DERIVED` guidance. Never turn `UNRESOLVED` into a fact.
- Use targeted corpus lookup only after canonical routing cannot answer the requested detail.
- Do not interpolate X/FOV between documented near/reference/far positions. Reuse `tools/head_geometry.py` for installation-envelope questions.

## State-changing work

For trigger, program, save, reset, or write operations, state the effect and follow: **PRECHECK → ACTION → OBSERVE → VERIFY**. Prefer read-only checks. Never describe a program-selection command as program creation.

## Response shape

Give a short recommendation, practical steps, expected observation, relevant caution, and source/status when it affects the answer. Keep internal YAML names out of the user-facing explanation.

## Targeted fallback

Use `python "$skillRoot\tools\run.py" corpus_lookup --query <text> --document <optional> --json` only for a narrow unresolved detail. It returns evidence records, not a synthesized answer. The wrapper resolves the canonical helpers and `skill_data` in this checkout, so it works through `%USERPROFILE%\.codex\skills\keyence-ljx` from another working directory.

# Architecture

Codex Skill → routing/workflows → canonical `skill_data` → deterministic helpers → targeted local raw-source fallback. Canonical knowledge is normalized facts, not manual extraction.

# Knowledge model

Statuses: `OFFICIAL_EXACT`, `OFFICIAL_CONTEXTUAL`, `DERIVED`, `OBSERVED_RUNTIME`, `COMMUNITY`, `UNRESOLVED`. Family relations: `SAME`, `DIFFERENT`, `FAMILY_SPECIFIC`, `NOT_SUPPORTED`, `NOT_VERIFIED`; `NOT_VERIFIED` is not `NOT_SUPPORTED`.

# Evidence model

Evidence types include `DIRECT_NATIVE`, `DIRECT_VISUAL`, `DIRECT_OCR_VERIFIED`, and `SUPPORTING`. Public evidence is metadata-only: canonical fact → document identity/SHA → page/locator. Raw evidence stays local.

# Installation

Clone the repository and run `scripts\install_skill.ps1`. The installer creates a junction only when the activation path is absent and never removes an existing path.

# Development

Classify a real user gap, collect targeted evidence locally, update canonical data, validate, benchmark, document the change, and commit. Public development excludes manufacturer sources; local source validation may use legally obtained sources.

# Validation

Public CI checks structural/canonical consistency and the deterministic benchmark without manuals. Local source validation additionally verifies manual hashes/pages.

# Release process

Validate, audit tracked files, update CHANGELOG/CURRENT_STATE, commit, tag `V01`-style release, then publish.

# Coverage

LJ-X8000 operational: GOOD; hardware: GOOD/PARTIAL; measurement: PARTIAL. LJ-S8000 and LJ-X8000A: PARTIAL/WEAK, with no silent propagation.
# Public and local validation

## Public validation

Run `scripts\validate.ps1` after a clean public clone. It validates canonical schema, routing, public evidence metadata, helpers and the deterministic benchmark. It does not require manufacturer PDFs or the raw corpus, and is the GitHub Actions validation path.

## Local source validation

Run `scripts\validate_sources.ps1` only with a legally obtained local source corpus. It validates raw chunk provenance and source-bound command evidence. `validate_measurement.py --source` fails explicitly when the local corpus is absent.

# Keyence LJ-X/LJ-S Skill V1

**Status:** `PUBLIC_MAIN_V01_2_VALIDATED`

V01.2 updates the public main branch with the current canonical capability and portable local activation. LJ-X8000 covers Height Difference/Width, 3D capture tuning, height-image preparation/reference, profile/continuous-profile measurement, measured-value correction, and result-output correlation. LJ-S8000 adds exact READY/EXP_BUSY/ERROR head-I/O records and I/O/backup workflows; family-unconfirmed 3D and UI guidance remains explicitly contextual.

- Public validation runs without manufacturer manuals or raw corpus.
- Local source validation remains available through `scripts/validate_sources.ps1`.
- Benchmark: 35 PASS, 5 EXPECTED_UNRESOLVED, 0 FAIL.
- Height Difference/Width: two measurement ranges, target roles, documented target choices, and documented measurement values are source-located. Numeric ROI sizes, thresholds, filter tuning, tool-specific correction behavior, and invalid-result behavior remain unresolved.
- Capture and preprocessing: direct-evidence records cover sensitivity adjustment, Dynamic Range, Exposure Time, Detection Sensitivity, Target Area, light-intensity control, Height Extraction, Zero Plane, and the six imported height filters. They route symptoms such as missing profile, multiple reflections, blur, unstable light feedback, curved-surface protrusions, and workpiece orientation shift to documented controls.
- 3D profile capability: Profile Measurement range-following, Continuous Profile Measurement, Profile Length, Cross-section Area, 1/2-Point measured-value correction, and result-output correlation fields are canonical and routable.
- LJ-S8000: exact head-I/O signals and backup/I/O workflows are source-located. 3D Differential/Search and UI/I/O/SD export-import guidance are `OFFICIAL_CONTEXTUAL`, not family-exact tool claims.
- LJ-X8000A remains family-aware with no propagated LJ-X8000 measurement facts.
- `%USERPROFILE%\.codex\skills\keyence-ljx` activates the thin skill junction; `tools\run.py` resolves canonical helpers and data from this repository even when the working directory is elsewhere.

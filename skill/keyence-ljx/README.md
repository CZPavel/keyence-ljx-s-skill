# KEYENCE LJ-X / LJ-S Codex Skill V1

Repository-local source lives in `skill/keyence-ljx`; activation is the junction `%USERPROFILE%\.codex\skills\keyence-ljx` to that directory.

Canonical knowledge remains in `skill_data`; the skill stores routing and policies only.

Examples:

```powershell
python tools\skill_lookup.py command T1 --controller LJ-X8000 --json
python tools\skill_lookup.py head LJ-X8900
python tools\corpus_lookup.py --query "Height Difference/Width" --json
python benchmarks\skill_v1\run_benchmark.py
```

Rebuild measurement records with `python tools\build_skill_data\build_measurement.py`, then rerun its validator and the benchmark.

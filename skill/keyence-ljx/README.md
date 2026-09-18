# KEYENCE LJ-X / LJ-S Codex Skill V1

Repository-local source lives in `skill/keyence-ljx`; activation is the junction `%USERPROFILE%\.codex\skills\keyence-ljx` to that directory.

Canonical knowledge remains in `skill_data`; the skill stores routing and policies only.

The activated junction is intentionally thin. Run canonical helpers through the
portable wrapper from the activated directory (or its resolved source):

```powershell
python "$env:USERPROFILE\.codex\skills\keyence-ljx\tools\run.py" skill_lookup command T1 --controller LJ-X8000 --json
python "$env:USERPROFILE\.codex\skills\keyence-ljx\tools\run.py" skill_lookup guidance "Detection level" --controller LJ-S8000 --mode 3D --json
python "$env:USERPROFILE\.codex\skills\keyence-ljx\tools\run.py" corpus_lookup --query "Height Difference/Width" --json
```

Repository development and validation commands remain rooted at the repository,
not at the activated skill junction.

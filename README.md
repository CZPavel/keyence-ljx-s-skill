# Keyence LJ-X / LJ-S Codex Skill

Independent open-source Codex Skill and source-grounded knowledge base for KEYENCE LJ-X/LJ-S laser-profiler commissioning, integration, diagnostics, head selection, and measurement-program guidance.

## Scope

LJ-X8000 is the deepest verified operational baseline. LJ-X8000A and LJ-S8000 are family-aware but have partial coverage; facts are never silently transferred between families.

This is not an official KEYENCE product, a controller driver, an MCP server, or a replacement for manufacturer documentation and machine-safety design.

## Install

```powershell
git clone https://github.com/CZPavel/keyence-ljx-s-skill.git
cd keyence-ljx-s-skill
.\scripts\install_skill.ps1
```

The installer creates `%USERPROFILE%\.codex\skills\keyence-ljx` only if it is absent. It never deletes or replaces an existing path.

## Use

```powershell
python tools\skill_lookup.py command T1 --controller LJ-X8000 --json
python tools\skill_lookup.py head LJ-X8900
python tools\head_geometry.py --head LJ-X8900 --required-z-span-mm 350
python benchmarks\skill_v1\run_benchmark.py
```

## Architecture

`skill/keyence-ljx` provides concise routing instructions. `skill_data` is canonical source of truth; helpers resolve facts and routes deterministically. The raw corpus is local-only and used only for targeted validation/fallback.

## Validation

V01 baseline: 23 benchmark routes pass, 2 cross-family cases are correctly `NOT_VERIFIED`, and 0 fail. Run `scripts\validate.ps1`.

## Sources, copyright and disclaimer

This independent project is not affiliated with, endorsed by, or sponsored by KEYENCE Corporation. KEYENCE and product names are trademarks of their respective owners. Manufacturer manuals are not redistributed; public provenance retains identifiers, hashes and page locators. Consult official documentation for safety, compliance and final commissioning.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT applies to original project code, documentation and normalized data only.

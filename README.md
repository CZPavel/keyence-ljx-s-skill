# Keyence LJ-X / LJ-S Codex Skill

Independent open-source Codex Skill and source-grounded knowledge base for KEYENCE LJ-X/LJ-S laser-profiler commissioning, integration, diagnostics, head selection, and measurement-program guidance.

## Scope

LJ-X8000 is the deepest verified operational baseline. LJ-S8000 has exact head-I/O and backup coverage plus clearly labelled contextual UI/3D guidance. LJ-X8000A is family-aware but remains lightly covered. Facts are never silently transferred between families.

Current LJ-X8000 coverage includes Height Difference/Width, six height-image filters, Height Extraction, Zero Plane, capture tuning, profile/continuous-profile measurement, profile corrections, result-output correlation, and symptom-to-control diagnostics. `OFFICIAL_CONTEXTUAL` records remain routable when a useful source lacks an established family/mode, but they never become family-specific claims.

This is not an official KEYENCE product, a controller driver, an MCP server, or a replacement for manufacturer documentation and machine-safety design.

## Install

```powershell
git clone https://github.com/CZPavel/keyence-ljx-s-skill.git
cd keyence-ljx-s-skill
.\scripts\install_skill.ps1
```

The installer creates `%USERPROFILE%\.codex\skills\keyence-ljx` only if it is absent. It never deletes or replaces an existing path. The activated skill contains a thin portable wrapper that resolves the canonical repository helpers and data.

## Use

```powershell
python tools\skill_lookup.py command T1 --controller LJ-X8000 --json
python tools\skill_lookup.py head LJ-X8900
python tools\head_geometry.py --head LJ-X8900 --required-z-span-mm 350
python tools\skill_lookup.py guidance "Detection level" --controller LJ-S8000 --mode 3D --json
python tools\skill_lookup.py operation "CMD READY" --controller LJ-S8000 --mode 3D --json
python benchmarks\skill_v1\run_benchmark.py
```

### LJ-X8000 PFRF benchmark

The standard-library-only diagnostic reads a selected range from the latest 2D
profile without changing controller configuration:

```powershell
python .\ljx_pfrf_benchmark.py --ip 192.168.10.10 --start-point 0 --points 100 --iterations 1000 --csv .\pfrf_100_points.csv --profile-csv .\pfrf_100_profile.csv
```

Start with a small RAW capture. It prints exact TX/RX bytes and timings and stops
on an unexpected frame instead of guessing whether asynchronous result output is
a PFRF response:

```powershell
python .\ljx_pfrf_benchmark.py --ip 192.168.10.10 --points 100 --iterations 3 --raw
```

The documented default Non-Procedural port is `8500` and the controller's
default delimiter is CR. Both are controller settings; pass `--port` and
`--delimiter crlf` or `--delimiter lf` when the installation differs. In the
controller's `All` mode, use separate `--tx-delimiter` and `--rx-delimiter`
arguments if command and result delimiters differ. Although PFRF is classified
READ_ONLY for configuration, every call temporarily stops current measurement;
Continuous Trigger must be 500 Hz or lower. See
[`docs/PFRF_PROTOCOL_CONTRACT.md`](docs/PFRF_PROTOCOL_CONTRACT.md) before live
use, especially when asynchronous result output is enabled.

Sweep the standard point counts and create a summary:

```powershell
python .\ljx_pfrf_benchmark.py --ip 192.168.10.10 --iterations 100 --sweep --csv .\pfrf_sweep.csv
```

If a sweep stops on an error or ambiguous frame, its summary row retains the
machine-readable failure status, first-byte/completion/transfer timings, byte
count, and diagnostic text.

### Simulated 12 FPS camera event

`--camera-fps` is an absolute `perf_counter_ns()` scheduler, not a real camera
integration and not an LJ-X trigger. It reports host event-to-complete-PFRF-data
timing, jitter and the margin to the next simulated event. Start with RAW:

```powershell
python .\ljx_pfrf_benchmark.py `
  --ip 192.168.10.10 --head 1 --start-point 0 --points 100 `
  --iterations 3 --camera-fps 12 --raw
```

Ten-second diagnostic run:

```powershell
python .\ljx_pfrf_benchmark.py `
  --ip 192.168.10.10 --head 1 --start-point 0 --points 100 `
  --iterations 120 --camera-fps 12 --warmup 10
```

Long run with per-frame metadata CSV and long-format profiles:

```powershell
python .\ljx_pfrf_benchmark.py `
  --ip 192.168.10.10 --head 1 --start-point 0 --points 100 `
  --iterations 1000 --camera-fps 12 --warmup 10 `
  --csv .\pfrf_12fps.csv --profile-csv .\pfrf_12fps_profiles.csv
```

Compare `100, 200, 300, 500, 1000, 3200` points at the same cadence:

```powershell
python .\ljx_pfrf_benchmark.py `
  --ip 192.168.10.10 --head 1 --start-point 0 --iterations 120 `
  --camera-fps 12 --camera-sweep --csv .\pfrf_camera_sweep.csv
```

The result is only *host-event correlated*: PFRF has no currently documented
profile timestamp/counter that proves profile age relative to a camera event.

### PFRF availability diagnosis

When a live GUI profile exists but `PFRF,1,0,100` returns `ER,PFRF,03`, run the
three canonical request forms without changing controller state:

```powershell
python .\ljx_pfrf_benchmark.py `
  --ip 192.168.10.10 --port 8500 --head 1 --diagnose-pfrf --raw
```

It sends exactly `PFRF,1`, `PFRF,1,1`, and `PFRF,1,0,100`, using the configured
delimiter. It stops on unsolicited/ambiguous data, prints the exact `ER` code,
and previews rather than dumps a successful full profile.

## Architecture

`skill/keyence-ljx` provides concise routing instructions. `skill_data` is canonical source of truth; helpers resolve facts and routes deterministically. The raw corpus is local-only and used only for targeted validation/fallback. When invoked through the global activation from another project, use `%USERPROFILE%\.codex\skills\keyence-ljx\tools\run.py` to reach the same canonical helpers without a duplicate data copy.

## Validation

Public validation, source validation when the local corpus is available, `pytest`, and the deterministic benchmark are maintained separately. Current benchmark: 35 PASS, 5 expected unresolved, 0 fail. Run `scripts\validate.ps1`.

## Sources, copyright and disclaimer

This independent project is not affiliated with, endorsed by, or sponsored by KEYENCE Corporation. KEYENCE and product names are trademarks of their respective owners. Manufacturer manuals are not redistributed; public provenance retains identifiers, hashes and page locators. Consult official documentation for safety, compliance and final commissioning.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT applies to original project code, documentation and normalized data only.

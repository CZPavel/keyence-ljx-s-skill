param()
$root=Split-Path -Parent $PSScriptRoot
$checks=@('validate_signals.py','validate_workflows.py','validate_family_deltas.py','validate_hardware.py')
python "$root\.github\validate_public.py"; if($LASTEXITCODE){exit $LASTEXITCODE}
foreach($c in $checks){ python "$root\tools\build_skill_data\$c"; if($LASTEXITCODE){exit $LASTEXITCODE} }
python "$root\tools\build_skill_data\validate_measurement.py" --public; if($LASTEXITCODE){exit $LASTEXITCODE}
python "$root\benchmarks\skill_v1\run_benchmark.py"; exit $LASTEXITCODE

param()
$root=Split-Path -Parent $PSScriptRoot
$checks=@('validate_command_source_blocks.py','validate_signals.py','validate_workflows.py','validate_family_deltas.py','validate_hardware.py','validate_measurement.py')
foreach($c in $checks){ python "$root\tools\build_skill_data\$c"; if($LASTEXITCODE){exit $LASTEXITCODE} }
python "$root\benchmarks\skill_v1\run_benchmark.py"; exit $LASTEXITCODE

param()
$root=Split-Path -Parent $PSScriptRoot
python "$root\tools\build_skill_data\validate_command_source_blocks.py"; if($LASTEXITCODE){exit $LASTEXITCODE}
python "$root\tools\build_skill_data\validate_measurement.py" --source; exit $LASTEXITCODE

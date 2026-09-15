param([string]$Version='V01')
$root=Split-Path -Parent $PSScriptRoot; $out=Join-Path $root 'dist'; New-Item -ItemType Directory -Force -Path $out | Out-Null
$asset=Join-Path $out "keyence-ljx-s-skill-$Version.zip"
Compress-Archive -Path "$root\skill","$root\skill_data","$root\tools\skill_lookup.py","$root\tools\head_geometry.py","$root\tools\corpus_lookup.py","$root\README.md","$root\LICENSE","$root\NOTICE.md","$root\sources" -DestinationPath $asset -Force
Write-Host $asset

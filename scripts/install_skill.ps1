param([string]$ActivationPath = (Join-Path $HOME '.codex\skills\keyence-ljx'))
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = (Resolve-Path -LiteralPath (Join-Path $repoRoot 'skill\keyence-ljx')).Path
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) { throw "Skill source is incomplete: $source" }
if (-not (Test-Path -LiteralPath (Join-Path $source 'tools\run.py') -PathType Leaf)) { throw "Portable helper wrapper is missing: $source" }
if (-not (Test-Path -LiteralPath $ActivationPath)) { New-Item -ItemType Junction -Path $ActivationPath -Target $source | Out-Null; Write-Host "Installed: $ActivationPath"; exit 0 }
$item=Get-Item -LiteralPath $ActivationPath
if ($item.LinkType -in 'Junction','SymbolicLink' -and $item.Target -contains $source) { Write-Host "Already active: $ActivationPath"; exit 0 }
throw "Activation path exists and is not this Skill. Nothing was changed: $ActivationPath"

param(
  [string]$AudioDir = "data/raw/audio",
  [string]$TextDir = "data/raw/text",
  [string]$OutDir = "data/finetune/manifests",
  [string]$LanguageId = "vi",
  [double]$DevRatio = 0.05
)

$ErrorActionPreference = "Stop"

Write-Host "[Manifest] AudioDir : $AudioDir"
Write-Host "[Manifest] TextDir  : $TextDir"
Write-Host "[Manifest] OutDir   : $OutDir"
Write-Host "[Manifest] Lang     : $LanguageId"
Write-Host "[Manifest] DevRatio : $DevRatio"

uv run python finetune/prepare_manifest.py `
  --audio_dir $AudioDir `
  --text_dir $TextDir `
  --out_dir $OutDir `
  --language_id $LanguageId `
  --dev_ratio $DevRatio

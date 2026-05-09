param(
  [string]$Tokenizer = "eustlb/higgs-audio-v2-tokenizer",
  [int]$NjPerGpu = 1,
  [switch]$SkipErrors
)

$ErrorActionPreference = "Stop"

$env:TOKENIZERS_PARALLELISM = "false"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

$skipArg = ""
if ($SkipErrors) {
  $skipArg = "--skip_errors"
}

Write-Host "[Stage 1] Extract train tokens"
uv run python -m omnivoice.scripts.extract_audio_tokens `
  --input_jsonl data/finetune/manifests/train.jsonl `
  --tar_output_pattern data/finetune/tokens/train/audios/shard-%06d.tar `
  --jsonl_output_pattern data/finetune/tokens/train/txts/shard-%06d.jsonl `
  --tokenizer_path $Tokenizer `
  --nj_per_gpu $NjPerGpu `
  --shuffle False $skipArg

Write-Host "[Stage 1] Extract dev tokens"
uv run python -m omnivoice.scripts.extract_audio_tokens `
  --input_jsonl data/finetune/manifests/dev.jsonl `
  --tar_output_pattern data/finetune/tokens/dev/audios/shard-%06d.tar `
  --jsonl_output_pattern data/finetune/tokens/dev/txts/shard-%06d.jsonl `
  --tokenizer_path $Tokenizer `
  --nj_per_gpu $NjPerGpu `
  --shuffle False $skipArg

Write-Host "Done. Check data/finetune/tokens/{train,dev}/data.lst"

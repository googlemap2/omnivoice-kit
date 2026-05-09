param(
  [string]$TrainJsonl = "data/finetune/manifests/train.jsonl",
  [string]$DevJsonl = "data/finetune/manifests/dev.jsonl",
  [string]$TokenDir = "data/finetune/tokens",
  [string]$TokenizerPath = "eustlb/higgs-audio-v2-tokenizer",
  [string]$TrainConfig = "finetune/train_config_finetune_sdpa.json",
  [string]$DataConfig = "finetune/data_config_finetune.json",
  [string]$OutputDir = "exp/voice_clone_finetune",
  [string]$GpuIds = "0",
  [int]$NumGpus = 1
)

$ErrorActionPreference = "Stop"

Write-Host "Stage 1/2: Tokenize train/dev manifests"
uv run python -m omnivoice.scripts.extract_audio_tokens `
  --input_jsonl $TrainJsonl `
  --tar_output_pattern "$TokenDir/train/audios/shard-%06d.tar" `
  --jsonl_output_pattern "$TokenDir/train/txts/shard-%06d.jsonl" `
  --tokenizer_path $TokenizerPath `
  --nj_per_gpu 2 `
  --shuffle True

uv run python -m omnivoice.scripts.extract_audio_tokens `
  --input_jsonl $DevJsonl `
  --tar_output_pattern "$TokenDir/dev/audios/shard-%06d.tar" `
  --jsonl_output_pattern "$TokenDir/dev/txts/shard-%06d.jsonl" `
  --tokenizer_path $TokenizerPath `
  --nj_per_gpu 2 `
  --shuffle False

Write-Host "Stage 2/2: Fine-tune OmniVoice"
uv run accelerate launch `
  --gpu_ids $GpuIds `
  --num_processes $NumGpus `
  -m omnivoice.cli.train `
  --train_config $TrainConfig `
  --data_config $DataConfig `
  --output_dir $OutputDir

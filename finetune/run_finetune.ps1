param(
  [string]$GpuIds = "0",
  [int]$NumGpus = 1,
  [string]$TrainConfig = "finetune/train_config_finetune_sdpa.json",
  [string]$DataConfig = "finetune/data_config_finetune.json",
  [string]$OutputDir = "exp/voice_clone_finetune"
)

$ErrorActionPreference = "Stop"

Write-Host "[Fine-tune] GPU IDs: $GpuIds, Num GPUs: $NumGpus"

$env:CUDA_VISIBLE_DEVICES = $GpuIds
$env:TOKENIZERS_PARALLELISM = "false"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

uv run accelerate launch --num_processes $NumGpus -m omnivoice.cli.train `
  --train_config $TrainConfig `
  --data_config $DataConfig `
  --output_dir $OutputDir

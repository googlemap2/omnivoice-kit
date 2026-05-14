param(
    [string[]]$ModelIds,
    [string]$Revision = "main",
    [string]$ModelsRoot = "models"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DefaultLocalDir([string]$RepoId, [string]$RootDir) {
    $repoName = ($RepoId -split "/")[-1]
    return Join-Path $RootDir $repoName
}

if (-not $ModelIds -or $ModelIds.Count -eq 0) {
    $rawInput = Read-Host "Nhap model id (cach nhau boi dau phay), vd: k2-fsa/OmniVoice, openai/whisper-large-v3"
    $ModelIds = $rawInput -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
}

if (-not $ModelIds -or $ModelIds.Count -eq 0) {
    Write-Error "Khong co model id nao duoc cung cap."
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupPy = Join-Path $scriptDir "backup_model.py"

if (-not (Test-Path $backupPy)) {
    Write-Error "Khong tim thay backup_model.py tai: $backupPy"
    exit 1
}

New-Item -ItemType Directory -Path $ModelsRoot -Force | Out-Null

$ok = @()
$failed = @()

foreach ($repoId in $ModelIds) {
    $localDir = Get-DefaultLocalDir -RepoId $repoId -RootDir $ModelsRoot
    Write-Host ""
    Write-Host "==== Backup $repoId ====" -ForegroundColor Cyan
    Write-Host "Target: $localDir"
    Write-Host "Revision: $Revision"

    & python $backupPy --repo-id $repoId --revision $Revision --local-dir $localDir
    if ($LASTEXITCODE -eq 0) {
        $ok += $repoId
        Write-Host "Backup thanh cong: $repoId" -ForegroundColor Green
    } else {
        $failed += $repoId
        Write-Host "Backup that bai: $repoId" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "===== Tong ket =====" -ForegroundColor Yellow
Write-Host "Thanh cong: $($ok.Count)"
foreach ($id in $ok) { Write-Host "  - $id" }
Write-Host "That bai: $($failed.Count)"
foreach ($id in $failed) { Write-Host "  - $id" }

if ($failed.Count -gt 0) {
    exit 1
}

<#
.SYNOPSIS
  このリポジトリの .claude\skills\ を PC の %USERPROFILE%\.claude\skills\ にインストールする。
  既存の同名スキルは .claude\skills_backup\<日時>\ に退避してから上書き（消さない）。
.EXAMPLE
  install_skills.bat をダブルクリック
  pwsh -File install_skills.ps1            # 通常
  pwsh -File install_skills.ps1 -Pull      # 先に git pull で最新化してから入れる
#>
param(
  [string]$Source = (Join-Path $PSScriptRoot '.claude\skills'),
  [string]$Target = (Join-Path $HOME '.claude\skills'),
  [switch]$Pull
)
$ErrorActionPreference = 'Stop'
if ($Pull -and (Test-Path (Join-Path $PSScriptRoot '.git'))) {
  Push-Location $PSScriptRoot; git pull --ff-only; Pop-Location
}
if (-not (Test-Path $Source)) { throw "skills folder not found: $Source" }
New-Item -ItemType Directory -Force -Path $Target | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$installed = @()
Get-ChildItem -LiteralPath $Source -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
  $dst = Join-Path $Target $_.Name
  if (Test-Path $dst) {
    $bk = Join-Path ((Split-Path $Target -Parent) + [IO.Path]::DirectorySeparatorChar + 'skills_backup') $stamp
    New-Item -ItemType Directory -Force -Path $bk | Out-Null
    Move-Item -LiteralPath $dst -Destination (Join-Path $bk $_.Name)
  }
  Copy-Item -LiteralPath $_.FullName -Destination $dst -Recurse
  Get-ChildItem -LiteralPath $dst -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
  $installed += $_.Name
}
"installed $($installed.Count) skills -> $Target"
$installed | ForEach-Object { "  /$_" }
'Claude Code を開き直すと全プロジェクトで使えます（例: /portfolio-a3-spread）。'

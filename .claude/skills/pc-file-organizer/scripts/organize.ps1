<#
.SYNOPSIS
  デスクトップ／外付けHDDのファイル整理（削除しない・計画→承認→実行→元に戻す）。
.EXAMPLE
  # 1) 棚卸し（読み取りのみ）
  pwsh -File organize.ps1 -Mode Inventory -Root "$env:USERPROFILE\Desktop"
  # 2) 計画を作る（plan.csv を確認してもらう）
  pwsh -File organize.ps1 -Mode Plan -Root "$env:USERPROFILE\Desktop"
  # 3) 承認後に実行（plan.csv の通りに移動、move_log.csv を記録）
  pwsh -File organize.ps1 -Mode Apply
  # 4) 元に戻す
  pwsh -File organize.ps1 -Mode Undo
  外付けHDD: -Root "E:\" -Dest "E:\整理済み" -Recurse
#>
param(
  [ValidateSet('Inventory', 'Plan', 'Apply', 'Undo')] [string]$Mode = 'Plan',
  [string]$Root = [Environment]::GetFolderPath('Desktop'),
  [string]$Dest = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) '整理済み'),
  [string]$WorkDir = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'クロードコード\file-organizer'),
  [switch]$Recurse
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$PlanCsv = Join-Path $WorkDir 'plan.csv'
$LogCsv = Join-Path $WorkDir 'move_log.csv'
$Stamp = Get-Date -Format 'yyyyMMdd'

$Rules = [ordered]@{
  '3D\STL_印刷用'    = '.stl', '.3mf', '.obj', '.ply'
  '3D\スライス済'     = '.gcode', '.ctb', '.cbddlp', '.photon', '.pwmx', '.goo'
  '3D\Blender'       = '.blend'
  '3D\Rhino'         = '.3dm', '.gh'
  '3D\Fusion_STEP'   = '.f3d', '.f3z', '.step', '.stp', '.igs', '.iges'
  '3D\ZBrush'        = '.ztl', '.zpr'
  '3D\交換形式'       = '.fbx', '.glb', '.gltf', '.usd', '.usdz'
  '図面'             = '.dwg', '.dxf', '.vwx', '.jww', '.sfc'
  '写真'             = '.jpg', '.jpeg', '.png', '.heic', '.tif', '.tiff', '.cr2', '.nef', '.arw', '.dng', '.webp'
  '動画'             = '.mp4', '.mov', '.avi', '.mkv', '.m4v'
  'ドキュメント'       = '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.ppt', '.pptx', '.txt', '.md', '.rtf'
  'アーカイブ'        = '.zip', '.rar', '.7z', '.lzh'
  "_整理待ち\$Stamp\インストーラ" = '.exe', '.msi', '.dmg'
}
$Skip = '.lnk', '.url', '.ini', '.sys', '.tmp', '.part', '.crdownload'

function Get-Files {
  $p = @{ LiteralPath = $Root; File = $true; Force = $false; ErrorAction = 'SilentlyContinue' }
  if ($Recurse) { $p.Recurse = $true }
  Get-ChildItem @p | Where-Object {
    -not ($_.Attributes -band [IO.FileAttributes]::Hidden) -and
    -not ($_.Attributes -band [IO.FileAttributes]::System) -and
    ($Skip -notcontains $_.Extension.ToLower()) -and
    -not $_.FullName.StartsWith($Dest, [StringComparison]::OrdinalIgnoreCase)
  }
}

function Get-Category($f) {
  $ext = $f.Extension.ToLower()
  foreach ($k in $Rules.Keys) {
    if ($Rules[$k] -contains $ext) {
      if ($k -eq '写真' -or $k -eq '動画') { return "$k\$($f.LastWriteTime.ToString('yyyy'))\$($f.LastWriteTime.ToString('yyyy-MM'))" }
      return $k
    }
  }
  return 'その他'
}

switch ($Mode) {
  'Inventory' {
    $files = @(Get-Files)
    $inv = Join-Path $WorkDir "inventory_$Stamp.csv"
    $files | Select-Object FullName, Extension, Length, LastWriteTime | Export-Csv $inv -NoTypeInformation -Encoding utf8
    "files: $($files.Count)   total: {0:N1} GB   -> $inv" -f (($files | Measure-Object Length -Sum).Sum / 1GB)
    '--- by extension (top 15) ---'
    $files | Group-Object { $_.Extension.ToLower() } | Sort-Object Count -Descending | Select-Object -First 15 |
      ForEach-Object { '{0,-8} {1,6} files  {2,10:N1} MB' -f $_.Name, $_.Count, (($_.Group | Measure-Object Length -Sum).Sum / 1MB) }
    '--- largest 10 ---'
    $files | Sort-Object Length -Descending | Select-Object -First 10 | ForEach-Object { '{0,10:N1} MB  {1}' -f ($_.Length / 1MB), $_.FullName }
  }
  'Plan' {
    $files = @(Get-Files)
    # duplicates: same size first, then SHA256
    $dupe = @{}
    $files | Group-Object Length | Where-Object Count -gt 1 | ForEach-Object {
      $_.Group | ForEach-Object { [pscustomobject]@{ F = $_; H = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } } |
        Group-Object H | Where-Object Count -gt 1 | ForEach-Object {
          $keep = $_.Group | Sort-Object { $_.F.FullName.Length }, { $_.F.LastWriteTime } | Select-Object -First 1
          $_.Group | Where-Object { $_ -ne $keep } | ForEach-Object { $dupe[$_.F.FullName] = $keep.F.FullName }
        }
    }
    $taken = @{}
    $plan = foreach ($f in $files) {
      if ($dupe.ContainsKey($f.FullName)) { $cat = "_整理待ち\$Stamp\重複"; $why = "duplicate of $($dupe[$f.FullName])" }
      else { $cat = Get-Category $f; $why = "ext $($f.Extension.ToLower())" }
      $dir = Join-Path $Dest $cat
      $target = Join-Path $dir $f.Name
      $n = 2
      while ((Test-Path -LiteralPath $target) -or $taken.ContainsKey($target.ToLower())) {
        $target = Join-Path $dir ('{0}_{1}{2}' -f $f.BaseName, $n, $f.Extension); $n++
      }
      $taken[$target.ToLower()] = 1
      [pscustomobject]@{ Source = $f.FullName; Target = $target; Reason = $why; SizeMB = [math]::Round($f.Length / 1MB, 2) }
    }
    @($plan) | Export-Csv $PlanCsv -NoTypeInformation -Encoding utf8
    "planned moves: $(@($plan).Count)  (duplicates: $($dupe.Count))  -> $PlanCsv"
    @($plan) | Group-Object { Split-Path (Split-Path $_.Target -Parent) -Leaf } | Sort-Object Count -Descending |
      ForEach-Object { '{0,-20} {1,5}' -f $_.Name, $_.Count }
    'Nothing was moved. Review plan.csv, then run -Mode Apply.'
  }
  'Apply' {
    if (-not (Test-Path $PlanCsv)) { throw "no plan: run -Mode Plan first" }
    $plan = Import-Csv $PlanCsv
    $log = foreach ($p in $plan) {
      $status = 'moved'
      try {
        if (-not (Test-Path -LiteralPath $p.Source)) { $status = 'missing' }
        elseif (Test-Path -LiteralPath $p.Target) { $status = 'target-exists' }
        else {
          New-Item -ItemType Directory -Force -Path (Split-Path $p.Target -Parent) | Out-Null
          Move-Item -LiteralPath $p.Source -Destination $p.Target
        }
      } catch { $status = "error: $($_.Exception.Message)" }
      [pscustomobject]@{ Source = $p.Source; Target = $p.Target; Status = $status; Time = (Get-Date -Format s) }
    }
    $log | Export-Csv $LogCsv -NoTypeInformation -Encoding utf8
    $log | Group-Object Status | ForEach-Object { '{0,-14} {1}' -f $_.Name, $_.Count }
    "log -> $LogCsv   (undo: -Mode Undo)"
  }
  'Undo' {
    if (-not (Test-Path $LogCsv)) { throw "no move_log.csv" }
    $log = @(Import-Csv $LogCsv | Where-Object Status -eq 'moved')
    [array]::Reverse($log)
    $ok = 0
    foreach ($l in $log) {
      if ((Test-Path -LiteralPath $l.Target) -and -not (Test-Path -LiteralPath $l.Source)) {
        New-Item -ItemType Directory -Force -Path (Split-Path $l.Source -Parent) | Out-Null
        Move-Item -LiteralPath $l.Target -Destination $l.Source; $ok++
      }
    }
    "restored: $ok / $($log.Count)"
    Rename-Item $LogCsv ("move_log_undone_{0}.csv" -f (Get-Date -Format yyyyMMddHHmmss))
  }
}

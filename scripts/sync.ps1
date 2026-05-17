$ErrorActionPreference = "Stop"

$repo = "https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
$tmp = Join-Path $env:TEMP ("bellosoft-sync-" + [System.IO.Path]::GetRandomFileName())

$syncFolders = @(
    ".github"
    ".agents"
    ".claude"
    ".kilo"
    "_bmad"
    ".vscode"
)

$protectedPathPrefixes = @(
    ".github/skills/bmad-tea"
    ".github/skills/reports"
    ".github/CODEOWNERS"
)

function Get-ContentHash($path) {
    $content = [System.IO.File]::ReadAllText($path) -replace "`r`n", "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    return [System.BitConverter]::ToString($md5.ComputeHash($bytes)) -replace "-", ""
}

function Sync-Folder($srcBase, $destBase, $logLabel) {
    if (-not (Test-Path $srcBase)) { return }

    foreach ($file in (Get-ChildItem -Path $srcBase -Recurse -File -Force)) {
        if ($file.LinkType -eq "SymbolicLink") { continue }

        $src = $file.FullName
        $rel = [System.IO.Path]::GetRelativePath($srcBase, $src) -replace "\\", "/"
        $dest = Join-Path $destBase ($rel -replace "/", "\")
        $relNorm = "$logLabel/$rel"

        $protected = $false
        foreach ($prefix in $protectedPathPrefixes) {
            if ($relNorm -eq $prefix -or $relNorm -like "$prefix/*") {
                Write-Host "     ⏭ Skipping $relNorm (protected)"
                $protected = $true
                break
            }
        }
        if ($protected) { continue }

        if (Test-Path $dest) {
            if ((Get-ContentHash $src) -eq (Get-ContentHash $dest)) {
                Write-Host "     ⏭ Skipping $relNorm (unchanged)"
                continue
            }
        }

        New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
        Copy-Item -Path $src -Destination $dest -Force
        Write-Host "     ✅ $relNorm"
    }
}

$cwd = (Get-Location).Path
Write-Host "🔄 Syncing Bellosoft project defaults into: $cwd"

git clone --depth=1 --quiet $repo $tmp

foreach ($folder in $syncFolders) {
    $src = Join-Path $tmp $folder
    $dest = Join-Path $cwd $folder
    if (Test-Path $src) {
        Write-Host "  → $folder/"
        Sync-Folder $src $dest $folder
    }
}

Remove-Item -Recurse -Force $tmp

Write-Host "✅ Sync complete."
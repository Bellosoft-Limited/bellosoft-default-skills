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

    $srcBase = $srcBase.TrimEnd('\', '/')

    foreach ($file in (Get-ChildItem -Path $srcBase -Recurse -File -Force)) {
        $src = $file.FullName
        $rel = $src.Substring($srcBase.Length + 1) -replace "\\", "/"
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

Write-Host "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet $repo $tmp

foreach ($folder in $syncFolders) {
    $src = Join-Path $tmp $folder
    $dest = ".\$folder"
    if (Test-Path $src) {
        Write-Host "  → $folder/"
        Sync-Folder $src $dest $folder
    }
}

Remove-Item -Recurse -Force $tmp

Write-Host "✅ Sync complete."
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

function Test-SymlinkPrivilege {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ContentHash($path) {
    $content = [System.IO.File]::ReadAllText($path) -replace "`r`n", "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    return [System.BitConverter]::ToString($md5.ComputeHash($bytes)) -replace "-", ""
}

function Sync-Symlinks($srcBase, $destBase) {
    if (-not (Test-Path $srcBase)) { return }

    Get-ChildItem -Path $srcBase -Recurse -Force | Where-Object { $_.LinkType -eq "SymbolicLink" } | ForEach-Object {
        $rel = [System.IO.Path]::GetRelativePath($srcBase, $_.FullName) -replace "\\", "/"
        $dest = Join-Path $destBase ($rel -replace "/", "\")
        $target = $_.Target

        if (Test-Path $dest) {
            Write-Host "     ⏭ Skipping symlink $rel (already exists)"
            return
        }

        New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
        New-Item -ItemType SymbolicLink -Path $dest -Target $target -Force | Out-Null
        Write-Host "     🔗 $rel -> $target"
    }
}

function Sync-Folder($srcBase, $destBase, $logLabel) {
    if (-not (Test-Path $srcBase)) { return }

    foreach ($file in (Get-ChildItem -Path $srcBase -Recurse -File -Force)) {
        # Skip files that are inside symlinked directories
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

if (-not (Test-SymlinkPrivilege)) {
    Write-Warning "⚠️  Not running as Administrator — symlinks may fail. Enable Developer Mode or run as Admin."
}

git clone --depth=1 --quiet $repo $tmp

foreach ($folder in $syncFolders) {
    $src = Join-Path $tmp $folder
    $dest = Join-Path $cwd $folder
    if (Test-Path $src) {
        Write-Host "  → $folder/"
        Sync-Folder $src $dest $folder
        Sync-Symlinks $src $dest
    }
}

Remove-Item -Recurse -Force $tmp

Write-Host "✅ Sync complete."
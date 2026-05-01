$ErrorActionPreference = "Stop"

$repo = "https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
$tmp = Join-Path $env:TEMP ("bellosoft-sync-" + [System.IO.Path]::GetRandomFileName())

# Folders to sync from company core into each client repo.
# NOTE: .github/core/ and .github/stack/ are subfolders of .github/ and synced automatically.
$syncFolders = @(
    ".github",           # Copilot instructions, agents, prompts, skills, hooks, workflows, core, stack
    "_bmad",             # BMAD methodology config
    ".vscode",           # VS Code settings (chat.* configs)
    "scripts"            # Sync scripts (self-updating)
)

$protectedFiles = @("config.yaml", "config.yml", ".env")

# Paths the sync script will NEVER overwrite.
$protectedPathPrefixes = @(
    ".github/skills/bmad-tea",
    ".github/skills/reports",
    ".github/CODEOWNERS"          # Each client may have their own
)

function Get-ContentHash($path) {
    $content = [System.IO.File]::ReadAllText($path) -replace "`r`n", "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    return [System.BitConverter]::ToString($md5.ComputeHash($bytes)) -replace "-", ""
}

function Sync-Folder($srcBase, $destBase, $logLabel) {
    if (-not (Test-Path $srcBase)) { return }

    Get-ChildItem -Path $srcBase -Recurse -File -Force | ForEach-Object {
        $src = $_.FullName
        $rel = $src.Substring($srcBase.Length + 1) -replace "\\", "/"
        $dest = Join-Path $destBase ($rel -replace "/", "\")

        $relNorm = "$logLabel/$rel"

        $filename = $_.Name
        if ($protectedFiles -contains $filename -and (Test-Path $dest)) {
            Write-Host "     ⏭ Skipping $relNorm (protected file)"
            return
        }

        foreach ($prefix in $protectedPathPrefixes) {
            if ($relNorm -like "$prefix/*" -or $relNorm -eq $prefix) {
                Write-Host "     ⏭ Skipping $relNorm (protected)"
                return
            }
        }

        if (Test-Path $dest) {
            if ((Get-ContentHash $src) -eq (Get-ContentHash $dest)) {
                Write-Host "     ⏭ Skipping $relNorm (unchanged)"
                return
            }
        }

        New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
        Copy-Item -Path $src -Destination $dest -Force
        Write-Host "     ✅ $relNorm"
    }
}

Write-Host "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet $repo $tmp

# Sync top-level allow-listed folders
foreach ($folder in $syncFolders) {
    $src = Join-Path $tmp $folder
    $dest = ".\$folder"
    if (Test-Path $src) {
        Write-Host "  → $folder/"
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Sync-Folder $src $dest $folder
    }
}

Remove-Item -Recurse -Force $tmp

Write-Host "✅ Sync complete."
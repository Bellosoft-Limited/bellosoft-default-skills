$ErrorActionPreference = "Stop"

$repo = "https://github.com/Bellosoft-Limited/bellosoft-default-skills.git"
$tmp = Join-Path $env:TEMP ("bellosoft-sync-" + [System.IO.Path]::GetRandomFileName())

$protectedFiles = @("config.yaml", "config.yml", ".env")

function Get-ContentHash($path) {
    $content = [System.IO.File]::ReadAllText($path) -replace "`r`n", "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    return [System.BitConverter]::ToString($md5.ComputeHash($bytes)) -replace "-", ""
}

Write-Host "🔄 Syncing Bellosoft project defaults..."

git clone --depth=1 --quiet $repo $tmp

# Get ALL directories including hidden (dotfolders like .github, .vscode)
Get-ChildItem -Path $tmp -Directory -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
    $folderName = $_.Name
    $srcFolder = $_.FullName
    Write-Host "  → Copying $folderName/"

    New-Item -ItemType Directory -Force -Path ".\$folderName" | Out-Null

    Get-ChildItem -Path $srcFolder -Recurse -File -Force | ForEach-Object {
        $src = $_.FullName
        $rel = $src.Substring($srcFolder.Length + 1)
        $dest = Join-Path ".\$folderName" $rel
        $filename = $_.Name

        # Skip protected files if they already exist
        if ($protectedFiles -contains $filename -and (Test-Path $dest)) {
            Write-Host "     ⏭ Skipping $folderName\$rel (protected)"
            return
        }

        # Skip if files are identical (normalize line endings before comparing)
        if (Test-Path $dest) {
            $srcHash = Get-ContentHash $src
            $destHash = Get-ContentHash $dest
            if ($srcHash -eq $destHash) {
                Write-Host "     ⏭ Skipping $folderName\$rel (unchanged)"
                return
            }
        }

        New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
        Copy-Item -Path $src -Destination $dest -Force
        Write-Host "     ✅ $folderName\$rel"
    }
}

Remove-Item -Recurse -Force $tmp

Write-Host "✅ Sync complete."
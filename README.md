# bellosoft-default-skills

Shared project configuration files automatically synced across all Bellosoft projects.

---

## What gets synced

Every **folder** at the root of this repo gets copied into the target project. Currently includes:

- `.github/` — GitHub Actions workflows, PR templates, issue templates
- `.vscode/` — Editor settings, recommended extensions
- `_bmad/` — BMAD methodology config and templates

Files named `config.yaml`, `config.yml`, or `.env` are **never overwritten** if they already exist in the target project.

---

## Syncing into a project

Run from the **root of the target project**.

**Bash (Linux / Mac / WSL / Git Bash):**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Bellosoft-Limited/bellosoft-default-skills/master/sync.sh)
```

**PowerShell (Windows):**
```powershell
irm https://raw.githubusercontent.com/Bellosoft-Limited/bellosoft-default-skills/master/sync.ps1 | iex
```

Safe to run multiple times — it overwrites everything except protected files.

---

## Adding new shared config folders

1. Clone this repo:
   ```bash
   git clone https://github.com/Bellosoft-Limited/bellosoft-default-skills.git
   cd bellosoft-default-skills
   ```

2. Add your new folder at the root:
   ```bash
   mkdir .mynewconfig
   # add files inside it
   ```

3. Commit and push:
   ```bash
   git add .
   git commit -m "add .mynewconfig"
   git push
   ```

The next time anyone runs the sync command in a project, the new folder will be copied in automatically.

---

## Protecting files from being overwritten

If a file inside a synced folder should never overwrite an existing local version (like `config.yaml`), add its filename to the `PROTECTED_FILES` array in `sync.sh` and `sync.ps1`:

**sync.sh:**
```bash
PROTECTED_FILES=("config.yaml" "config.yml" ".env" "your-file-here")
```

**sync.ps1:**
```powershell
$protectedFiles = @("config.yaml", "config.yml", ".env", "your-file-here")
```

Commit both files after updating.

---

## Repository structure

```
bellosoft-default-skills/
├── .github/               # Shared GitHub config
├── .vscode/               # Shared editor config
├── _bmad/                 # Shared BMAD config
├── sync.sh                # Sync script for Bash
├── sync.ps1               # Sync script for PowerShell
└── README.md              # This file
```
# .kilo

Kilo Code configuration for this project.

## Contents

| Path | Description |
|------|-------------|
| `kilo.jsonc` | Kilo Code settings |
| `agents/` | Agent definitions (mirrors `.claude/agents`) |
| `skills/` | Skills (mirrors `.claude/skills`) |

`agents` and `skills` are not included in this folder — they mirror `.claude/agents` and `.claude/skills`.
You can either create symlinks (recommended) or copy the contents manually.

---

## Option A — Symlinks (recommended)

Keeps `agents` and `skills` in sync with `.claude` automatically.

**Linux / macOS:**
```bash
ln -s "../.claude/agents" ".kilo/agents"
ln -s "../.claude/skills" ".kilo/skills"
```

**Windows — elevated CMD (run as Administrator):**
```cmd
mklink /D ".kilo\agents" "..\\.claude\\agents"
mklink /D ".kilo\skills" "..\\.claude\\skills"
```

**Windows — PowerShell (run as Administrator):**
```powershell
New-Item -ItemType SymbolicLink -Path ".kilo\agents" -Target "..\.claude\agents"
New-Item -ItemType SymbolicLink -Path ".kilo\skills" -Target "..\.claude\agents"
```

---

## Option B — Copy contents

If you can't create symlinks, copy the folders manually:

```bash
cp -r .claude/agents .kilo/agents
cp -r .claude/skills .kilo/skills
```

**Windows:**
```powershell
Copy-Item -Recurse .claude\agents .kilo\agents
Copy-Item -Recurse .claude\skills .kilo\skills
```

> Note: With this option, changes to `.claude/agents` or `.claude/skills` won't automatically reflect in `.kilo`. Re-run the copy when they change.
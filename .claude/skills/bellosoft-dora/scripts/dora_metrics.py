#!/usr/bin/env python3
"""
Bellosoft DORA Metrics Collector.

Fetches and computes the 4 DORA metrics from Jira + GitHub + Dokploy.

Usage:
  python3 dora_metrics.py --project AP --days 30
  python3 dora_metrics.py --project AU --days 90
  python3 dora_metrics.py --setup   # One-time credential + project setup

Config file: docs/planning-artifacts/project-dora-config.md
Credentials: .secrets/jira-*.txt, .secrets/dokploy-*.txt, gh CLI auth
Skip flags:  .secrets/skip-jira.txt, .secrets/skip-github.txt, .secrets/skip-dokploy.txt
"""
import argparse, json, os, sys, re
from datetime import datetime, timezone, timedelta
from subprocess import run
from pathlib import Path


# ── Credential / skip helpers ───────────────────────────────────────────
def _read(path):
    try:
        return Path(path).read_text().strip()
    except (FileNotFoundError, OSError):
        return None


def _write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(value + "\n")


def load_credentials():
    """Load creds from .secrets/ and skip flags. Missing = None."""
    return {
        "jira_url":      _read(".secrets/jira-url.txt"),
        "jira_user":     _read(".secrets/jira-username.txt"),
        "jira_token":    _read(".secrets/jira-api-token.txt"),
        "dokploy_url":   _read(".secrets/dokploy-url.txt"),
        "dokploy_token": _read(".secrets/dokploy-api-token.txt"),
        # Skip flags — truthy means user explicitly opted out
        "skip_jira":     _read(".secrets/skip-jira.txt"),
        "skip_github":   _read(".secrets/skip-github.txt"),
        "skip_dokploy":  _read(".secrets/skip-dokploy.txt"),
    }


# ── Project config (no hardcoded defaults) ─────────────────────────────
CONFIG_PATH = Path("docs/planning-artifacts/project-dora-config.md")


def load_project_config(project_key):
    """Load project config from the config file. Returns dict or None if not found."""
    if not CONFIG_PATH.exists():
        return None
    text = CONFIG_PATH.read_text(encoding="utf-8")
    # Find the section for this project key
    pattern = re.compile(
        r"^## " + re.escape(project_key) + r"(?:\s.*)?$",
        re.MULTILINE
    )
    m = pattern.search(text)
    if not m:
        return None

    # Extract lines until the next ## heading or EOF
    section_start = m.end()
    next_section = re.search(r"^## ", text[section_start:], re.MULTILINE)
    section = text[section_start: section_start + next_section.start()] if next_section else text[section_start:]

    cfg = {"key": project_key}
    for line in section.split("\n"):
        line = line.strip().lstrip("- ")
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k == "name":
            cfg["name"] = v
        elif k == "jira_board":
            try:
                cfg["jira_board"] = int(v)
            except ValueError:
                pass
        elif k == "github_repo":
            cfg["github_repo"] = None if v in ("None", "none", "") else v
        elif k == "dokploy_app_ids":
            cfg["dokploy_apps"] = [x.strip().strip("\"'") for x in v.strip("[]").split(",") if x.strip()]
        elif k == "dokploy_compose_ids":
            cfg["dokploy_compose_ids"] = [x.strip().strip("\"'") for x in v.strip("[]").split(",") if x.strip()]
    return cfg


def save_project_config(cfg):
    """Write or update a project section in the config file."""
    key = cfg["key"]
    lines = [
        f"## {key} ({cfg.get('name', key)})",
        f"- name: {cfg.get('name', key)}",
        f"- jira_board: {cfg.get('jira_board', '')}",
        f"- github_repo: {cfg.get('github_repo', 'None')}",
        f"- dokploy_app_ids: [{', '.join(cfg.get('dokploy_apps', []))}]",
        f"- dokploy_compose_ids: [{', '.join(cfg.get('dokploy_compose_ids', []))}]",
    ]
    new_section = "\n".join(lines) + "\n"

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        text = CONFIG_PATH.read_text(encoding="utf-8")
        pattern = re.compile(r"^## " + re.escape(key) + r"(?:\s.*)?$", re.MULTILINE)
        m = pattern.search(text)
        if m:
            # Replace existing section
            next_sec = re.search(r"^## ", text[m.end():], re.MULTILINE)
            if next_sec:
                text = text[:m.start()] + new_section + "\n" + text[m.end() + next_sec.start():]
            else:
                text = text[:m.start()] + new_section
            CONFIG_PATH.write_text(text, encoding="utf-8")
            return
        with open(CONFIG_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + new_section)
    else:
        CONFIG_PATH.write_text("# Project DORA Config\n\n" + new_section, encoding="utf-8")

    print(f"  ✅ Project config saved to {CONFIG_PATH}", file=sys.stderr)


def setup_project(project_key, creds):
    """Interactive setup for a project's config. Returns populated cfg dict."""
    print(f"\n📋 Project '{project_key}' not found in config. Let's set it up.", file=sys.stderr)
    cfg = {"key": project_key}

    cfg["name"] = input(f"  Project name (e.g. AutomaPost): ").strip() or project_key

    if not creds.get("skip_jira"):
        val = input(f"  Jira board ID for {project_key} (integer, or Enter to skip): ").strip()
        if val:
            try:
                cfg["jira_board"] = int(val)
            except ValueError:
                print("  ⚠ Not an integer, skipping board ID.", file=sys.stderr)

    if not creds.get("skip_github"):
        val = input(f"  GitHub repo (e.g. Org/repo, or Enter to skip): ").strip()
        cfg["github_repo"] = val if val else None

    cfg["dokploy_apps"] = []
    cfg["dokploy_compose_ids"] = []
    if not creds.get("skip_dokploy") and creds.get("dokploy_url") and creds.get("dokploy_token"):
        compose_ids = auto_discover_dokploy(creds, project_key)
        cfg["dokploy_compose_ids"] = compose_ids

    save_project_config(cfg)
    return cfg


# ── HTTP helpers ────────────────────────────────────────────────────────
def rest_get(url, user=None, token=None, method="GET", data=None, auth_mode="basic"):
    cmd = ["curl", "-s", "-X", method, "-H", "Accept: application/json"]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    if auth_mode == "basic" and user and token:
        cmd += ["-u", f"{user}:{token}"]
    elif auth_mode in ("apikey", "header") and token:
        cmd += ["-H", "x-api-key: " + token]
    cmd.append(url)
    r = run(cmd, capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def gh_api(path):
    r = run(["gh", "api", path, "--jq", "."], capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout) if r.stdout.strip() else None


# ── Data collectors ─────────────────────────────────────────────────────
def collect_jira(creds, project_key, board_id, since):
    result = {"sprints": [], "done_issues": [], "lead_times": [], "bugs_any": 0,
              "bugs_done": 0, "mttr_hours": [], "issues_total": 0, "type_done": {}}

    if creds.get("skip_jira"):
        print("  ⏭ Jira skipped (opted out)", file=sys.stderr)
        return result

    if not all([creds.get("jira_url"), creds.get("jira_user"), creds.get("jira_token")]):
        print("  ⚠ Jira credentials missing — run `--setup` to configure", file=sys.stderr)
        return result

    if not board_id:
        print("  ⚠ No Jira board ID configured for this project — run `--setup` to add it", file=sys.stderr)
        return result

    url, user, token = creds["jira_url"], creds["jira_user"], creds["jira_token"]
    def jira(path):
        return rest_get(f"{url}{path}", user, token, auth_mode="basic")

    start, total = 0, None
    sprints = []
    while True:
        sp = jira(f"/rest/agile/1.0/board/{board_id}/sprint?startAt={start}&maxResults=50")
        if not sp or not sp.get("values"):
            break
        sprints.extend(sp["values"])
        start += 50
        if total is None: total = sp.get("total", 0)
        if start >= total: break

    for s in sprints:
        if s.get("state") == "closed" and s.get("endDate"):
            try:
                ed = datetime.fromisoformat(s["endDate"].replace("Z", "+00:00"))
                if ed >= since:
                    result["sprints"].append({"name": s["name"], "end": ed})
            except ValueError: pass

    start, total = 0, None
    issues = []
    while True:
        iss = jira(f"/rest/agile/1.0/board/{board_id}/issue?startAt={start}&maxResults=100&fields=summary,issuetype,status,created,resolutiondate,updated")
        if not iss or not iss.get("issues"):
            break
        issues.extend(iss["issues"])
        start += 100
        if total is None: total = iss.get("total", 0)
        if start >= total: break
    result["issues_total"] = len(issues)

    done_issues = [i for i in issues if i.get("fields",{}).get("status",{}).get("statusCategory",{}).get("key") == "done"]
    result["done_issues"] = done_issues

    for issue in done_issues[:60]:
        key = issue["key"]
        cl = jira(f"/rest/api/3/issue/{key}/changelog?maxResults=100")
        if not cl: continue
        in_prog, dtime = None, None
        for hist in cl.get("values", []):
            for item in hist.get("items", []):
                if item.get("field") != "status": continue
                to_str = item.get("toString", "")
                ts = hist.get("created", "")
                t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if to_str == "In Progress" and in_prog is None: in_prog = t
                if to_str == "Done": dtime = t
        if dtime is None:
            res = issue["fields"].get("resolutiondate", "")
            if res: dtime = datetime.fromisoformat(res.replace("Z", "+00:00"))
        if in_prog and dtime and dtime > in_prog:
            result["lead_times"].append((dtime - in_prog).total_seconds() / 86400)

    for issue in issues:
        f = issue["fields"]
        itype = f.get("issuetype", {}).get("name", "?")
        scat = f.get("status", {}).get("statusCategory", {}).get("key", "?")
        if scat == "done":
            result["type_done"][itype] = result["type_done"].get(itype, 0) + 1
        if itype == "Bug":
            result["bugs_any"] += 1
            if scat == "done": result["bugs_done"] += 1

    for issue in issues:
        f = issue["fields"]
        if f.get("issuetype", {}).get("name") != "Bug": continue
        created = f.get("created", "")
        resolved = f.get("resolutiondate", "")
        scat = f.get("status", {}).get("statusCategory", {}).get("key", "")
        if created and resolved and scat == "done":
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            r_ = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
            result["mttr_hours"].append((r_ - c).total_seconds() / 3600)
    return result


def collect_github(creds, repo, since):
    result = {"prs": [], "pr_cycle_hours": [], "commits": 0, "gh_deploys": [], "gh_deploy_count": 0}

    if creds.get("skip_github"):
        print("  ⏭ GitHub skipped (opted out)", file=sys.stderr)
        return result

    if not repo:
        print("  ⚠ No GitHub repo configured for this project — run `--setup` to add it", file=sys.stderr)
        return result

    prs = gh_api(f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30")
    if prs:
        for pr in prs:
            merged = pr.get("merged_at") or (pr.get("pull_request") or {}).get("merged_at")
            if merged:
                m = datetime.fromisoformat(merged.replace("Z", "+00:00"))
                if m >= since:
                    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    cycle_h = (m - created).total_seconds() / 3600
                    result["prs"].append({"num": pr["number"], "title": pr["title"], "merged": merged[:10], "cycle_h": cycle_h})
                    result["pr_cycle_hours"].append(cycle_h)

    since_str = since.strftime("%Y-%m-%d")
    commits = gh_api(f"repos/{repo}/commits?since={since_str}T00:00:00Z&per_page=100")
    result["commits"] = len(commits) if commits else 0

    runs = gh_api(f"repos/{repo}/actions/runs?status=success&per_page=20")
    if runs:
        for run_ in runs.get("workflow_runs", []):
            name = run_.get("name", "")
            if "deploy" in name.lower() or "release" in name.lower():
                created = run_.get("created_at", "")
                if created:
                    c = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if c >= since:
                        result["gh_deploy_count"] += 1
                        result["gh_deploys"].append({"name": name, "date": created[:10]})
    return result


def collect_dokploy(creds, proj_cfg, since):
    result = {"deployments": [], "deploy_count": 0}

    if creds.get("skip_dokploy"):
        print("  ⏭ Dokploy skipped (opted out)", file=sys.stderr)
        return result

    url = creds.get("dokploy_url")
    token = creds.get("dokploy_token")
    if not url or not token:
        print("  ⚠ Dokploy credentials missing — run `--setup` to configure", file=sys.stderr)
        return result

    apps = proj_cfg.get("dokploy_apps", [])
    composes = proj_cfg.get("dokploy_compose_ids", [])
    if not apps and not composes:
        print("  ⚠ No Dokploy apps or compose IDs configured for this project — run `--setup` to add them", file=sys.stderr)
        return result

    def fetch(endpoint):
        return rest_get(f"{url}{endpoint}", token=token, auth_mode="apikey")

    for app_id in apps:
        data = fetch(f"/api/deployment.all?applicationId={app_id}")
        if not data: continue
        items = data if isinstance(data, list) else data.get("deployments", data.get("values", []))
        for dep in items:
            ts = dep.get("createdAt") or dep.get("created_at", "")
            if not ts: continue
            try:
                c = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if c >= since:
                    result["deployments"].append({"id": app_id, "status": dep.get("status","?"), "date": ts[:10], "title": "", "source": "app"})
                    result["deploy_count"] += 1
            except ValueError: pass

    for cid in composes:
        data = fetch(f"/api/deployment.allByCompose?composeId={cid}")
        if not data or not isinstance(data, list): continue
        for dep in data:
            ts = dep.get("createdAt") or dep.get("created_at", "")
            if not ts: continue
            try:
                c = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if c >= since:
                    status = dep.get("status", "?")
                    title = dep.get("title", "?")[:60]
                    result["deployments"].append({"id": cid, "status": status, "date": ts[:10], "title": title, "source": "compose"})
                    result["deploy_count"] += 1
            except ValueError: pass

    return result


def auto_discover_dokploy(creds, project_key):
    url = creds.get("dokploy_url")
    token = creds.get("dokploy_token")
    if not url or not token:
        return []

    print(f"  🔍 Checking Dokploy for deployments matching \"{project_key}\"...", file=sys.stderr)
    projects = rest_get(f"{url}/api/project.all", token=token, auth_mode="apikey")
    if not projects or not isinstance(projects, list):
        return []

    target = project_key.lower()
    candidates = []
    for p in projects:
        pname = p.get("name", "").lower().replace(" ", "").replace("-", "")
        if target in pname or pname in target:
            for env in p.get("environments", []):
                for c in env.get("compose", []):
                    cid = c.get("composeId", "")
                    if cid:
                        candidates.append({"project": p.get("name"), "compose_id": cid, "compose_name": c.get("name")})

    if not candidates:
        print(f"  ⚠ No Dokploy compose stacks found matching \"{project_key}\"", file=sys.stderr)
        answer = input("  Enter Dokploy compose ID manually (or press Enter to skip): ").strip()
        return [answer] if answer else []

    print(f"  Found {len(candidates)} potential matches:", file=sys.stderr)
    for c in candidates:
        print(f"    • Project \"{c['project']}\" → compose \"{c['compose_name']}\" (ID: {c['compose_id']})", file=sys.stderr)

    answer = input(f"  Use these {len(candidates)} compose IDs? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes"):
        return [c["compose_id"] for c in candidates]
    manual = input("  Enter comma-separated compose IDs (or Enter to skip): ").strip()
    return [x.strip() for x in manual.split(",") if x.strip()] if manual else []


# ── Metrics computation ─────────────────────────────────────────────────
def classify(val, metric):
    if metric == "deploy_freq":
        if val >= 7:    return "🏆 Elite",  f"{val:.1f}/wk"
        if val >= 1:    return "🥇 High",   f"{val:.1f}/wk"
        if val >= 4/30: return "🥈 Medium", f"{val:.1f}/wk"
        return "🥉 Low", f"{val:.1f}/wk"
    if metric == "lead":
        if val < 1/24:  return "🏆 Elite",  f"{val*24:.1f}h"
        if val < 1:     return "🥇 High",   f"{val*24:.1f}h"
        if val <= 7:    return "🥇 High",   f"{val:.1f}d"
        if val <= 30:   return "🥈 Medium", f"{val:.1f}d"
        return "🥉 Low",  f"{val:.1f}d"
    if metric == "cfr":
        if val <= 15:   return "🏆🥇 Elite/High", f"{val:.1f}%"
        if val <= 30:   return "🥈 Medium",       f"{val:.1f}%"
        return "🥉 Low",  f"{val:.1f}%"
    if metric == "mttr":
        if val < 1:     return "🏆 Elite",   f"{val*60:.0f}m"
        if val <= 24:   return "🥇 High",    f"{val:.1f}h"
        if val <= 168:  return "🥈 Medium",  f"{val/24:.1f}d"
        return "🥉 Low",  f"{val/24:.1f}d"
    return "—", "—"


def compute_metrics(jira_data, gh_data, dok_data, days_back):
    weeks = max(days_back / 7, 1)
    deploy_count = len(jira_data["sprints"]) + gh_data["gh_deploy_count"] + dok_data["deploy_count"]
    deploy_freq = deploy_count / weeks
    jira_lead = sum(jira_data["lead_times"]) / len(jira_data["lead_times"]) if jira_data["lead_times"] else 0
    pr_lead = sum(gh_data["pr_cycle_hours"]) / len(gh_data["pr_cycle_hours"]) if gh_data["pr_cycle_hours"] else 0
    pr_lead_days = pr_lead / 24
    total_done = sum(jira_data["type_done"].values())
    cfr = (jira_data["bugs_done"] / total_done * 100) if total_done > 0 else 0
    mttr = sum(jira_data["mttr_hours"]) / len(jira_data["mttr_hours"]) if jira_data["mttr_hours"] else 0
    return {
        "deploy_freq": deploy_freq, "lead_time_jira": jira_lead, "lead_time_pr": pr_lead_days,
        "cfr": cfr, "mttr": mttr, "total_deployments": deploy_count,
        "jira_sprint_count": len(jira_data["sprints"]), "gh_deploy_count": gh_data["gh_deploy_count"],
        "dok_deploy_count": dok_data["deploy_count"], "lead_time_samples": len(jira_data["lead_times"]),
        "pr_cycle_samples": len(gh_data["pr_cycle_hours"]), "total_done": total_done,
        "bugs_any": jira_data["bugs_any"], "bugs_done": jira_data["bugs_done"],
        "mttr_samples": len(jira_data["mttr_hours"]), "issue_type_done": jira_data["type_done"],
    }


def print_report(m, proj_cfg, project_key, jira_data, gh_data, dok_data, days_back, since, now):
    df_t, df_v = classify(m["deploy_freq"], "deploy_freq")
    lt_t, lt_v = classify(m["lead_time_jira"], "lead")
    pr_t, pr_v = classify(m["lead_time_pr"], "lead") if gh_data["pr_cycle_hours"] else ("—", "—")
    cfr_t, cfr_v = classify(m["cfr"], "cfr")
    mttr_t, mttr_v = classify(m["mttr"], "mttr")
    lines = []
    lines.append("")
    lines.append("╔" + "═" * 74 + "╗")
    lines.append(f"║  📊 DORA METRICS — {project_key} ({proj_cfg.get('name','?')})  •  {since.strftime('%Y-%m-%d')} → {now.strftime('%Y-%m-%d')}  ({days_back}d)  ║")
    lines.append("╚" + "═" * 74 + "╝")
    lines.append("")
    lines.append(f"  {'Metric':<32} {'Your Value':<20} {'DORA Band':<18}  {'Target':<18}")
    lines.append("  " + "─" * 32 + " " + "─" * 20 + " " + "─" * 18 + "  " + "─" * 18)
    lines.append(f"  1. Deployment Frequency   {df_v:<20} {df_t:<18}  ≥7/wk (Elite)")
    lines.append(f"     Sources: {m['jira_sprint_count']} sprints + {m['gh_deploy_count']} GH deploys + {m['dok_deploy_count']} Dokploy")
    lines.append(f"  2. Lead Time (Jira cycle) {lt_v:<20} {lt_t:<18}  <1h (Elite)")
    if gh_data["pr_cycle_hours"]:
        lines.append(f"     Lead Time (PR cycle)    {pr_v:<20} {pr_t:<18}  <1h (Elite)")
    lines.append(f"  3. Change Failure Rate    {cfr_v:<20} {cfr_t:<18}  ≤15% (Elite/High)")
    lines.append(f"  4. Mean Time to Restore   {mttr_v:<20} {mttr_t:<18}  <1h (Elite)")
    lines.append("")
    lines.append("─" * 78)
    lines.append("  DATA SOURCES & RAW COUNTS")
    lines.append("─" * 78)
    lines.append(f"  🐙 GitHub ({gh_data.get('_repo','?') or 'none'})")
    if gh_data.get("commits") is not None:
        lines.append(f"      Commits:              {gh_data['commits']}")
    lines.append(f"      PRs merged:            {len(gh_data['prs'])}")
    for p in gh_data["prs"]:
        lines.append(f"        • #{p['num']} — {p['title'][:55]} ({p['merged']}, cycle: {p['cycle_h']:.0f}h)")
    lines.append(f"      Deploy workflow runs: {gh_data['gh_deploy_count']}")
    for d in gh_data["gh_deploys"]:
        lines.append(f"        • {d['name']} — {d['date']}")
    lines.append(f"  🚀 Dokploy ({dok_data.get('_url','?') or 'none'})")
    lines.append(f"      Deployments:           {dok_data['deploy_count']}")
    for d in dok_data["deployments"]:
        title_str = f" — {d['title']}" if d.get("title") else ""
        lines.append(f"        • {d['id'][:20]} — {d['date']} ({d['status']}){title_str}")
    lines.append(f"  📋 Jira (board {proj_cfg.get('jira_board','?')})")
    lines.append(f"      Sprint deployments:    {len(jira_data['sprints'])}")
    for rs in jira_data["sprints"]:
        lines.append(f"        • {rs['name']} (ended {rs['end'].strftime('%Y-%m-%d')})")
    lines.append(f"      Total issues:          {jira_data['issues_total']}")
    lines.append(f"      Completed issues:      {m['total_done']}")
    if m["issue_type_done"]:
        lines.append(f"      Issue types (Done):")
        for t, c in sorted(m["issue_type_done"].items(), key=lambda x: -x[1]):
            lines.append(f"        • {t}: {c}")
    lines.append(f"      Lead time samples:     {m['lead_time_samples']}")
    lines.append(f"      Bugs (any):            {m['bugs_any']}")
    lines.append(f"      Bugs (resolved):       {m['bugs_done']}")
    lines.append(f"      MTTR samples:          {m['mttr_samples']}")
    lines.append("")
    lines.append("─" * 78)
    lines.append("  RECOMMENDATIONS")
    lines.append("─" * 78)
    if m["deploy_freq"] < 1:
        lines.append("  🎯 **Deployment Frequency** is your biggest gap.")
        lines.append("     Action: Set up automated deploys on merge to main.")
    if m["lead_time_jira"] < 7 and m["lead_time_jira"] > 0:
        lines.append("  ✅ **Lead Time** is solid — code moves fast through the system.")
    if m["cfr"] == 0:
        lines.append("  ⚠️  **CFR** shows 0% — may undercount if production bugs aren't")
        lines.append("     tracked as Jira Bugs. Consider tracking all incidents in Jira.")
    elif m["cfr"] > 15:
        lines.append("  ⚠️  **CFR** above 15% — investigate quality pipeline gaps.")
    if m["mttr_samples"] == 0:
        lines.append("  ⚠️  **MTTR** has no data — track production incidents as Bugs with resolution dates.")
    lines.append("─" * 78)
    report = "\n".join(lines)
    print(report)
    return report


def save_report(report, project_key, now):
    output_dir = Path("docs/dora")
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = now.strftime("%Y-%m-%d")
    path = output_dir / f"dora-report-{project_key}-{date_str}.md"
    path.write_text(report, encoding="utf-8")
    print(f"\n  📝 Report saved: {path}", file=sys.stderr)
    return path


# ── Setup wizard ────────────────────────────────────────────────────────
def run_setup(creds):
    """Interactive credential + service opt-in setup."""
    print("🔧 DORA Metrics Setup\n", file=sys.stderr)

    # ── Jira ──
    jira_configured = all([creds.get("jira_url"), creds.get("jira_user"), creds.get("jira_token")])
    if creds.get("skip_jira"):
        print("  Jira: opted out (skip-jira.txt exists)", file=sys.stderr)
    elif jira_configured:
        print("  ✅ Jira: already configured", file=sys.stderr)
    else:
        connect = input("  Connect to Jira? [Y/n]: ").strip().lower()
        if connect in ("n", "no"):
            _write(".secrets/skip-jira.txt", "opted-out")
            print("  ⏭ Jira skipped — recorded in .secrets/skip-jira.txt", file=sys.stderr)
            creds["skip_jira"] = "opted-out"
        else:
            for key, label, filename in [
                ("jira_url",   "Jira URL (e.g. https://yourorg.atlassian.net)", "jira-url.txt"),
                ("jira_user",  "Jira email",                                    "jira-username.txt"),
                ("jira_token", "Jira API token",                                "jira-api-token.txt"),
            ]:
                if not creds.get(key):
                    val = input(f"    {label}: ").strip()
                    if val:
                        _write(f".secrets/{filename}", val)
                        creds[key] = val
                        print(f"    ✅ Saved {filename}", file=sys.stderr)
                else:
                    print(f"    ✅ {filename} already set", file=sys.stderr)

    # ── GitHub ──
    if creds.get("skip_github"):
        print("  GitHub: opted out (skip-github.txt exists)", file=sys.stderr)
    elif run(["gh", "auth", "status"], capture_output=True).returncode == 0:
        print("  ✅ GitHub: gh CLI already authenticated", file=sys.stderr)
    else:
        connect = input("  Connect to GitHub (via gh CLI)? [Y/n]: ").strip().lower()
        if connect in ("n", "no"):
            _write(".secrets/skip-github.txt", "opted-out")
            print("  ⏭ GitHub skipped — recorded in .secrets/skip-github.txt", file=sys.stderr)
            creds["skip_github"] = "opted-out"
        else:
            r = run(["gh", "auth", "status"], capture_output=True, text=True)
            if r.returncode == 0:
                print("    ✅ gh CLI already authenticated", file=sys.stderr)
            else:
                print("    ⚠ gh CLI not authenticated. Run: gh auth login", file=sys.stderr)

    # ── Dokploy ──
    dokploy_configured = creds.get("dokploy_url") and creds.get("dokploy_token")
    if creds.get("skip_dokploy"):
        print("  Dokploy: opted out (skip-dokploy.txt exists)", file=sys.stderr)
    elif dokploy_configured:
        print("  ✅ Dokploy: already configured", file=sys.stderr)
    else:
        connect = input("  Connect to Dokploy? [Y/n]: ").strip().lower()
        if connect in ("n", "no"):
            _write(".secrets/skip-dokploy.txt", "opted-out")
            print("  ⏭ Dokploy skipped — recorded in .secrets/skip-dokploy.txt", file=sys.stderr)
            creds["skip_dokploy"] = "opted-out"
        else:
            if not creds.get("dokploy_url"):
                val = input("    Dokploy URL (e.g. https://dokploy.example.com): ").strip()
                if val:
                    _write(".secrets/dokploy-url.txt", val)
                    creds["dokploy_url"] = val
                    print("    ✅ Saved dokploy-url.txt", file=sys.stderr)
            else:
                print("    ✅ dokploy-url.txt already set", file=sys.stderr)
            if not creds.get("dokploy_token"):
                val = input("    Dokploy API token: ").strip()
                if val:
                    _write(".secrets/dokploy-api-token.txt", val)
                    creds["dokploy_token"] = val
                    print("    ✅ Saved dokploy-api-token.txt", file=sys.stderr)
            else:
                print("    ✅ dokploy-api-token.txt already set", file=sys.stderr)

    print("\n✅ Setup complete. Run without --setup to collect metrics.", file=sys.stderr)


# ── Main ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Bellosoft DORA Metrics Collector")
    parser.add_argument("--project", "-p", default="AP", help="Project key (any key from project-dora-config.md)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Lookback period in days")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument("--setup", action="store_true", help="One-time credential + service setup")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)

    creds = load_credentials()

    if args.setup:
        run_setup(creds)
        return

    # Load project config — prompt for setup if not found
    proj_cfg = load_project_config(args.project)
    if not proj_cfg:
        print(f"  ⚠ Project '{args.project}' not found in {CONFIG_PATH}", file=sys.stderr)
        answer = input(f"  Set it up now? [Y/n]: ").strip().lower()
        if answer in ("n", "no"):
            print("  Aborted.", file=sys.stderr)
            sys.exit(1)
        proj_cfg = setup_project(args.project, creds)

    # Warn if credentials are missing for any non-skipped service
    needs_setup = []
    if not creds.get("skip_jira") and not all([creds.get("jira_url"), creds.get("jira_user"), creds.get("jira_token")]):
        needs_setup.append("Jira")
    if not creds.get("skip_dokploy") and (not creds.get("dokploy_url") or not creds.get("dokploy_token")):
        needs_setup.append("Dokploy")
    if needs_setup:
        print(f"  ⚠ Missing credentials for: {', '.join(needs_setup)}", file=sys.stderr)
        answer = input("  Run --setup now to configure them? [Y/n]: ").strip().lower()
        if answer not in ("n", "no"):
            run_setup(creds)
            creds = load_credentials()

    # Auto-discover Dokploy compose IDs if creds exist but none configured
    dok_composes = proj_cfg.get("dokploy_compose_ids", [])
    if (not dok_composes and not creds.get("skip_dokploy")
            and creds.get("dokploy_url") and creds.get("dokploy_token")):
        dok_composes = auto_discover_dokploy(creds, args.project)
        if dok_composes:
            proj_cfg["dokploy_compose_ids"] = dok_composes
            save_project_config(proj_cfg)

    print(f"\n🔍 Collecting DORA metrics for {args.project} ({args.days}d lookback)...", file=sys.stderr)
    print(f"   Jira board:          {proj_cfg.get('jira_board', '(not set)')}", file=sys.stderr)
    print(f"   GitHub repo:         {proj_cfg.get('github_repo', '(not set)')}", file=sys.stderr)
    print(f"   Dokploy compose IDs: {proj_cfg.get('dokploy_compose_ids', [])}", file=sys.stderr)
    print(file=sys.stderr)

    jira_data = collect_jira(creds, args.project, proj_cfg.get("jira_board"), since)
    gh_data = collect_github(creds, proj_cfg.get("github_repo"), since)
    gh_data["_repo"] = proj_cfg.get("github_repo")
    dok_data = collect_dokploy(creds, proj_cfg, since)
    dok_data["_url"] = creds.get("dokploy_url")

    metrics = compute_metrics(jira_data, gh_data, dok_data, args.days)

    report = print_report(metrics, proj_cfg, args.project, jira_data, gh_data, dok_data, args.days, since, now)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"  📝 Report saved: {args.output}", file=sys.stderr)
    else:
        save_report(report, args.project, now)


if __name__ == "__main__":
    main()

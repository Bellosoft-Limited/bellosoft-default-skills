#!/usr/bin/env python3
"""
Bellosoft DORA Metrics Collector.

Fetches and computes the 4 DORA metrics from Jira + GitHub + Dokploy.

Usage:
  python3 dora_metrics.py --project AP --days 30
  python3 dora_metrics.py --project AU --days 90
  python3 dora_metrics.py --project AUT --days 30 --output docs/dora/report.md
  python3 dora_metrics.py --setup   # One-time credential setup

Config file: docs/planning-artifacts/project-dora-config.md
Credentials: .secrets/jira-*.txt, .secrets/dokploy-*.txt, gh CLI auth
"""
import argparse, json, os, sys, urllib.parse
from datetime import datetime, timezone, timedelta
from subprocess import run
from pathlib import Path

# ── Default project config ─────────────────────────────────────────────
DEFAULT_PROJECTS = {
    "AP": {"name": "AutomaPost",     "jira_board": 4,  "github_repo": "Bellosoft-Limited/AutomaPost",  "dokploy_apps": [], "dokploy_compose_ids": ["Vvs8EzlgIAv4xjHJHOWg3"]},
    "AU": {"name": "123auto",        "jira_board": 5,  "github_repo": "Bellosoft-Limited/123auto",     "dokploy_apps": []},
    "AUT":{"name": "AutomaLead",     "jira_board": 8,  "github_repo": "Bellosoft-Limited/automaLead",   "dokploy_apps": []},
    "BI": {"name": "Bellosoft Int",  "jira_board": 42, "github_repo": None,                             "dokploy_apps": []},
}


def load_credentials():
    """Load creds from .secrets/, return dict. Missing = None."""
    def read(path):
        try:
            with open(path) as f:
                return f.read().strip()
        except (FileNotFoundError, OSError):
            return None
    return {
        "jira_url": read(".secrets/jira-url.txt"),
        "jira_user": read(".secrets/jira-username.txt"),
        "jira_token": read(".secrets/jira-api-token.txt"),
        "dokploy_url": read(".secrets/dokploy-url.txt"),
        "dokploy_token": read(".secrets/dokploy-api-token.txt"),
    }


def load_project_config(project_key):
    """Load project config from file or fall back to defaults."""
    config_path = Path("docs/planning-artifacts/project-dora-config.md")
    if config_path.exists():
        text = config_path.read_text()
        if f"## {project_key}" in text or f"## {project_key} (" in text:
            cfg = DEFAULT_PROJECTS.get(project_key, {}).copy()
            for line in text.split("\n"):
                if "jira_board:" in line:
                    try:
                        cfg["jira_board"] = int(line.split("jira_board:")[1].strip())
                    except: pass
                if "github_repo:" in line:
                    val = line.split("github_repo:")[1].strip()
                    cfg["github_repo"] = val if val != "None" else None
                if "dokploy_app_ids:" in line:
                    val = line.split("dokploy_app_ids:")[1].strip().strip("[]")
                    cfg["dokploy_apps"] = [v.strip().strip('"\'') for v in val.split(",") if v.strip()]
                if "dokploy_compose_ids:" in line:
                    val = line.split("dokploy_compose_ids:")[1].strip().strip("[]")
                    cfg["dokploy_compose_ids"] = [v.strip().strip('"\'') for v in val.split(",") if v.strip()]
            return cfg
    return DEFAULT_PROJECTS.get(project_key, {})


# ── HTTP helpers ────────────────────────────────────────────────────────
def rest_get(url, user=None, token=None, method="GET", data=None, auth_mode="basic"):
    """Generic REST client. auth_mode: 'basic' (Jira) or 'apikey' (Dokploy)."""
    cmd = ["curl", "-s", "-X", method, "-H", "Accept: application/json"]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]

    if auth_mode == "basic" and user and token:
        cmd += ["-u", f"{user}:{token}"]
    elif auth_mode == "apikey" and token:
        cmd += ["-H", "x-api-key: " + token]
    elif auth_mode == "header" and token:
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
    """GitHub API via gh CLI."""
    r = run(["gh", "api", path, "--jq", "."], capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout) if r.stdout.strip() else None


# ── Data collectors ─────────────────────────────────────────────────────
def collect_jira(creds, project_key, board_id, since):
    """Collect Jira data: sprints, issues, lead times."""
    result = {"sprints": [], "done_issues": [], "lead_times": [], "bugs_any": 0,
              "bugs_done": 0, "mttr_hours": [], "issues_total": 0, "type_done": {}}
    if not all([creds.get("jira_url"), creds.get("jira_user"), creds.get("jira_token")]):
        print("  \u26a0 Jira credentials missing, skipping", file=sys.stderr)
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


def collect_github(repo, since):
    """Collect GitHub data: PRs, commits, deploy workflow runs."""
    result = {"prs": [], "pr_cycle_hours": [], "commits": 0, "gh_deploys": [], "gh_deploy_count": 0}
    if not repo:
        print("  \u26a0 No GitHub repo configured, skipping", file=sys.stderr)
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
    """Collect Dokploy deployment data for apps AND compose stacks."""
    result = {"deployments": [], "deploy_count": 0}
    url = creds.get("dokploy_url")
    token = creds.get("dokploy_token")
    if not url or not token:
        print("  \u26a0 Dokploy credentials missing, skipping", file=sys.stderr)
        return result

    apps = proj_cfg.get("dokploy_apps", [])
    composes = proj_cfg.get("dokploy_compose_ids", [])
    if not apps and not composes:
        print("  \u26a0 No Dokploy apps or compose IDs configured, skipping", file=sys.stderr)
        return result

    def fetch(endpoint):
        return rest_get(f"{url}{endpoint}", token=token, auth_mode="apikey")

    # App-based deployments
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

    # Compose-based deployments (used by AP, most Bellosoft projects)
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
    """Query Dokploy projects to find matching compose IDs for a project key."""
    url = creds.get("dokploy_url")
    token = creds.get("dokploy_token")
    if not url or not token:
        return []

    print(f"  \U0001f50d Checking Dokploy for deployments matching \"{project_key}\"...", file=sys.stderr)
    projects = rest_get(f"{url}/api/project.all", token=token, auth_mode="apikey")
    if not projects or not isinstance(projects, list):
        return []

    # Try to match by name (case-insensitive)
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
        print(f"  \u26a0 No Dokploy compose stacks found matching \"{project_key}\"", file=sys.stderr)
        answer = input("  Enter Dokploy compose ID manually (or press Enter to skip): ").strip()
        if answer:
            return [answer]
        return []

    print(f"  Found {len(candidates)} potential matches:", file=sys.stderr)
    for c in candidates:
        print(f"    \u2022 Project \"{c['project']}\" \u2192 compose \"{c['compose_name']}\" (ID: {c['compose_id']})", file=sys.stderr)

    answer = input(f"  Use these {len(candidates)} compose IDs for Dokploy tracking? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes"):
        return [c["compose_id"] for c in candidates]
    manual = input("  Enter comma-separated compose IDs (or press Enter to skip): ").strip()
    if manual:
        return [x.strip() for x in manual.split(",") if x.strip()]
    return []


def save_dokploy_config(project_key, compose_ids):
    """Save Dokploy compose mapping to project config file."""
    config_path = Path("docs/planning-artifacts/project-dora-config.md")
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        text = config_path.read_text()
        # Update existing section or create new entry
        if f"## {project_key}" in text:
            new_text = []
            found_section = False
            found_compose = False
            for line in text.split("\n"):
                if line.startswith(f"## {project_key}") or line.startswith(f"## {project_key} ("):
                    found_section = True
                if found_section and not found_compose and line.strip().startswith("- "):
                    new_text.append(f"- dokploy_compose_ids: [{', '.join(compose_ids)}]")
                    found_compose = True
                if found_section and line.startswith("## ") and not line.startswith(f"## {project_key}"):
                    if not found_compose:
                        new_text.append(f"- dokploy_compose_ids: [{', '.join(compose_ids)}]")
                    found_section = False
                new_text.append(line)
            if not found_compose:
                new_text.append(f"- dokploy_compose_ids: [{', '.join(compose_ids)}]")
            config_path.write_text("\n".join(new_text))
        else:
            with open(str(config_path), "a") as f:
                f.write(f"\n## {project_key}\n- dokploy_compose_ids: [{', '.join(compose_ids)}]\n")
    else:
        config_path.write_text(f"# Project DORA Config\n## {project_key}\n- dokploy_compose_ids: [{', '.join(compose_ids)}]\n")

    print(f"  \u2705 Saved Dokploy mapping to {config_path}", file=sys.stderr)


# ── Metrics computation ─────────────────────────────────────────────────
def classify(val, metric):
    """Classify a raw metric value into DORA band."""
    if metric == "deploy_freq":
        if val >= 7:    return "\U0001f3c6 Elite",  f"{val:.1f}/wk"
        if val >= 1:    return "\U0001f947 High",   f"{val:.1f}/wk"
        if val >= 4/30: return "\U0001f948 Medium", f"{val:.1f}/wk"
        return "\U0001f949 Low", f"{val:.1f}/wk"
    if metric == "lead":
        if val < 1/24:  return "\U0001f3c6 Elite",  f"{val*24:.1f}h"
        if val < 1:     return "\U0001f947 High",   f"{val*24:.1f}h"
        if val <= 7:    return "\U0001f947 High",   f"{val:.1f}d"
        if val <= 30:   return "\U0001f948 Medium", f"{val:.1f}d"
        return "\U0001f949 Low",  f"{val:.1f}d"
    if metric == "cfr":
        if val <= 15:   return "\U0001f3c6\U0001f947 Elite/High", f"{val:.1f}%"
        if val <= 30:   return "\U0001f948 Medium",       f"{val:.1f}%"
        return "\U0001f949 Low",  f"{val:.1f}%"
    if metric == "mttr":
        if val < 1:     return "\U0001f3c6 Elite",   f"{val*60:.0f}m"
        if val <= 24:   return "\U0001f947 High",    f"{val:.1f}h"
        if val <= 168:  return "\U0001f948 Medium",  f"{val/24:.1f}d"
        return "\U0001f949 Low",  f"{val/24:.1f}d"
    return "\u2014", "\u2014"


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


# ── Output ──────────────────────────────────────────────────────────────
def print_report(m, proj_cfg, project_key, jira_data, gh_data, dok_data, days_back, since, now):
    df_t, df_v = classify(m["deploy_freq"], "deploy_freq")
    lt_t, lt_v = classify(m["lead_time_jira"], "lead")
    pr_t, pr_v = classify(m["lead_time_pr"], "lead") if gh_data["pr_cycle_hours"] else ("\u2014", "\u2014")
    cfr_t, cfr_v = classify(m["cfr"], "cfr")
    mttr_t, mttr_v = classify(m["mttr"], "mttr")
    lines = []
    lines.append("")
    lines.append("\u2554" + "\u2550" * 74 + "\u2557")
    lines.append(f"\u2551  \U0001f4ca DORA METRICS \u2014 {project_key} ({proj_cfg.get('name','?')})  \u2022  {since.strftime('%Y-%m-%d')} \u2192 {now.strftime('%Y-%m-%d')}  {'('+str(days_back)+'d)'}  \u2551")
    lines.append("\u255a" + "\u2550" * 74 + "\u255d")
    lines.append("")
    lines.append(f"  {'Metric':<32} {'Your Value':<20} {'DORA Band':<18}  {'Target':<18}")
    lines.append("  " + "─" * 32 + " " + "─" * 20 + " " + "─" * 18 + "  " + "─" * 18)
    lines.append(f"  1. Deployment Frequency   {df_v:<20} {df_t:<18}  \u22657/wk (Elite)")
    lines.append(f"     Sources: {m['jira_sprint_count']} sprints + {m['gh_deploy_count']} GH deploys + {m['dok_deploy_count']} Dokploy")
    lines.append(f"  2. Lead Time (Jira cycle) {lt_v:<20} {lt_t:<18}  <1h (Elite)")
    if gh_data["pr_cycle_hours"]:
        lines.append(f"     Lead Time (PR cycle)    {pr_v:<20} {pr_t:<18}  <1h (Elite)")
    lines.append(f"  3. Change Failure Rate    {cfr_v:<20} {cfr_t:<18}  \u226415% (Elite/High)")
    lines.append(f"  4. Mean Time to Restore   {mttr_v:<20} {mttr_t:<18}  <1h (Elite)")
    lines.append("")
    lines.append("\u2500" * 78)
    lines.append("  DATA SOURCES & RAW COUNTS")
    lines.append("\u2500" * 78)
    lines.append(f"  \U0001f419 GitHub ({gh_data.get('_repo','?') or 'none'})")
    if gh_data.get("commits") is not None:
        lines.append(f"      Commits:              {gh_data['commits']}")
    lines.append(f"      PRs merged:            {len(gh_data['prs'])}")
    for p in gh_data["prs"]:
        lines.append(f"        \u2022 #{p['num']} \u2014 {p['title'][:55]} ({p['merged']}, cycle: {p['cycle_h']:.0f}h)")
    lines.append(f"      Deploy workflow runs: {gh_data['gh_deploy_count']}")
    for d in gh_data["gh_deploys"]:
        lines.append(f"        \u2022 {d['name']} \u2014 {d['date']}")
    lines.append(f"  \U0001f680 Dokploy ({dok_data.get('_url','?') or 'none'})")
    lines.append(f"      Deployments:           {dok_data['deploy_count']}")
    for d in dok_data["deployments"]:
        title_str = f" \u2014 {d['title']}" if d.get("title") else ""
        lines.append(f"        \u2022 {d['id'][:20]} \u2014 {d['date']} ({d['status']}){title_str}")
    lines.append(f"  \U0001f4cb Jira (board {proj_cfg.get('jira_board','?')})")
    lines.append(f"      Sprint deployments:    {len(jira_data['sprints'])}")
    for rs in jira_data["sprints"]:
        lines.append(f"        \u2022 {rs['name']} (ended {rs['end'].strftime('%Y-%m-%d')})")
    lines.append(f"      Total issues:          {jira_data['issues_total']}")
    lines.append(f"      Completed issues:      {m['total_done']}")
    if m["issue_type_done"]:
        lines.append(f"      Issue types (Done):")
        for t, c in sorted(m["issue_type_done"].items(), key=lambda x: -x[1]):
            lines.append(f"        \u2022 {t}: {c}")
    lines.append(f"      Lead time samples:     {m['lead_time_samples']}")
    lines.append(f"      Bugs (any):            {m['bugs_any']}")
    lines.append(f"      Bugs (resolved):       {m['bugs_done']}")
    lines.append(f"      MTTR samples:          {m['mttr_samples']}")
    lines.append("")
    lines.append("\u2500" * 78)
    lines.append("  RECOMMENDATIONS")
    lines.append("\u2500" * 78)
    if m["deploy_freq"] < 1:
        lines.append("  \U0001f3af **Deployment Frequency** is your biggest gap.")
        lines.append("     The team is shipping code but may not be deploying to production.")
        lines.append("     Action: Set up automated deploys on merge to main, or use")
        lines.append("     trunk-based development with continuous deployment.")
    if m["lead_time_jira"] < 7 and m["lead_time_jira"] > 0:
        lines.append("  \u2705 **Lead Time** is solid \u2014 code moves fast through the system.")
    if m["cfr"] == 0:
        lines.append("  \u26a0\ufe0f  **CFR** shows 0% which looks elite, but may undercount if")
        lines.append("     production bugs aren't tracked as Jira Bugs or if hotfixes")
        lines.append("     bypass the project. Consider tracking all incidents in Jira.")
    elif m["cfr"] > 15:
        lines.append("  \u26a0\ufe0f  **CFR** above 15% \u2014 investigate quality pipeline gaps.")
    if m["mttr_samples"] == 0:
        lines.append("  \u26a0\ufe0f  **MTTR** has no data \u2014 no bugs were completed in this period.")
        lines.append("     Track production incidents as Bugs with resolution dates.")
    lines.append("\u2500" * 78)
    report = "\n".join(lines)
    print(report)
    return report


def save_report(report, project_key, now):
    output_dir = Path("docs/dora")
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = now.strftime("%Y-%m-%d")
    path = output_dir / f"dora-report-{project_key}-{date_str}.md"
    path.write_text(report)
    print(f"\n  \U0001f4dd Report saved: {path}", file=sys.stderr)
    return path


# ── Main ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Bellosoft DORA Metrics Collector")
    parser.add_argument("--project", "-p", default="AP", help="Project key (AP, AU, AUT, ...)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Lookback period in days")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument("--setup", action="store_true", help="One-time credential setup")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)

    if args.setup:
        print("\U0001f527 DORA Metrics Setup", file=sys.stderr)
        creds = load_credentials()
        changes = []
        for key, label, filename in [
            ("jira_url", "Jira URL (e.g. https://yourorg.atlassian.net)", "jira-url.txt"),
            ("jira_user", "Jira email", "jira-username.txt"),
            ("jira_token", "Jira API token", "jira-api-token.txt"),
        ]:
            if not creds[key]:
                val = input(f"  {label}: ").strip()
                with open(f".secrets/{filename}", "w") as f:
                    f.write(val + "\n")
                changes.append(filename)
                creds[key] = val

        if not creds["dokploy_url"]:
            val = input("  Dokploy URL (optional, e.g. https://dokploy.example.com): ").strip()
            if val:
                with open(".secrets/dokploy-url.txt", "w") as f:
                    f.write(val + "\n")
                changes.append("dokploy-url.txt")
                creds["dokploy_url"] = val

        if not creds["dokploy_token"]:
            val = input("  Dokploy API token (optional): ").strip()
            if val:
                with open(".secrets/dokploy-api-token.txt", "w") as f:
                    f.write(val + "\n")
                changes.append("dokploy-api-token.txt")
                creds["dokploy_token"] = val

        if changes:
            print(f"\n\u2705 Saved: {', '.join(changes)}", file=sys.stderr)
        else:
            print("\u2705 All credentials already configured", file=sys.stderr)
        return

    creds = load_credentials()
    proj_cfg = load_project_config(args.project)
    proj_cfg["key"] = args.project

    # Auto-discover Dokploy compose IDs if credentials exist but no IDs configured
    dok_composes = proj_cfg.get("dokploy_compose_ids", [])
    if not dok_composes and creds.get("dokploy_url") and creds.get("dokploy_token"):
        dok_composes = auto_discover_dokploy(creds, args.project)
        if dok_composes:
            save_dokploy_config(args.project, dok_composes)
            proj_cfg["dokploy_compose_ids"] = dok_composes

    print(f"\n\U0001f50d Collecting DORA metrics for {args.project} ({args.days}d lookback)...", file=sys.stderr)
    print(f"   Jira board: {proj_cfg.get('jira_board','?')}", file=sys.stderr)
    print(f"   GitHub repo: {proj_cfg.get('github_repo','?')}", file=sys.stderr)
    print(f"   Dokploy compose IDs: {proj_cfg.get('dokploy_compose_ids',[])}", file=sys.stderr)
    print(file=sys.stderr)

    jira_data = collect_jira(creds, args.project, proj_cfg.get("jira_board"), since)
    gh_data = collect_github(proj_cfg.get("github_repo"), since)
    gh_data["_repo"] = proj_cfg.get("github_repo")
    dok_data = collect_dokploy(creds, proj_cfg, since)
    dok_data["_url"] = creds.get("dokploy_url")

    metrics = compute_metrics(jira_data, gh_data, dok_data, args.days)

    report = print_report(metrics, proj_cfg, args.project, jira_data, gh_data, dok_data, args.days, since, now)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report)
        print(f"  \U0001f4dd Report saved: {args.output}", file=sys.stderr)
    else:
        save_report(report, args.project, now)


if __name__ == "__main__":
    main()

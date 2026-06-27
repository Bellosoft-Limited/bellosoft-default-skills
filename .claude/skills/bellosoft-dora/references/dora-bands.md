# DORA Performance Bands

Reference: Forsgren, N., Humble, J., Kim, G. (2018). *Accelerate*
DORA State of DevOps Reports (2014–2024)

## 1. Deployment Frequency

| Band | Frequency | Benchmark |
|------|-----------|-----------|
| 🏆 Elite | On-demand (multiple deploys per day) | ≥ 7 deploys/week |
| 🥇 High | Between once per day and once per week | ≥ 1 deploys/week |
| 🥈 Medium | Between once per week and once per month | ≥ 0.25 deploys/week |
| 🥉 Low | Less than once per month | < 0.25 deploys/week |

**Proxies:** Fix-version releases, sprint cadence, deploy workflow runs, Dokploy deploys, Jira sprints.

## 2. Lead Time for Changes

| Band | Lead Time | Benchmark |
|------|-----------|-----------|
| 🏆 Elite | Less than one hour | < 1 hour |
| 🥇 High | Between one day and one week | 1–7 days |
| 🥈 Medium | Between one week and one month | 7–30 days |
| 🥉 Low | More than one month | > 30 days |

**Proxies:** PR creation-to-merge time, Jira In Progress → Done cycle time, commit-to-deploy interval.

## 3. Change Failure Rate (CFR)

| Band | Failure Rate | Benchmark |
|------|-------------|-----------|
| 🏆🥇 Elite / High | 0–15% | ≤ 15% |
| 🥈 Medium | 16–30% | 16–30% |
| 🥉 Low | > 30% | > 30% |

> ⚠️ In the 2021+ DORA reports, Elite and High bands were merged for CFR.

**Proxies:** Bugs created ÷ total completed issues, hotfix PRs, revert rate.

## 4. Mean Time to Restore (MTTR)

| Band | MTTR | Benchmark |
|------|------|-----------|
| 🏆 Elite | Less than one hour | < 1 hour |
| 🥇 High | Less than one day | 1–24 hours |
| 🥈 Medium | Between one day and one week | 1–7 days |
| 🥉 Low | More than one week | > 7 days |

**Proxies:** Bug creation-to-resolution time (Jira), hotfix PR cycle time.

## Elite vs Low Performance Gap

| Metric | Gap |
|--------|-----|
| Deployment frequency | 182× more frequent |
| Lead time for changes | 127× faster |
| Mean time to restore | 2,604× faster |
| Change failure rate | 7× lower |

## Key Research Findings

- Teams that deploy more frequently have **lower** failure rates (not higher)
- Faster lead times correlate with faster recovery
- Throughput and stability **reinforce each other**
- Trunk-based development, short-lived branches (< 24h), and daily commits consistently outperform feature branching
- Elite teams never use code freezes

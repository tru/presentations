---
Title: LLVM Release Process - EuroLLVM 2026
slides:
  theme: theme.css
  separator_vertical: "^\r?\n--\r?\n$"
---

## LLVM Release Process
### EuroLLVM 2026 Status Update
Cullen Rhodes, Douglas Yung, Tobias Hieta

---

# Introductions

---

# Recent Changes

* Two new Release Managers: **Cullen** and **Douglas**
* Stricter enforcement of acceptance criteria
* Automation updates
* Dropped split source packages

---

# Current Process

* Major release every **6 months**
* Branch: 2nd Tuesday in **January** (even) / **July** (odd)
* Point releases every 2 weeks, typically through X.1.8 or X.1.9

---

# LLVM 21 Release Timeline

<img src="release_timeline.png" style="width:100%;max-height:55vh;object-fit:contain;" />

---

# RC Acceptance Criteria

| Phase | Accepted |
|-------|----------|
| RC1 | Bug fixes, important optimizations, completion of features **started before branch** |
| RC2 / RC3 | Bug fixes, very safe backend-specific improvements |
| Final (X.1.0) | Critical bugs and regressions only |
| Point releases | Bug fixes, critical performance, must maintain API+ABI compat |

---

# By the Numbers

| Release | PRs Merged | PRs Rejected |
|---------|-----------|--------------|
| 20.x    | 346       | 53           |
| 21.x    | 287       | 68           |
| 22.x    | 233       | 76           |

Rejection rate rising: **13%** → **19%** → **25%**

---

# PRs Merged by Phase

<img src="phase_line_chart.png" style="width:100%;max-height:55vh;object-fit:contain;" />

RC1→RC2 always **4× busier** than Branch→RC1 &nbsp;·&nbsp; RC3→Final: **4 PRs** (20.x) vs **34–40** (21.x / 22.x)

---

# PRs by Subproject

<img src="subproject_chart.png" style="width:100%;max-height:65vh;object-fit:contain;" />

---

# Clang: Subsystems

<img src="clang_subsystems.png" style="width:100%;max-height:65vh;object-fit:contain;" />

---

# LLVM Core: Subsystems

<img src="llvm_subsystems.png" style="width:100%;max-height:65vh;object-fit:contain;" />

---

# LLVM Core: Backends

<img src="llvm_backends.png" style="width:100%;max-height:65vh;object-fit:contain;" />

---

# Who Reviews PRs

<img src="approver_chart.png" style="width:100%;max-height:55vh;object-fit:contain;" />

**nikic** alone: 48 PRs across 3 releases &nbsp;·&nbsp; top 5 reviewers handle the majority of all approvals

---

# Who Submits PRs

<img src="contributor_chart.png" style="width:100%;max-height:55vh;object-fit:contain;" />

~40 people do repeated work &nbsp;·&nbsp; most contributors appear only once

---

# What Works

* Predictable cadence
* Community knows when to expect a release
* Milestone tracking on GitHub
* Release manager availability and responsiveness

---

# What Doesn't Work

1. **No defined inclusion criteria** — every PR is a judgement call
2. **Flaky CI** blocks binary releases even when the code is ready
3. **Accidental ABI breakage** slips through reviews
4. **RC phase PR flood** — nobody looks until RC1 ships

---

# Join us at the Roundtable

### Right after this talk

What works? What should change? Come tell us.

---

# Q&A

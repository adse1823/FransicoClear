# SF Traffic Optimization — Roadmap & Checklists

**Goal:** Reduce traffic delay and signal wait times by improving signal timings with AI.  
This README is the single source of truth. No features land unless they’re in the current phase.

---

## Phase 0 — Foundations ✅/⬜
- [*] Clean repo structure (`backend/`, `frontend/`, `data/`, `scripts/`)
- [ ] Pinned deps (`numpy==1.26.4`, `pandas==2.2.2`)
- [ ] `scripts/run_both.sh` runs backend+frontend locally
- [ ] `/docs` shows endpoints; screenshots in README

**Exit criteria**
- [ ] Fresh clone → start → UI working, no 500s

---

## Phase 1 — MVP Routing App
- [ ] `/stats`, `/nodes`, `/shortest-path*`, `/graph-geo`, `/path-geo`
- [ ] Streamlit: source/dest dropdowns, compute path
- [ ] Map shows full network (gray) + path (highlight)
- [ ] Segment table (from, to, road_name, length) + totals
- [ ] Error banners for invalid nodes / no path

**Exit criteria**
- [ ] Known pair returns path+table in < 2s
- [ ] Graceful 404/400, no stack traces in UI

---

## Phase 2 — Data Contracts & Validation
- [ ] Schemas for `nodes.csv`, `edges.csv` (+ `signal_plans.csv` placeholder)
- [ ] Validator script (types, ranges, nulls)
- [ ] CI/guard script blocks bad data

**Exit criteria**
- [ ] Any bad CSV fails fast with clear error

---

## Phase 3 — Traffic Data Ingestion
- [ ] ETL to parquet for volumes/speeds/turns (synthetic allowed)
- [ ] 1+ week of time series for a corridor
- [ ] Data profiling notebook (nulls, spikes, gaps)

**Exit criteria**
- [ ] Time series present & profiled for corridor

---

## Phase 4 — Digital Twin (SUMO) v0
- [ ] Graph → SUMO network conversion
- [ ] Stub flows + fixed-time controllers
- [ ] Scenario runner (AM/PM)

**Exit criteria**
- [ ] SUMO runs two scenarios and exports KPIs

---

## Phase 5 — Calibration & Baselines
- [ ] Demand & signal calibration to field-like metrics
- [ ] Add actuated baseline
- [ ] KPI report: delay, queues, stops, travel time

**Exit criteria**
- [ ] Sim metrics within ±10–15% of field ref (or benchmark)

---

## Phase 6 — Classical Optimization (Corridor)
- [ ] Offset optimizer (progression/green wave)
- [ ] Split allocator with legal constraints
- [ ] Batch generate “Plan v1” per corridor

**Exit criteria**
- [ ] ≥5–10% delay reduction vs fixed/actuated
- [ ] No constraint violations

---

## Phase 7 — Scenario Coverage & Robustness
- [ ] Scenario library (AM/PM/weekend/incident/school/rain)
- [ ] Robustness test harness (mean & worst-case deltas)

**Exit criteria**
- [ ] Gains hold across ≥4 scenarios; no >3% regression

---

## Phase 8 — RL Sandbox
- [ ] Gym/TraCI multi-agent env
- [ ] Single-agent + multi-agent PPO/A2C baselines
- [ ] Action masking for hard safety constraints

**Exit criteria**
- [ ] Stable training; no violations in rollouts

---

## Phase 9 — Safe RL + Evaluation
- [ ] CTDE training; safety layer (clamp/filter actions)
- [ ] Eval vs classical optimizers over scenario library
- [ ] Confidence intervals & ablation reports

**Exit criteria**
- [ ] ≥10–20% delay reduction vs baselines; zero violations

---

## Phase 10 — Ops Service (Advisory)
- [ ] Stateless service to output plans/actions every Δt
- [ ] Human-readable diffs; JSON/CSV exports
- [ ] Immutable audit logs for each recommendation

**Exit criteria**
- [ ] 1 week advisory run; operators can review diffs

---

## Phase 11 — Shadow Mode Pilot
- [ ] Real-time ingest (or replay) + compute; no actuation
- [ ] Compare recommended vs actual outcomes live
- [ ] Alerting & dashboards

**Exit criteria**
- [ ] Significant gains predicted; no safety incidents

---

## Phase 12 — Limited Control Pilot
- [ ] Actuate 1–3 intersections with guardrails
- [ ] Watchdog + auto-rollback + manual override
- [ ] Pilot runbook & rollback drill

**Exit criteria**
- [ ] ≥10% measured corridor improvement; zero incidents

---

## Phase 13 — City-Scale & Governance
- [ ] Time-series store + batch lake
- [ ] Model registry, approvals, RBAC
- [ ] Drift detection, SLOs, alerting, rollout strategy

**Exit criteria**
- [ ] Regular re-optimization; versioned rollouts; sustained KPIs

---

## Non-Goals (until after Phase 12)
- Live multi-city support
- Complex turn restrictions beyond baseline legal rules
- Pedestrian personalization
- Monetization/billing

---

## Quick Start (Local)
```bash
# From repo root
bash scripts/run_both.sh
# Open http://localhost:8501  (UI)
# Open http://localhost:8000/docs  (API docs)

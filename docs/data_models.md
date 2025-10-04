
---

# `docs/data_models.md`

```markdown
# Data Models (Final Product)

This document lists the core entities, keys, fields, and main relationships that support:
- map edits (add/remove connections),
- time-of-day & day type selection,
- digital twin build & simulation runs,
- accident injection,
- KPI comparison (before/after),
- (optional) signal optimization with guardrails.

---

## Conventions
- **IDs:** strings (ULID/UUIDv7 recommended).
- **Time:** ISO-8601 UTC (e.g., `2025-10-03T08:05:00Z`). Time-of-day stored as `HH:MM`.
- **Geo:** WGS84 (`lon`, `lat`) as floats.
- **Units:** `length_m`, `speed_kph`, `flow_vph`, `queue_m`, `delay_s`.
- **Storage:** Parquet for fact tables; JSON/GeoJSON for configs/diffs.

---

## 1) Core Network

### Node
- **PK:** `node_id` (string)
- **Fields:**  
  - `node_id` (str)  
  - `lon` (float, −180..180)  
  - `lat` (float, −90..90)  
  - `name` (str, optional)  
  - `attrs` (object, optional)
- **Notes:** Intersection or anchor point.

### Edge (Link)
- **PK:** `edge_id` (string)
- **Fields:**  
  - `edge_id` (str)  
  - `u` (str, FK→Node)  
  - `v` (str, FK→Node)  
  - `length_m` (float > 0)  
  - `lanes` (int ≥ 1)  
  - `speed_kph` (float > 0)  
  - `one_way` (bool, default false)  
  - `name` (str, optional)  
  - `functional_class` (str, optional)  
  - `attrs` (object, optional)
- **Notes:** Geometry implied by node coordinates (store polyline if curves matter).

### NetworkVersion
- **PK:** `network_version_id` (string)
- **Fields:**  
  - `network_version_id` (str)  
  - `parent_version_id` (str, FK→NetworkVersion, nullable)  
  - `checksum` (str)  
  - `created_at` (datetime)
- **Purpose:** Immutable snapshot for reproducibility (baseline or baseline + applied edits).

---

## 2) Scenario & Edits

### Scenario
- **PK:** `scenario_id` (string)
- **Fields:**  
  - `scenario_id` (str)  
  - `name` (str)  
  - `base_network_version` (str, FK→NetworkVersion)  
  - `day_type_id` (str, FK→DayType)  
  - `time_of_day` (string `HH:MM`)  
  - `created_at` (datetime)  
  - `description` (str, optional)
- **Relations:** has many `ScenarioEdit`, `Incident`.

### ScenarioEdit
- **PK:** `edit_id` (string)
- **Fields:**  
  - `edit_id` (str)  
  - `scenario_id` (str, FK→Scenario)  
  - `type` (enum: `add_edge | remove_edge | modify_edge`)  
  - `edge_id` (str, FK→Edge; nullable for `add_edge`)  
  - `geometry` (GeoJSON, for `add_edge`)  
  - `delta_json` (object, for `modify_edge`, e.g., `{ "lanes": -1 }`)  
  - `created_at` (datetime)
- **Notes:** A diff against the baseline network.

### Incident
- **PK:** `incident_id` (string)
- **Fields:**  
  - `incident_id` (str)  
  - `scenario_id` (str, FK→Scenario)  
  - `edge_id` (str, FK→Edge)  
  - `start_time` (datetime)  
  - `duration_min` (int > 0)  
  - `severity` (enum: `lane_drop | closure`)  
  - `lanes_lost` (int ≥ 0; required if `lane_drop`)  
  - `note` (str, optional)
- **Notes:** Accident/closure that reduces capacity or blocks a link.

---

## 3) Time & Demand

### DayType
- **PK:** `day_type_id` (string; e.g., `Weekday | Weekend | Event`)
- **Fields:**  
  - `day_type_id` (str)  
  - `demand_profile_id` (str, FK→DemandProfile)

### DemandProfile
- **PK:** `demand_profile_id` (string)
- **Fields:**  
  - `demand_profile_id` (str)  
  - `level` (enum: `global | corridor | link`)  
  - `targets` (array of IDs; only if not global)  
  - `bins` (array of `{ start:"HH:MM", end:"HH:MM", multiplier: float }`)
- **Notes:** Drives flows for the twin (e.g., AM peak multipliers).

---

## 4) Digital Twin & Simulation

### TwinConfig
- **PK:** `twin_config_id` (string)
- **Fields:**  
  - `twin_config_id` (str)  
  - `scenario_id` (str, FK→Scenario)  
  - `resolved_network_version` (str, FK→NetworkVersion)  
  - `demand_profile_id` (str, FK→DemandProfile)  
  - `sim_engine` (str; e.g., `SUMO`)  
  - `engine_params` (object: `{ step_length_s, warmup_min, seed }`)  
  - `resolved_time_window` (object `{ start: datetime, end: datetime }`)
- **Purpose:** Exact, immutable configuration used for a run.

### SimulationRun
- **PK:** `run_id` (string)
- **Fields:**  
  - `run_id` (str)  
  - `twin_config_id` (str, FK→TwinConfig)  
  - `controller` (enum: `baseline | optimized`)  
  - `controller_params` (object, optional)  
  - `started_at` (datetime)  
  - `ended_at` (datetime)  
  - `status` (enum: `queued | running | succeeded | failed`)  
  - `notes` (str, optional)
- **Relations:** produces many `SimKpi`; has one `RunSummary`.

### SimKpi (fact table)
- **Composite key:** (`run_id`, `edge_id`, `t_bin_start`)
- **Fields:**  
  - `run_id` (str, FK→SimulationRun)  
  - `edge_id` (str, FK→Edge)  
  - `t_bin_start` (datetime)  
  - `delay_s` (float)  
  - `queue_m` (float)  
  - `speed_kph` (float)  
  - `flow_vph` (float)  
  - `stops_per_km` (float, optional)
- **Storage:** Parquet; partition by `run_id`/date.

### RunSummary
- **PK & FK:** `run_id` (str, FK→SimulationRun)
- **Fields:**  
  - `avg_delay_s` (float)  
  - `p95_travel_time_s` (float)  
  - `max_queue_m` (float)  
  - `top_bottlenecks` (array of `{ edge_id, queue_m }`)

---

## 5) (Optional) Signal Optimization

### SignalConstraints
- **PK:** `constraints_id` (string)
- **Fields:**  
  - `constraints_id` (str)  
  - `scenario_id` (str, FK→Scenario)  
  - `min_green_s`, `max_green_s` (int)  
  - `ped_walk_s`, `ped_flash_s`, `clearance_s` (int)  
  - `cycle_min_s`, `cycle_max_s` (int)  
  - `coordination_groups` (array/object, optional)
- **Purpose:** Hard safety/legal bounds.

### OptimizationResult
- **PK:** `opt_id` (string)
- **Fields:**  
  - `opt_id` (str)  
  - `scenario_id` (str, FK→Scenario)  
  - `plan` (array of `{ node_id, cycle_s, splits{}, offset_s }`)  
  - `expected_kpi_delta` (object: `{ avg_delay_s, max_queue_m, ... }`)  
  - `validated_in_run_id` (str, FK→SimulationRun, optional)  
  - `created_at` (datetime)

---

## 6) Governance (minimal but useful)

### ScenarioVersion
- **PK:** `scenario_version_id` (string)
- **Fields:**  
  - `scenario_version_id` (str)  
  - `scenario_id` (str, FK→Scenario)  
  - `created_at` (datetime)  
  - `author` (str)  
  - `hash` (str)  
  - `comment` (str, optional)

### AuditLog
- **PK:** `event_id` (string)
- **Fields:**  
  - `event_id` (str)  
  - `ts` (datetime)  
  - `actor` (str)  
  - `action` (enum: `create_scenario | apply_edit | run_twin | optimize`)  
  - `target_id` (str)  
  - `payload_digest` (str/object, optional)

---

## Key Relationships (summary)
- `Edge(u,v)` → `Node.node_id`  
- `Scenario.base_network_version` → `NetworkVersion`  
- `Scenario` → many `ScenarioEdit`, `Incident`  
- `Scenario.day_type_id` → `DayType` → `DemandProfile`  
- `TwinConfig` derived from `Scenario`; `SimulationRun` uses `TwinConfig`  
- `SimulationRun` → many `SimKpi`, one `RunSummary`  
- (Optional) `OptimizationResult` for a `Scenario`, validated by `SimulationRun`

---

## Validation Rules (high-level)
- Node lon/lat in bounds; Edge `u != v`; positive `length_m`, `speed_kph`; `lanes ≥ 1`.
- Edits reference existing edges (except adds); geometry valid for `add_edge`.
- Incident durations positive; lane drops cannot exceed existing lanes.
- Every run stores its exact `TwinConfig` (reproducibility).
- Any proposed plan must satisfy `SignalConstraints` *before* simulation.


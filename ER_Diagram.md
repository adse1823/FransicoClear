erDiagram
  %% ========= Core Network =========
  NODE {
    string node_id PK
    float  lon
    float  lat
    string name
  }

  EDGE {
    string edge_id PK
    string u FK  "-> NODE.node_id"
    string v FK  "-> NODE.node_id"
    float  length_m
    int    lanes
    float  speed_kph
    bool   one_way
    string name
  }

  NETWORK_VERSION {
    string network_version_id PK
    string parent_version_id FK "-> NETWORK_VERSION.network_version_id"
    string checksum
    datetime created_at
  }

  %% ========= Scenario & Edits =========
  SCENARIO {
    string  scenario_id PK
    string  name
    string  base_network_version FK "-> NETWORK_VERSION.network_version_id"
    string  day_type_id FK "-> DAY_TYPE.day_type_id"
    string  time_of_day  "HH:MM"
    datetime created_at
  }

  SCENARIO_EDIT {
    string edit_id PK
    string scenario_id FK "-> SCENARIO.scenario_id"
    string type  "add_edge | remove_edge | modify_edge"
    string edge_id FK "-> EDGE.edge_id (nullable for add)"
    json   delta_json  "attrs change for modify"
    geojson geometry   "for add_edge"
    datetime created_at
  }

  INCIDENT {
    string incident_id PK
    string scenario_id FK "-> SCENARIO.scenario_id"
    string edge_id FK "-> EDGE.edge_id"
    datetime start_time
    int      duration_min
    string   severity     "lane_drop | closure"
    int      lanes_lost
  }

  %% ========= Time & Demand =========
  DAY_TYPE {
    string day_type_id PK  "Weekday | Weekend | Event"
    string demand_profile_id FK "-> DEMAND_PROFILE.demand_profile_id"
  }

  DEMAND_PROFILE {
    string demand_profile_id PK
    string level  "global | corridor | link"
    json   targets "corridor_ids or edge_ids when not global"
    json   bins    "[{start,end,multiplier}]"
  }

  %% ========= Twin & Simulation =========
  TWIN_CONFIG {
    string  twin_config_id PK
    string  scenario_id FK "-> SCENARIO.scenario_id"
    string  resolved_network_version FK "-> NETWORK_VERSION.network_version_id"
    string  demand_profile_id FK "-> DEMAND_PROFILE.demand_profile_id"
    string  sim_engine  "e.g., SUMO"
    json    engine_params "{step_length_s,warmup_min,seed}"
  }

  SIMULATION_RUN {
    string  run_id PK
    string  twin_config_id FK "-> TWIN_CONFIG.twin_config_id"
    string  controller  "baseline | optimized"
    json    controller_params
    datetime started_at
    datetime ended_at
    string  status "queued|running|succeeded|failed"
  }

  SIM_KPI {
    string  kpi_id PK
    string  run_id FK "-> SIMULATION_RUN.run_id"
    string  edge_id FK "-> EDGE.edge_id"
    datetime t_bin_start
    float   delay_s
    float   queue_m
    float   speed_kph
    float   flow_vph
    float   stops_per_km
  }

  RUN_SUMMARY {
    string  run_id PK FK "-> SIMULATION_RUN.run_id"
    float   avg_delay_s
    float   p95_travel_time_s
    float   max_queue_m
    json    top_bottlenecks "[{edge_id,queue_m}]"
  }

  %% ========= Optimization (optional, guard-railed) =========
  SIGNAL_CONSTRAINTS {
    string constraints_id PK
    string scenario_id FK "-> SCENARIO.scenario_id"
    int    min_green_s
    int    max_green_s
    int    ped_walk_s
    int    ped_flash_s
    int    clearance_s
    int    cycle_min_s
    int    cycle_max_s
    json   coordination_groups
  }

  OPTIMIZATION_RESULT {
    string opt_id PK
    string scenario_id FK "-> SCENARIO.scenario_id"
    json   plan "per-signal: cycle,splits,offsets"
    json   expected_kpi_delta "{avg_delay_s, max_queue_m}"
    string validated_in_run_id FK "-> SIMULATION_RUN.run_id"
    datetime created_at
  }

  %% ========= Relationships =========
  NODE ||--o{ EDGE : "endpoints (u,v)"
  NETWORK_VERSION ||--o{ SCENARIO : "baseline reference"
  SCENARIO ||--o{ SCENARIO_EDIT : has
  SCENARIO ||--o{ INCIDENT : has
  DAY_TYPE ||--|| DEMAND_PROFILE : "selects profile"
  SCENARIO ||--|| DAY_TYPE : "uses"
  SCENARIO ||--o{ SIGNAL_CONSTRAINTS : "optional"
  SCENARIO ||--o{ TWIN_CONFIG : "derives"
  TWIN_CONFIG ||--o{ SIMULATION_RUN : "executions"
  SIMULATION_RUN ||--o{ SIM_KPI : "produces"
  SIMULATION_RUN ||--|| RUN_SUMMARY : "summarizes"
  EDGE ||--o{ SIM_KPI : "metrics-by-edge"
  SCENARIO ||--o{ OPTIMIZATION_RESULT : "yields"
  SIMULATION_RUN ||--o{ OPTIMIZATION_RESULT : "validated_by (optional)"
  NETWORK_VERSION ||--o{ NETWORK_VERSION : "parent (version lineage)"

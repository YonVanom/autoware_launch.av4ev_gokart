# Autoware Tuning Notes — roboracer_offroad (1/10 scale, pumptrack)

Vehicle: **roboracer_offroad** — wheelbase 0.324 m, max steer 0.4 rad, scale ≈ 1/10.
Track: paved pumptrack circuit, continuous closed loop.

All changes are relative to the upstream `offroad_launch` defaults.
Files are under `src/launcher/autoware_launch/offroad_launch/`.

---

## 1. Velocity & Acceleration Limits

**File:** `config/planning/scenario_planning/common/common.param.yaml`

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `max_vel` | 4.17 m/s | **5.0 m/s** | Raise ceiling from 15 km/h to 18 km/h; actual top speed is limited by curvature |
| `normal.max_acc` | 1.0 m/s² | **1.5 m/s²** | RC car can accelerate harder than a full-size vehicle at this scale |
| `normal.max_jerk` | 1.0 m/s³ | **1.5 m/s³** | Match acceleration budget |
| `limit.max_acc` | 1.0 m/s² | **1.5 m/s²** | Hard cap to match normal budget |
| `limit.max_jerk` | 1.5 m/s³ | **2.0 m/s³** | Allow snappier speed transitions |

---

## 2. Velocity Smoother (Curvature-Based Speed Limiting)

**File:** `config/planning/scenario_planning/common/autoware_velocity_smoother/velocity_smoother.param.yaml`

### Lateral acceleration limits

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `lateral_acceleration_limits` | [2.0, 2.0, 2.0, 2.0] m/s² | **[3.5, 3.5, 3.5, 3.5]** | RC car at scale can sustain ~3.5 m/s² lateral acceleration; default was too conservative and killed corner entry speed |
| `decel_distance_before_curve` | 2.5 m | **1.5 m** | Proportional to wheelbase; full-size 2.5 m is about 7× wheelbase, RC equivalent is ~2.3 m |
| `decel_distance_after_curve` | 2.0 m | **1.0 m** | Same scaling rationale |

### Steering-rate-based speed limits

The default `velocity_thresholds` were all above the car's actual maximum speed, so the steering-rate limiter was never active. The defaults were also tuned for a slow hydraulic steering system (~11 °/s), not an RC servo (~80 °/s at low speed).

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `velocity_thresholds` | [0.1, 0.3, 20.0, 30.0] m/s | **[0.5, 1.0, 3.0, 5.0]** | Rescaled to the RC car's operating speed range (0–18 km/h) |
| `steering_angle_rate_limits` | [11.5, 11.5, 10.5, 3.5] °/s | **[80.0, 70.0, 55.0, 40.0]** | RC servo is roughly 6–8× faster than the hydraulic system the defaults model |

---

## 3. MPC Lateral Controller

**File:** `config/control/trajectory_follower/lateral/mpc.param.yaml`

### Path curvature smoothing window

The smoothing window is defined in index steps (not meters). With `traj_resample_dist: 0.1 m`, a window of 3 gives 0.3 m — appropriate for a 0.324 m wheelbase. The default of 15 gave a 1.5 m window, which over-smoothed corners at RC scale.

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `curvature_smoothing_num_traj` | 15 | **3** | 0.3 m window ≈ 1× wheelbase |
| `curvature_smoothing_num_ref_steer` | 15 | **3** | Same — affects feed-forward steer reference |

### Prediction horizon

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `mpc_prediction_horizon` | 50 steps | **20 steps** | 50 × 0.1 s = 5 s look-ahead is excessive for a 1/10 scale car at <5 m/s; 2 s (20 steps) is appropriate |
| `mpc_min_prediction_length` | 5.0 m | **1.5 m** | Proportional to wheelbase; default 5 m is ~15× wheelbase |

### Cost weights

Default weights were tuned for a full-size vehicle prioritising passenger comfort (low lateral error weight, high steering smoothness weight). For RC racing, tracking accuracy matters more.

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `mpc_weight_lat_error` | 1.0 | **5.0** | Stronger tracking — corrects drift faster |
| `mpc_weight_heading_error` | 0.0 | **0.3** | Small heading correction prevents under-steering on entry |
| `mpc_weight_steering_input` | 1.0 | **0.2** | Less penalty on steer magnitude lets the controller use more of the servo range |
| `mpc_weight_steering_input_squared_vel` | 0.25 | **0.05** | Same |
| `mpc_weight_lat_jerk` | 0.1 | **0.01** | RC car is not comfort-sensitive; allow snappier lateral corrections |
| `mpc_weight_terminal_lat_error` | 1.0 | **5.0** | Terminal constraint keeps the horizon endpoint on track |
| `mpc_low_curvature_thresh_curvature` | 0.0 | **0.02** | Enable the low-curvature parameter set for straights (prevents aggressive steering on straight sections) |

### Vehicle model — actuator dynamics

RC servos are significantly faster than the hydraulic/electric actuators modelled by the defaults.

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `input_delay` | 0.24 s | **0.08 s** | Measured RC servo command-to-response delay |
| `vehicle_model_steer_tau` | 0.27 s | **0.12 s** | RC servo first-order time constant |

### Steering rate limits

Default limits were defined for a full-size vehicle (low speeds 10–20 m/s, low rates 40–60 °/s). Rescaled to RC car operating envelope.

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `steer_rate_lim_dps_list_by_curvature` | [40, 50, 60] °/s | **[60, 80, 120]** | Higher curvature → allow faster steering |
| `steer_rate_lim_dps_list_by_velocity` | [60, 50, 40] °/s | **[120, 90, 60]** | Lower speed → allow faster steering; limits tighten with speed |
| `velocity_list_for_steer_rate_lim` | [10, 15, 20] m/s | **[1.0, 2.5, 5.0]** | Rescaled to RC car max speed of ~5 m/s |

### Noise filter

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `steering_lpf_cutoff_hz` | 3.0 Hz | **10.0 Hz** | Default 3 Hz cut-off was too aggressive for a fast RC servo — it attenuated legitimate fast steering commands |

---

## 4. Behavior Path Planner

**File:** `config/planning/scenario_planning/lane_driving/behavior_planning/behavior_path_planner/behavior_path_planner.param.yaml`

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `input_path_interval` | 2.0 m | **0.5 m** | Higher resolution path from behavior layer; 0.2 m was tested but caused SIGSEGV in goal planner's `fillLaneIdsFromMap` — 0.5 m is the safe minimum |
| `output_path_interval` | 2.0 m | **0.5 m** | Same limit applies |

> **Note:** Do not go below 0.5 m for either parameter. Path points below this density cause a null-pointer dereference inside `GoalPlannerModule::refinePathForGoal` when points fall outside lane boundaries.

---

## 5. Path Optimizer (Motion Planning)

**File:** `config/planning/scenario_planning/lane_driving/motion_planning/autoware_path_optimizer/path_optimizer.param.yaml`

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `mpt.common.output_delta_arc_length` | 0.5 m | **0.1 m** | Higher output resolution for smoother trajectory tracking |
| `mpt.common.delta_arc_length` | 1.0 m | **0.2 m** | Finer optimization grid (100 pts × 0.2 m = 20 m range) for sharper corner representation |
| `mpt.clearance.hard_clearance_from_road` | 0.0 m | **0.1 m** | Small margin from road boundary (note: `hard_constraint: false` so this acts as soft) |
| `mpt.clearance.soft_clearance_from_road` | 0.1 m | **0.2 m** | Encourage path to stay away from lane edges; larger values made corner cutting worse |

---

## 6. Planning Validator

**File:** `config/planning/scenario_planning/common/planning_validator/trajectory_checker.param.yaml`

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `curvature.threshold` | 1.0 /m | **2.0 /m** | RC car max curvature ≈ tan(0.4 rad) / 0.324 m ≈ 1.3 /m; default was too tight and triggered false positives |
| `relative_angle.enable` | true | **false** | The 115° threshold was triggered by a genuine geometric discontinuity at the circuit seam (not a planning error); no threshold value fixes it without hiding real errors elsewhere |
| `trajectory_shift.lat_shift_th` | 0.5 m | **0.2 m** | Tighter lateral shift detection appropriate for a narrower RC car lane |

---

## 7. Localization — Pose Initializer

**File:** `config/localization/pose_initializer.param.yaml`

The default 1.0 m x/y covariance spread the NDT initialisation particles over an area much larger than the RC car's lane width (~0.4 m), causing the scan matcher to lock onto the wrong part of the map.

| Parameter | Default | Current | Reason |
|-----------|---------|---------|--------|
| `gnss_particle_covariance` (x, y diagonal) | 1.0 m² | **0.1 m²** | Tighter GNSS initialisation spread; reduces false-positive NDT convergence |
| `output_pose_covariance` (x, y diagonal) | 1.0 m² | **0.1 m²** | Tighter output covariance passed downstream to NDT |

> **Note:** The `initial_pose_offset_model` parameters in `ndt_scan_matcher.param.yaml` were tested (reducing `ndt/resolution` to 0.2 m and tightening the offset model) but reverted — they degraded scan matching quality. NDT parameters are left at upstream defaults.

---

## 8. Circuit Route Planner (Custom Package)

**Package:** `src/universe/autoware_universe/planning/autoware_circuit_route_planner/`

A custom node that publishes a rolling-window `LaneletRoute` to `/planning/mission_planning/route` for continuous closed-loop circuit driving without a fixed goal. Integrated into `offroad_launch` via the `use_circuit_planner:=true` launch argument.

**File:** `config/circuit_route_planner.param.yaml`

| Parameter | Default | Reason |
|-----------|---------|--------|
| `lookahead_distance_m` | 30.0 m | How far ahead the route window extends. Keep below the circuit perimeter to avoid the window wrapping all the way around |
| `backward_lanelets_num` | 2 | Lanelets behind the car included in the route. Provides overlap so `behavior_path_planner`'s internal `current_route_lanelet_` tracking stays valid across window shifts |

**Launch:**
```bash
ros2 launch offroad_launch e2e_simulator.launch.xml \
  vehicle_model:=roboracer_offroad \
  sensor_model:=roboracer_offroad_isaac_sensor_kit \
  map_path:=$HOME/autoware_map/pumptrack/ \
  launch_vehicle_interface:=true \
  use_circuit_planner:=true
```

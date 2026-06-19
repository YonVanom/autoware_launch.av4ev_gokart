# Autoware Tuning Notes — offroad_launch_minimal (1/10 scale, racing circuit)

Vehicle: **roboracer_offroad** — wheelbase 0.324 m, max steer 0.4 rad, scale ≈ 1/10.
Target: racing on a closed indoor circuit; maximise lap speed via late braking, high cornering velocity, and fast straight-line acceleration.

All parameter changes are relative to the upstream `autoware_launch` defaults (i.e. the files in `src/launcher/autoware_launch/autoware_launch/config/`), except where noted as "relative to offroad_launch". The `offroad_launch` package documents the baseline RC-car adaptation; this file documents the additional racing-specific tuning on top.

All files referenced below live under `src/launcher/autoware_launch/offroad_launch_minimal/`.

---

## 1. Velocity & Acceleration Limits

**File:** `config/planning/scenario_planning/common/common.param.yaml`

This file is loaded by the `autoware_velocity_smoother` (JerkFiltered algorithm) and sets the hard kinematic envelope for all planned trajectories.

| Parameter | autoware_launch default | offroad_launch | **offroad_launch_minimal** | Reason |
|-----------|------------------------|----------------|---------------------------|--------|
| `max_vel` | 4.17 m/s (15 km/h) | 5.0 m/s | **8.0 m/s** | Raise ceiling to allow full-speed straights; the velocity smoother never exceeds this regardless of lane speed limits in the map |
| `normal.max_acc` | 1.0 m/s² | 1.5 m/s² | **3.0 m/s²** | Aggressive acceleration out of corners |
| `normal.min_acc` | -1.0 m/s² | -1.0 m/s² | **-4.0 m/s²** | Hard braking budget for corner entry; the smoother plans deceleration using this limit |
| `normal.max_jerk` | 1.0 m/s³ | 1.5 m/s³ | **5.0 m/s³** | Rapid throttle application on corner exit |
| `normal.min_jerk` | -1.0 m/s³ | -1.0 m/s³ | **-5.0 m/s³** | Sharp brake onset at corner entry |
| `limit.max_acc` | 1.0 m/s² | 1.5 m/s² | **5.0 m/s²** | Hard ceiling matching racing budget |
| `limit.min_acc` | -2.5 m/s² | -2.5 m/s² | **-6.0 m/s²** | Hard braking ceiling (emergency / saturated stop) |
| `limit.max_jerk` | 1.5 m/s³ | 2.0 m/s³ | **8.0 m/s³** | Allow sharp acceleration transitions |
| `limit.min_jerk` | -1.5 m/s³ | -1.5 m/s³ | **-8.0 m/s³** | Allow sharp brake onset |

---

## 2. Velocity Smoother — Curvature-Based Speed Limiting

**File:** `config/planning/scenario_planning/common/autoware_velocity_smoother/velocity_smoother.param.yaml`

This filter computes the maximum safe velocity at each trajectory point from the local curvature: `v_max = sqrt(a_lat_limit × R)`. It also limits the rate at which the car decelerates before a curve.

### Lateral acceleration limits

| Parameter | autoware_launch | offroad_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|----------------|---------------------------|--------|
| `lateral_acceleration_limits` | [1.0, 1.0, 1.0, 1.0] m/s² | [3.5, 3.5, 3.5, 3.5] | **[6.0, 6.0, 6.0, 6.0]** | At 6 m/s² and 2 m radius the car may reach 3.5 m/s (~12 km/h) in a corner; start here and reduce if the car slides |
| `min_curve_velocity` | 2.0 m/s | 2.0 m/s | **1.0 m/s** | Allow the planner to slow to 1 m/s in very tight sections; 2 m/s was preventing the car from braking into hairpins |
| `decel_distance_before_curve` | 3.5 m (autoware_launch) | 1.5 m | **0.8 m** | Later braking is faster; 0.8 m is approximately 2.5× the wheelbase |
| `decel_distance_after_curve` | 2.0 m | 1.0 m | **0.4 m** | Accelerate out of the corner sooner |
| `min_decel_for_lateral_acc_lim_filter` | -2.5 m/s² | -2.5 m/s² | **-4.0 m/s²** | The smoother may apply up to -4 m/s² when slowing for a curve (matches normal.min_acc budget) |

### Steering-rate-based speed limits

These prevent the planner from outputting a trajectory that would require the servo to move faster than it physically can.

| Parameter | autoware_launch | offroad_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|----------------|---------------------------|--------|
| `velocity_thresholds` | [0.1, 0.3, 20.0, 30.0] m/s | [0.5, 1.0, 3.0, 5.0] | **[0.5, 1.0, 4.0, 8.0]** | Table extended to 8 m/s to cover racing speed range |
| `steering_angle_rate_limits` | [11.5, 11.5, 10.5, 3.5] °/s | [80.0, 70.0, 55.0, 40.0] | **[80.0, 70.0, 55.0, 40.0]** | Unchanged from offroad_launch; matches RC servo capability |

### Smoother algorithm (JerkFiltered QP)

**File:** `config/planning/scenario_planning/common/autoware_velocity_smoother/JerkFiltered.param.yaml`

| Parameter | autoware_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|---------------------------|--------|
| `over_a_weight` | 500.0 | **200.0** | Relaxed penalty lets the QP solver reach planned acceleration limits more readily |
| `over_j_weight` | 200.0 | **100.0** | Same — allow snappier jerk profile at corner entry and exit |
| `over_v_weight` | 10000.0 | **10000.0** | Unchanged; never exceed the planned speed |

---

## 3. MPC Lateral Controller

**File:** `config/control/trajectory_follower/lateral/mpc.param.yaml`

This file combines the RC-car baseline tuning from `offroad_launch` with additional racing-specific changes. Refer to `offroad_launch/TUNING_NOTES.md` for the derivation of the RC-specific baseline values (`input_delay`, `vehicle_model_steer_tau`, `curvature_smoothing_num_*`, `steering_lpf_cutoff_hz`, `steer_rate_lim_*`).

### Prediction horizon

| Parameter | upstream default | offroad_launch | **offroad_launch_minimal** | Reason |
|-----------|-----------------|----------------|---------------------------|--------|
| `mpc_prediction_horizon` | 50 steps | **20 steps** | **30 steps** | At the racing target of 6–8 m/s, 20 steps (2 s) provides only 12–16 m of look-ahead. 30 steps (3 s) extends this to 18–24 m, which is sufficient to anticipate braking zones on a compact circuit without over-solving |
| `mpc_prediction_dt` | 0.1 s | 0.1 s | **0.1 s** | Unchanged |
| `mpc_min_prediction_length` | 5.0 m | 1.5 m | **1.5 m** | Unchanged from offroad_launch; proportional to wheelbase |

### Cost weights

The upstream defaults favour passenger comfort (low lateral error weight, high steer-smoothness weight). Racing prioritises tight path tracking over smoothness.

| Parameter | upstream default | offroad_launch | **offroad_launch_minimal** | Reason |
|-----------|-----------------|----------------|---------------------------|--------|
| `mpc_weight_lat_error` | 1.0 | 5.0 | **10.0** | Aggressive correction of lateral deviation keeps the car on the racing line |
| `mpc_weight_heading_error` | 0.0 | 0.3 | **0.5** | Stronger heading correction reduces understeer on corner entry |
| `mpc_weight_heading_error_squared_vel` | 0.0 | 0.3 | **0.5** | Same — scales the correction with speed |
| `mpc_weight_steering_input` | 1.0 | 0.2 | **0.1** | Lower penalty on steer magnitude gives the controller access to more of the servo range |
| `mpc_weight_steering_input_squared_vel` | 0.25 | 0.05 | **0.02** | Same |
| `mpc_weight_lat_jerk` | 0.1 | 0.01 | **0.005** | Further relaxed; allow snappier lateral corrections without comfort penalty |
| `mpc_weight_terminal_lat_error` | 1.0 | 5.0 | **10.0** | Terminal constraint keeps the horizon endpoint on the racing line |
| `mpc_acceleration_limit` | 2.0 m/s² | 2.0 m/s² | **4.0 m/s²** | Internal MPC velocity-shaping limit; raised to match the planned acceleration budget |

### Steering rate limits (velocity-based table)

Extended to cover racing speeds beyond the 5 m/s ceiling of the offroad_launch table.

| Parameter | offroad_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|---------------------------|--------|
| `velocity_list_for_steer_rate_lim` | [1.0, 2.5, 5.0] m/s | **[1.0, 3.0, 6.0, 8.0]** | Table now spans the full racing speed envelope |
| `steer_rate_lim_dps_list_by_velocity` | [120.0, 90.0, 60.0] °/s | **[120.0, 100.0, 70.0, 50.0]** | Limits tighten gracefully at 6 and 8 m/s to prevent steering oscillation at speed |

---

## 4. PID Longitudinal Controller

**File:** `config/control/trajectory_follower/longitudinal/pid.param.yaml`

### Drive-state gains

| Parameter | upstream default | **offroad_launch_minimal** | Reason |
|-----------|-----------------|---------------------------|--------|
| `kp` | 1.0 | **1.5** | Snappier velocity error correction; reduces the lag between planned and actual speed through corners |
| `ki` | 0.1 | **0.2** | Faster steady-state error elimination on long straights |
| `max_i_effort` | 0.3 | **0.4** | Wider integrator authority to match the larger ki |

### Acceleration and jerk limits

These are the controller-side hard clamps on the acceleration command output. They should be at or above the planning-side values so the controller is never artificially limited below what the planner intended.

| Parameter | upstream default | **offroad_launch_minimal** | Reason |
|-----------|-----------------|---------------------------|--------|
| `max_acc` | 3.0 m/s² | **5.0 m/s²** | Controller ceiling matches `limit.max_acc` in common.param.yaml |
| `min_acc` | -5.0 m/s² | **-6.0 m/s²** | Controller floor matches `limit.min_acc`; allows full emergency deceleration budget |
| `max_jerk` | 2.0 m/s³ | **8.0 m/s³** | Matches `limit.max_jerk`; allows sharp throttle on corner exit |
| `min_jerk` | -5.0 m/s³ | **-8.0 m/s³** | Matches `limit.min_jerk`; allows sharp brake onset |

### Smooth-stop deceleration profile

The smooth-stop state is entered as the car approaches a waypoint with target velocity = 0 (e.g. at the end of a mission, or a stop line). More aggressive deceleration keeps stopping distance short.

| Parameter | upstream default | **offroad_launch_minimal** | Reason |
|-----------|-----------------|---------------------------|--------|
| `smooth_stop_max_strong_acc` | -0.5 m/s² | **-1.0 m/s²** | Stronger initial deceleration on stop approach |
| `smooth_stop_min_strong_acc` | -0.8 m/s² | **-1.5 m/s²** | Lower bound for the strong-decel phase |
| `smooth_stop_weak_acc` | -0.3 m/s² | **-0.5 m/s²** | Gentle hold phase; slightly firmer for a shorter crawl-to-stop distance |
| `smooth_stop_weak_stop_acc` | -0.8 m/s² | **-1.5 m/s²** | Deceleration when creeping to the final stop |
| `smooth_stop_strong_stop_acc` | -3.4 m/s² | **-5.0 m/s²** | Emergency halt if the car overshoots the stop point |

---

## 5. Behavior Path Planner — Path Resolution

**File:** `config/planning/scenario_planning/lane_driving/behavior_planning/behavior_path_planner/behavior_path_planner.param.yaml`

Copied from `offroad_launch` (unchanged); included here because `autoware_launch_minimal` would otherwise inherit the coarser `autoware_launch` defaults.

| Parameter | autoware_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|---------------------------|--------|
| `input_path_interval` | 2.0 m | **0.5 m** | Finer path from the behavior layer; 2 m intervals produce choppy trajectories on the tight circuit corners |
| `output_path_interval` | 2.0 m | **0.5 m** | Same |

> **Warning:** Do not go below 0.5 m for either parameter. Path point density below this threshold triggers a null-pointer dereference inside `GoalPlannerModule::refinePathForGoal` when points fall outside the lane boundary polygon. This was discovered in `offroad_launch` testing.

---

## 6. Path Optimizer — Trajectory Resolution

**File:** `config/planning/scenario_planning/lane_driving/motion_planning/autoware_path_optimizer/path_optimizer.param.yaml`

Copied from `offroad_launch` (unchanged); included for the same reason as the BPP config above.

| Parameter | autoware_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|---------------------------|--------|
| `common.output_delta_arc_length` | 0.5 m | **0.1 m** | Higher output resolution allows the controller to react to curvature changes that are smaller than the wheelbase |
| `mpt.common.delta_arc_length` | 1.0 m | **0.2 m** | Finer optimization grid; 100 points × 0.2 m = 20 m planning range with sub-wheelbase resolution |

---

## 7. Planning Validator

**File:** `config/planning/scenario_planning/common/planning_validator/trajectory_checker.param.yaml`

Copied from `offroad_launch` (unchanged).

| Parameter | autoware_launch | **offroad_launch_minimal** | Reason |
|-----------|----------------|---------------------------|--------|
| `curvature.threshold` | 1.0 /m | **2.0 /m** | RC car maximum curvature ≈ tan(0.4 rad) / 0.324 m ≈ 1.3 /m; 1.0 /m triggered false-positive validator failures |
| `relative_angle.enable` | true | **false** | A genuine geometric discontinuity at the circuit loop-closure seam triggered this check; no finite threshold value would distinguish it from real planning errors |
| `trajectory_shift.lat_shift_th` | 0.5 m | **0.2 m** | Tighter threshold appropriate for a car with a 0.255 m wheel tread |

---

## 8. RC-Car Baseline Parameters (inherited from offroad_launch)

These parameters were established in `offroad_launch` for the RC car and are carried into this config unchanged. See `offroad_launch/TUNING_NOTES.md` for full derivation.

### MPC — actuator dynamics

| Parameter | autoware_launch | offroad_launch / offroad_launch_minimal |
|-----------|----------------|----------------------------------------|
| `input_delay` | 0.24 s | **0.08 s** — measured servo command-to-response delay |
| `vehicle_model_steer_tau` | 0.27 s | **0.12 s** — measured servo first-order time constant |
| `steering_lpf_cutoff_hz` | 3.0 Hz | **10.0 Hz** — 3 Hz attenuated legitimate fast steering commands |

### MPC — curvature smoothing window

| Parameter | autoware_launch | offroad_launch / offroad_launch_minimal |
|-----------|----------------|----------------------------------------|
| `curvature_smoothing_num_traj` | 15 | **3** — 15 × 0.1 m = 1.5 m window over-smoothed corners; 3 × 0.1 m ≈ 1× wheelbase |
| `curvature_smoothing_num_ref_steer` | 15 | **3** — same |

### MPC — curvature-based steer rate limits

| Parameter | autoware_launch | offroad_launch / offroad_launch_minimal |
|-----------|----------------|----------------------------------------|
| `steer_rate_lim_dps_list_by_curvature` | [40, 50, 60] °/s | **[60, 80, 120]** — rescaled to RC servo capability |

---

## Tuning Guidance

### If the car slides / understeers in corners
Reduce `lateral_acceleration_limits` in `velocity_smoother.param.yaml` from 6.0 toward 4.0–5.0 m/s². This is the primary lever for corner speed. Changes take effect without rebuilding (symlinked config).

### If the car oscillates laterally on straights
Reduce `mpc_prediction_horizon` from 30 back to 20. At very high speeds a longer horizon can cause the MPC to over-correct for distant curvature.

### If velocity tracking lags noticeably (car underachieves planned speed on straights)
Increase `kp` in `pid.param.yaml` (try 2.0). If integral windup occurs, reduce `max_i_effort`.

### If braking overshoots stop points
Reduce `smooth_stop_strong_stop_acc` toward -3.4 m/s². If the car brakes too late before planned stops, reduce `decel_distance_before_curve` further (already at 0.8 m; minimum practical value depends on latency).

### If the stop-line module causes unwanted stops on circuit
Disable it in `config/planning/preset/minimal_preset.yaml` by setting `launch_stop_line_module: "false"`. The circuit planner does not insert stop lines, but stop-line map elements in the lanelet2 map will still be respected if the module is active.

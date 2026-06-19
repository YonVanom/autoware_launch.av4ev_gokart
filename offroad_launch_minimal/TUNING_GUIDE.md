# Track Tuning Guide — offroad_launch_minimal

This guide answers the question: *"the car is doing X, which parameter do I change?"*

Parameters are grouped by the symptom you observe, not by the file they live in. All files are under `config/` relative to this package. Config files are symlinked, so changes take effect at the next planning cycle without a rebuild or restart unless noted.

---

## Quick Reference

| Symptom | Primary knob | File |
|---------|-------------|------|
| Too slow on straights | `max_vel` | `planning/…/common/common.param.yaml` |
| Too fast / too slow in corners | `lateral_acceleration_limits` | `planning/…/autoware_velocity_smoother/velocity_smoother.param.yaml` |
| Brakes too early before corners | `decel_distance_before_curve` | same |
| Brakes too late before corners | `decel_distance_before_curve` | same |
| Accelerates too slowly out of corners | `normal.max_acc`, `decel_distance_after_curve` | `common.param.yaml`, velocity_smoother |
| Drifts wide on corner exit | `mpc_weight_lat_error` | `control/trajectory_follower/lateral/mpc.param.yaml` |
| Oscillates / weaves on straights | `mpc_prediction_horizon`, `mpc_weight_steering_input` | mpc.param.yaml |
| Velocity lags — car runs slower than planned | `kp` | `control/trajectory_follower/longitudinal/pid.param.yaml` |
| Overshoots stop points | `smooth_stop_strong_stop_acc` | pid.param.yaml |
| Cuts corners (inside of lane) | `mpt.clearance.soft_clearance_from_road` | `planning/…/autoware_path_optimizer/path_optimizer.param.yaml` |
| Path is choppy through corners | `lateral_acceleration_limits` (too high) OR `delta_arc_length` (too coarse) | velocity_smoother OR path_optimizer |

---

## 1. Speed on Straights

The velocity smoother caps all planned speeds at `max_vel`. The car will never plan to go faster than this regardless of map speed limits.

**File:** `config/planning/scenario_planning/common/common.param.yaml`

```
max_vel: 8.0    ← raise to go faster on straights, lower to slow everything down
```

**Also check:** the lanelet2 map speed limits. If the map's `speed_limit` tag is below your `max_vel`, the map wins. Edit the `.osm` file and change `speed_limit` to a value above your target `max_vel` (we use 50 km/h as a ceiling and let config be the real constraint).

**Acceleration rate on straights:**
```
normal.max_acc: 3.0    ← m/s², raise for faster acceleration out of corners
normal.max_jerk: 5.0   ← m/s³, raise to allow sharper throttle onset
```

---

## 2. Corner Speed

Corner speed is determined by: `v_corner = sqrt(lateral_acceleration_limit × R)`

where R is the corner radius in metres. This is the single most important parameter for circuit pace.

**File:** `config/planning/scenario_planning/common/autoware_velocity_smoother/velocity_smoother.param.yaml`

```
lateral_acceleration_limits: [1.5, 1.5, 1.5, 1.5]
```

### Targeting a specific corner speed

| Target speed | Radius 1 m | Radius 1.5 m | Radius 2 m | Radius 3 m |
|-------------|-----------|-------------|-----------|-----------|
| 5 km/h (1.4 m/s) | 1.9 m/s² | 1.3 m/s² | 1.0 m/s² | 0.6 m/s² |
| 6 km/h (1.7 m/s) | 2.8 m/s² | 1.9 m/s² | 1.4 m/s² | 0.9 m/s² |
| 8 km/h (2.2 m/s) | 4.9 m/s² | 3.3 m/s² | 2.4 m/s² | 1.6 m/s² |
| 10 km/h (2.8 m/s) | 7.6 m/s² | 5.1 m/s² | 3.8 m/s² | 2.6 m/s² |
| 15 km/h (4.2 m/s) | — | — | 8.6 m/s² | 5.7 m/s² |

*To use the table: estimate your tightest corner radius from the map, pick your target speed in that corner, read off the required limit.*

**If the car slides in corners:** reduce the limit until the car holds its line cleanly. Start from sliding and work down in 0.5 m/s² steps.

**Minimum corner speed floor** (prevents the planner going below this even in hairpins):
```
min_curve_velocity: 1.0    ← m/s, raise if the car creeps dangerously slowly through tight corners
```

---

## 3. Braking Point (Corner Entry)

These control how far before a curve the velocity smoother begins decelerating.

**File:** `config/planning/scenario_planning/common/autoware_velocity_smoother/velocity_smoother.param.yaml`

```
decel_distance_before_curve: 0.8   ← metres before the corner entry; shorter = later braking
decel_distance_after_curve:  0.4   ← metres past the apex before the smoother allows acceleration
```

**Maximum braking deceleration** the smoother is allowed to apply when slowing for a corner:
```
min_decel_for_lateral_acc_lim_filter: -4.0   ← m/s², more negative = harder braking
```

**If the car brakes too early:** reduce `decel_distance_before_curve` in 0.2 m steps.

**If the car is still going too fast at corner entry** despite early braking: the lateral acceleration limit is too high, not the braking distance. Reduce `lateral_acceleration_limits` instead.

**If the car brakes harshly (jerky deceleration into corners):** make `min_decel_for_lateral_acc_lim_filter` less negative (e.g. -2.5) so the smoother transitions to corner speed more gently.

---

## 4. Acceleration Out of Corners

Two parameters jointly control how quickly the car gets back to full speed after an apex:

**File:** `config/planning/scenario_planning/common/common.param.yaml`
```
normal.max_acc: 3.0    ← m/s², the acceleration budget the velocity smoother plans with
normal.max_jerk: 5.0   ← m/s³, how sharply the acceleration can ramp up
```

**File:** `config/planning/scenario_planning/common/autoware_velocity_smoother/velocity_smoother.param.yaml`
```
decel_distance_after_curve: 0.4   ← shorter = smoother begins acceleration sooner after apex
```

**File:** `config/control/trajectory_follower/longitudinal/pid.param.yaml`
```
kp: 1.5    ← PID proportional gain; raise if the car is slow to reach planned velocity
max_acc: 5.0   ← controller-side acceleration ceiling; keep at or above normal.max_acc
```

---

## 5. Path Tracking — Lateral (Steering)

The MPC trades off lateral tracking accuracy against steering smoothness. More tracking weight means the car tracks the racing line more aggressively but may feel nervous.

**File:** `config/control/trajectory_follower/lateral/mpc.param.yaml`

### Drifting wide on corner exit or entry
```
mpc_weight_lat_error: 10.0        ← raise to snap the car back to the line faster
mpc_weight_terminal_lat_error: 10.0   ← same effect at the far end of the horizon
```

### Oscillating / weaving on straights
```
mpc_prediction_horizon: 30        ← try reducing to 20; longer horizon can cause over-correction at speed
mpc_weight_steering_input: 0.1    ← raise to penalise large steering commands and damp oscillation
mpc_weight_lat_jerk: 0.005        ← raise to smooth out rapid steering reversals
```

### Car understeers (turns too little, goes wide)
```
mpc_weight_heading_error: 0.5     ← raise to penalise heading deviation; corrects the nose earlier
```

### Steering feels sluggish
```
mpc_weight_steering_input: 0.1    ← reduce to allow larger steering commands
mpc_weight_steering_input_squared_vel: 0.02   ← same
```

### Look-ahead distance

The MPC look-ahead window is `horizon × dt` seconds, which at speed translates to `horizon × dt × v` metres.

```
mpc_prediction_horizon: 30    ← steps
mpc_prediction_dt: 0.1        ← seconds per step
```

| Horizon | Look-ahead at 5 m/s | Look-ahead at 8 m/s |
|---------|--------------------|--------------------|
| 20 steps (2 s) | 10 m | 16 m |
| 30 steps (3 s) | 15 m | 24 m |
| 50 steps (5 s) | 25 m | 40 m |

For a compact indoor circuit, 20–30 steps is usually right. Longer horizons improve anticipatory braking on fast, wide circuits but cause oscillation on tight technical circuits.

---

## 6. Path Tracking — Longitudinal (Speed)

**File:** `config/control/trajectory_follower/longitudinal/pid.param.yaml`

### Car consistently runs slower than the planned trajectory
```
kp: 1.5    ← raise (try 2.0); proportional gain drives velocity error to zero faster
ki: 0.2    ← raise slightly if there is a persistent steady-state offset
```

Too-high `kp` causes the velocity to hunt (oscillate around the target). Back off by 0.25 if this occurs.

### Car overshoots stop points
```
smooth_stop_strong_stop_acc: -5.0   ← more negative = harder emergency hold; try -3.4 for gentler stop
```

### Braking is too abrupt when decelerating to a planned waypoint
```
max_jerk: 8.0    ← reduce to 3.0–5.0 to soften the deceleration onset
min_jerk: -8.0   ← reduce magnitude to e.g. -4.0 for a smoother brake-ramp
```

---

## 7. Path Shape — Corner Geometry

These control how the motion planner optimises the physical path through corners, independent of speed.

**File:** `config/planning/scenario_planning/lane_driving/motion_planning/autoware_path_optimizer/path_optimizer.param.yaml`

### Car cuts corners (clips inside of curve)
```
mpt.clearance.soft_clearance_from_road: 0.2   ← raise (e.g. 0.3) to push the path away from road edges
```

### Trajectory looks jagged or choppy
```
mpt.common.delta_arc_length: 0.2          ← reduce (try 0.1) for finer optimisation grid; note: slower solve time
common.output_delta_arc_length: 0.1       ← output resolution; keep at 0.1 m for the controller
```

**File:** `config/planning/scenario_planning/lane_driving/behavior_planning/behavior_path_planner/behavior_path_planner.param.yaml`

```
input_path_interval: 0.5     ← do not go below 0.5 m (causes null-pointer crash in goal planner)
output_path_interval: 0.5    ← same
```

---

## 8. Track-Type Presets

### Tight technical circuit (hairpins, narrow corridors)
```yaml
# velocity_smoother.param.yaml
lateral_acceleration_limits: [1.0, 1.0, 1.0, 1.0]   # slow corners
decel_distance_before_curve: 0.5                       # brake early for tight turns
min_curve_velocity: 1.0

# common.param.yaml
max_vel: 5.0          # straight speed limited by circuit length
normal.max_acc: 2.0   # moderate acceleration

# mpc.param.yaml
mpc_prediction_horizon: 20   # short horizon for compact circuit
mpc_weight_lat_error: 12.0   # tight tracking
```

### Wide fast circuit (sweeping corners, long straights)
```yaml
# velocity_smoother.param.yaml
lateral_acceleration_limits: [4.0, 4.0, 4.0, 4.0]   # fast corners
decel_distance_before_curve: 1.5                       # later braking
min_curve_velocity: 1.5

# common.param.yaml
max_vel: 8.0
normal.max_acc: 3.0

# mpc.param.yaml
mpc_prediction_horizon: 40   # longer horizon to anticipate fast sweepers
mpc_weight_lat_error: 8.0    # slightly relaxed to avoid over-correction at speed
```

### Mixed (tight infield, fast back straight)
Start from the tight preset and increase only `max_vel` and `normal.max_acc`. The lateral acceleration limit will naturally allow faster speeds on the straighter sections since the curvature filter is inactive where the road is straight — the limit only applies where curvature exceeds `curvature_threshold: 0.02 /m`.

---

## 9. Stability Budget

These are the controller-side hard limits. They should always be set **at or above** the planning-side limits so the controller is never artificially capped below what the planner intended. If you raise planning limits, raise these to match.

**File:** `config/control/trajectory_follower/longitudinal/pid.param.yaml`

| Controller limit | Should match or exceed |
|-----------------|----------------------|
| `max_acc: 5.0` | `common.param.yaml → limit.max_acc` |
| `min_acc: -6.0` | `common.param.yaml → limit.min_acc` |
| `max_jerk: 8.0` | `common.param.yaml → limit.max_jerk` |
| `min_jerk: -8.0` | `common.param.yaml → limit.min_jerk` |

**File:** `config/control/trajectory_follower/lateral/mpc.param.yaml`

| Controller limit | Should match planning budget |
|-----------------|------------------------------|
| `mpc_acceleration_limit: 4.0` | `common.param.yaml → normal.max_acc` |
| `acceleration_limit: 4.0` | same |

---

## 10. Workflow

1. **Set the map speed limit** above your target max speed (we use 50 km/h). Let config, not the map, be the constraint.
2. **Set `lateral_acceleration_limits`** to target your desired corner speed using the table in section 2.
3. **Set `max_vel`** to your target straight-line speed.
4. **Run a lap.** Identify the primary problem (too slow, too fast in corners, drifting, oscillating).
5. **Use sections 3–7** to address each symptom one parameter at a time. Restart the stack between changes to `common.param.yaml` or any launch-file-referenced config; velocity_smoother and MPC params reload at runtime.
6. **Iterate.** The lateral acceleration limit is the dominant variable — get that right first before tuning MPC weights.

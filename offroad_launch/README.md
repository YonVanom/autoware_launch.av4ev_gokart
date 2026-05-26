# offroad_launch

This launch package is based on offroad_launch with configuration changes specific for the **RoboRacer Off-Road**. Configuration changes as well as the reasoning are described below.

## Configuration Changes

### Context

These changes are designed for a **RoboRacer Off-Road, a 1/10 scale RC vehicle operating on uneven, hilly terrain**. Due to the vehicle’s small size and LiDAR placement, the sensor has a limited vertical field of view and often fails to capture enough of the ground surface when traversing hill crests, dips, or banked turns. As a result, the system frequently operates on sparse or incomplete point clouds, which negatively impacts scan matching, localization, and downstream modules.

In practice, this led to unstable localization and frequent false-positive instability detections, leading to emergency braking. Additionally, when driving downhill the LiDAR often interprets the ground ahead as an obstacle, triggering unnecessary stopping behavior. The following changes relax strict thresholds and disable modules that are not well-suited for this scale and terrain, improving overall robustness at the cost of reduced conservatism.

---

## Modified Files and Changes

### Localization

#### `offroad_launch/config/localization/localization_error_monitor.param.yaml`
- `error_ellipse_size_lateral_direction`: **0.3 → 1.0**
- `warn_ellipse_size_lateral_direction`: **0.25 → 0.7**

**Reasoning:**  
Increase tolerance to lateral drift caused by reduced feature visibility on uneven terrain.

---

#### `offroad_launch/config/localization/ndt_scan_matcher/ndt_scan_matcher.param.yaml`
- `required_distance`: **10.0 → 1.0**
- `converged_param_nearest_voxel_transformation_likelihood`: **2.3 → 0.5**
- `resolution`: **2.0 → 1.0**

**Reasoning:**  
Allows scan matching to proceed with short-range or sparse LiDAR data and reduces rejection of imperfect (but usable) matches. The finer NDT voxel resolution improves matching quality for the close-range, densely-clustered point clouds produced by the RGB-D camera.

---

#### `offroad_launch/config/localization/ndt_scan_matcher/pointcloud_preprocessor/voxel_grid_filter.param.yaml`
- `voxel_size_x`: **3.0 → 0.3**
- `voxel_size_y`: **3.0 → 0.3**
- `voxel_size_z`: **3.0 → 0.3**

**Reasoning:**  
The point cloud is generated from an RGB-D camera depth image. Points from this sensor are tightly clustered in close-range regions. With a 3.0 m voxel size, most of these closely-spaced points are collapsed into very few voxels, leaving an insufficient number of points for the NDT scan matcher. Reducing to 0.3 m retains enough points to support reliable scan matching.

---

#### `offroad_launch/config/localization/pose_initializer.param.yaml`
- `stop_check_enabled`: **set to false (overridden)**

**Reasoning:**  
Allow (re-)initialization of localization with GNSS, even if the car is moving slightly. (E.g., on a hill).

---

#### `offroad_launch/config/localization/pose_instability_detector.param.yaml`
- `pose_estimator_longitudinal_tolerance`: **0.11 → 0.5**
- `pose_estimator_angular_tolerance`: **0.0175 → 0.1**

**Reasoning:**  
Accounts for pitch changes and pose variation on hills, reducing false instability triggers.

---

### Perception

#### `offroad_launch/config/perception/obstacle_segmentation/ground_segmentation/ground_segmentation.param.yaml`
- `global_slope_max_angle_deg`: **10.0 → 20.0**
- `local_slope_max_angle_deg`: **13.0 → 25.0**

**Reasoning:**  
Improves ground classification on steep slopes and banked terrain.

---

### Planning

#### `offroad_launch/config/planning/mission_planning/mission_planner/mission_planner.param.yaml`
- `reroute_time_threshold`: **10.0 → 1.0**
- `minimum_reroute_length`: **30.0 → 1.0**

**Reasoning:**  
Enables faster rerouting.

---

#### `offroad_launch/config/planning/preset/default_preset.yaml`

The following modules were disabled (set `"true"` → `"false"`):
- obstacle stop  
- obstacle slow down  
- obstacle cruise  
- dynamic obstacle stop  
- out-of-lane  
- obstacle velocity limiter  
- run-out  
- road user stop  

**Reasoning:**  
When driving downhill, the LiDAR frequently detects the ground ahead as an obstacle. This results in false positives that trigger unnecessary stopping or oscillatory behavior. These modules are tuned for full-scale vehicles in structured environments and are not robust to the geometry and sensing limitations of a small RC platform on uneven terrain.

---

## Trade-offs

These changes improve robustness and drivability on uneven terrain by increasing tolerance to noisy or incomplete LiDAR data and by removing modules that misinterpret the environment. However, they also reduce strict safety checks and disable several obstacle handling behaviors, making this configuration unsuitable for full-scale or safety-critical deployments without further validation.

---

## Structure

![offroad_launch](./offroad_launch.drawio.svg)

## Package Dependencies

Please see `<exec_depend>` in `package.xml`.

## Usage

You can use the command as follows at shell script to launch `*.launch.xml` in `launch` directory.

```bash
ros2 launch offroad_launch autoware.launch.xml map_path:=/path/to/map_folder vehicle_model:=lexus sensor_model:=aip_xx1
```

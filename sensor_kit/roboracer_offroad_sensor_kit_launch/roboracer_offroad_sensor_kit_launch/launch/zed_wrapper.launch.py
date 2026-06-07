import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution


def generate_launch_description():
    pkg = get_package_share_directory('roboracer_offroad_sensor_kit_launch')
    override = os.path.join(pkg, 'config', 'zed_wrapper_lifetime.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_model',
            default_value='zedx',
            description='ZED camera model',
        ),
        DeclareLaunchArgument(
            'area_file',
            default_value='/home/nvidia/ros2_ws/src/zed_slam/data/maps/your_map.area',
            description='Path to the .area map file for lifetime/localize mode',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('zed_wrapper'),
                    'launch', 'zed_camera.launch.py',
                )
            ),
            launch_arguments={
                'camera_model': LaunchConfiguration('camera_model'),
                # Absolute namespace so ZED topics stay at /zed/zed_node/...
                # even when this file is included inside the /sensing push-namespace.
                'namespace': '/zed',
                'ros_params_override_path': override,
                'param_overrides': [
                    TextSubstitution(text='pos_tracking.area_file_path:='),
                    LaunchConfiguration('area_file'),
                ],
            }.items(),
        ),
    ])

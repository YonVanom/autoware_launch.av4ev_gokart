import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import ComposableNodeContainer


def generate_launch_description():
    pkg = get_package_share_directory('roboracer_offroad_sensor_kit_launch')
    override = os.path.join(pkg, 'config', 'zed_wrapper_lifetime.yaml')

    # The ZED launch file computes the load target as:
    #   full_container_name = '/' + namespace_val + '/' + container_name_val
    # With namespace='zed' and container_name='zed_container' this gives /zed/zed_container.
    # We pre-create the container here with an absolute namespace so it always lands at
    # /zed/zed_container regardless of any push-namespace active in the calling launch
    # (e.g. Autoware's /sensing push from tier4_sensing_launch).
    zed_container = ComposableNodeContainer(
        name='zed_container',
        namespace='/zed',
        package='rclcpp_components',
        executable='component_container_isolated',
        arguments=['--use_multi_threaded_executor', '--ros-args', '--log-level', 'info'],
        output='screen',
        composable_node_descriptions=[],
    )

    return LaunchDescription([
        zed_container,
        DeclareLaunchArgument(
            'camera_model',
            default_value='zedxm',
            description='ZED camera model',
        ),
        DeclareLaunchArgument(
            'area_file',
            default_value='/home/autoware/autoware_map/hallway/area_map.area',
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
                'namespace': 'zed',
                # Tell the wrapper to use our pre-created container instead of
                # spawning its own — its own container would land at /sensing/zed/
                # under Autoware's push-namespace, not at the /zed/ path it computes.
                'container_name': 'zed_container',
                # The wrapper's inline parameter dict overrides YAML values, so
                # these must be set here rather than in the YAML.
                'publish_tf': 'false',
                'publish_map_tf': 'false',
                'ros_params_override_path': override,
                'param_overrides': [
                    TextSubstitution(text='pos_tracking.area_file_path:='),
                    LaunchConfiguration('area_file'),
                ],
            }.items(),
        ),
    ])

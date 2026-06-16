"""Launch a dummy empty occupancy grid publisher for simulator mode."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="offroad_launch_minimal",
            executable="sim_control_mode_publisher.py",
            name="sim_occupancy_grid_publisher",
            output="log",
        ),
    ])

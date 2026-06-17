"""Launch a dummy empty occupancy grid publisher."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="offroad_launch_minimal",
            executable="occupancy_grid_publisher.py",
            name="occupancy_grid_publisher",
            output="log",
        ),
    ])

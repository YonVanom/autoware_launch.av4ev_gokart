#!/usr/bin/env python3
"""Publish a dummy empty OccupancyGrid.

BehaviorPathPlanner's isDataReady() blocks until /perception/occupancy_grid_map/map
arrives.  In the minimal stack the obstacle segmentation pipeline doesn't produce
an occupancy grid (time-series filter is off), so planning never outputs a trajectory.
An empty grid (all cells -1 = unknown) satisfies the check without adding fake obstacles.
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import Header


class OccupancyGridPublisher(Node):
    def __init__(self):
        super().__init__("occupancy_grid_publisher")
        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._pub = self.create_publisher(
            OccupancyGrid, "/perception/occupancy_grid_map/map", qos
        )
        self._timer = self.create_timer(1.0, self._publish)

    def _publish(self):
        msg = OccupancyGrid()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.info.resolution = 0.5
        msg.info.width = 1
        msg.info.height = 1
        msg.data = [-1]  # unknown — no obstacles
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OccupancyGridPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Drive turtle1 around a square. Run inside the container: python3 /ws/scripts/draw_square.py"""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


class SquareDriver(Node):
    def __init__(self, side=2.0, speed=1.0):
        super().__init__("square_driver")
        self.pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.sub = self.create_subscription(Pose, "/turtle1/pose", self._on_pose, 10)
        self.pose = None
        self.side = side
        self.speed = speed

    def _on_pose(self, msg):
        self.pose = msg

    def _wait_for_pose(self):
        while rclpy.ok() and self.pose is None:
            rclpy.spin_once(self, timeout_sec=0.1)

    def _drive(self, linear, angular, target):
        """Publish a constant twist until the turtle has covered `target`."""
        self._wait_for_pose()
        start = (self.pose.x, self.pose.y, self.pose.theta)
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        while rclpy.ok():
            self.pub.publish(twist)
            rclpy.spin_once(self, timeout_sec=0.02)
            if linear:
                moved = math.hypot(self.pose.x - start[0], self.pose.y - start[1])
            else:
                moved = abs(math.atan2(math.sin(self.pose.theta - start[2]),
                                       math.cos(self.pose.theta - start[2])))
            if moved >= target:
                break
        self.pub.publish(Twist())  # stop

    def draw(self):
        for _ in range(4):
            self._drive(self.speed, 0.0, self.side)
            self._drive(0.0, self.speed, math.pi / 2 - 0.02)


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        node.draw()
    finally:
        node.pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

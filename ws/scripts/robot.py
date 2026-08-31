#!/usr/bin/env python3
"""Closed-loop driving for a differential-drive robot on /cmd_vel + /odom + /scan.

Works against anything exposing the standard mobile-base interface, simulated or
real. Odometry closes the loop on distance and heading; the laser scan is a hard
safety stop, so a bad command cannot drive the robot into a wall.

    python3 /ws/scripts/robot.py status
    python3 /ws/scripts/robot.py forward 1.5
    python3 /ws/scripts/robot.py turn -90
    python3 /ws/scripts/robot.py square 1.0
    python3 /ws/scripts/robot.py wander 60
"""
import argparse
import math
import random
import sys

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan

SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=5,
)

# Stop this far from anything ahead, and treat readings inside this cone as "ahead".
STOP_DISTANCE = 0.35
FRONT_CONE_DEG = 30.0


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


class Robot(Node):
    def __init__(self, cmd_topic="/cmd_vel", odom_topic="/odom", scan_topic="/scan"):
        super().__init__("claude_robot_driver")
        self.msg_type = self._resolve_cmd_type(cmd_topic)
        self.pub = self.create_publisher(self.msg_type, cmd_topic, 10)
        self.create_subscription(Odometry, odom_topic, self._on_odom, 10)
        self.create_subscription(LaserScan, scan_topic, self._on_scan, SENSOR_QOS)
        self.odom = None
        self.scan = None

    def _resolve_cmd_type(self, topic, timeout=5.0):
        """Jazzy moved several bases from Twist to TwistStamped; match whatever is there.

        Discovery has not settled the moment the node comes up, so poll the graph
        briefly rather than reading it once and guessing wrong.
        """
        deadline = self.get_clock().now().nanoseconds + timeout * 1e9
        while rclpy.ok():
            for name, types in self.get_topic_names_and_types():
                if name == topic and types:
                    return TwistStamped if "TwistStamped" in types[0] else Twist
            if self.get_clock().now().nanoseconds > deadline:
                return Twist
            rclpy.spin_once(self, timeout_sec=0.1)
        return Twist

    def _on_odom(self, msg):
        self.odom = msg

    def _on_scan(self, msg):
        self.scan = msg

    # --- state ------------------------------------------------------------
    def wait_ready(self, timeout=15.0):
        deadline = self.get_clock().now().nanoseconds + timeout * 1e9
        while rclpy.ok() and self.odom is None:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.get_clock().now().nanoseconds > deadline:
                raise SystemExit(f"no odometry received in {timeout:.0f}s — is the robot running?")

    @property
    def pose(self):
        p = self.odom.pose.pose
        return p.position.x, p.position.y, yaw_of(p.orientation)

    def front_distance(self):
        """Closest return within the forward cone, or inf when nothing is in range."""
        if self.scan is None:
            return math.inf
        half = math.radians(FRONT_CONE_DEG) / 2.0
        best = math.inf
        for i, r in enumerate(self.scan.ranges):
            if not math.isfinite(r) or r < self.scan.range_min or r > self.scan.range_max:
                continue
            angle = self.scan.angle_min + i * self.scan.angle_increment
            if abs(math.atan2(math.sin(angle), math.cos(angle))) <= half:
                best = min(best, r)
        return best

    def clearest_direction(self, max_abs_deg=150.0, sector_deg=30.0):
        """Bearing (degrees, +ve = left) of the sector with the most room."""
        if self.scan is None:
            return 90.0
        sectors = {}
        for i, r in enumerate(self.scan.ranges):
            if not math.isfinite(r) or r < self.scan.range_min:
                r = self.scan.range_max
            angle = math.degrees(self.scan.angle_min + i * self.scan.angle_increment)
            angle = (angle + 180.0) % 360.0 - 180.0
            if abs(angle) > max_abs_deg:
                continue
            key = round(angle / sector_deg) * sector_deg
            # A sector is only as passable as its worst reading.
            sectors[key] = min(sectors.get(key, math.inf), r)
        if not sectors:
            return 90.0
        # Prefer the roomiest sector, breaking ties toward the smallest turn.
        return max(sectors, key=lambda k: (sectors[k], -abs(k)))

    # --- motion -----------------------------------------------------------
    def _publish(self, linear, angular):
        if self.msg_type is TwistStamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.linear.x = float(linear)
            msg.twist.angular.z = float(angular)
        else:
            msg = Twist()
            msg.linear.x = float(linear)
            msg.angular.z = float(angular)
        self.pub.publish(msg)

    def stop(self):
        for _ in range(5):
            self._publish(0.0, 0.0)
            rclpy.spin_once(self, timeout_sec=0.02)

    def forward(self, distance, speed=0.18):
        """Drive straight, stopping early if the laser sees something too close."""
        self.wait_ready()
        x0, y0, _ = self.pose
        blocked = False
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.02)
            if self.front_distance() < STOP_DISTANCE:
                blocked = True
                break
            x, y, _ = self.pose
            if math.hypot(x - x0, y - y0) >= distance:
                break
            self._publish(speed, 0.0)
        self.stop()
        x, y, _ = self.pose
        return math.hypot(x - x0, y - y0), blocked

    def turn(self, degrees, speed=0.7):
        self.wait_ready()
        _, _, yaw0 = self.pose
        target = math.radians(degrees)
        direction = math.copysign(1.0, target)
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.02)
            _, _, yaw = self.pose
            turned = abs(angle_diff(yaw, yaw0))
            if turned >= abs(target) - 0.02:
                break
            self._publish(0.0, direction * speed)
        self.stop()
        _, _, yaw = self.pose
        return math.degrees(abs(angle_diff(yaw, yaw0)))


def cmd_status(robot, _args):
    robot.wait_ready()
    for _ in range(20):
        rclpy.spin_once(robot, timeout_sec=0.05)
    x, y, yaw = robot.pose
    front = robot.front_distance()
    print(f"pose      x={x:+.3f} m  y={y:+.3f} m  yaw={math.degrees(yaw):+.1f} deg")
    print(f"cmd type  {robot.msg_type.__name__}")
    print(f"front     {front:.3f} m" if math.isfinite(front) else "front     clear")


def cmd_forward(robot, args):
    moved, blocked = robot.forward(args.distance)
    print(f"moved {moved:.3f} m" + ("  (stopped: obstacle ahead)" if blocked else ""))


def cmd_turn(robot, args):
    print(f"turned {robot.turn(args.degrees):.1f} deg")


def cmd_square(robot, args):
    for i in range(4):
        moved, blocked = robot.forward(args.side)
        print(f"side {i + 1}: {moved:.3f} m" + ("  (blocked)" if blocked else ""))
        print(f"corner {i + 1}: {robot.turn(90):.1f} deg")


def cmd_wander(robot, args):
    """Drive forward until something blocks the way, then turn toward open space."""
    robot.wait_ready()
    end = robot.get_clock().now().nanoseconds + args.seconds * 1e9
    stuck = 0
    while rclpy.ok() and robot.get_clock().now().nanoseconds < end:
        moved, blocked = robot.forward(1.0)
        x, y, _ = robot.pose
        print(f"x={x:+.2f} y={y:+.2f}  moved {moved:.2f} m" + ("  blocked" if blocked else ""))
        if not blocked:
            stuck = 0
            continue
        # Repeated no-progress means the clearest sector is a dead end; break the
        # symmetry with a large random turn instead of picking it again.
        stuck = stuck + 1 if moved < 0.05 else 0
        if stuck >= 2:
            bearing = random.choice([-1, 1]) * random.randint(90, 170)
            stuck = 0
        else:
            bearing = robot.clearest_direction()
        print(f"  turning {bearing:+.0f} deg toward open space")
        robot.turn(bearing)
    robot.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cmd-topic", default="/cmd_vel")
    parser.add_argument("--odom-topic", default="/odom")
    parser.add_argument("--scan-topic", default="/scan")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="print pose and nearest obstacle ahead")
    p = sub.add_parser("forward", help="drive straight N metres")
    p.add_argument("distance", type=float)
    p = sub.add_parser("turn", help="rotate N degrees (negative = clockwise)")
    p.add_argument("degrees", type=float)
    p = sub.add_parser("square", help="drive a square with the given side length")
    p.add_argument("side", type=float, nargs="?", default=1.0)
    p = sub.add_parser("wander", help="explore, avoiding obstacles, for N seconds")
    p.add_argument("seconds", type=float, nargs="?", default=60.0)

    args = parser.parse_args()
    handlers = {"status": cmd_status, "forward": cmd_forward, "turn": cmd_turn,
                "square": cmd_square, "wander": cmd_wander}

    rclpy.init()
    robot = Robot(args.cmd_topic, args.odom_topic, args.scan_topic)
    try:
        handlers[args.command](robot, args)
    except KeyboardInterrupt:
        pass
    finally:
        robot.stop()
        robot.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())

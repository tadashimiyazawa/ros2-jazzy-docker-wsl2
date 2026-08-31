import time, rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

rclpy.init()
n = Node("rtf_probe")
qos = QoSProfile(reliability=QoSReliabilityPolicy.BEST_EFFORT,
                 history=QoSHistoryPolicy.KEEP_LAST, depth=5)
samples = []
n.create_subscription(Clock, "/clock",
                      lambda m: samples.append((time.time(), m.clock.sec + m.clock.nanosec * 1e-9)), qos)
t_end = time.time() + 12
while rclpy.ok() and time.time() < t_end:
    rclpy.spin_once(n, timeout_sec=0.1)
if len(samples) < 2:
    print(f"not enough /clock samples ({len(samples)})")
else:
    (w0, s0), (w1, s1) = samples[0], samples[-1]
    print(f"wall {w1-w0:.2f}s  sim {s1-s0:.2f}s  ->  real-time factor {(s1-s0)/(w1-w0):.2f}")
rclpy.shutdown()

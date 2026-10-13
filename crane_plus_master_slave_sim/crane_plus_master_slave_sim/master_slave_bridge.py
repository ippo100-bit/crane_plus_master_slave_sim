# Copyright 2026 ippo100-bit
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Copy the leader arm's joint angles to the follower arm.

Same idea as master_slave_controller in ShotaAk/crane_plus PR #2, with the
safety features a real leader-follower setup needs:

* joint mapping, sign inversion and offset per joint
* follower joint limits
* follower speed limit (no sudden jump when tracking starts)
* enable switch (the follower only tracks while enabled)
* leader timeout (the follower holds still when leader data stops)
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool

from crane_plus_master_slave_sim.mapping import map_targets, step_towards


class MasterSlaveBridge(Node):

    def __init__(self):
        super().__init__('master_slave_bridge')

        self.declare_parameter('leader_joints', [''])
        self.declare_parameter('follower_joints', [''])
        self.declare_parameter('invert', [False])
        self.declare_parameter('offset', [0.0])
        self.declare_parameter('lower_limit', [-math.pi])
        self.declare_parameter('upper_limit', [math.pi])
        self.declare_parameter('max_velocity', 1.5)  # rad/s
        self.declare_parameter('rate', 50.0)  # Hz
        self.declare_parameter('leader_timeout', 0.2)  # s
        self.declare_parameter('enabled', True)

        self.leader_joints = list(self.get_parameter('leader_joints').value)
        self.follower_joints = list(self.get_parameter('follower_joints').value)
        n = len(self.leader_joints)
        self.invert = self._per_joint('invert', n)
        self.offset = self._per_joint('offset', n)
        self.lower = self._per_joint('lower_limit', n)
        self.upper = self._per_joint('upper_limit', n)
        if len(self.follower_joints) != n:
            raise ValueError('leader_joints and follower_joints must have the same length')

        self.max_velocity = float(self.get_parameter('max_velocity').value)
        self.rate = float(self.get_parameter('rate').value)
        self.leader_timeout = float(self.get_parameter('leader_timeout').value)
        self.enabled = bool(self.get_parameter('enabled').value)

        # The follower starts at 0 rad, like a robot that has just powered on.
        self.current = [min(max(0.0, lo), hi) for lo, hi in zip(self.lower, self.upper)]
        self.leader_positions = {}
        self.last_leader_time = None
        self.timed_out = False

        self.pub = self.create_publisher(JointState, 'follower/joint_states', 10)
        self.create_subscription(JointState, 'leader/joint_states', self._on_leader, 10)
        self.create_service(SetBool, '~/enable', self._on_enable)
        self.create_timer(1.0 / self.rate, self._on_timer)

        self.get_logger().info(
            f'Tracking {n} joints: '
            + ', '.join(f'{a} -> {b}' for a, b in zip(self.leader_joints, self.follower_joints)))

    def _per_joint(self, name, n):
        values = list(self.get_parameter(name).value)
        if len(values) == 1 and n > 1:
            values = values * n
        if len(values) != n:
            raise ValueError(f'{name} must have {n} entries')
        return values

    def _on_leader(self, msg):
        for name, pos in zip(msg.name, msg.position):
            self.leader_positions[name] = pos
        self.last_leader_time = self.get_clock().now()

    def _on_enable(self, request, response):
        self.enabled = request.data
        response.success = True
        response.message = 'tracking enabled' if self.enabled else 'tracking disabled'
        self.get_logger().info(response.message)
        return response

    def _leader_fresh(self):
        if self.last_leader_time is None:
            return False
        age = (self.get_clock().now() - self.last_leader_time).nanoseconds * 1e-9
        fresh = age <= self.leader_timeout
        if not fresh and not self.timed_out:
            self.get_logger().warn('Leader data timed out; follower holds its position')
        self.timed_out = not fresh
        return fresh

    def _on_timer(self):
        if self.enabled and self._leader_fresh():
            targets = map_targets(self.leader_positions, self.leader_joints,
                                  self.invert, self.offset)
            if targets is not None:
                self.current = step_towards(self.current, targets, self.lower, self.upper,
                                            self.max_velocity / self.rate)

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.follower_joints
        msg.position = self.current
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MasterSlaveBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

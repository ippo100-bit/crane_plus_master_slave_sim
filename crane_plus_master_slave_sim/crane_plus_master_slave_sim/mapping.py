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

"""Pure functions that turn leader angles into follower angles (no ROS needed)."""


def map_targets(leader_positions, leader_joints, invert, offsets):
    """Turn leader angles into follower targets (None if a leader joint is missing)."""
    targets = []
    for name, inv, off in zip(leader_joints, invert, offsets):
        if name not in leader_positions:
            return None
        value = leader_positions[name]
        targets.append((-value if inv else value) + off)
    return targets


def step_towards(current, targets, lower, upper, max_step):
    """Move each joint towards its clamped target by at most max_step."""
    out = []
    for cur, tgt, lo, hi in zip(current, targets, lower, upper):
        tgt = min(max(tgt, lo), hi)
        delta = max(-max_step, min(max_step, tgt - cur))
        out.append(cur + delta)
    return out

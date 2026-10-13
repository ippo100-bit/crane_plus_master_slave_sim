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

"""Two CRANE+ V2 arms in RViz: move the leader with sliders, the follower copies it."""

import os

from ament_index_python.packages import get_package_share_directory
from crane_plus_description.robot_description_loader import RobotDescriptionLoader
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def arm_nodes(name, y):
    description = ParameterValue(RobotDescriptionLoader().load(), value_type=str)
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=name,
        output='both',
        parameters=[{'robot_description': description, 'frame_prefix': name + '/'}],
    )
    place = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name=name + '_placement',
        arguments=['--x', '0', '--y', str(y), '--z', '0',
                   '--frame-id', 'world', '--child-frame-id', name + '/world'],
    )
    return [rsp, place]


def generate_launch_description():
    share = get_package_share_directory('crane_plus_master_slave_sim')

    declare_config = DeclareLaunchArgument(
        'config',
        default_value=os.path.join(share, 'config', 'master_slave.yaml'),
        description='Bridge parameter file (joint mapping, inversion, limits).')
    declare_leader_gui = DeclareLaunchArgument(
        'leader_gui',
        default_value='true',
        description='Move the leader with sliders. Set false when another node '
                    '(e.g. the mini arm Pico reader) publishes /leader/joint_states.')
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true', description='Start RViz.')

    leader_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        namespace='leader',
        output='screen',
        condition=IfCondition(LaunchConfiguration('leader_gui')),
    )

    bridge = Node(
        package='crane_plus_master_slave_sim',
        executable='master_slave_bridge',
        name='master_slave_bridge',
        output='screen',
        parameters=[LaunchConfiguration('config')],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', os.path.join(share, 'rviz', 'master_slave.rviz')],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription(
        [declare_config, declare_leader_gui, declare_rviz]
        + arm_nodes('leader', 0.2)
        + arm_nodes('follower', -0.2)
        + [leader_gui, bridge, rviz]
    )

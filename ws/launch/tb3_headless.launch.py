#!/usr/bin/env python3
"""TurtleBot3 in Gazebo with no Gazebo GUI.

turtlebot3_gazebo's own launch files always start `gz sim -g` alongside the
server, and killing that client tears the whole launch down (on_exit_shutdown).
This is the same launch minus the client, so the simulation runs as a pure
server and RViz2 does the visualising:

    ros2 launch /ws/launch/tb3_headless.launch.py
    ros2 launch /ws/launch/tb3_headless.launch.py world:=empty_world.world
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    tb3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    launch_file_dir = os.path.join(tb3_gazebo, 'launch')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    use_sim_time = LaunchConfiguration('use_sim_time')
    world = LaunchConfiguration('world')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')

    world_path = PathJoinSubstitution([tb3_gazebo, 'worlds', world])

    # -s is server-only: no gz client, so nothing needs the GPU.
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': ['-r -s -v2 ', world_path],
                          'on_exit_shutdown': 'true'}.items()
    )

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    spawn_turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={'x_pose': x_pose, 'y_pose': y_pose}.items()
    )

    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.path.join(tb3_gazebo, 'models'))

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='turtlebot3_world.world',
                              description='World file under turtlebot3_gazebo/worlds'),
        DeclareLaunchArgument('model', default_value='burger',
                              description='burger or waffle'),
        # turtlebot3_gazebo's included launch files read this from the environment
        # and fail outright when it is unset, so set it here rather than relying
        # on the caller having exported it.
        SetEnvironmentVariable('TURTLEBOT3_MODEL', LaunchConfiguration('model')),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x_pose', default_value='-2.0'),
        DeclareLaunchArgument('y_pose', default_value='-0.5'),
        set_env_vars_resources,
        gzserver_cmd,
        spawn_turtlebot_cmd,
        robot_state_publisher_cmd,
    ])

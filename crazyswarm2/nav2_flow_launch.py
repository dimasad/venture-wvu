import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

MAP = os.path.expanduser('~/ros2_ws/map.yaml')
PARAMS = os.path.expanduser('~/ros2_ws/nav2_params.yaml')
CRAZYFLIES = os.path.expanduser('~/ros2_ws/crazyflies.yaml')

# ===================================================================
#  WHERE YOU PUT THE DRONE ON THE MAP  (metres, map coordinates)
#  Must be FREE SPACE - not inside an obstacle, not on a wall.
#  Arena 3.0 x 6.0.
# ===================================================================
START_X = '0.75'
START_Y = '0.75'
START_YAW = '0.0'      # drone must point along +X
# ===================================================================

def generate_launch_description():
    nav2 = get_package_share_directory('nav2_bringup')

    return LaunchDescription([

        # 1. Crazyflie server. With the Flow deck it publishes: cf1/odom -> cf1
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('crazyflie'),
                             'launch', 'launch.py')),
            launch_arguments={'crazyflies_yaml_file': CRAZYFLIES,
                              'backend': 'cflib',
                              'gui': 'false',
                              'teleop': 'false',
                              'mocap': 'false'}.items()),

        # 2. Static transform  map -> cf1/odom

	Node(package='tf2_ros', executable='static_transform_publisher',
		     name='map_to_odom',
		     arguments=[START_X, START_Y, '0',
		                START_YAW, '0', '0',
		                'map', 'world'],          # <-- 'world', not 'cf1/odom'
		     output='screen'),
        # 3. Velocity mux. Takes off on the first /cmd_vel message.
        Node(package='crazyflie_examples', executable='vel_mux',
             name='vel_mux', output='screen',
             parameters=[{'hover_height': 0.5},
                         {'incoming_twist_topic': '/cmd_vel'},
                         {'robot_prefix': '/cf1'}]),

        # 4. Map server
        Node(package='nav2_map_server', executable='map_server',
             name='map_server', output='screen',
             parameters=[{'yaml_filename': MAP},
                         {'use_sim_time': False}]),

        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_map', output='screen',
             parameters=[{'use_sim_time': False},
                         {'autostart': True},
                         {'node_names': ['map_server']}]),

        # 5. Nav2 navigation only. No AMCL.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2, 'launch', 'navigation_launch.py')),
            launch_arguments={'params_file': PARAMS,
                              'use_sim_time': 'False'}.items()),

        # 6. RViz
        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', os.path.join(nav2, 'rviz',
                                           'nav2_default_view.rviz')],
             output='screen'),
    ])

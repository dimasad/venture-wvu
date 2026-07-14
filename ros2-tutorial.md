---
title: ROS 2 Programming Basics and TurtleBot3 Navigation
---

# ROS 2 Programming Basics and TurtleBot3 Navigation

## 1. Overview and Objective

This morning's lecture covered the concepts every ROS 2 system is built from: nodes, messages, topics, services, actions, parameters, TF2, launch, packages, workspaces, and distributions. This activity is where you use those concepts to build something yourself.

You will create a ROS 2 workspace and package from scratch, write a publisher node and a subscriber node in Python, start both with a single launch file, and then move to a full simulated robot: a TurtleBot3 running Nav2. You will localize it, drive it by hand, send it autonomous navigation goals, and finally build a map of an unknown environment with SLAM and save it to disk.

Work through the sections in order. Each one builds on the previous.

By the end of this activity, you will be able to:

1. Create and build a ROS 2 workspace and an `ament_python` package.
2. Write, build, and run a Python node that publishes to a topic.
3. Write, build, and run a Python node that subscribes to a topic.
4. Start multiple nodes at once with a Python launch file.
5. Bring up a simulated TurtleBot3 with Nav2, localize it, and send it navigation goals.
6. Build a map of an unknown environment with SLAM and save it to disk.

## 2. Before You Start

Open a terminal in your WSL2 Ubuntu 24.04 environment and confirm ROS 2 is sourced and healthy:

```bash
printenv ROS_DISTRO        # should print: jazzy
ros2 doctor                # checks your install for common problems
```

If `ROS_DISTRO` is empty, source it and check that it is in your `~/.bashrc` (see step 6 of the install guide):

```bash
source /opt/ros/jazzy/setup.bash
```

Do not move on until both commands run cleanly.

## 3. Create a Workspace

A workspace is a directory containing ROS 2 packages, built with `colcon` and sourced on top of your `/opt/ros/jazzy` underlay. You will reuse this same workspace for the rest of the program, so create it somewhere you will remember.

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
```

The workspace is still empty, so this build has nothing to compile, but it creates `build/`, `install/`, and `log/` directories and confirms `colcon` works. Source the new overlay:

```bash
source ~/ros2_ws/install/setup.bash
```

Check that your overlay is now ahead of the underlay on the package search path:

```bash
echo $AMENT_PREFIX_PATH | tr ':' '\n'
```

You should see `~/ros2_ws/install` listed before `/opt/ros/jazzy`. You will need to re-run the `source` command above (or add it to `~/.bashrc`, after the line that sources `/opt/ros/jazzy/setup.bash`) in every new terminal for the rest of this activity.

## 4. Create a Package

Packages are the basic unit you build and share code in. Create an `ament_python` package, the type used for Python-only nodes:

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python --dependencies rclpy std_msgs --license Apache-2.0 ros2_tutorial
```

This generates a `ros2_ws/src/ros2_tutorial/` directory with a `package.xml`, `setup.py`, `setup.cfg`, a `resource/` marker file, and a `ros2_tutorial/` module directory where your node code will live. The `--dependencies` flag already added `rclpy` and `std_msgs` as declared dependencies in `package.xml`.

Build it and confirm it shows up as an installed package:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep ros2_tutorial
```

`--symlink-install` links your Python source files into the install directory instead of copying them, so edits to your `.py` files take effect immediately, without rebuilding. You still need to rebuild whenever you add a new file or change `setup.py`, such as when you add an entry point in the next section.

## 5. Publisher Node: Talker

You will write the same kind of node you ran during the install verification (`demo_nodes_cpp/talker`), except this time you write it yourself.

Create `~/ros2_ws/src/ros2_tutorial/ros2_tutorial/talker.py`:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Talker(Node):

    def __init__(self):
        super().__init__('talker')
        self.publisher_ = self.create_publisher(String, 'chatter', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)
        self.count = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello, world! {self.count}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count += 1


def main(args=None):
    rclpy.init(args=args)
    node = Talker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

`create_publisher(String, 'chatter', 10)` declares a publisher on the `chatter` topic carrying `std_msgs/msg/String` messages, with a queue depth of 10. `create_timer(0.5, self.timer_callback)` calls `timer_callback` every 0.5 seconds, which is where the message actually gets published.

Register `talker` as a runnable executable. Open `setup.py` and add a line inside `entry_points` / `console_scripts`:

```python
entry_points={
    'console_scripts': [
        'talker = ros2_tutorial.talker:main',
    ],
},
```

Build and run it:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 run ros2_tutorial talker
```

You should see `Publishing: "Hello, world! 0"` and so on, twice a second. Leave it running, open a second terminal, source both the underlay and the overlay, and confirm the messages are really going out over the topic:

```bash
ros2 topic echo /chatter
```

Do not move on until `ros2 topic echo /chatter` shows live messages from your `talker` node. Stop both with Ctrl+C when you are done.

## 6. Subscriber Node: Listener

Now write the other half. Create `~/ros2_ws/src/ros2_tutorial/ros2_tutorial/listener.py`:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Listener(Node):

    def __init__(self):
        super().__init__('listener')
        self.subscription = self.create_subscription(
            String, 'chatter', self.listener_callback, 10)

    def listener_callback(self, msg):
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = Listener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Add its entry point in `setup.py` next to `talker`:

```python
entry_points={
    'console_scripts': [
        'talker = ros2_tutorial.talker:main',
        'listener = ros2_tutorial.listener:main',
    ],
},
```

Build and run it, without starting `talker` this time:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 run ros2_tutorial listener
```

In a second terminal, publish a single message from the CLI, the same way you drove the turtle this morning:

```bash
ros2 topic pub --once /chatter std_msgs/msg/String "{data: 'Hello from the CLI'}"
```

Your `listener` terminal should print `I heard: "Hello from the CLI"`. Do not move on until this works. Stop the listener with Ctrl+C.

## 7. Launch Both Nodes Together

Real ROS 2 systems have many nodes running at once. A launch file starts them all with a single command. Create `~/ros2_ws/src/ros2_tutorial/launch/talker_listener_launch.py`:

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros2_tutorial',
            executable='talker',
        ),
        Node(
            package='ros2_tutorial',
            executable='listener',
        ),
    ])
```

Run it directly by file path, no rebuild needed since this file is not installed anywhere:

```bash
ros2 launch ~/ros2_ws/src/ros2_tutorial/launch/talker_listener_launch.py
```

You should see both nodes' log output interleaved in the same terminal: `talker` publishing and `listener` receiving, from a single command. Stop both with Ctrl+C.

## 8. TurtleBot3 Navigation with Nav2 (Simulation)

The rest of this activity moves from your own nodes to a full simulated robot. Nav2 is the ROS 2 navigation stack: given a map and a goal pose, it localizes the robot, plans a path, and drives it there while avoiding obstacles, using the actions and costmaps introduced this morning.

### 8.1 Install Nav2 and the TurtleBot3 simulation

```bash
sudo apt install ros-$ROS_DISTRO-navigation2 ros-$ROS_DISTRO-nav2-bringup
sudo apt install ros-$ROS_DISTRO-nav2-minimal-tb*
```

The second command installs the minimal TurtleBot3 description and simulation packages that Nav2's getting-started example uses. Jazzy uses the modern Gazebo simulator, so you do not need to set a `TURTLEBOT3_MODEL` environment variable or install `turtlebot3-gazebo`; those are only needed on older distributions with Gazebo Classic.

### 8.2 Launch the TurtleBot3 simulation with Nav2

```bash
ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False
```

`headless` defaults to true, which skips the 3D Gazebo window; `headless:=False` keeps it visible so you can watch the robot move. This single launch file starts the AMCL localizer, the map server with a built-in sandbox map, the robot state publisher, a Gazebo instance running the TurtleBot3, and RViz2, all at once, the same way `talker_listener_launch.py` started two nodes for you a moment ago, just with many more.

Give it a minute; Gazebo and RViz2 both take a while to open the first time. If Nav2 does not activate automatically, click the Startup button in the bottom left corner of the RViz2 window.

Do not move on until you see both the Gazebo window, with the robot in a simulated environment, and the RViz2 window, with a gray occupancy grid map.

### 8.3 Give an initial pose estimate

Nav2 starts with no idea where the robot actually is on the map; you have to tell it. Compare the robot's pose in the Gazebo window to its position on the map in RViz2, then in RViz2:

1. Click the "2D Pose Estimate" button in the toolbar.
2. Click and hold on the map at the robot's approximate location, then drag in the direction the robot is facing, and release.

A cloud of small arrows (the AMCL particle filter) should appear around that point. It does not need to be exact; Nav2 refines the estimate as the robot moves. If it looks badly wrong, click "2D Pose Estimate" and try again.

### 8.4 Drive with keyboard teleop

Before handing control to Nav2, drive the robot yourself and watch the particle cloud track it. Install a generic keyboard teleop tool, the same idea as `turtle_teleop_key` from this morning, but for a `Twist` on `/cmd_vel` instead of turtlesim:

```bash
sudo apt install ros-$ROS_DISTRO-teleop-twist-keyboard
```

In a new terminal (source both underlay and overlay):

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Follow the on-screen key legend (`i` forward, `,` backward, `j`/`l` to turn, `k` to stop) to drive the robot around. Watch the RViz2 window: the particle cloud should tighten around the robot as it moves and AMCL narrows down its estimate. Stop with Ctrl+C when you are satisfied Nav2 knows where the robot is.

### 8.5 Send Nav2 goals and monitor execution

With the pose estimate set, click "Navigation2 Goal" in the RViz2 toolbar, then click and drag on the map to choose a target position and orientation. Watch RViz2: a planned path appears, local and global costmaps update, and the robot drives itself to the goal in both RViz2 and Gazebo.

This goal is sent the same way `rotate_absolute` was this morning: as an action, with feedback while it runs and a result at the end. You can send the same goal from the CLI instead of clicking in RViz2:

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}" \
  --feedback
```

Try sending a few goals to different points on the map, including ones that require the robot to navigate around obstacles. Watch it plan, replan, and recover on its own.

### 8.6 Build a map with SLAM instead of a fixed map

So far the robot has been localizing itself against a map that was already given to it. Now do the opposite: start with no map at all, and build one. Stop the simulation from section 8.2 with Ctrl+C in its terminal, then launch it again with SLAM enabled instead of AMCL and the fixed map:

```bash
ros2 launch nav2_bringup tb3_simulation_launch.py slam:=True headless:=False
```

This runs SLAM Toolbox in place of AMCL and the map server. There is no pre-built map this time, so you will not see the sandbox occupancy grid at startup, and there is no initial pose to set; SLAM builds the map and tracks the robot's pose in it from scratch as it moves.

### 8.7 Drive around to build the map

Start keyboard teleop again the same way as in section 8.4:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Drive the robot slowly through the environment, covering as much open space as you can and revisiting a few areas from different directions. Watch RViz2: the occupancy grid fills in live as the robot's lidar sees more of the world. Keep driving until the map covers the whole environment with clean, closed walls, then stop with Ctrl+C.

### 8.8 Save the map using the CLI

The map SLAM Toolbox is building only exists in memory until you save it to disk. Do that with a single CLI command, in a new terminal:

```bash
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "{name: {data: '~/my_map'}}"
```

This calls a service on the running map server, the same request/response pattern behind `/clear` and `/spawn` this morning. It writes `~/my_map.yaml` and `~/my_map.pgm`. Check that both files exist:

```bash
ls -l ~/my_map.yaml ~/my_map.pgm
```

This is the same kind of map file that `tb3_simulation_launch.py` loaded for you back in section 8.2, except now you built it yourself. You could pass it back in with `map:=~/my_map.yaml` on a future run of the simulation without SLAM.

## 9. If You Finish Early

- Add a third node to `ros2_tutorial` that subscribes to `chatter` and republishes a modified version of the message on a new topic. Confirm the chain with `ros2 topic echo`.
- Turn the publish rate in `talker.py` into a declared ROS 2 parameter instead of a hardcoded `0.5`, and change it at runtime with `ros2 param set` while the node is running.
- Send a Nav2 goal through the `NavigateToPose` action from a Python script using `rclpy`, instead of the CLI or RViz2, and print the feedback messages as they arrive.
- Run `ros2 run tf2_tools view_frames` while the TurtleBot3 simulation is running and compare its frame tree to the turtlesim one from this morning.
- Load the map you saved in section 8.8 back into a fresh, non-SLAM run of `tb3_simulation_launch.py` with `map:=~/my_map.yaml` and confirm the robot localizes and navigates against it.

---
title: Flying Crazyflies with ROS 2
---

# Flying Crazyflies with ROS 2: Waypoint Navigation with Obstacle Avoidance

# Nav2 Autonomous Navigation with the Crazyflie + Flow Deck

Navigate a Crazyflie around obstacles using **Nav2:** ROS 2's professional navigation stack.

---

## 1. Goal and concept

**Goal:** click a point in RViz (or send it from Python), and the drone plans a path around obstacles and flies there autonomously.

**How the drone "knows" about obstacles:**

The drone has **no obstacle sensors**. Obstacles exist in a **static map file** you load into Nav2. The tapes on the floor arena illustrate the obstacles.

**How the drone knows where it is:**

The **Flow deck** (downward optical-flow camera + laser rangefinder) gives a **relative** position estimate. Wherever you place the drone and power it on becomes its origin `(0, 0)`.

So you must **tell Nav2 where that starting point is on the map**. That is done with a static transform in the launch file

Your local pose gets transformed into a global (map) pose using the start position you supply manually.

What do you need?

| Component | Job |
| --- | --- |
| **Flow deck** | Where is the drone? (relative pose → `world → cf1` TF) |
| **Static transform** | Where did the drone start on the map? (`map → world`) |
| **Static map** | Where are the obstacles? |
| **Nav2 planner** | Compute a path from A to B avoiding obstacles |
| **Nav2 controller** | Turn that path into velocity commands |
| **vel_mux** | Take off, then convert `Twist` → drone motion |

---

## 2. Requirements

On Windows, we must share the USB device with the WSL2 Linux subsystem. 
On a PowerShell running as administrator, run

```
winget install dorssel.usbipd-win
usbipd list
```

Find the BUSID associated with the CrazyRadio, for example 1-5. 
Use this as <BUSID> in the command below to attach it to WSL.

```
usbipd bind --busid=<BUSID>
usbipd attach --wsl --busid=<BUSID>
```

Next, on Linux, install Nav2 and Crazyswarm2:

```bash
sudo apt install -y ros-humble-navigation2 ros-humble-nav2-bringup
sudo apt install -y ros-humble-teleop-twist-keyboard
sudo apt install -y ros-humble-crazyflie*
sudo apt install -y python3-pip3
sudo pip3 install --ignore-installed cflib rowan transforms3d
```

Then run the following command to enable your Linux user to use the crazyflie usb devices.

```bash
sudo adduser $USER plugdev
cat <<EOF | sudo tee /etc/udev/rules.d/99-bitcraze.rules > /dev/null
# Crazyradio (normal operation)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="7777", MODE="0664", GROUP="plugdev"
# Bootloader
SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="0101", MODE="0664", GROUP="plugdev"
# Crazyflie (over USB)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0664", GROUP="plugdev"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## 3. Config file

Save the file below as [`~/ros2_ws/crazyflies.yaml`](crazyswarm2/crazyflies.yaml), changing the `uri` line.

```yaml
{% include_relative crazyswarm2/crazyflies.yaml %}
```

We do `pose` and `odom` logging to give Nav2 the TF it needs to localize the drone.

---

## 4. Map files

Put the files [`map.pgm`](crazyswarm2/map.pgm), 
[`map.yaml`](crazyswarm2/map.yaml), and 
[`nav2_params.yaml`](crazyswarm2/nav2_params.yaml) in the folder 
`~/ros2_ws/`.

The file `map.pgm` is an image where each pixel value determines if a cell is occupied or free, while `map.yaml` has the map geometry and metadata, as shown belo. The `origin` is the real-world coordinate of the image's bottom-left pixel:

```yaml
{% include_relative crazyswarm2/map.yaml %}
```

---

## 5. Launch file

Create [`~/ros2_ws/nav2_flow_launch.py`](crazyswarm2/nav2_flow_launch.py):

```python
{% include_relative crazyswarm2/nav2_flow_launch.py %}
```

---

## 6. Part 0: Fly with teleop

Before using Nav2, confirm the drone flies under manual control. This verifies the radio link, `vel_mux`, and `/cmd_vel` all work.

**Pre-flight:** **close cfclient** → fresh battery → drone placed at `(START_X, START_Y)` pointing +X → Crazyradio plugged in.

**Terminal 1 — launch:**

```bash
ros2 launch ~/ros2_ws/nav2_flow_launch.py
```

**Terminal 2 — teleop:**

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Steps:**

1. Press `t` — the drone takes off and hovers at 0.5 m.
2. Press `i`, `,`, `j`, `l` — it should move in each direction.
3. Press `b` — it lands.

If this works, the flight chain is good. Move on to Nav2.

## 6. Part 1: Fly it from RViz

**Pre-flight:** **close cfclient** → fresh battery → drone placed at `(START_X, START_Y)` pointing +X → Crazyradio in.

```bash
ros2 launch nav2_flow_launch.py
```

Verify before clicking anything:

```bash
ros2 run tf2_ros tf2_echo map cf1     # drone should appear at your start position
ros2 lifecycle get /bt_navigator      # must say: active
```

In RViz:

1. Confirm the **map** appears and the drone is at the right spot on it.
2. Click **"Nav2 Goal"** and click a free spot on the map.
3. Nav2 plans a path (you'll see the line), and the drone flies it, **around** the obstacles.

> Skip **"2D Pose Estimate"** — it publishes to AMCL, which we do not run. The drone's start position comes from the static transform in the launch file.
> 

**Check it works:** put the goal on the far side of a taped obstacle. The planned path should curve around it, not through it.

**Landing:** Nav2 does not land. Use teleop and press `b`.

---

## 7. Part 2: Send goals from Python

RViz is for sending goals interactivelly. In autonomous missions, we need to send the goals programatically.

Save as `~/ros2_ws/nav_mission.py`:

```python
#!/usr/bin/env python3
"""
nav_mission.py — Fly to a waypoint with Nav2, then land.
"""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Twist

WAYPOINTS = [
    (0.5, 4.0),
]

class NavMission(Node):
    def __init__(self):
        super().__init__('nav_mission')
        self.client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.index = 0
        self.done = False

    def make_goal(self, x, y):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(x)
        goal.pose.pose.position.y = float(y)
        goal.pose.pose.orientation.w = 1.0
        return goal

    def send_next(self):
        if self.index >= len(WAYPOINTS):
            self.get_logger().info('Mission complete. Landing...')
            self.land()
            return
        x, y = WAYPOINTS[self.index]
        self.get_logger().info(f'Going to waypoint {self.index + 1}: ({x},{y})')
        self.client.wait_for_server()
        future = self.client.send_goal_async(self.make_goal(x, y))
        future.add_done_callback(self.on_accepted)

    def on_accepted(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal rejected!')
            self.done = True
            return
        handle.get_result_async().add_done_callback(self.on_arrived)

    def on_arrived(self, future):
        self.get_logger().info(f'Reached waypoint {self.index + 1}')
        self.index += 1
        self.send_next()

    def land(self):
        """vel_mux lands when it receives a Twist with negative linear.z."""
        cmd = Twist()
        cmd.linear.z = -1.0        # <<< negative z triggers landing
        for _ in range(5):
            self.cmd_pub.publish(cmd)
            time.sleep(0.1)
        self.get_logger().info('Land command sent.')
        self.done = True

def main():
    rclpy.init()
    node = NavMission()
    node.send_next()

    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.1)

    time.sleep(4)          # let it descend
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

In a new terminal Ros2 source and run it **while the Nav2 launch is still up**.

```bash
python3 ~/ros2_ws/nav_mission.py
```

**What just happened:** you sent a goal to Nav2's `navigate_to_pose` action. Nav2 planned the path, avoided the mapped obstacles, and drove the drone there.

---

## 8. Your tasks

### Task 1: Multi-waypoint patrol

Add waypoints to `WAYPOINTS` so the drone visits 4 points in sequence. Place them so at least two legs must route around a taped obstacle.

### Task 2: Complete the missing pieces

The script below is **incomplete**. Copy and paste in a python file (Save as `~/ros2_ws/nav_mission.py`) Fill in the `TODO's` .

```python
"""
nav_mission.py: Fly a patrol route, report progress, handle failures, land.
"""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Twist

WAYPOINTS = [
#############################################################
# TODO 1: Define a sequence of four waypoints.

#############################################################
]

LOOP_FOREVER = False    # TODO 4 (DONE): set True to repeat the patrol

class Patrol(Node):
    def __init__(self):
        super().__init__('patrol')
        self.client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.index = 0
        self.done = False

    def make_goal(self, x, y):
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        #############################################################
        # TODO 2 (DONE): set the goal position from x and y
        #############################################################
        goal.pose.pose.orientation.w = 1.0
        return goal

    def send_next(self):
        if self.index >= len(WAYPOINTS):
            # TODO 4 (DONE): loop instead of quitting
            #############################################################
           
            #############################################################
                
        x, y = WAYPOINTS[self.index]
        self.get_logger().info(f'--> Waypoint {self.index + 1}: ({x}, {y})')
        self.client.wait_for_server()
        future = self.client.send_goal_async(
            self.make_goal(x, y),
            feedback_callback=self.on_feedback)     # TODO 3
        future.add_done_callback(self.on_accepted)

    def on_feedback(self, msg):
        #############################################################
        # TODO 3 (DONE): print the remaining distance to the goal
 
        #############################################################
               
    def on_accepted(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal rejected — is it inside the map?')
            self.land()
            return
        handle.get_result_async().add_done_callback(self.on_arrived)

    def on_arrived(self, future):
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Reached waypoint {self.index + 1}')
            self.index += 1
            self.send_next()
        else:
            self.get_logger().error(
                f'Waypoint {self.index + 1} FAILED (status {status}). Landing.')
            self.land()

    def land(self):
        """vel_mux lands when it receives a Twist with negative linear.z."""
        cmd = Twist()
        cmd.linear.z = -1.0
        for _ in range(5):
            self.cmd_pub.publish(cmd)
            time.sleep(0.1)
        self.get_logger().info('Land command sent.')
        self.done = True

def main():
    rclpy.init()
    node = Patrol()
    node.send_next()

    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.1)

    time.sleep(4)          # let it descend
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**The TODOs:**

1. Define 4+ patrol waypoints.
2. Set `goal.pose.pose.position.x/y` from the arguments.
3. Print live distance-to-goal from the feedback callback.
4. Make `LOOP_FOREVER` loop the patrol.

### Task 3: Send a goal that's impossible

Set a waypoint **inside** a taped obstacle. What does Nav2 do? Why? Make your code handle it gracefully instead of hanging.

---

---

## 9. Quick reference

```bash
# Launch (single terminal)
ros2 launch ~/ros2_ws/nav2_flow_launch.py

# ALWAYS verify before flying:
ros2 lifecycle get /bt_navigator      # must be: active
ros2 run tf2_ros tf2_echo map cf1     # must print a translation

# Python mission (launch must be running)
python3 ~/ros2_ws/nav_mission.py

# Teleop (take off / land)
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=/cmd_vel
#   t = take off, b = land
```

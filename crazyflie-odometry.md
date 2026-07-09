---
title: Position Control and Odometry Drift with the Crazyflie
---

# Position Control and Odometry Drift with the Crazyflie

## 1. Overview and Objective

Mobile robots need to know their position relative to the objects they interact with. There are two main types of position sensors used in robotics: relative and absolute.
An **absolute** sensor, such as GPS or a motion-capture system, reports position with respect to a fixed external reference, so its error stays bounded no matter how long or how far the robot has traveled. A **relative** sensor, such as a wheel encoder or an optical-flow camera, only measures how much the robot moved since the last reading. Each reading of a relative sensor carries its own small error, and estimating position by adding them up one after another lets that error accumulate: the longer the robot moves, the further its estimate can wander from the truth. This accumulation is **odometry drift**, and it is unavoidable with a relative sensor alone, however accurate each individual reading is.

In this activity you will fly a **Crazyflie** quadcopter fitted with a **Flow deck V2** (a downward-facing camera and range sensor that lets the drone estimate its own position) and see this drift for yourself.
You will command the drone in three different ways:

1. The **MotionCommander**, which moves the drone by relative displacements from wherever it currently is.
2. **Position setpoints** sent directly to the drone's controller, one after another, without any smoothing.
3. The **HighLevelCommander**'s `go_to` method, which uses an onboard planner to generate a smooth trajectory to an absolute waypoint.

You will then design a short mission that starts and ends at the same physical point, print the drone's own estimate of its position, and measure with a ruler how far the real landing point is from the real takeoff point. The gap between what the drone believes and where it actually is, is the **odometry drift** you are here to observe.

**By the end of this activity, you will be able to:**

1. Explain the difference between a position tracking error and a position estimation error.
2. Command a Crazyflie using relative motion, direct position setpoints, and planned trajectories.
3. Read the drone's estimated position from a running script.
4. Quantify the accumulated drift of a simple position-hold flight using physical measurements.

---

## 2. Safety Instructions

- Tie back long hair before handling or flying a drone. Propellers spin fast enough to catch loose hair.
- Fly only in the area designated for flight at the back of the room. Keep the rest of the room clear of drones.
- Never intentionally fly into people or objects. Land immediately if a flight goes somewhere you did not expect.

---

## 3. Setup

All the steps below assume Windows. Follow the official documentation linked at each step; it is kept up to date by Bitcraze and will always be more current than anything reproduced here.

### 3.1 Install Python

Install Python 3 from the official build at <https://python.org>. During installation, check the **"Add python.exe to PATH"** checkbox.

After installing, open a terminal and confirm both commands work:

```
python --version
pip --version
```

### 3.2 Install cflib

`cflib` is the Python library used to talk to the Crazyflie from your own scripts.

```
pip install cflib
```

Official installation instructions: <https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/installation/install/>

### 3.3 Install cfclient

`cfclient` is the graphical ground-station application used to verify the connection and fly by hand before writing any code.

```
pip install cfclient
```

Official installation instructions: <https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/installation/install/>

### 3.4 Install the CrazyRadio and Crazyflie USB drivers with Zadig

Windows does not ship a driver for the Bitcraze USB devices, so one has to be installed manually with a tool called **Zadig**. This needs to be done once for the **CrazyRadio PA** dongle, and again for the **Crazyflie** itself if you ever plug it directly into the computer with a USB cable.

Official instructions: <https://www.bitcraze.io/documentation/repository/crazyradio-firmware/master/building/usbwindows/>

1. Download Zadig from <http://zadig.akeo.ie/>.
2. Plug in the CrazyRadio PA dongle. Windows may show a driver installation window; let it fail or close it.
3. Launch Zadig, select the CrazyRadio device from the list, choose the **libusb** driver, and click **Install**.
4. If you also plan to connect the Crazyflie itself over USB, plug it in, and repeat the same steps in Zadig for it.

---

## 4. How the Crazyflie Controls Its Position

### 4.1 The cascaded PID controller

The Crazyflie firmware controls attitude and position with a **cascaded PID controller**: an outer position loop produces the attitude and thrust targets that an inner attitude loop tracks, which in turn feeds an even faster rate loop that drives the motors. Every loop closes around the drone's own **state estimate**, produced by an Extended Kalman filter that fuses the IMU with the Flow deck's optical-flow and range measurements.

![Crazyflie cascaded PID controller](https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/images/cascaded_pid_controller.png)

### 4.2 Position setpoints versus trajectories

You can drive the position loop in two different ways:

- **Sending a position setpoint directly.** Each setpoint you send becomes the immediate target of the position controller. If consecutive setpoints are far apart, the controller will try to get there as fast as its gains allow, which can look abrupt. This is the mode used by `send_position_setpoint` in `autonomous_sequence.py` below.
- **Sending a trajectory.** The **HighLevelCommander**'s `go_to` method does not hand a raw target to the position controller. Instead, it asks an onboard planner to compute a smooth 7th-order polynomial path from the drone's current state to the goal, with bounded velocity and acceleration, and then feeds the position controller a continuous stream of intermediate setpoints along that path. The result is a much smoother flight for the same start and end point.

### 4.3 Tracking error versus estimation error

These two quantities are easy to conflate, but they are answers to different questions:

- **Tracking error** is the gap between the *commanded* setpoint and the *estimated* position. It tells you how well the cascaded PID controller is following the reference it was given. It says nothing about where the drone really is.
- **Estimation error** is the gap between the *estimated* position and the drone's *true* position in the room. Because the Flow deck only measures relative motion (optical flow and short-range height), and never an absolute position, every small error in each measurement accumulates over time. This accumulation is **odometry drift**: the controller can have excellent tracking and still land far from where it thinks it is, simply because its own sense of "where" has wandered.

Today's activity is designed to make the second kind of error visible, since the first kind is usually small enough not to notice.

---

## 5. Verify the Setup with cfclient

1. Look at the label on the underside of the Crazyflie's frame for the last two hexadecimal digits `xx` of its radio address. You will need it both for the client and for your own scripts, as part of a URI `radio://0/80/2M/E7E7E7E7Exx`. If the label underneath the crazyflie says `A0`, for example, then the address of the drone is `E7E7E7E7EA0` and its URI is `radio://0/80/2M/E7E7E7E7EA0`.
2. Plug in the CrazyRadio PA dongle, launch **cfclient**, and click **Scan**.
3. Select your Crazyflie's address from the dropdown next to the **Connect** button and click **Connect**.
4. Open the **Flight Control** tab and enable **Hover** (assisted) mode, which requires the Flow deck and holds the drone's height and horizontal position automatically. Use the **Take Off**, **Land**, and directional move buttons in the GUI to fly the drone by hand for a few seconds, staying inside the designated flight area.

Do not move on until you can reliably take off, move around, and land using the GUI.

---

## 6. Flying with the Python API

The full API reference is at <https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/api/cflib/>. Keep it open as you go through the examples; you will need it for the challenge later.

Before running any example, edit its `URI` (or `uri`) variable to match the address you read off your Crazyflie in the previous section.

### 6.1 MotionCommander: relative displacement

Run <https://github.com/bitcraze/crazyflie-lib-python/blob/master/examples/autonomy/motion_commander_demo.py>.

The `MotionCommander` takes off automatically when constructed and lands automatically when it goes out of scope. Every call, such as `mc.forward(0.8)` or `mc.turn_left(90)`, is a relative displacement or turn from wherever the drone currently is, sent to the firmware as a stream of velocity setpoints.

### 6.2 Position setpoints sent directly

Run <https://github.com/bitcraze/crazyflie-lib-python/blob/master/examples/autonomy/autonomous_sequence.py>.

This script arms the Crazyflie, takes off, and then repeatedly calls `cf.commander.send_position_setpoint(x, y, z, yaw)` for each waypoint in `sequence`, 50 times over 5 seconds per waypoint, before moving to the next one. It also starts a log configuration that prints the Kalman filter's estimated position (`kalman.stateX/Y/Z`) to the console, which is how you will read the drone's own belief of where it is.

### 6.3 HighLevelCommander: planned trajectories with go_to

Create a new script, `autonomous_sequence_go_to.py`, that flies the same square pattern as `autonomous_sequence.py`, but replaces the manual position-setpoint loop with a series of `go_to` calls, and lands with `land()` instead of a final `go_to(x=0, y=0, z=0, yaw=0, duration_s=1)`. Use keyword arguments so the waypoints stay easy to read:

```python
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.utils.reset_estimator import reset_estimator

uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')


def position_callback(timestamp, data, logconf):
    print('pos: ({}, {}, {})'.format(
        data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ']))


def start_position_printing(scf):
    log_conf = LogConfig(name='Position', period_in_ms=500)
    log_conf.add_variable('kalman.stateX', 'float')
    log_conf.add_variable('kalman.stateY', 'float')
    log_conf.add_variable('kalman.stateZ', 'float')

    scf.cf.log.add_config(log_conf)
    log_conf.data_received_cb.add_callback(position_callback)
    log_conf.start()


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        reset_estimator(scf)
        start_position_printing(scf)

        commander = scf.cf.high_level_commander

        scf.cf.supervisor.send_arming_request(True)
        time.sleep(1.0)

        commander.takeoff(absolute_height_m=0.4, duration_s=2.0)
        time.sleep(3.0)

        commander.go_to(x=0.0, y=0.0, z=1.2, yaw=0, duration_s=2.0)
        time.sleep(2.5)

        commander.go_to(x=0.5, y=-0.5, z=1.2, yaw=0, duration_s=2.0)
        time.sleep(2.5)

        commander.go_to(x=0.5, y=0.5, z=1.2, yaw=0, duration_s=2.0)
        time.sleep(2.5)

        commander.go_to(x=-0.5, y=0.5, z=1.2, yaw=0, duration_s=2.0)
        time.sleep(2.5)

        commander.go_to(x=-0.5, y=-0.5, z=1.2, yaw=0, duration_s=2.0)
        time.sleep(2.5)

        commander.go_to(x=0.0, y=0.0, z=1.2, yaw=0, duration_s=2.0)
        time.sleep(2.5)
        
        commander.go_to(x=0.0, y=0.0, z=0.4, yaw=0, duration_s=2.0)
        time.sleep(2.5)

        commander.land(absolute_height_m=0.0, duration_s=2.0)
        time.sleep(2.0)
        
        commander.stop()
```

Compare how this flight looks and sounds to the raw position-setpoint version from 6.2. Look at the `duration_s` argument of `go_to`: it is what lets the planner produce a smooth path instead of a snap to the target.

---

## 7. Challenge: Program a Mission

Using the room's hoops, arches, and boxes as obstacles and waypoints, design and fly a short mission of your own that:

- Starts and lands at the same marked point on the floor.
- Passes through or around at least three of the room's elements.
- Uses either the `MotionCommander` or the `HighLevelCommander`'s `go_to`, your choice.
- Prints the estimated position (as in the examples above) at least at takeoff and right before landing.

Mark your takeoff point on the floor with tape before you start.

---

## 8. Quantify the Drift

For your mission from the challenge:

1. Note the estimated position printed right before landing. Is there tracking error?
2. Use a ruler to measure the real distance on the floor between your marked takeoff point and where the drone actually landed.
3. Compare that measured distance with what the printed position claimed. The difference between the two is the odometry drift accumulated over your mission.
4. Repeat with a mission of a different length or number of waypoints, and discuss with your group whether the drift grows with flight time, distance traveled, or number of waypoints.

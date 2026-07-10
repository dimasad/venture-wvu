---
title: Absolute Position Control of the Crazyflie with the Loco Positioning System
---

# Absolute Position Control of the Crazyflie with the Loco Positioning System


## 1. Introduction

After positioning the drone using the Flow deck V2, a relative position sensor, we will now use the Loco Positioning System, an absolute position sensor, for moving the drone directly in world coordinates. The Loco Positioning System is a miniature indoor “GPS” out of ultra-wideband radio beacons placed around the room.

By the end of this tutorial you will:

- Understand how a drone knows its own position indoors.
- Understand how the installed Loco Positioning System works and check it.
- Run a mission where the drone flies a shape completely on its own.
- Understand the flight code line by line.
- Modify the mission yourself (a task is proposed at the end).

---

## 2. UWB Radio Localization

Small radio boxes called anchors are placed around the room at known, measured positions.
The drone carries a small radio board, the Loco deck that listens to the anchors and determines out how far it is from each.
Knowing its distance to beacons whose positions are known, the drone computes its own `(x, y, z)` position using the same principle the GPS uses.
It does this on board, many times per second, so it always knows where it is.
A program on your laptop then just says "take off, go here, now here, land," and the drone can fly the path itself.

The anchors and the drone use **Ultra-Wideband (UWB)** radio. Radio travels at the speed of light, a known constant, so by measuring how long a message takes to travel, the drone converts time into distance.
Imagine being told "you are 3 m from this corner." You could be anywhere on a circle. Add "and 4 m from that corner" and the possibilities shrink. Add more beacons and add height, and only one 3D point fits. The drone does this with the eight anchors to pin down its exact position. 

Real measurements are noisy. The drone runs a **Kalman filter** that blends the noisy distances with what it knows about its own motion to produce one smooth, reliable position estimate. This is built into the drone's firmware.
The Loco system has two working modes. **This tutorial uses TDoA2**, the mode built for multiple anchors and (later) multiple drones:

- **TDoA2 (Time Difference of Arrival):** the anchors continuously broadcast, synchronized to a "master" anchor, and the drone only *listens*. Because it only listens, the system can position many drones at once. It is designed for **8 anchors placed at the corners of a box**.
- **TWR (Two-Way Ranging):** the drone pings each anchor directly. Simpler and slightly more forgiving, but supports only one drone. (Not used here.)

One key rule for TDoA2: the drone should fly **inside the box formed by the anchors** (the "convex hull"). Accuracy drops quickly outside it, which is why 8 anchors in a box shape matter.

## 3. System layout

The 8 anchors are **already installed** in the room, you don't place or measure them. But you should understand the layout, because the drone flies inside the box they form, and the flight positions in the code are relative to this same coordinate frame.
The anchors sit at the 8 corners of the flight area box.

The X and Y axes are marked on the ground with masking tape, by the anchor 0, while the Z axis is vertical, pointing up. 
Anchor **0** marks the origin `(0, 0, 0)` on the ground below it; from there **X** runs along the short 3.2 m side, **Y** along the long 4.9 m side, and **Z** points up to 1.6 m. Anchors **0, 2, 5, 7** are mounted low, near the floor, and **1, 3, 4, 6** are mounted high, one at each corner.

> **The exact stored coordinates are already in the system**, matching the [anchor configuration file](assets/config/loco_config.yaml). To see the real `(x, y, z)` for each anchor ID on your setup, open the Loco Positioning tab (Step 4.2) and click **Configure positions,**  every anchor's position is listed there. **You do not need to change them.** Use Configure positions to read the exact values if you want them for your flight code.


Important details when using the system:

- The usable flight volume is **inside** this box. Keep every flight path within it, accuracy drops off outside the anchor box.
- When you start the drone, you place it flat inside this volume pointing along **+X** (along the 3.20 m side).

## 4. Set up

### Step 4.1 — Connect to the drone

1. Launch the client:
    
    ```bash
    cfclient
    ```
    
2. Click **Scan** (top-left). Your drone appears in the drop-down, e.g. `radio://0/80/2M/E7E7E7E7E7`.
3. Select it and click **Connect**. Live numbers in the flight-data area mean you're connected.

### Step 4.2 — Open the Loco Positioning view

1. In the top menu bar, click **View**.
2. Go to **Tabs**.
3. Click **Loco Positioning Tab** (it gets a checkmark).
4. A new **Loco Positioning** tab appears, click it.


### Step 4.3 Verify it works

1. In the Loco Positioning tab, check the **anchor status boxes**: you want **eight green boxes**. Green = the drone hears that anchor. All red = the drone and anchors are in different modes. A few black/red = those anchors aren't heard (check power, line of sight to the master).
2. Look at the **3D graph**: eight anchor points and a marker for the drone. Rotate by dragging, zoom with the scroll wheel.
3. **Pick up the drone and move it by hand.** The marker should follow,  move left, marker left; lift 1 m, marker rises 1 m.
4. Only continue once the marker tracks smoothly and sits in the right place. If it jumps or sits wrong, re-check the anchor positions and IDs in Step 4.2.

---

## 6. Run the autonomous mission

### Step 6.1 — Copy the drone's address

From the drop-down next to Scan/Connect, copy your URI (e.g. `radio://0/80/2M/E7E7E7E7E7`).

### Step 6.2 — Disconnect cfclient

Only one program can use the radio at a time. Click **Disconnect** in cfclient (leave the drone powered on).

### Step 6.3 — Create the flight program

Save this as `fly_square.py`, and paste your URI into the `URI` line.

```python
"""
Flies a Crazyflie 2.1 autonomously using the Loco Positioning System
"""

import time
import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig
from cflib.positioning.motion_commander import MotionCommander
from cflib.positioning.position_hl_commander import PositionHlCommander

# ─── PASTE YOUR DRONE'S ADDRESS BETWEEN THE QUOTES ───
URI = "radio://0/80/2M/E7E7E7E7E7"

# Flight settings — keep them small and gentle
TAKEOFF_HEIGHT = 0.6  # hover height, meters
SQUARE_SIDE = 1.0  # side length of the square, meters
SPEED = 0.5  # movement speed, meters/second

# Global variable to store the drone's (x,y,z) position
position = None

def wait_until_position_is_ready(scf):
    """
    Wait until the position estimate has settled before flying.
    We watch how much the estimate is 'wobbling' and only continue
    once it is steady, so the drone doesn't take off confused.
    """
    print("Waiting for the drone to work out where it is...")
    log = LogConfig(name="variance", period_in_ms=100)
    log.add_variable("kalman.varPX", "float")
    log.add_variable("kalman.varPY", "float")
    log.add_variable("kalman.varPZ", "float")

    recent = {"x": [1000] * 10, "y": [1000] * 10, "z": [1000] * 10}
    steady_enough = 0.001

    with SyncLogger(scf, log) as logger:
        for _, data, _ in logger:
            recent["x"].append(data["kalman.varPX"])
            recent["x"].pop(0)
            recent["y"].append(data["kalman.varPY"])
            recent["y"].pop(0)
            recent["z"].append(data["kalman.varPZ"])
            recent["z"].pop(0)
            wobble = max(max(v) - min(v) for v in recent.values())
            if wobble < steady_enough:
                print("Position is steady. Ready to fly!")
                break


def position_callback(timestamp, data, logconf):
    """Code run each time a new position log data arrives."""
    # Retrieve position from log data
    x = data["kalman.stateX"]
    y = data["kalman.stateY"]
    z = data["kalman.stateZ"]

    # Update global position variable
    global position
    position = x, y, z

    # Display on the terminal
    print("current position: ", position)


def configure_position_log(scf):
    log_conf = LogConfig(name="Position", period_in_ms=100)
    log_conf.add_variable("kalman.stateX", "float")
    log_conf.add_variable("kalman.stateY", "float")
    log_conf.add_variable("kalman.stateZ", "float")

    scf.cf.log.add_config(log_conf)
    log_conf.data_received_cb.add_callback(position_callback)
    log_conf.start()


def prepare_drone(scf):
    """Wait until the estimation is stable and configure logs."""
    wait_until_position_is_ready(scf)
    configure_position_log(scf)
    time.sleep(0.2)
    print("Waiting to get the current position")
    while position is None:
        time.sleep(0.5)
        print(".", end=None)
    print()


def fly_the_square(scf):
    """Take off, fly a square, and land."""
    x0, y0, z0 = position
    x1 = x0 + SQUARE_SIDE
    y1 = y0 + SQUARE_SIDE
    # MotionCommander takes off when it starts and lands when it ends.
    with PositionHlCommander(scf, default_height=TAKEOFF_HEIGHT) as pc:
        print("Taking off...")
        time.sleep(4)  # hover a moment to steady

        print("Moving toward X+")
        pc.go_to(x=x1, y=y0, velocity=SPEED)

        print("Moving toward Y+")
        pc.go_to(x=x1, y=y1, velocity=SPEED)

        print("Moving toward X-")
        pc.go_to(x=x0, y=y1, velocity=SPEED)

        print("Moving toward Y-")
        pc.go_to(x=x0, y=y0, velocity=SPEED)

        print("Hovering around start.")
        
        time.sleep(1)
        print("Landing...")  # lands automatically on exit


if __name__ == "__main__":
    cflib.crtp.init_drivers()  # get the radio ready
    print("Connecting to the drone...")
    with SyncCrazyflie(URI) as scf:  # connect
        prepare_drone(scf)  # confirm it knows where it is
        fly_the_square(scf)  # fly!
        print("All done.")
```

### Step 6.4 — Run it

1. Place the drone flat, pointing **+X**, well **inside** the anchor box.
2. Make sure the area is clear and everyone knows how to stop it.
3. Run it:
```python
python fly_square.py
```

The drone connects, settles its position, takes off to 1 m, flies a 0.5 m square, returns near the start, and lands, on its own.

**Stop at any time:** `Ctrl + C`, or pull the battery.

---

## 7. Understand the code

Read this so you can change the mission with confidence.

**The imports** bring in the tools: `cflib.crtp` (radio drivers), `SyncCrazyflie` (the connection), `LogConfig`/`SyncLogger` (reading data back from the drone), and `PositionHlCommander` (flies the drone to absolute `(x, y, z)` points instead of relative distances).

**`URI`** is the drone's radio address, which drone to talk to.

**The settings** (`TAKEOFF_HEIGHT`, `SQUARE_SIDE`, `SPEED`) are plain numbers you can change. `SQUARE_SIDE` is added to the drone's own starting position to get the far corners of the square, so the shape is always drawn around wherever the drone happens to be placed.

**`wait_until_position_is_ready`** reads three "variance" values from the drone, roughly, how *unsure* the drone is about its x, y, z position. It keeps the last 10 readings and waits until they stop changing much (the estimate has "settled"). This prevents taking off while the drone is still figuring out where it is.

**`position_callback`** runs automatically every time the drone sends a new position reading. It reads `kalman.stateX/Y/Z`, the Kalman filter's current best estimate of the drone's `(x, y, z)`, stores it in the global `position` variable, and prints it, so you can watch the drone's estimated position update live on the terminal.

**`configure_position_log`** sets up the log that drives `position_callback`: it tells the drone which three variables to stream (`kalman.stateX/Y/Z`, every 100 ms) and registers `position_callback` to run each time a new reading arrives.

**`prepare_drone`** resets the position estimate (tells the Kalman filter to start fresh), waits for it to settle, then starts the position log and waits until `position` actually holds a reading before returning. This guarantees the mission below has a real, current `(x0, y0, z0)` to build its flight path from, instead of assuming the drone starts at the origin.

**`fly_the_square`** is the mission. It reads the drone's current position (`x0, y0, z0`, filled in by the log above) and computes `x1 = x0 + SQUARE_SIDE`, `y1 = y0 + SQUARE_SIDE`, the far corners of the square. The line `with PositionHlCommander(scf, default_height=TAKEOFF_HEIGHT) as pc:` is where the drone **takes off** to the given height. Inside the block, each `pc.go_to(x=..., y=..., velocity=...)` call is an **absolute** target, "fly to this exact `(x, y)` point in the room", not "move this far from where you are." The drone uses its own live LPS position to correct itself en route, so it still lands on each corner accurately even if it drifted slightly on the way there. The four calls visit the corners `(x0,y0) → (x1,y0) → (x1,y1) → (x0,y1) → (x0,y0)` in order, tracing a square and returning to the start. When the `with` block ends, the drone **lands automatically**.

**The `__main__` block** is where the program starts: it initializes the radio, connects, prepares the drone, and runs the mission.

**The mental model:** the drone continuously reports its own live position; your laptop reads that once to know where "home" is, then sends absolute target coordinates in that same room frame. The drone handles getting from one target to the next itself, correcting for drift along the way, so you describe *where* it should be, not *how far* it should move.

---

## 8. Your task: fly a different shape

Now make the drone do something other than a square. Pick one (or invent your own):

**Task A — Triangle.** Make the drone fly a triangle and return to start. Hint: pick three `(x, y)` points around `(x0, y0)` and visit them in order, each with its own `pc.go_to(x=..., y=..., velocity=SPEED)`.

**Task B — Rectangle at two heights.** Fly a rectangle (e.g. 0.8 m × 0.4 m) with a sequence of `go_to` corners, then call `pc.go_to(x=x0, y=y0, z=z0 + 0.5, velocity=SPEED)` to rise, and fly the same rectangle again higher before landing.

**Task C — Letter or initials.** Trace the first letter of your name in the air as a sequence of absolute `(x, y)` waypoints passed to `pc.go_to`, each one a stroke of the letter.

**Rules to keep it safe and working:**

- Keep every waypoint **inside the anchor box,** don't let the path leave the volume
the anchors form, or the position estimate degrades.
- Keep `SPEED` at 0.3 m/s or lower while learning.
- Keep heights modest (0.5–1.0 m).
- Change **only the movement lines** inside `fly_the_square` (you can rename it). Do not add estimator/tuning parameters, the default settings are what fly reliably.
- Test with the area clear and a hand on `Ctrl + C`.

**Stretch goal:** instead of writing out each `go_to` call by hand, define your waypoints as a list of `(x, y, z)` tuples and loop over them, calling `pc.go_to(x=x, y=y, z=z, velocity=SPEED)` for each one in turn.

---

## 9. Where to learn more

- [Bitcraze official documentation](https://www.bitcraze.io/documentation/start/) (the makers of the Crazyflie and Loco system).
- The [`cflib` Python examples](https://github.com/bitcraze/crazyflie-lib-python/tree/master/examples), waypoint flights and multi-drone scripts.
- The [Loco Positioning System documentation](https://www.bitcraze.io/documentation/tutorials/getting-started-with-loco-positioning-system/), TWR/TDoA details and anchor placement.

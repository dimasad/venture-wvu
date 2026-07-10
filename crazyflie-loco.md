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

## 3. System layout (reference)

The 8 anchors are **already installed** in the room, you don't place or measure them. But you should understand the layout, because the drone flies inside the box they form, and the flight positions in the code are relative to this same coordinate frame.

The anchors sit at the **8 corners of the room-sized box**. Anchor **0** marks the origin `(0, 0, 0)` in one bottom corner; from there **X** runs along the short 3.2 m side, **Y** along the long 4.9 m side, and **Z** points up to 1.60 m. Anchors **0, 2, 5, 7** are near the floor and **1, 3, 4, 6** are up high, one at each corner.

The room is a box of 4.20 m (X) × 3.20 m (Y) × 1.60 m (Z)** with the origin at anchor 0.

> **The exact stored coordinates are already in the system.** To see the real `(x, y, z)` for each anchor ID on your setup, open the Loco Positioning tab (Step 4.2) and click **Configure positions,**  every anchor's position is listed there. **You do not need to change them.** Use Configure positions to read the exact values if you want them for your flight code.


Key things to take from this:

- The **origin (0,0,0) is at anchor 0**; **+X** runs along the 4.90 m side, **+Y** along the 3.20 m side, **+Z** is up to 1.60 m.
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

> **If Scan finds nothing:** the battery is almost always low, charge it, make sure the M4 LED blinks, and unplug any USB cable (the drone must run on its battery).
> 

### Step 4.2 — Open the Loco Positioning view

1. In the top menu bar, click **View**.
2. Go to **Tabs**.
3. Click **Loco Positioning Tab** (it gets a checkmark).
4. A new **Loco Positioning** tab appears, click it.

---

## 5. Verify it works (do not skip)

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
fly_square.py
Flies a Crazyflie 2.1 autonomously using the Loco Positioning System:
takes off, flies a small square, and lands. No manual control.
"""

import time
import cflib.crtp
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig
from cflib.positioning.motion_commander import MotionCommander

# ─── PASTE YOUR DRONE'S ADDRESS BETWEEN THE QUOTES ───
URI = 'radio://0/80/2M/E7E7E7E7E7'

# Flight settings — keep them small and gentle
TAKEOFF_HEIGHT = 1.0   # hover height, meters
SQUARE_SIDE    = 1.0   # side length of the square, meters
SPEED          = 0.3   # movement speed, meters/second

def wait_until_position_is_ready(scf):
    """
    Wait until the position estimate has settled before flying.
    We watch how much the estimate is 'wobbling' and only continue
    once it is steady, so the drone doesn't take off confused.
    """
    print('Waiting for the drone to work out where it is...')
    log = LogConfig(name='variance', period_in_ms=100)
    log.add_variable('kalman.varPX', 'float')
    log.add_variable('kalman.varPY', 'float')
    log.add_variable('kalman.varPZ', 'float')

    recent = {'x': [1000] * 10, 'y': [1000] * 10, 'z': [1000] * 10}
    steady_enough = 0.001

    with SyncLogger(scf, log) as logger:
        for _, data, _ in logger:
            recent['x'].append(data['kalman.varPX']); recent['x'].pop(0)
            recent['y'].append(data['kalman.varPY']); recent['y'].pop(0)
            recent['z'].append(data['kalman.varPZ']); recent['z'].pop(0)
            wobble = max(max(v) - min(v) for v in recent.values())
            if wobble < steady_enough:
                print('Position is steady. Ready to fly!')
                break

def prepare_drone(scf):
    """Reset the position estimate so the drone starts fresh and clean."""
    scf.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.cf.param.set_value('kalman.resetEstimation', '0')
    wait_until_position_is_ready(scf)

def fly_the_square(scf):
    """Take off, fly a square, and land — all automatically."""
    # MotionCommander takes off when it starts and lands when it ends.
    with MotionCommander(scf, default_height=TAKEOFF_HEIGHT) as drone:
        print('Taking off...')
        time.sleep(4)                        # hover a moment to steady

        print('Flying the square...')
        drone.forward(SQUARE_SIDE, velocity=SPEED)
        drone.left(SQUARE_SIDE,    velocity=SPEED)
        drone.back(SQUARE_SIDE,    velocity=SPEED)
        drone.right(SQUARE_SIDE,   velocity=SPEED)

        time.sleep(1)
        print('Landing...')                  # lands automatically on exit

if __name__ == '__main__':
    cflib.crtp.init_drivers()                # get the radio ready
    print('Connecting to the drone...')
    with SyncCrazyflie(URI) as scf:          # connect
        prepare_drone(scf)                   # confirm it knows where it is
        fly_the_square(scf)                  # fly!
        print('All done.')
```

### Step 6.4 — Run it

1. Place the drone flat, pointing **+X**, well **inside** the anchor box.
2. Make sure the area is clear and everyone knows how to stop it.
3. Run it:
    
    **Windows:** `python fly_square.py`**Ubuntu:** `python3 fly_square.py`
    

The drone connects, settles its position, takes off to 1 m, flies a 0.5 m square, returns near the start, and lands, on its own.

**Stop at any time:** `Ctrl + C`, or pull the battery.

---

## 7. Understand the code

Read this so you can change the mission with confidence.

**The imports** bring in the tools: `cflib.crtp` (radio drivers), `SyncCrazyflie` (the connection), `LogConfig`/`SyncLogger` (reading data back from the drone), and `MotionCommander` (simple movement commands).

**`URI`** is the drone's radio address, which drone to talk to.

**The settings** (`TAKEOFF_HEIGHT`, `SQUARE_SIDE`, `SPEED`) are plain numbers you can change. Everything about the shape and speed of the flight is controlled here and in the movement lines.

**`wait_until_position_is_ready`** reads three "variance" values from the drone, roughly, how *unsure* the drone is about its x, y, z position. It keeps the last 10 readings and waits until they stop changing much (the estimate has "settled"). This prevents taking off while the drone is still figuring out where it is.

**`prepare_drone`** resets the position estimate (tells the Kalman filter to start fresh), then calls the wait function above. Always done right before flying.

**`fly_the_square`** is the mission. The line `with MotionCommander(scf, default_height=TAKEOFF_HEIGHT) as drone:` is where the drone **takes off** to the given height. Inside the block, each command moves the drone a set distance:

- `drone.forward(d)` / `drone.back(d)` — move along +X / −X by `d` meters
- `drone.left(d)` / `drone.right(d)` — move along +Y / −Y
- `drone.up(d)` / `drone.down(d)` — change height
- `drone.turn_left(deg)` / `drone.turn_right(deg)` — rotate in place

Each takes an optional `velocity=` in m/s. When the `with` block ends, the drone **lands automatically**. So four moves,  forward, left, back, right, trace a square and return to start.

**The `__main__` block** is where the program starts: it initializes the radio, connects, prepares the drone, and runs the mission.

**The mental model:** your laptop sends the drone target moves; the drone uses its live LPS position to carry them out. You describe *what* path to fly; the drone handles *how* to fly it.

---

## 8. Your task: fly a different shape

Now make the drone do something other than a square. Pick one (or invent your own):

**Task A — Triangle.** Make the drone fly a triangle and return to start. Hint: a triangle needs turns that aren't 90°. Combine moves with `drone.turn_left(deg)` between straight segments, or use forward/left/right moves of different lengths.

**Task B — Rectangle at two heights.** Fly a rectangle (e.g. 0.8 m × 0.4 m), then use `drone.up(0.5)` and fly the same rectangle again higher, then land.

**Task C — Letter or initials.** Trace the first letter of your name in the air using a sequence of `forward` / `back` / `left` / `right` / `up` / `down` moves.

**Rules to keep it safe and working:**

- Keep every move **inside the anchor box,** don't let the path leave the volume
the anchors form, or the position estimate degrades.
- Keep `SPEED` at 0.3 m/s or lower while learning.
- Keep heights modest (0.5–1.0 m).
- Change **only the movement lines** inside `fly_the_square` (you can rename it). Do not add estimator/tuning parameters, the default settings are what fly reliably.
- Test with the area clear and a hand on `Ctrl + C`.

**Stretch goal:** instead of relative moves (`forward`, `left`, …), learn the high-level commander's *go-to* command to fly to exact `(x, y, z)` points in the room, and visit a list of waypoints you define.

---

## 9. Every-flight routine (quick reference)

Once set up, a flying session is just:

1. Charge and insert a battery.
2. Power on all 8 anchors.
3. Power on the drone (wait for the blinking M4 LED).
4. cfclient → **Scan** → **Connect**.
5. **View → Tabs → Loco Positioning Tab**; confirm 8 green boxes and the marker follows the drone when you move it by hand.
6. Click **Disconnect** in cfclient.
7. Run your Python program.

---

---

## 10. Troubleshooting

| Problem | Likely cause | Fix |
| --- | --- | --- |
| Scan finds no drone | Battery low, or drone not fully on | Charge; confirm M4 LED blinks; unplug USB |
| All 8 anchor boxes red | Drone and anchors in different modes | Re-check the anchors are all in TDoA2 |
| A few anchor boxes red/black | Those anchors not heard | Check their power and clear line of sight to the master (anchor 0) |
| Position marker in wrong place | Stored anchor positions or IDs off | Check the stored `(x,y,z)` per ID in Configure positions (Step 4.2); confirm each physical anchor matches its ID in the diagram (Section 3) |
| Position noisy, worse near edges | Flying outside the anchor box | Keep the whole path inside the 8-anchor box |
| Program can't connect | cfclient still holds the radio | Click **Disconnect** in cfclient first |
| Drone flips on takeoff | Prop in wrong position, or not level at start, or extra tuning params added | Check props are correct/undamaged; start on a flat level surface; use the code exactly as given |
| Drone drifts or won't hold height | Weak battery, or poor anchor geometry | Fresh battery; spread anchors in a proper box |
| Loco tab greyed out | Loco deck not detected | Re-seat the deck and power-cycle the drone |

---

## 11. Where to learn more

- Bitcraze official documentation (the makers of the Crazyflie and Loco system).
- The `cflib` Python examples, waypoint flights and multi-drone scripts.
- The Loco Positioning System documentation, TWR/TDoA details and anchor placement.

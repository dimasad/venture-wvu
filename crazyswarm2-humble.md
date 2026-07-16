---
title: Quick start of crazyswarm2 with ROS2 Humble
---

# Quick start of crazyswarm2 with ROS2 Humble

## Attach the radio to WSL

On a PowerShell terminal on Windows, run the following command to attach the radio to WSL.

```powershell
wsl -e true
usbipd list
usbipd attach --wsl --busid=<BUSID>
```

## Import the WSL2 image

I created a WSL2 image of Ubuntu 22.04 with ROS2 Humble and all the required software installed, download the file  [humble.tar.gz](https://drive.google.com/file/d/1lxUs47skEtg5NJySSWyeFaGdhLY-FXJC/view) to begin. Then, on a PowerShell terminal on Windows, enter the directory where the image is stored and run the following command to import it with the name `humble`:

```powershell
wsl --import humble humble humble.tar.gz
```

## Update the drone's address

Open a WSL terminal on the imported `humble` image and edit the file `~/ros2_ws/crazyflies.yaml`. Change the address to reflect the address of the drone you are using.

## Turn on the drone and teleoperate

Place the drone on the flying area and run the teleoperation.

```bash
ros2 launch ~/ros2_ws/nav2_flow_launch.py
```

On another `humble` terminal,

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Run a mission with Nav2

Place the drone on a known start area, reboot it, launch `nav2_flow_launch.py`, and set Nav2 goals on RViz.

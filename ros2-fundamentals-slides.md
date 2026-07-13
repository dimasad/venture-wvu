---
marp: true
title: "Introduction to ROS 2: Overview & Fundamental Concepts"
theme: default
paginate: true
size: 16:9
header: "Introduction to ROS"
style: |
  section {
    font-size: 27px;
  }
  section.lead {
    text-align: center;
  }
  h1 {
    color: #1d3557;
  }
  h2 {
    color: #1d3557;
  }
  pre {
    font-size: 0.62em;
    line-height: 1.3;
  }
  code {
    font-size: 0.9em;
  }
  table {
    font-size: 0.7em;
  }
  blockquote {
    border-left: 6px solid #1d3557;
    padding-left: 0.6em;
    color: #333;
    font-size: 0.85em;
  }
---

<!-- _class: lead -->
<!-- _header: "" -->
<!-- _footer: "" -->

# Introduction to ROS 2

## Overview & Fundamental Concepts

Jazzy Jalisco · Simulated robots

Venture into WVU — Space Robotics

---

## Today

- **Morning (this session, ~2h):** lecture — what ROS 2 is, and the concepts every ROS 2 system is built from.
- **Afternoon (~2h):** hands-on — explore these concepts yourself, individually, in simulation.
- **Later this program:** write your own nodes, then deploy **Nav2** on a real robot.

Everything today runs in simulation, inside a WSL2 Ubuntu 24.04 environment or Docker.

---

## Agenda

1. What is ROS 2? Use cases, the "ROS graph"
2. **Nodes**
3. **Messages / Interfaces**
4. **Topics**
5. **Services**
6. **Actions**
7. **Parameters**
8. **TF2** (coordinate frames)
9. **Launch**
10. **Packages**, **Workspaces**, **Distributions**

We'll pause after almost every concept to run it live in a terminal.

---

## Before we start: sanity check

Open a terminal in your WSL2 Ubuntu 24.04 environment and run:

```bash
printenv ROS_DISTRO     # should print: jazzy
ros2 doctor             # checks your install for common problems
```

> **Try it:** if `ROS_DISTRO` is empty, you likely forgot to source ROS 2 —
> see step 6 of the install guide: `source /opt/ros/jazzy/setup.bash`.

We'll use **turtlesim**, a tiny 2D simulator that ships with `ros-jazzy-desktop`,
for almost every live demo today. No Gazebo, no GPU — it runs fine in WSL2.

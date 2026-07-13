---
title: Installing ROS 2 Jazzy on macOS with Docker
---

# Installing ROS 2 Jazzy on macOS with Docker

ROS 2 Jazzy does not provide native macOS packages. The simplest way to get a working
ROS 2 Jazzy environment on a Mac is to run it inside a container with **Docker
Desktop**, using the official ROS Docker image.

## 1. Install Docker Desktop

1. Download Docker Desktop for Mac:
   - Apple Silicon (M1/M2/M3/M4): <https://desktop.docker.com/mac/main/arm64/Docker.dmg>
   - Intel: <https://desktop.docker.com/mac/main/amd64/Docker.dmg>
2. Open the downloaded `Docker.dmg` and drag **Docker** into the **Applications**
   folder.
3. Launch **Docker** from Applications and complete the first-run setup (you can skip
   creating a Docker account if not needed).
4. Verify the install in a terminal:

   ```bash
   docker --version
   docker run hello-world
   ```

Official installation instructions: <https://docs.docker.com/desktop/setup/install/mac-install/>

## 2. Pull the ROS 2 Jazzy base image

```bash
docker pull osrf/ros:jazzy-desktop
```

This is the official ROS 2 Jazzy desktop image, built by the Open Source Robotics Foundation (OSRF).

Official ROS Docker images: <https://hub.docker.com/r/osrf/ros>
ROS documentation on using Docker: <https://docs.ros.org/en/jazzy/How-To-Guides/Run-2-nodes-in-single-or-separate-docker-containers.html>

## 3. Run a container

Start a persistent, named container:

```bash
docker run -it --name ros2_jazzy osrf/ros:jazzy-desktop bash
```

This drops you into a shell inside the container with ROS 2 Jazzy already sourced.
Leaving the container with `exit` stops it; restart and reattach later with:

```bash
docker start -ai ros2_jazzy
```

## 4. Test the install

With the container from step 3 running, open a **second terminal** on the Mac and
attach a second shell to the same container:

```bash
docker exec -it ros2_jazzy bash
```

In the first terminal:

```bash
ros2 run demo_nodes_cpp talker
```

In the second terminal:

```bash
ros2 run demo_nodes_py listener
```

If the listener prints messages received from the talker, the install works.

---
title: Installing ROS 2 Jazzy on WSL2
---

# Installing ROS 2 Jazzy on WSL2

ROS 2 **Jazzy Jalisco** targets **Ubuntu 24.04 (Noble)**. On Windows, the simplest way
to get a working Ubuntu 24.04 environment is the Windows Subsystem for Linux (WSL2) —
no dual-boot or separate virtual machine required.

## 1. Install WSL2 with Ubuntu 24.04

1. Open **PowerShell as Administrator**.
2. Run:

   ```powershell
   wsl --install -d Ubuntu-24.04
   ```

3. Restart Windows if prompted.
4. Launch **Ubuntu 24.04** from the Start menu and create your Linux username and
   password when asked.

Official instructions: <https://learn.microsoft.com/en-us/windows/wsl/install>

## 2. Update Ubuntu

Inside the Ubuntu terminal:

```bash
sudo apt update && sudo apt upgrade -y
```

## 3. Enable the Ubuntu Universe repository

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
```

## 4. Add the ROS 2 apt repository

```bash
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"
sudo apt install /tmp/ros2-apt-source.deb
```

## 5. Install ROS 2 Jazzy

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install ros-jazzy-desktop
sudo apt install ros-dev-tools
```

Official installation guide (this is the source for steps 2-5):
<https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>

## 6. Source ROS 2 in every new shell

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 7. Initialize rosdep

```bash
sudo rosdep init
rosdep update
```

Reference: <https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html>

## 8. Test the install

In one terminal:

```bash
ros2 run demo_nodes_cpp talker
```

In a second terminal (new terminal windows automatically reconnect to the same WSL
instance):

```bash
ros2 run demo_nodes_py listener
```

If the listener prints messages received from the talker, the install works.

## 9. GUI apps (RViz2, Gazebo)

Recent versions of WSL2 include **WSLg**, which lets Linux GUI applications (RViz2,
Gazebo, `rqt`, etc.) display directly on the Windows desktop with no extra setup.
If a GUI window fails to appear, make sure WSL is fully up to date:

```powershell
wsl --update
```

Official WSLg documentation: <https://github.com/microsoft/wslg>

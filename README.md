## Software-In-The-Loop (SITL) with ATMOS and PX4 Autopilot

To Setup SITL with ATMOS, please follow [this](https://atmos.discower.io/pages/Simulation/). 


### SITL with px4-mpc
To control ATMOS in simulation, [px4-mpc](https://github.com/riviere-robot-lab-nyu/px4-mpc) is a greate tool to use. Follow the instructions [here](https://github.com/riviere-robot-lab-nyu/px4-mpc?tab=readme-ov-file#setup) to install. 

### SITL with px4-mpc example
To run control in SITL with ATMOS and PX4 Autopilot, you will need at least 3 terminals: **Gazebo** environment that simulates robot and publishing states, **Micro-XRCE-DDS** agent to bridege ROS communication, and a **ros launch file** for mpc control. **[QGroundControl](https://atmos.discower.io/pages/PX4/#setting-up-qgroundcontrol)** might be helpful to change/check modes (offboard) of the robot, but it's not required.

### tmux example for SITL with px4-mpc 
```=shell
#!/bin/bash

docker start ros2-cuda-desktop-px4-autopilot-test
SESSION_NAME="${1:-px4-ws}"
tmux kill-session -t "$SESSION_NAME" 2>/dev/null

tmux new-session -d -s "$SESSION_NAME" 
tmux splitw -v
tmux splitw -v
tmux splitw -h


tmux send-keys -t "$SESSION_NAME:0.0" 'echo launch ros2 offboard control' Enter
tmux send-keys -t "$SESSION_NAME:0.0" 'docker exec -it ros2-cuda-desktop-px4-autopilot-test bash' Enter
tmux send-keys -t "$SESSION_NAME:0.0" 'cd /home/PX4-Autopilot-ros2-test/PX4-Autopilot' Enter

# source px4-mpc workspace (including offboard control and maybe px4-msgs)
tmux send-keys -t "$SESSION_NAME:0.0" 'source /home/PX4-Autopilot-ros2-test/px4-mpc/install/setup.bash' Enter
tmux send-keys -t "$SESSION_NAME:0.0" 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:"/home/PX4-Autopilot-ros2-test/acados/lib"' Enter
tmux send-keys -t "$SESSION_NAME:0.0" 'export ACADOS_SOURCE_DIR="/home/PX4-Autopilot-ros2-test/acados"' Enter
tmux send-keys -t "$SESSION_NAME:0.0" 'ros2 launch px4_mpc mpc_spacecraft_launch.py mode:=wrench namespace:=pop setpoint_from_rviz:=False' 
# tmux send-keys -t "$SESSION_NAME:0.0" 'ros2 launch px4_mpc mpc_quadrotor_launch.py'


tmux send-keys -t "$SESSION_NAME:0.1" 'echo run SITL' Enter
tmux send-keys -t "$SESSION_NAME:0.1" 'docker exec -it ros2-cuda-desktop-px4-autopilot-test bash' Enter
tmux send-keys -t "$SESSION_NAME:0.1" 'source /home/PX4-Autopilot-ros2-test/px4-mpc/install/setup.bash' Enter
tmux send-keys -t "$SESSION_NAME:0.1" 'cd /home/PX4-Autopilot-ros2-test/PX4-Autopilot' Enter
## drone example
# tmux send-keys -t "$SESSION_NAME:0.1" 'make px4_sitl gz_x500' Enter
# atmos example
tmux send-keys -t "$SESSION_NAME:0.1" 'PX4_UXRCE_DDS_NS=pop make px4_sitl_spacecraft gz_atmos' Enter

tmux send-keys -t "$SESSION_NAME:0.2" 'echo run MicroXRCEAgent' Enter
tmux send-keys -t "$SESSION_NAME:0.2" 'docker exec -it ros2-cuda-desktop-px4-autopilot-test bash' Enter
tmux send-keys -t "$SESSION_NAME:0.2" 'source /home/PX4-Autopilot-ros2-test/px4-mpc/install/setup.bash' Enter
tmux send-keys -t "$SESSION_NAME:0.2" 'cd /home/PX4-Autopilot-ros2-test' Enter
tmux send-keys -t "$SESSION_NAME:0.2" 'MicroXRCEAgent udp4 -p 8888' Enter 

tmux send-keys -t "$SESSION_NAME:0.3" 'echo run SITL' Enter
tmux send-keys -t "$SESSION_NAME:0.3" 'docker exec -it ros2-cuda-desktop-px4-autopilot-test bash' Enter
tmux send-keys -t "$SESSION_NAME:0.3" 'source /home/PX4-Autopilot-ros2-test/px4-mpc/install/setup.bash' Enter
tmux send-keys -t "$SESSION_NAME:0.3" 'cd /home/PX4-Autopilot-ros2-test/PX4-Autopilot' Enter
tmux send-keys -t "$SESSION_NAME:0.3" 'ros2 topic echo /pop/fmu/out/vehicle_odometry' 

# tmux send-keys -t "$SESSION_NAME:0.3" 'echo 4 run QGroundControl (local)' Enter
# tmux send-keys -t "$SESSION_NAME:0.3" 'cd /home/cpw/workspace/PX4-Autopilot' Enter
# tmux send-keys -t "$SESSION_NAME:0.3" './QGroundControl-x86_64.AppImage'

tmux attach -t "$SESSION_NAME"
```

### Notes
The main changes of this branch are just modifying ip to local host for SITL with ATMOS. [Check rc.sc_defaults and rc.uuv_defaults](https://github.com/PX4/PX4-Autopilot/compare/main...riviere-robot-lab-nyu:PX4-Autopilot:cpw-sitl-dev#diff-99a020cc41cfc24893ae4039591616722bfca58d798c8fa41a26a341baac9aaf). You can also use the [original repo](https://github.com/riviere-robot-lab-nyu/PX4-Autopilot/tree/main) and change these value manually.  

For general functionailty of PX4 Drone Autopilot, please refer to the [original repo](https://github.com/riviere-robot-lab-nyu/PX4-Autopilot/tree/main).
# trajectory_setpoint6dof → trajectory_setpoint changes

Subscribe to standard `trajectory_setpoint` (DDS-bridged) instead of `trajectory_setpoint6dof`.
Revert by swapping the commented-out lines back.

---

## PositionControl/PositionControl.hpp

```
// #include <uORB/topics/trajectory_setpoint6dof.h>
#include <uORB/topics/trajectory_setpoint.h>

// void setInputSetpoint(const trajectory_setpoint6dof_s &setpoint);
void setInputSetpoint(const trajectory_setpoint_s &setpoint);

// static const trajectory_setpoint6dof_s empty_trajectory_setpoint;
static const trajectory_setpoint_s empty_trajectory_setpoint;
```

## PositionControl/PositionControl.cpp

```
// const trajectory_setpoint6dof_s ScPositionControl::empty_trajectory_setpoint = {...6dof...};
const trajectory_setpoint_s ScPositionControl::empty_trajectory_setpoint = {0, {NAN,NAN,NAN}, {NAN,NAN,NAN}, {NAN,NAN,NAN}, {NAN,NAN,NAN}, NAN, NAN};

// void ScPositionControl::setInputSetpoint(const trajectory_setpoint6dof_s &setpoint)
// { _quat_sp = Quatf(setpoint.quaternion); }
void ScPositionControl::setInputSetpoint(const trajectory_setpoint_s &setpoint)
{
    // derives _quat_sp from setpoint.yaw (NaN yaw → NaN quaternion → hold attitude)
    if (PX4_ISFINITE(setpoint.yaw)) { _quat_sp = Quatf(Eulerf(0,0,setpoint.yaw)); }
    else                            { _quat_sp = Quatf(NAN,NAN,NAN,NAN); }
}
```

## SpacecraftPositionControl.hpp

```
// #include <uORB/topics/trajectory_setpoint6dof.h>
#include <uORB/topics/trajectory_setpoint.h>

// uORB::Subscription _trajectory_setpoint_sub{ORB_ID(trajectory_setpoint6dof)};
uORB::Subscription _trajectory_setpoint_sub{ORB_ID(trajectory_setpoint)};

// trajectory_setpoint6dof_s _setpoint{ScPositionControl::empty_trajectory_setpoint};
trajectory_setpoint_s     _setpoint{ScPositionControl::empty_trajectory_setpoint};

// trajectory_setpoint6dof_s generateFailsafeSetpoint(...);
trajectory_setpoint_s     generateFailsafeSetpoint(...);
```

## SpacecraftPositionControl.cpp

```
// trajectory_setpoint6dof_s SpacecraftPositionControl::generateFailsafeSetpoint(...)
trajectory_setpoint_s SpacecraftPositionControl::generateFailsafeSetpoint(...)

// trajectory_setpoint6dof_s failsafe_setpoint = ...
trajectory_setpoint_s failsafe_setpoint = ...

// Manual mode yaw: q_sp.copyTo(_setpoint.quaternion)  →  _setpoint.yaw = _manual_yaw_sp
```

---

## Python-side (no rebuild needed)

```python
# Use standard topic and message type — no change needed from original
self.trajectory_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', 10)

# Fix position setpoint: must be NaN for pure velocity control
sp.position = [float('nan'), float('nan'), float('nan')]  # was [0.0, 0.0, 0.0]
offboard_msg.position = False  # was True
offboard_msg.velocity = True
```

## Params to verify on vehicle

- `SPC_POS_P = 0`
- `SPC_POS_I = 0`
- `SPC_VEL_I = 0` (optional, prevents integral windup during testing)

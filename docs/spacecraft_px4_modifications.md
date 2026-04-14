# PX4 Spacecraft Modifications

Summary of changes made to support spacecraft (MAV_TYPE_SPACECRAFT_ORBITER = 45) operation.
All changes are conditional on `system_type == 45` or default to safe values (default parameter = 1.0),
so they do not affect any other vehicle type.

---

## 1. Control Allocator — Motor Output Limit (`CA_MOT_MAX_ALL`)

**Files changed:**
- `src/modules/control_allocator/module.yaml`
- `src/modules/control_allocator/ControlAllocator.hpp`
- `src/modules/control_allocator/ControlAllocator.cpp`

### What was added

A new parameter `CA_MOT_MAX_ALL` (float, 0.0–1.0, default 1.0) that applies a fractional upper
limit to the output of all motors simultaneously.

### Why

The spacecraft thrusters may need to be limited below 100% — e.g. to protect hardware during
testing, enforce a thrust ceiling, or match a calibrated operating range.

### How it works

Previously, the only way to limit motor output was to clip individual actuator setpoints after
the control allocation solver had already produced its solution. This is incorrect because the
solver (especially `ControlAllocationSequentialDesaturation`) computes a globally optimal solution
assuming motors can reach 1.0. Post-hoc clipping of individual motors destroys this balance and
introduces unintended torques.

The correct approach is to inject the limit into `_actuator_max` before allocation runs. The
solver already uses `_actuator_max` as hard bounds in its desaturation loop, so it finds the
optimal solution within the constrained actuator space and properly scales the full
torque/thrust vector.

**Implementation:**

1. `parameters_updated()` — reads `CA_MOT_MAX_ALL` into `_motor_max_limit` before
   `update_effectiveness_matrix_if_needed()` is called, so the value is available when bounds
   are set.

2. `update_effectiveness_matrix_if_needed()` — sets `maximum[motor] = _motor_max_limit` (instead
   of the previous hardcoded `1.f`) for every motor actuator. For reversible motors,
   `minimum[motor] = -_motor_max_limit` is also applied. Servo and other actuator bounds remain
   at ±1.0 and are unaffected.

3. `publish_actuator_controls()` — the post-allocation `math::constrain()` clip that previously
   enforced the limit was removed. The solver now enforces the bounds natively.

**Parameter:**

| Parameter     | Type  | Range   | Default | Description                              |
|---------------|-------|---------|---------|------------------------------------------|
| `CA_MOT_MAX_ALL` | float | 0.0–1.0 | 1.0 | Fractional upper limit for all motors. 1.0 = full range (no change from default behaviour). |

---

## 2. Commander — Spacecraft Failsafe Navigation State Override

**File changed:** `src/modules/commander/Commander.cpp`

### What was added

Two blocks of code that intercept PX4's failsafe navigation state transitions and enforce
spacecraft-appropriate behaviour.

---

### 2a. Nav state override in `handleModeIntentionAndFailsafe()`

**Location:** Inside `Commander::handleModeIntentionAndFailsafe()`, after `_vehicle_status.failsafe`
is set and before `_mode_management.updateActiveConfigOverrides()`.

**What it does:**

After the failsafe framework sets `_vehicle_status.nav_state`, this block checks whether the
resulting state is one that has no meaning for a spacecraft (Land, Takeoff, VTOL Takeoff,
Precision Land, Descend, RTL) and overrides it to `NAVIGATION_STATE_AUTO_LOITER` (Hold).
`nav_state_display` is also updated so QGC shows the correct mode name.

**Why this location matters:**

The failsafe framework reasserts the nav state every Commander loop iteration for as long as the
failsafe condition (e.g. RC lost) remains active. An override placed only at publish time would
be undone on the next iteration before publish. Placing the override inside
`handleModeIntentionAndFailsafe()` — which runs every iteration and sets nav_state immediately
before it is consumed — means the override is applied each time the failsafe reasserts, and the
published state is always the overridden value.

`_vehicle_status.failsafe` is intentionally left `true` so QGC and telemetry still report that a
failsafe condition is active.

**Root cause of the cascade:**

PX4's failsafe framework cascades actions when a mode cannot run
(`framework.cpp`: Hold → RTL → Land → Descend). This cascade fires inside `_failsafe.update()`
before Commander can intervene. When the spacecraft has no position estimate (e.g. Mocap not
running during bench testing), Hold requires local position and fails the `modeCanRun()` check,
causing the cascade to Land/Descend. The override catches the final cascaded state regardless of
which step in the cascade produced it.

**Modes blocked:**

| nav_state blocked              | Reason                                      |
|-------------------------------|---------------------------------------------|
| `NAVIGATION_STATE_AUTO_LAND`   | No landing concept for spacecraft           |
| `NAVIGATION_STATE_AUTO_TAKEOFF`| No takeoff concept for spacecraft           |
| `NAVIGATION_STATE_AUTO_VTOL_TAKEOFF` | Not applicable                        |
| `NAVIGATION_STATE_AUTO_PRECLAND` | Not applicable                            |
| `NAVIGATION_STATE_DESCEND`     | Would command downward thrust               |
| `NAVIGATION_STATE_AUTO_RTL`    | No home position concept for spacecraft     |

---

### 2b. Motor kill during active failsafe

**Location:** Inside `Commander::run()`, in the `actuator_armed` assembly block, before
`actuator_armed` is published.

**What it does:**

When the vehicle is a spacecraft and `_vehicle_status.failsafe` is true, sets
`_actuator_armed.kill = true`. This instructs all output drivers to zero all motor outputs
immediately. When the failsafe clears (e.g. RC reconnects), `kill` is set back to `false`
automatically and normal motor operation resumes without requiring a rearm.

**Why:**

When the spacecraft enters the Hold/Loiter mode (from 2a above), the position controller
attempts to maintain position by commanding thrust. In a bench test environment without active
Mocap, or in a scenario where the operator has disconnected the controller intentionally, firing
thrusters is undesirable and potentially dangerous. Zeroing motor outputs during any failsafe
condition is the safe default for a spacecraft.

**Behaviour summary:**

| Condition                        | `kill` flag | Motor outputs |
|----------------------------------|-------------|---------------|
| Normal operation, no failsafe    | false       | Normal        |
| Failsafe active (e.g. RC lost)   | true        | All zero      |
| Failsafe cleared (RC reconnected)| false       | Normal        |

---

## Notes

- All spacecraft-specific guards check `_vehicle_status.system_type == 45`
  (`MAV_TYPE_SPACECRAFT_ORBITER`). This value is set from the `MAV_TYPE` parameter. The airframe
  file `70001_samtmos` sets `param set-default MAV_TYPE 45`. If using a different airframe or
  setting parameters manually in QGC, ensure `MAV_TYPE = 45` is set.
- `COM_RCL_EXCEPT` should be set to `6` (bits: Auto modes + Offboard) to suppress RC loss
  failsafe retriggering once the vehicle is already in an auto/offboard mode.
- `NAV_RCL_ACT` should be set to `1` (Hold) so that if the failsafe fires from a manual mode,
  the intended action is Hold rather than Return or Land.

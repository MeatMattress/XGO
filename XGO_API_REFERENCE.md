# XGO Robot API Reference

## ELECFREAKS CM4 XGO V2 — Complete Programming Guide

| Spec | Value |
|------|-------|
| **Model** | ELECFREAKS CM4 XGO V2 (with arm and gripper) |
| **DOF** | 15 — 12 leg servos + 3 arm/gripper servos |
| **CPU** | Raspberry Pi CM4, Quad-Core Cortex-A72 @ 1.5GHz |
| **RAM** | 4 GB |
| **Storage** | 32 GB Micro SD |
| **WiFi** | Dual-band 2.4GHz/5GHz + Bluetooth 5.0 |
| **OS** | Debian Buster (Python 3.9) |
| **Serial Port** | `/dev/ttyAMA0` @ 115200 baud |
| **Display** | 2-inch LCD, 320x240, SPI interface |
| **Camera** | USB camera (OpenCV compatible) |
| **AI Accelerator** | Google Coral EdgeTPU (USB) |

### Software Versions

| Package | Version | Location |
|---------|---------|----------|
| `xgo-pythonlib` | 0.3.5 | `~/.local/lib/python3.9/site-packages/` |
| `xgolib` | 1.4.2 | xgolib/__init__.py |
| `xgoedu` | 1.3.6 | xgoedu/__init__.py |
| `xgoscreen` | — | xgoscreen/LCD_2inch.py |

### Quick Start

```python
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0', version='xgolite')
dog.forward(15)
```

---

## Table of Contents

1. [Initialization & Connection](#1-initialization--connection)
2. [Movement Control](#2-movement-control)
3. [Body Pose: Translation](#3-body-pose-translation)
4. [Body Pose: Attitude (Rotation)](#4-body-pose-attitude-rotation)
5. [Periodic Motion](#5-periodic-motion)
6. [Leg Control](#6-leg-control)
7. [Servo/Motor Control](#7-servomotor-control)
8. [Gaits & Actions](#8-gaits--actions)
9. [Arm & Gripper Control](#9-arm--gripper-control)
10. [Sensors & Feedback](#10-sensors--feedback)
11. [LED Control](#11-led-control)
12. [Display (LCD)](#12-display-lcd)
13. [Audio](#13-audio)
14. [Camera & Vision](#14-camera--vision)
15. [AI & Education Functions (XGOEDU)](#15-ai--education-functions-xgoedu)
16. [Speech (Baidu Cloud API)](#16-speech-baidu-cloud-api)
17. [Coral EdgeTPU Integration](#17-coral-edgetpu-integration)
18. [Serial Protocol](#18-serial-protocol)
19. [Configuration & Utilities](#19-configuration--utilities)
20. [Safety Limits & Best Practices](#20-safety-limits--best-practices)
21. [Appendix A: Version-Specific Parameter Limits](#appendix-a-version-specific-parameter-limits)
22. [Appendix B: File System Layout](#appendix-b-file-system-layout)
23. [Appendix C: Helper Classes](#appendix-c-helper-classes)
24. [Appendix D: Troubleshooting](#appendix-d-troubleshooting)

---

## 1. Initialization & Connection

### `XGO(port, baud=115200, version="xgomini", verbose=False)`

Creates and initializes the robot connection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | str | — | Serial port path (e.g., `'/dev/ttyAMA0'`) |
| `baud` | int | 115200 | Baud rate |
| `version` | str | `"xgomini"` | Robot version: `"xgomini"`, `"xgolite"`, or `"xgorider"` |
| `verbose` | bool | False | Print serial TX/RX data for debugging |

**Behavior:**
1. Opens serial port `/dev/ttyAMA0` (hardcoded internally, ignores `port` param for connection but stores it)
2. Sleeps 0.25s for serial initialization
3. Reads firmware version via `read_firmware()` — first character determines version:
   - `'M'` → xgomini limits
   - `'L'` → xgolite limits
   - `'R'` → xgorider limits
4. Calls `reset()` (action 255 + 1s sleep)
5. Reads initial yaw angle for `turn_to()` reference
6. Sleeps 1s

**Total startup time: ~2.5 seconds**

```python
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0', version='xgolite')
print(dog.read_firmware())   # e.g., "L1.0"
print(dog.read_battery())    # e.g., 85
```

**Source:** `xgolib/__init__.py:175-201`

---

## 2. Movement Control

All velocity methods accept a `runtime` parameter. If `runtime > 0`, the method blocks for that duration then sends a stop command.

### `move_x(step, runtime=0)`

Move forward (positive) or backward (negative).

| Parameter | Type | Range | Unit |
|-----------|------|-------|------|
| `step` | float | [-25, 25] (Lite/Mini) | mm/s |
| `runtime` | float | >= 0 | seconds |

```python
dog.move_x(15)        # Walk forward at 15 mm/s
dog.move_x(-10)       # Walk backward at 10 mm/s
dog.move_x(20, 3)     # Walk forward for 3 seconds, then stop
```

### `move_y(step, runtime=0)`

Move left (positive) or right (negative).

| Parameter | Type | Range | Unit |
|-----------|------|-------|------|
| `step` | float | [-18, 18] (Lite/Mini) | mm/s |
| `runtime` | float | >= 0 | seconds |

```python
dog.move_y(10)   # Strafe left
dog.move_y(-10)  # Strafe right
```

### `turn(step, runtime=0)`

Rotate left (positive) or right (negative).

| Parameter | Type | Range | Unit |
|-----------|------|-------|------|
| `step` | float | [-100, 100] (Lite/Mini) | deg/s |
| `runtime` | float | >= 0 | seconds |

```python
dog.turn(50)     # Rotate left at 50 deg/s
dog.turn(-50)    # Rotate right at 50 deg/s
```

### Convenience Methods

| Method | Equivalent |
|--------|-----------|
| `forward(step)` | `move_x(abs(step))` |
| `back(step)` | `move_x(-abs(step))` |
| `left(step)` | `move_y(abs(step))` |
| `right(step)` | `move_y(-abs(step))` |
| `turnleft(step)` | `turn(abs(step))` |
| `turnright(step)` | `turn(-abs(step))` |
| `move(direction, step)` | `move_x(step)` if direction='x', `move_y(step)` if direction='y' |

### `stop()`

Stops all movement. Sends: `move_x(0)`, `move_y(0)`, `mark_time(0)`, `turn(0)`.

```python
dog.stop()
```

### Distance-Based Movement

#### `move_x_by(distance, vx=18, k=0.035, mintime=0.55)`

Move forward/backward by a computed distance. Blocks until complete.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `distance` | float | — | Distance to travel (sign = direction) |
| `vx` | float | 18 | Velocity magnitude |
| `k` | float | 0.035 | Time scaling factor |
| `mintime` | float | 0.55 | Minimum movement time |

Runtime formula: `k * abs(distance) + mintime`

#### `move_y_by(distance, vy=18, k=0.0373, mintime=0.5)`

Move left/right by a computed distance. Same pattern as `move_x_by`.

#### `turn_by(theta, mintime, vyaw=16, k=0.08)`

Turn by a specified angle. Blocks until complete.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `theta` | float | — | Angle to turn (sign = direction) |
| `mintime` | float | — | Minimum turn time |
| `vyaw` | float | 16 | Rotation speed |
| `k` | float | 0.08 | Time scaling factor |

#### `turn_to(theta, vyaw=60, emax=10)`

Turn to an absolute angle using IMU feedback loop. References the initial yaw read at startup.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `theta` | float | — | Target angle relative to init_yaw |
| `vyaw` | float | 60 | Rotation speed |
| `emax` | float | 10 | Error tolerance (degrees) |

```python
dog.turn_to(90)    # Turn to 90 degrees from initial heading
dog.turn_to(-45)   # Turn to -45 degrees from initial heading
```

**Source:** `xgolib/__init__.py:236-324`

---

## 3. Body Pose: Translation

### `translation(direction, data)`

Shift the body position while keeping feet stationary.

| Parameter | Type | Description |
|-----------|------|-------------|
| `direction` | str or list | `'x'`, `'y'`, `'z'` or list like `['x','y','z']` |
| `data` | float or list | Position value(s) |

**Ranges (XGO-Lite):**

| Axis | Range | Unit | Description |
|------|-------|------|-------------|
| X | [-25, 25] | mm | Forward/backward body shift |
| Y | [-18, 18] | mm | Left/right body shift |
| Z | [60, 110] | mm | Body height |

**Ranges (XGO-Mini):**

| Axis | Range | Unit | Description |
|------|-------|------|-------------|
| X | [-35, 35] | mm | Forward/backward body shift |
| Y | [-19.5, 19.5] | mm | Left/right body shift |
| Z | [75, 120] | mm | Body height |

```python
# Single axis
dog.translation('z', 85)              # Set height to 85mm

# Multiple axes at once
dog.translation(['x', 'y', 'z'], [10, 5, 90])

# Reset to default height
dog.translation('z', 85)  # Lite default ~85mm
```

**Source:** `xgolib/__init__.py:326-346`

---

## 4. Body Pose: Attitude (Rotation)

### `attitude(direction, data)`

Rotate the body while keeping feet stationary.

| Parameter | Type | Description |
|-----------|------|-------------|
| `direction` | str or list | `'r'` (roll), `'p'` (pitch), `'y'` (yaw), or list |
| `data` | float or list | Angle value(s) in degrees |

**Ranges (XGO-Lite):**

| Axis | Range | Unit |
|------|-------|------|
| Roll (r) | [-20, 20] | degrees |
| Pitch (p) | [-10, 10] | degrees |
| Yaw (y) | [-12, 12] | degrees |

**Ranges (XGO-Mini):**

| Axis | Range | Unit |
|------|-------|------|
| Roll (r) | [-20, 20] | degrees |
| Pitch (p) | [-22, 22] | degrees |
| Yaw (y) | [-16, 16] | degrees |

```python
dog.attitude('r', 10)                      # Tilt 10 degrees right
dog.attitude('p', -5)                      # Pitch forward 5 degrees
dog.attitude(['r', 'p', 'y'], [5, -3, 8]) # Combined
```

**Source:** `xgolib/__init__.py:348-368`

---

## 5. Periodic Motion

### `periodic_rot(direction, period)`

Make the body oscillate rotationally.

| Parameter | Type | Description |
|-----------|------|-------------|
| `direction` | str or list | `'r'`, `'p'`, `'y'`, or list |
| `period` | float or list | Period in seconds [1.5, 8], or 0 to stop |

```python
dog.periodic_rot('p', 3)   # Pitch oscillation, 3-second period
dog.periodic_rot('p', 0)   # Stop
```

### `periodic_tran(direction, period)`

Make the body oscillate translationally.

| Parameter | Type | Description |
|-----------|------|-------------|
| `direction` | str or list | `'x'`, `'y'`, `'z'`, or list |
| `period` | float or list | Period in seconds [1.5, 8], or 0 to stop |

```python
dog.periodic_tran('z', 2)  # Bounce up/down, 2-second period
dog.periodic_tran('z', 0)  # Stop
```

### `mark_time(data)`

March in place (lift legs rhythmically).

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `data` | float | Lite: [10, 25], Mini: [10, 35], or 0 | Step height in mm, 0 to stop |

```python
dog.mark_time(15)  # March with 15mm step height
dog.mark_time(0)   # Stop marching
```

**Source:** `xgolib/__init__.py:471-530`

---

## 6. Leg Control

### `leg(leg_id, data)`

Control individual leg position in 3D space.

| Parameter | Type | Description |
|-----------|------|-------------|
| `leg_id` | int | 1-4 |
| `data` | list[3] | [x, y, z] position |

**Leg Numbering:**

```
      FRONT
   1 ┌─────┐ 2
     │     │
     │     │
   3 └─────┘ 4
       REAR
```

| Leg | ID | Position |
|-----|------|----------|
| 1 | Front-Left | |
| 2 | Front-Right | |
| 3 | Rear-Left | |
| 4 | Rear-Right | |

**Position Ranges (XGO-Lite):**

| Axis | Range | Unit |
|------|-------|------|
| X | [-25, 25] | mm |
| Y | [-18, 18] | mm |
| Z | [60, 110] | mm |

**Position Ranges (XGO-Mini):**

| Axis | Range | Unit |
|------|-------|------|
| X | [-35, 35] | mm |
| Y | [-18, 18] | mm |
| Z | [75, 115] | mm |

```python
dog.leg(1, [0, 0, 80])    # Front-left leg to position [0, 0, 80]
dog.leg(2, [10, 5, 90])   # Front-right leg
```

**Source:** `xgolib/__init__.py:393-413`

---

## 7. Servo/Motor Control

### Motor ID Mapping

```
Leg 1 (Front-Left):   11=lower, 12=middle, 13=upper
Leg 2 (Front-Right):  21=lower, 22=middle, 23=upper
Leg 3 (Rear-Left):    31=lower, 32=middle, 33=upper
Leg 4 (Rear-Right):   41=lower, 42=middle, 43=upper
Arm:                   51=shoulder, 52=elbow, 53=gripper
```

Full MOTOR_ID list: `[11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51, 52, 53]`

### Motor Angle Limits (degrees)

**XGO-Lite:**

| Index | Motor Position | Range |
|-------|---------------|-------|
| 0 (x1) | Lower (per leg) | [-70, 50] |
| 1 (x2) | Middle (per leg) | [-70, 90] |
| 2 (x3) | Upper (per leg) | [-30, 30] |
| 3 (51) | Arm shoulder | [-65, 65] |
| 4 (52) | Arm elbow | [-115, 70] |
| 5 (53) | Arm gripper | [-85, 100] |

**XGO-Mini:**

| Index | Motor Position | Range |
|-------|---------------|-------|
| 0 (x1) | Lower (per leg) | [-73, 57] |
| 1 (x2) | Middle (per leg) | [-66, 93] |
| 2 (x3) | Upper (per leg) | [-31, 31] |
| 3 (51) | Arm shoulder | [-65, 65] |
| 4 (52) | Arm elbow | [-85, 50] |
| 5 (53) | Arm gripper | [-75, 90] |

### `motor(motor_id, data)`

Control individual servo(s).

| Parameter | Type | Description |
|-----------|------|-------------|
| `motor_id` | int or list[int] | Motor ID(s) from table above |
| `data` | float or list[float] | Angle(s) in degrees (within limits) |

```python
# Single motor
dog.motor(11, 20)                       # Leg 1 lower servo to 20 degrees

# Multiple motors
dog.motor([11, 12, 13], [10, -20, 5])   # Leg 1 all servos
```

**Note:** Motor 51 (claw/gripper) is internally redirected to `claw()` method.

### `motor_speed(speed)`

Set servo rotation speed. Only applies to individual servo control mode.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `speed` | int | 1-255 | Speed (1=slowest, 255=fastest, 0 treated as 1) |

```python
dog.motor_speed(50)   # Slow servo movement
dog.motor_speed(255)  # Maximum speed
```

### `unload_motor(leg_id)`

Disable torque for a specific leg or arm (robot will collapse on that limb).

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `leg_id` | int | 1-5 | 1-4 = legs, 5 = arm |

### `unload_allmotor()`

Disable torque on ALL servos. **WARNING: Robot will collapse!**

### `load_motor(leg_id)`

Re-enable torque for a specific leg or arm.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `leg_id` | int | 1-5 | 1-4 = legs, 5 = arm |

### `load_allmotor()`

Re-enable torque on all servos.

### `moveToMid()`

Move all servos to their center/neutral position.

**Source:** `xgolib/__init__.py:415-595, 863`

---

## 8. Gaits & Actions

### `pace(mode)`

Set step frequency.

| Mode | Value | Description |
|------|-------|-------------|
| `"normal"` | 0x00 | Default pace |
| `"slow"` | 0x01 | Slower steps |
| `"high"` | 0x02 | Faster steps |

### `gait_type(mode)`

Set walking gait.

| Mode | Value | Description |
|------|-------|-------------|
| `"trot"` | 0x00 | Diagonal legs move together (default) |
| `"walk"` | 0x01 | One leg at a time |
| `"high_walk"` | 0x02 | High-stepping walk |
| `"slow_trot"` | 0x03 | Slow trot |

### `imu(mode)`

Enable/disable self-stabilization (IMU balance).

| Parameter | Type | Value | Description |
|-----------|------|-------|-------------|
| `mode` | int | 0 | Disable self-balance |
| `mode` | int | 1 | Enable self-balance |

### `perform(mode)`

Enable/disable continuous action loop (cycles through preset actions).

| Parameter | Type | Value | Description |
|-----------|------|-------|-------------|
| `mode` | int | 0 | Stop performing |
| `mode` | int | 1 | Start cycling actions |

### `action(action_id, wait=False)`

Execute a preset action.

| Parameter | Type | Description |
|-----------|------|-------------|
| `action_id` | int | 1-255 (see table below) |
| `wait` | bool | If True, blocks for the action's duration |

### `reset()`

Reset all parameters to initial state. Calls `action(255)` then sleeps 1 second.

### Complete Action ID Table

| ID | Action | Duration (s) |
|----|--------|-------------|
| 1 | Get down | 3 |
| 2 | Stand up | 3 |
| 3 | Creep forward | 5 |
| 4 | Circle walk | 5 |
| 5 | Swing | 4 |
| 6 | Pee (raise leg) | 4 |
| 7 | Sit | 4 |
| 8 | Wave | 4 |
| 9 | Stretch | 4 |
| 10 | Wave (extended) | 7 |
| 11 | Pray / beg | 7 |
| 12 | Looking for food | 5 |
| 13 | Dance | 7 |
| 14 | Nod | 10 |
| 15 | Shake head | 6 |
| 16 | Warm up | 6 |
| 17 | High five | 4 |
| 18 | Hug | 6 |
| 19 | OK gesture | 10 |
| 20 | Push-up | 9 |
| 21 | Look around | 8 |
| 22 | Jump | 7 |
| 23 | Stand ready | 6 |
| 24 | Roll | 7 |
| 128 | Extended action 1 | 10 |
| 129 | Extended action 2 | 10 |
| 130 | Extended action 3 | 10 |
| 255 | Force reset | 1 |

**Note:** Action IDs 1-24 correspond to gesture recognition responses in the demo system (e.g., action 1 maps to "Good" gesture, action 19 to "OK" gesture). Action 20 (push-up) has a special animated sequence with intermediate z-translations in the demo code.

```python
dog.action(13)              # Dance (non-blocking)
dog.action(13, wait=True)   # Dance (blocks for 7 seconds)
dog.action(255)             # Force reset
```

**Source:** `xgolib/__init__.py:370-392, 532-581`

---

## 9. Arm & Gripper Control

The XGO V2 has a 3-DOF arm: shoulder (motor 51), elbow (motor 52), gripper (motor 53).

### `arm(arm_x, arm_z)`

Control arm position in Cartesian coordinates.

| Parameter | Type | Range | Unit |
|-----------|------|-------|------|
| `arm_x` | float | [-80, 155] | mm (forward/backward) |
| `arm_z` | float | [-95, 155] | mm (up/down) |

```python
dog.arm(50, 80)    # Arm forward and up
dog.arm(0, 0)      # Arm neutral
```

### `arm_polar(arm_theta, arm_r)`

Control arm position in polar coordinates.

| Parameter | Type | Range | Unit |
|-----------|------|-------|------|
| `arm_theta` | float | [70, 270] | degrees |
| `arm_r` | float | [80, 140] | mm (radius) |

```python
dog.arm_polar(170, 110)  # Arm at 170 degrees, 110mm reach
```

### `arm_mode(mode)`

Enable or disable arm control mode.

| Parameter | Type | Value | Description |
|-----------|------|-------|-------------|
| `mode` | int | 0x00 | Disable arm mode |
| `mode` | int | 0x01 | Enable arm mode |

### `arm_speed(speed)`

Set arm movement speed.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `speed` | int | 1-255 | 1=slowest, 255=fastest (0 treated as 1) |

### `claw(pos)`

Control gripper open/close position.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `pos` | int | 0-255 | 0=closed, 255=fully open |

```python
dog.claw(255)  # Open gripper
dog.claw(0)    # Close gripper
dog.claw(128)  # Half open
```

### Teaching Mode

#### `teach(mode, pos_id)`

Record or replay leg positions.

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `mode` | str | `"record"` or `"play"` | Mode |
| `pos_id` | int | position slot ID | Storage slot |

#### `teach_arm(mode, pos_id)`

Record or replay arm positions.

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `mode` | str | `"record"` or `"play"` | Mode |
| `pos_id` | int | position slot ID | Storage slot |

```python
# Record current arm position to slot 1
dog.teach_arm("record", 1)

# Replay stored position from slot 1
dog.teach_arm("play", 1)
```

**Source:** `xgolib/__init__.py:791-893`

---

## 10. Sensors & Feedback

### `read_battery()`

Returns battery level as integer 0-100 (percentage).

```python
level = dog.read_battery()  # e.g., 85
```

### `read_firmware()`

Returns firmware version string. First character identifies the variant.

```python
fw = dog.read_firmware()  # e.g., "L1.0" (L=Lite, M=Mini, R=Rider)
```

### `read_roll()`

Returns body roll angle in degrees (float, 2 decimal places).

### `read_pitch()`

Returns body pitch angle in degrees (float, 2 decimal places).

### `read_yaw()`

Returns body yaw angle in degrees (float, 2 decimal places).

### `read_imu()`

Returns full 9-axis IMU data as a list of 9 floats.

| Index | Value | Unit | Conversion |
|-------|-------|------|------------|
| 0-2 | Accelerometer (ax, ay, az) | m/s² | raw / 16384 * 9.8 |
| 3-5 | Gyroscope (gx, gy, gz) | deg/s | raw / 16.4 |
| 6-8 | Angles (roll, pitch, yaw) | radians | raw / 180 * π |

```python
imu = dog.read_imu()
ax, ay, az = imu[0], imu[1], imu[2]
gx, gy, gz = imu[3], imu[4], imu[5]
roll_rad, pitch_rad, yaw_rad = imu[6], imu[7], imu[8]
```

### `read_imu_int16(direction)`

Returns raw 16-bit integer IMU reading for one axis.

| Parameter | Type | Values |
|-----------|------|--------|
| `direction` | str | `"roll"`, `"pitch"`, or `"yaw"` |

### `read_motor()`

Returns list of 15 float values — angles for all servos in order: [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51, 52, 53].

```python
angles = dog.read_motor()  # List of 15 floats
```

### `read_lib_version()`

Returns the xgolib version string (e.g., `"1.4.2"`).

**Source:** `xgolib/__init__.py:611-759`

---

## 11. LED Control

### `rider_led(index, color)`

Control RGB LEDs. Primarily for the XGO Rider variant, but the command is available.

| Parameter | Type | Description |
|-----------|------|-------------|
| `index` | int | LED index |
| `color` | list[3] | [R, G, B] values, 0-255 each |

```python
dog.rider_led(0, [255, 0, 0])   # LED 0 to red
dog.rider_led(0, [0, 255, 0])   # LED 0 to green
```

**Serial address:** `0x68 + index`, data = 3 bytes [R, G, B].

**Source:** `xgolib/__init__.py:1097-1100`

---

## 12. Display (LCD)

The robot has a 2-inch LCD (240x320 pixels) driven over SPI. Two levels of API are available.

### High-Level API (XGOEDU class)

Requires: `from xgoedu import XGOEDU; edu = XGOEDU()`

#### `lcd_clear()`

Clear screen to black.

#### `lcd_text(x, y, content, color="WHITE", fontsize=15)`

Draw text at position.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | int | — | X position |
| `y` | int | — | Y position |
| `content` | str | — | Text to display |
| `color` | str | "WHITE" | Color name or hex |
| `fontsize` | int | 15 | Font size in points |

#### `lcd_line(x1, y1, x2, y2, color="WHITE", width=2)`

Draw a line from (x1,y1) to (x2,y2).

#### `lcd_circle(x1, y1, x2, y2, angle0, angle1, color="WHITE", width=2)`

Draw an arc within a bounding box.

#### `lcd_round(center_x, center_y, radius, color, width=2)`

Draw a circle by center and radius.

#### `lcd_rectangle(x1, y1, x2, y2, fill=None, outline="WHITE", width=2)`

Draw a rectangle.

#### `lcd_picture(filename, x=0, y=0)`

Display an image file. Loads from `/home/pi/xgoPictures/{filename}`.

#### `display_text_on_screen(content, color, start_x=2, start_y=2, font_size=20, screen_width=320, screen_height=240)`

Display paginated text that auto-wraps. Handles multi-page content with button navigation.

### Low-Level API (LCD_2inch class)

```python
import xgoscreen.LCD_2inch as LCD_2inch
display = LCD_2inch.LCD_2inch()
display.Init()
```

#### `Init()`

Initialize the display hardware (SPI + ST7789 controller setup).

#### `ShowImage(image, Xstart=0, Ystart=0)`

Display a PIL Image. Automatically converts RGB888 to RGB565. Handles both 240x320 (portrait) and 320x240 (landscape) images.

```python
from PIL import Image
img = Image.new("RGB", (320, 240), "blue")
display.ShowImage(img)
```

#### `SetWindows(Xstart, Ystart, Xend, Yend)`

Set the active display window region.

#### `clear()`

Clear display to white (fills with 0xFF).

### LCD Hardware Config

| Setting | Value |
|---------|-------|
| Resolution | 240x320 (portrait), used as 320x240 (landscape) |
| SPI Bus | 0, Device 0 |
| SPI Speed | 40 MHz |
| RST Pin | GPIO 27 |
| DC Pin | GPIO 25 |
| BL Pin | GPIO 0 (PWM backlight) |
| Color Format | RGB565 |
| Controller | ST7789 |

**Source:** `xgoscreen/LCD_2inch.py`, `xgoscreen/lcdconfig.py`, `xgoedu/__init__.py`

---

## 13. Audio

Requires XGOEDU: `from xgoedu import XGOEDU; edu = XGOEDU()`

### `xgoSpeaker(filename)`

Play an audio file from `/home/pi/xgoMusic/` using mplayer.

```python
edu.xgoSpeaker("bark.mp3")
```

### `xgoAudioRecord(filename="record", seconds=5)`

Record audio from microphone.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename` | str | "record" | Output filename (without extension) |
| `seconds` | int | 5 | Recording duration |

Output: `/home/pi/xgoMusic/{filename}.wav` (S32_LE, 8000Hz, mono)

### `xgoVideo(filename)`

Play a video file from `/home/pi/xgoVideos/` with LCD display and synchronized audio.

### `xgoVideoAudio(filename)`

Play only the audio track of a video file.

**Source:** `xgoedu/__init__.py`

---

## 14. Camera & Vision

Requires XGOEDU: `from xgoedu import XGOEDU; edu = XGOEDU()`

### Camera Control

#### `xgoCamera(switch)`

Toggle live camera preview on LCD.

| Parameter | Type | Description |
|-----------|------|-------------|
| `switch` | bool | True=start preview, False=stop |

#### `xgoTakePhoto(filename="photo")`

Capture a single photo. Saved to `/home/pi/xgoPictures/{filename}.jpg`.

#### `xgoVideoRecord(filename="record", seconds=5)`

Record video. Saved to `/home/pi/xgoVideos/{filename}.mp4` at 15fps.

#### `camera(filename="camera")`

Interactive camera mode. Button A=photo, Button B=video, Button C=exit.

### Vision Methods

All vision methods accept `target="camera"` (live camera) or a file path string.

#### `gestureRecognition(target="camera")`

Hand gesture detection using MediaPipe.

**Returns:** `(gesture_name, center_position)` or `None`

| Gesture | Description |
|---------|-------------|
| `'Good'` | Thumbs up |
| `'Ok'` | OK sign |
| `'Rock'` | Rock gesture |
| `'Stone'` | Fist |
| `'1'` | One finger |
| `'2'` | Two fingers |
| `'3'` | Three fingers |
| `'4'` | Four fingers |
| `'5'` | Open hand |

```python
result = edu.gestureRecognition()
if result:
    gesture, position = result
    print(f"Detected: {gesture} at {position}")
```

#### `yoloFast(target="camera")`

YOLO v5 object detection (ONNX model at `/home/pi/model/Model.onnx`).

**Returns:** `(class_name, (x, y))` or `None`

Detects 80 COCO classes: person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant, bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors, teddy bear, hair drier, toothbrush.

#### `face_detect(target="camera")`

Face detection using MediaPipe.

**Returns:** `[x, y, w, h]` bounding rectangle or `None`

Detected landmarks: left_eye, right_eye, nose, mouth, left_ear, right_ear.

#### `emotion(target="camera")`

Emotion classification on detected faces.

**Returns:** `(emotion_label, (x, y))` or `None`

| Emotion Labels |
|---------------|
| `'Angry'` |
| `'Happy'` |
| `'Neutral'` |
| `'Sad'` |
| `'Surprise'` |

#### `agesex(target="camera")`

Age and gender classification.

**Returns:** `(gender, age_range, (x, y))` or `None`

| Gender | Age Ranges |
|--------|-----------|
| `'Male'` | `'(0-2)'`, `'(4-6)'`, `'(8-12)'`, `'(15-20)'`, `'(25-32)'`, `'(38-43)'`, `'(48-53)'`, `'(60-100)'` |
| `'Female'` | Same ranges |

#### `posenetRecognition(target="camera")`

Skeleton/pose detection using MediaPipe Pose.

**Returns:** List of 4 joint angles `[ankle, knee, hip, shoulder]` or `None`

#### `QRRecognition(target="camera")`

QR code and barcode decoding using pyzbar.

**Returns:** List of decoded strings.

```python
codes = edu.QRRecognition()
# e.g., ["https://example.com"]
```

#### `ColorRecognition(target="camera", mode='R')`

Color blob detection in HSV space.

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `mode` | str | `'R'`, `'G'`, `'B'`, `'Y'` | Red, Green, Blue, Yellow |

**Returns:** `((x, y), radius)` or `None`

#### `BallRecognition(color_mask, target="camera", p1=36, p2=15, minR=6, maxR=35)`

Circular object detection using HoughCircles.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `color_mask` | — | — | Color mask from `cap_color_mask()` |
| `p1` | int | 36 | Canny edge upper threshold |
| `p2` | int | 15 | Circle accumulator threshold |
| `minR` | int | 6 | Minimum circle radius |
| `maxR` | int | 35 | Maximum circle radius |

**Returns:** `(x, y, radius)` tuple.

#### `cap_color_mask(position=None, scale=25, h_error=20, s_limit=[90, 255], v_limit=[90, 230])`

Interactive color range calibration tool. Returns HSV color bounds `[lower, upper]` for use with `BallRecognition`.

**Source:** `xgoedu/__init__.py`

---

## 15. AI & Education Functions (XGOEDU)

### `XGOEDU()`

Constructor — initializes LCD display (320x240), GPIO buttons, loads font.

**Attributes:**

| Attribute | Description |
|-----------|-------------|
| `display` | LCD_2inch display object |
| `splash` | PIL Image (320x240) for drawing |
| `draw` | PIL ImageDraw for drawing |
| `font` | TrueType font (msyh.ttc, 15pt) |
| `key1` | GPIO 17 (Button A) |
| `key2` | GPIO 22 (Button B) |
| `key3` | GPIO 23 (Button C) |
| `key4` | GPIO 24 (Button D) |

### `xgoButton(button)`

Read button state.

| Parameter | Type | Values | GPIO |
|-----------|------|--------|------|
| `button` | str | `'a'` | 17 |
| | | `'b'` | 22 |
| | | `'c'` | 23 |
| | | `'d'` | 24 |

**Returns:** `True` (pressed) or `False` (not pressed). Includes 20ms debounce.

```python
if edu.xgoButton('a'):
    print("Button A pressed!")
```

### OpenCV Drawing Helpers

These draw directly on OpenCV frames (not the LCD):

- `rectangle(frame, z, colors, size)` — Draw rectangle on frame
- `circle(frame, xy, rad, colors, tk)` — Draw circle on frame
- `text(frame, text, xy, font_size, colors, size)` — Draw text on frame
- `cv2AddChineseText(img, text, position, textColor=(0, 255, 0), textSize=30)` — Draw Chinese/Unicode text using PIL

**Source:** `xgoedu/__init__.py`

---

## 16. Speech (Baidu Cloud API)

Requires XGOEDU and internet connection.

### `SpeechRecognition(seconds=3)`

Record audio and convert to text via Baidu ASR API.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seconds` | int | 3 | Recording duration |

**Returns:** Recognized text string.

**Config:** DEV_PID=1537 (Mandarin), 16kHz sample rate.

### `SpeechSynthesis(texts)`

Convert text to speech via Baidu TTS API. Plays audio through speaker.

| Parameter | Type | Description |
|-----------|------|-------------|
| `texts` | str | Text to synthesize |

**Config:** PER=0 (female voice), SPD=5, PIT=5, VOL=5. Output: `/home/pi/xgoMusic/result.wav`.

**Note:** Both methods require valid Baidu API credentials configured in the source.

**Source:** `xgoedu/__init__.py`

---

## 17. Coral EdgeTPU Integration

### Overview

The robot has a Google Coral EdgeTPU USB accelerator for running quantized TFLite models. The primary integration is YOLO-based object detection.

### EdgeTPUModel Class

**File:** `/home/pi/edgetpu-yolo/edgetpumodel.py`

#### Constructor

```python
from edgetpumodel import EdgeTPUModel

model = EdgeTPUModel(
    model_file='/home/pi/edgetpu-yolo/yolov5s-int8_edgetpu_160.tflite',
    names_file='/home/pi/edgetpu-yolo/data/coco.yaml',
    conf_thresh=0.25,
    iou_thresh=0.45,
    filter_classes=None,
    agnostic_nms=False,
    max_det=1000,
    v8=False
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_file` | str | — | Path to EdgeTPU-compiled .tflite model |
| `names_file` | str | — | Path to YAML class names file |
| `conf_thresh` | float | 0.25 | Detection confidence threshold |
| `iou_thresh` | float | 0.45 | NMS IoU threshold |
| `filter_classes` | list | None | Only output specific classes |
| `agnostic_nms` | bool | False | Class-agnostic NMS |
| `max_det` | int | 1000 | Maximum detections |
| `v8` | bool | False | Set True for YOLOv8 models |

#### `forward(x, with_nms=True)`

Run inference on an image tensor.

| Parameter | Type | Description |
|-----------|------|-------------|
| `x` | np.ndarray | Image tensor (C,H,W) or (H,W,C), float32 [0,1] |
| `with_nms` | bool | Apply NMS post-processing |

**Returns:** Detection array `[x1, y1, x2, y2, confidence, class_id]` per detection.

**Quantization:** Input is scaled via `(x / input_scale) + input_zero`. YOLOv5 uses uint8, YOLOv8 uses int8.

#### `predict(image_path, save_img=True, save_txt=True)`

End-to-end prediction from file path. Saves annotated image and JSON results.

#### `get_image_size()`

Returns expected model input dimensions as `(height, width)`.

#### `get_last_inference_time(with_nms=True)`

Returns list `[inference_time]` or `[inference_time, nms_time]` in seconds.

#### `get_scaled_coords(xyxy, output_image, pad)`

Rescale bounding boxes from model input coordinates to original image coordinates.

#### `process_predictions(det, output_image, pad, output_path, save_img=True, save_txt=True, hide_labels=False, hide_conf=False)`

Post-process detections with optional visualization and file output.

### Available TFLite Models

Located in `/home/pi/edgetpu-yolo/`:

| Model | Resolution | File | Notes |
|-------|-----------|------|-------|
| YOLOv5s | 160x160 | `yolov5s-int8_edgetpu_160.tflite` | Fastest |
| YOLOv5n | 160x160 | `yolov5n-int8_edgetpu_160.tflite` | Nano variant |
| YOLOv5s | 192x192 | `yolov5s-int8_edgetpu_192.tflite` | |
| YOLOv5s | 224x224 | `yolov5s-int8_edgetpu_224.tflite` | Most accurate v5 |
| YOLOv8n | 160x160 | `yolov8n_full_integer_quant_edgetpu_160.tflite` | v8=True |
| YOLOv8n | 192x192 | `yolov8n_full_integer_quant_edgetpu_192.tflite` | v8=True |
| YOLOv8s | 160x160 | `yolov8s_full_integer_quant_edgetpu_160.tflite` | v8=True |
| YOLOv8s | 192x192 | `yolov8s_full_integer_quant_edgetpu_192.tflite` | v8=True |

All models detect 80 COCO classes. Class 0 = person.

### Robot Integration Patterns

#### Pattern 1: Gripper Control on Detection (clawYolo.py)

Threaded architecture: detection thread + control thread. Close gripper when person detected.

```python
import threading
from edgetpumodel import EdgeTPUModel
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0', version='xgolite')
model = EdgeTPUModel('yolov5s-int8_edgetpu_160.tflite', 'data/coco.yaml')

# Detection thread sets shared flag
# Control thread reads flag:
if person_detected:
    dog.claw(0)      # Close
else:
    dog.claw(255)    # Open
```

#### Pattern 2: Follow-Me Person Tracking (followMe.py)

Person tracking with bounding box center for steering. Deadzone of ±20 pixels from frame center.

```python
frame_center_x = 160
if person_detected:
    bbox_center_x = (x1 + x2) // 2
    if bbox_center_x < frame_center_x - 20:
        dog.turn(-50)      # Turn left
    elif bbox_center_x > frame_center_x + 20:
        dog.turn(50)       # Turn right
    else:
        dog.move('x', 5)   # Move forward
else:
    dog.stop()
```

#### Pattern 3: DetectionSystem with LCD (detect.py)

Full detection pipeline with live LCD display output.

```python
from edgetpumodel import EdgeTPUModel
import xgoscreen.LCD_2inch as LCD_2inch

display = LCD_2inch.LCD_2inch()
display.Init()
model = EdgeTPUModel(model_path, names_path)

# Continuous loop:
preds = model.forward(net_image)
# Display annotated frame on LCD:
display.ShowImage(pil_image)
```

### Alternative Inference Backends

| Backend | File | Description |
|---------|------|-------------|
| MediaPipe + EdgeTPU | `image_dete.py` | Uses `tflite_support` with `enable_edgetpu=True` |
| TFLite Runtime direct | `yoloFastNew.py` | `load_delegate('libedgetpu.so.1.0')` |
| ONNX Runtime (CPU) | `yolofast.py` | ONNX model at `/home/pi/model/Model.onnx`, no EdgeTPU |

### Pycoral Library

The Coral SDK is installed at `/home/pi/coral/pycoral/`.

Key functions:
- `pycoral.utils.edgetpu.make_interpreter(model_path)` — Create EdgeTPU interpreter
- `pycoral.adapters.common.input_size(interpreter)` — Get model input dimensions
- `pycoral.adapters.common.output_tensor(interpreter, index)` — Get output tensor
- Device selection: `None` (auto), `":N"` (Nth device), `"usb"`, `"pci"`

**Source:** `/home/pi/edgetpu-yolo/edgetpumodel.py`, `/home/pi/CustomXGO/clawYolo.py`, `/home/pi/CustomXGO/followMe.py`

---

## 18. Serial Protocol

### UART Protocol

The XGO library communicates with the servo controller MCU over UART.

| Setting | Value |
|---------|-------|
| Port | `/dev/ttyAMA0` |
| Baud Rate | 115200 |
| Data Bits | 8 |
| Stop Bits | 1 |
| Parity | None |

### Write Frame Format

```
[0x55] [0x00] [LEN] [MODE] [ADDR] [DATA...] [CHECKSUM] [0x00] [0xAA]
  │      │      │      │      │       │          │         │      │
  │      │      │      │      │       │          │         │      └─ End byte
  │      │      │      │      │       │          │         └──────── Padding
  │      │      │      │      │       │          └────────────────── Checksum
  │      │      │      │      │       └───────────────────────────── Data payload
  │      │      │      │      └───────────────────────────────────── Command address
  │      │      │      └──────────────────────────────────────────── 0x01=write, 0x02=read
  │      │      └─────────────────────────────────────────────────── data_bytes + 8
  │      └────────────────────────────────────────────────────────── Fixed 0x00
  └───────────────────────────────────────────────────────────────── Start byte
```

**Checksum calculation:**
```
CHECKSUM = 255 - (LEN + MODE + ADDR + sum(DATA)) % 256
```

### Read Request Format

```
[0x55, 0x00, 0x09, 0x02, ADDR, READ_LEN, CHECKSUM, 0x00, 0xAA]
```

Response uses the same frame format with data payload.

### Command Address Table

| Address | Name | Data Len | R/W | Description |
|---------|------|----------|-----|-------------|
| 0x01 | BATTERY | 1 | R | Battery level (0-100) |
| 0x03 | PERFORM | 1 | W | Continuous action mode (0/1) |
| 0x04 | CALIBRATION | 1 | W | Software calibration (1=start, 0=end) |
| 0x05 | UPGRADE | 1 | W | Firmware upgrade trigger |
| 0x06 | SET_ORIGIN | 1 | W | Reset odometry origin |
| 0x07 | FIRMWARE_VERSION | 10 | R | Firmware version string |
| 0x09 | GAIT_TYPE | 1 | W | Gait selection (0-3) |
| 0x13 | BT_NAME | 1-10 | W | Bluetooth name (ASCII) |
| 0x20 | UNLOAD/LOAD_MOTOR | 1 | W | Motor torque control |
| 0x21 | TEACH_RECORD | 1 | W | Record teaching position |
| 0x22 | TEACH_PLAY | 1 | W | Play teaching position |
| 0x23 | TEACH_ARM_RECORD | 1 | W | Record arm position |
| 0x24 | TEACH_ARM_PLAY | 1 | W | Play arm position |
| 0x30 | VX | 1 | W | Forward velocity (128=zero) |
| 0x31 | VY | 1 | W | Lateral velocity (128=zero) |
| 0x32 | VYAW | 1 | W | Rotation velocity (128=zero) |
| 0x33 | TRANSLATION_X | 1 | W | Body X translation |
| 0x34 | TRANSLATION_Y | 1 | W | Body Y translation |
| 0x35 | TRANSLATION_Z | 1 | W | Body Z translation (height) |
| 0x36 | ATTITUDE_R | 1 | W | Body roll |
| 0x37 | ATTITUDE_P | 1 | W | Body pitch |
| 0x38 | ATTITUDE_Y | 1 | W | Body yaw |
| 0x39 | PERIODIC_ROT_R | 1 | W | Periodic roll |
| 0x3A | PERIODIC_ROT_P | 1 | W | Periodic pitch |
| 0x3B | PERIODIC_ROT_Y | 1 | W | Periodic yaw |
| 0x3C | MARK_TIME | 1 | W | March in place height |
| 0x3D | MOVE_MODE | 1 | W | Pace mode (0-2) |
| 0x3E | ACTION | 1 | W | Action ID trigger |
| 0x3F | MOVE_TO | 2 | W | Absolute position (int16) |
| 0x40-0x4B | LEG_POS | 12 | W | Leg positions (4 legs × 3 axes) |
| 0x50-0x5E | MOTOR_ANGLE | 15 | RW | 15 servo angles |
| 0x5C | MOTOR_SPEED | 1 | W | Servo speed (1-255) |
| 0x5F | MOVE_TO_MID | 1 | W | Center all servos |
| 0x61 | IMU | 1 | W | Self-stabilize on/off |
| 0x62 | ROLL | 4 | R | Roll angle (float32) |
| 0x63 | PITCH | 4 | R | Pitch angle (float32) |
| 0x64 | YAW | 4 | R | Yaw angle (float32) |
| 0x65 | IMU_DATA | 24 | R | Full IMU (9 values) |
| 0x66 | ROLL_INT16 | 2 | R | Roll (int16) |
| 0x67 | PITCH_INT16 | 2 | R | Pitch (int16) |
| 0x68 | YAW_INT16 | 2 | R | Yaw (int16) |
| 0x69 | LED_COLOR | 3 | W | RGB LED color |
| 0x71 | CLAW | 1 | W | Gripper position (0-255) |
| 0x72 | ARM_MODE | 1 | W | Arm enable (0/1) |
| 0x73 | ARM_X | 1 | W | Arm X position |
| 0x74 | ARM_Z | 1 | W | Arm Z position |
| 0x75 | ARM_SPEED | 1 | W | Arm speed (1-255) |
| 0x76 | ARM_THETA | 1 | W | Arm polar angle |
| 0x77 | ARM_R | 1 | W | Arm polar radius |
| 0x80 | PERIODIC_TRAN_X | 1 | W | Periodic X translation |
| 0x81 | PERIODIC_TRAN_Y | 1 | W | Periodic Y translation |
| 0x82 | PERIODIC_TRAN_Z | 1 | W | Periodic Z translation |
| 0x90 | OUTPUT_ANALOG | 1 | W | Analog output |
| 0x91 | OUTPUT_DIGITAL | 1 | W | Digital output |

### Data Encoding

All parameter values are encoded as unsigned bytes (0-255) using `conver2u8`:

```
byte_value = int(255 / (limit_max - limit_min) * (real_value - limit_min))
```

Velocity commands (VX, VY, VYAW) use 128 as the zero point (128 = stopped).

### TCP App Protocol (Flask Server)

The app server (`app_dogzilla.py`) uses a TCP protocol with hex ASCII framing:

```
$<TYPE><FUNC><LEN><DATA...><CHECKSUM>#
```

| Code | Function | Description |
|------|----------|-------------|
| 0x02 | Battery query | Returns battery level |
| 0x0F | Mode selection | Func 0-5 for different modes |
| 0x11 | Joystick | X/Y analog input |
| 0x12 | Button control | Direction buttons 1-6 |
| 0x13 | Step width | Adjust step size |
| 0x14 | Pace frequency | 1=slow, 2=normal, 3=high |
| 0x15 | IMU toggle | Self-stabilization on/off |
| 0x16 | Gait type | 0=trot, 1=walk |
| 0x17 | Calibration | Enter/exit calibration |
| 0x18-0x1A | Translation | X/Y/Z body translation |
| 0x20-0x25 | Attitude | Body pose angles |
| 0x31 | Action | Execute action ID |
| 0x32 | Perform | Continuous action on/off |
| 0x33 | Reset | Reset to defaults |
| 0x41 | Motor | Single motor control (3 params) |
| 0x51 | Leg | Leg control (leg 1-4, 3 params) |
| 0xAA | Calibration state | With 0x55 verification |

Checksum: `sum(all_fields) % 256`

**Source:** `xgolib/__init__.py:203-229, 664-738`, `/home/pi/RaspberryPi-CM4-main/app/app_dogzilla.py`

---

## 19. Configuration & Utilities

### `calibration(state)`

**WARNING: Use with extreme caution! This permanently alters servo offset positions.**

| Parameter | Type | Values |
|-----------|------|--------|
| `state` | str | `'start'` or `'end'` |

```python
dog.calibration('start')  # Enter calibration mode
# ... adjust servos manually ...
dog.calibration('end')    # Save and exit calibration
```

### `set_origin()`

Reset the odometry/position reference point.

### `move_to(data)`

Move to an absolute position (int16 encoded).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | int | Target position (signed 16-bit) |

### `bt_rename(name)`

Rename the Bluetooth interface.

| Parameter | Type | Constraints |
|-----------|------|------------|
| `name` | str | ASCII only, max 10 characters |

### `btRename(name)`

Alternative Bluetooth rename.

| Parameter | Type | Constraints |
|-----------|------|------------|
| `name` | str | Alphanumeric only, max 20 characters |

### `output_analog(data)`

Set analog output value.

### `output_digital(data)`

Set digital output value.

### `set_move_mintime(mintime)`

Set minimum movement time for distance-based movement methods.

| Parameter | Type | Default |
|-----------|------|---------|
| `mintime` | float | 0.65 |

### `upgrade(filename)`

**WARNING: Experimental — source code says "Do not use".**

Firmware upgrade procedure:
1. Sends upgrade command
2. Waits for 0x55 acknowledgment (10s timeout)
3. Changes baud to 350000
4. Sends binary firmware file
5. Changes baud back to 115200

**Source:** `xgolib/__init__.py:741-789, 935-953`

---

## 20. Safety Limits & Best Practices

### Always Use Cleanup

```python
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0', version='xgolite')
try:
    # ... your code ...
    dog.forward(15)
    time.sleep(3)
finally:
    dog.stop()
    dog.reset()
```

### Battery Monitoring

- Check `read_battery()` regularly
- Avoid operation below 20%
- Low battery causes erratic servo behavior

### Servo Protection

- All parameter values are **clamped** by the library — values outside limits are clipped to min/max
- `motor_speed(255)` is maximum speed; use lower values for controlled movement
- Avoid rapid back-and-forth commands without small delays (~50ms between sequential servo commands)
- `unload_allmotor()` drops the robot — only use when the robot is physically supported

### Calibration Warning

- `calibration('start')` / `calibration('end')` **permanently** modifies servo zero positions
- Only use when the robot is on a flat surface with legs properly positioned
- Incorrect calibration can cause the robot to walk crooked or damage servos

### Serial Port

- The serial port is **single-threaded** — do not share an XGO instance across threads without a mutex/lock
- Only one program should access `/dev/ttyAMA0` at a time
- The constructor takes ~2.5 seconds; create the XGO instance once and reuse it

### EdgeTPU

- 160px models are fastest (~30ms inference), 224px most accurate
- The EdgeTPU runs warm under continuous inference — allow brief pauses in tight loops
- Camera default resolution is 320x240

### Upgrade Warning

- The `upgrade()` method is marked as experimental/testing — **do not use** unless you have a known-good firmware file and understand the risks of bricking the servo controller

---

## Appendix A: Version-Specific Parameter Limits

### XGO-Lite

| Parameter | Limit |
|-----------|-------|
| Translation X | [-25, 25] mm |
| Translation Y | [-18, 18] mm |
| Translation Z | [60, 110] mm |
| Attitude Roll | [-20, 20] deg |
| Attitude Pitch | [-10, 10] deg |
| Attitude Yaw | [-12, 12] deg |
| Leg X | [-25, 25] mm |
| Leg Y | [-18, 18] mm |
| Leg Z | [60, 110] mm |
| Motor Lower | [-70, 50] deg |
| Motor Middle | [-70, 90] deg |
| Motor Upper | [-30, 30] deg |
| Arm Shoulder (51) | [-65, 65] deg |
| Arm Elbow (52) | [-115, 70] deg |
| Arm Gripper (53) | [-85, 100] deg |
| VX | [-25, 25] mm/s |
| VY | [-18, 18] mm/s |
| VYAW | [-100, 100] deg/s |
| Mark Time Height | [10, 25] mm |
| Period | [1.5, 8] seconds |
| Arm X | [-80, 155] mm |
| Arm Z | [-95, 155] mm |
| Arm Theta | [70, 270] deg |
| Arm R | [80, 140] mm |

### XGO-Mini

| Parameter | Limit |
|-----------|-------|
| Translation X | [-35, 35] mm |
| Translation Y | [-19.5, 19.5] mm |
| Translation Z | [75, 120] mm |
| Attitude Roll | [-20, 20] deg |
| Attitude Pitch | [-22, 22] deg |
| Attitude Yaw | [-16, 16] deg |
| Leg X | [-35, 35] mm |
| Leg Y | [-18, 18] mm |
| Leg Z | [75, 115] mm |
| Motor Lower | [-73, 57] deg |
| Motor Middle | [-66, 93] deg |
| Motor Upper | [-31, 31] deg |
| Arm Shoulder (51) | [-65, 65] deg |
| Arm Elbow (52) | [-85, 50] deg |
| Arm Gripper (53) | [-75, 90] deg |
| VX | [-25, 25] mm/s |
| VY | [-18, 18] mm/s |
| VYAW | [-100, 100] deg/s |
| Mark Time Height | [10, 35] mm |
| Period | [1.5, 8] seconds |
| Arm X | [-80, 155] mm |
| Arm Z | [-95, 155] mm |
| Arm Theta | [70, 270] deg |
| Arm R | [80, 140] mm |

### XGO-Rider

| Parameter | Limit |
|-----------|-------|
| Translation Z | [60, 120] mm |
| Attitude Roll | [-17, 17] deg |
| VX | [-1.5, 1.5] m/s |
| VY | [-1.0, 1.0] m/s |
| VYAW | [-360, 360] deg/s |

---

## Appendix B: File System Layout

```
/home/pi/
├── xgoMusic/                    # Audio files for xgoSpeaker()
├── xgoPictures/                 # Image files for lcd_picture() and xgoTakePhoto()
├── xgoVideos/                   # Video files for xgoVideo() and xgoVideoRecord()
├── model/
│   └── Model.onnx               # ONNX model for yoloFast()
├── edgetpu-yolo/                # EdgeTPU YOLO models and code
│   ├── edgetpumodel.py          # EdgeTPUModel class
│   ├── detect.py                # DetectionSystem with LCD
│   ├── testDetect.py            # Detection with bbox output
│   ├── nms.py                   # NMS implementation
│   ├── utils.py                 # Image preprocessing utilities
│   ├── data/coco.yaml           # COCO class names
│   ├── yolov5s-int8_edgetpu_*.tflite
│   ├── yolov5n-int8_edgetpu_*.tflite
│   └── yolov8*_edgetpu_*.tflite
├── CustomXGO/                   # Custom integration scripts
│   ├── clawYolo.py              # Gripper + detection
│   └── followMe.py              # Person following
├── RaspberryPi-CM4-main/        # Demo system and Flask app
│   ├── app/
│   │   ├── app_dogzilla.py      # Flask server + TCP protocol
│   │   └── DOGZILLALib.py       # DOGZILLA class (alternative API)
│   └── demos/                   # Demo scripts
├── coral/pycoral/               # Google Coral pycoral SDK
└── .local/lib/python3.9/site-packages/
    ├── xgolib/__init__.py       # XGO main library (v1.4.2)
    ├── xgoedu/__init__.py       # Education library (v1.3.6)
    └── xgoscreen/
        ├── LCD_2inch.py         # LCD display driver
        └── lcdconfig.py         # SPI/GPIO configuration
```

---

## Appendix C: Helper Classes

### `hands` Class (xgoedu)

MediaPipe-based hand detection and gesture recognition.

| Method | Returns | Description |
|--------|---------|-------------|
| `run(cv_img)` | list[dict] | Detect hands. Each dict: `center`, `rect`, `dlandmark`, `hand_angle`, `right_left` |
| `calc_palm_moment(image, landmarks)` | (x, y) | Hand centroid |
| `calc_bounding_rect(image, landmarks)` | [x1, y1, x2, y2] | Bounding rectangle |
| `hand_angle(hand_)` | list[5] | Finger angles [thumb, index, middle, ring, pinky] |
| `vector_2d_angle(v1, v2)` | float | Angle between 2D vectors |

### `yoloXgo` Class (xgoedu)

ONNX-based YOLO object detection.

| Method | Returns | Description |
|--------|---------|-------------|
| `run(img)` | list[dict] | Detect objects. Each dict: `classes`, `score`, `xywh` |
| `preprocess(src_img, size)` | np.ndarray | Resize and normalize |
| `nms(dets, thresh=0.45)` | filtered dets | Non-maximum suppression |

### `face_detection` Class (xgoedu)

MediaPipe-based face detection.

| Method | Returns | Description |
|--------|---------|-------------|
| `run(cv_img)` | list | Detect faces |
| `draw_detection(image, detection)` | dict | Extract landmarks: `id`, `score`, `rect`, `right_eye`, `left_eye`, `nose`, `mouth`, `right_ear`, `left_ear` |

---

## Appendix D: Troubleshooting

### Serial Port Permission Denied

```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

### Camera Not Found

```bash
# Check if camera is connected
ls /dev/video*
# Test with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### EdgeTPU Not Detected

```bash
# Check USB connection
lsusb | grep Google
# Should show: Google Inc. (or Global Unichip Corp.)

# Verify pycoral installation
python3 -c "import pycoral; print('OK')"

# Check delegate
python3 -c "from tflite_runtime.interpreter import load_delegate; load_delegate('libedgetpu.so.1.0'); print('OK')"
```

### Import Errors

```bash
# Check installed packages
pip3 show xgo-pythonlib
pip3 list | grep xgo

# Verify xgolib
python3 -c "from xgolib import XGO; print('OK')"

# Verify xgoedu (requires display hardware)
python3 -c "from xgoedu import XGOEDU; print('OK')"
```

### Robot Not Responding

1. Check battery level: `dog.read_battery()` — charge if below 20%
2. Check serial connection: `ls -la /dev/ttyAMA0`
3. Ensure no other process is using the serial port: `fuser /dev/ttyAMA0`
4. Try power cycling the robot
5. Check firmware: `dog.read_firmware()` — should return a valid version string

### LCD Display Black/White

```python
import xgoscreen.LCD_2inch as LCD_2inch
display = LCD_2inch.LCD_2inch()
display.Init()  # Must call Init() before ShowImage()
```

### Servo Jitter or Overheating

- Reduce command frequency (add 50ms sleep between commands)
- Lower `motor_speed()` to reduce strain
- Check battery — low voltage causes servo instability
- Use `unload_motor()` on unused limbs to reduce power draw

---
title: Building an Obstacle-Avoiding Rover
---

# Building an Obstacle-Avoiding Rover: Closing the Sense–Think–Act Loop

## 1. Overview and Objective

Every autonomous machine — from a robot vacuum to a self-driving car — runs the same fundamental cycle, repeated over and over.

> **Sense** the environment, **Think** about what to do and then **Act** on the world.

In this activity you will build this complete loop from scratch on a small robotic rover. By the end of the session, your rover will drive around the room on its own, exploring the environment and steering away from obstacles.

The rover consists of:

- An **Arduino Uno** microcontroller (the thinking device),
- An **Arduino Motor Shield** stacked on top of it (a dual H-bridge that lets the Arduino drive motors),
- Two **DC motors** with wheels (the actuator),
- Two **HC-SR04 ultrasonic rangefinders**, left and right (the sensors),
- A **battery** to power the motors.

You will progress in stages: first verifying the toolchain, then testing sensors and motors individually, and finally writing the program that ties everything together.

**By the end of this activity, you will be able to:**

1. Upload code to an Arduino and use the Serial Monitor for debugging.
2. Read distance measurements from an ultrasonic sensor using a library.
3. Use an H-bridge motor driver to control the speed and direction of DC motors.
4. Combine sensing and actuation with simple `if`/`else` logic to produce autonomous behavior.

---

## 2. Setup

### 2.1 Install the Arduino IDE

Download and install the Arduino IDE (version 2.x) from the official website:

- Download: <https://www.arduino.cc/en/software>
- Official installation instructions: <https://docs.arduino.cc/software/ide-v2/tutorials/getting-started/ide-v2-downloading-and-installing/>

Once installed, open the IDE, connect the Arduino Uno to the computer with the USB cable, and select the board and port under **Tools → Board: "Arduino Uno"** and **Tools → Port**.

### 2.2 Install the Ultrasonic library

The HC-SR04 sensor is easiest to use through a driver library. We will use the **Ultrasonic** library by **Erick Simões**.

1. In the Arduino IDE, open **Tools → Manage Libraries…**
2. Search for `Ultrasonic` and install the library by Erick Simões.

Official instructions on installing libraries: <https://docs.arduino.cc/software/ide-v2/tutorials/ide-v2-installing-a-library/>

Library homepage (for reference): <https://github.com/ErickSimoes/Ultrasonic>

---

## 3. Initial Tests

Before wiring anything, verify that code can be compiled and uploaded, and that the sensors work.

### 3.1 Blink

1. Open **File → Examples → 01.Basics → Blink**.
2. Make sure a standalone Arduino board (without the rover) is connected to the computer and click **Upload** (the right-arrow button).
3. Confirm that the built-in LED on the Arduino blinks once per second.

If the LED blinks, your toolchain works: the IDE compiles code, uploads it over USB, and the board runs it. If the upload fails, double-check the board and port selection under **Tools**.

The [Blink](https://docs.arduino.cc/built-in-examples/basics/Blink/) example program, reproduced below, shows the basic functionality and structure of an Arduino program.

The program logic is built around two functions. **`setup()`** runs once when the board powers on or resets, and is where pins and other one-time configuration go. **`loop()`** runs repeatedly after `setup()` finishes, and is where the board's ongoing behavior lives.

**`pinMode(pin, mode)`** configures a pin's role before it is used. The argument `LED_BUILTIN` is a constant that maps to `13`, the pin number to which the built-in LED is connected and `OUTPUT` tells the board that the pin will be driven by the program rather than read as an input.

**`digitalWrite(pin, value)`** sets a digital pin's voltage. `HIGH` drives the pin to 5 V (logic 1) and `LOW` drives it to 0 V (logic 0). A pin holds whatever state it was last written to — after `digitalWrite(LED_BUILTIN, HIGH)`, the pin stays HIGH indefinitely, not just for an instant, until another `digitalWrite()` call changes it.

**`delay(ms)`** pauses execution for the given number of milliseconds, blocking the rest of `loop()` from running until it returns.

```cpp
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}
```

### 3.2 Reading the ultrasonic sensors

The HC-SR04 measures distance by emitting a short ultrasonic burst and timing how long its echo takes to return. Each sensor has four pins:

| Sensor pin | Purpose |
|---|---|
| Vcc | 5 V power |
| Trig | Input: commands the sensor to send a burst |
| Echo | Output: reports the time of flight |
| GND | Ground |

Connect **both** sensors to the Arduino with female–male jumper cables (no breadboard needed):

| Sensor | Vcc | Trig | Echo | GND |
|---|---|---|---|---|
| **Right** | 5V | D7 | D6 | GND |
| **Left** | IOREF | D5 | D4 | GND |

> **Important:** Do **not** connect anything to pins 3, 8, 9, 11, 12, or 13 — these are used by the Motor Shield to control the motors. The IOREF pin is connected to the Arduino's 5 V supply, so it can power the second sensor without a breadboard.

Create a new sketch with the following code and upload it:

```cpp
#include <Ultrasonic.h>  // Load the library

// Arduino pins connected to each sensor's Trig and Echo pins
int RIGHT_TRIGGER_PIN = 7;
int RIGHT_ECHO_PIN    = 6;
int LEFT_TRIGGER_PIN  = 5;
int LEFT_ECHO_PIN     = 4;

// Threshold to determine if an object is close (in cm)
int CLOSE = 10; 

// Declare the two ultrasonic sensor objects
Ultrasonic uleft(LEFT_TRIGGER_PIN, LEFT_ECHO_PIN);
Ultrasonic uright(RIGHT_TRIGGER_PIN, RIGHT_ECHO_PIN);

void setup() {
  Serial.begin(9600); // Initialize serial port
}

void loop() {
  // Read the distances in centimeters and save to variables
  int left_dist  = uleft.read();
  int right_dist = uright.read();

  // Print both readings to the serial port
  Serial.print("L: ");
  Serial.print(left_dist);
  Serial.print(" cm   R: ");
  Serial.print(right_dist);
  Serial.println(" cm");

  // Print notices if something is close to either sensor
  if (left_dist <= CLOSE) {
    Serial.println("Object close to left sensor!");
  }
  if (right_dist <= CLOSE) {
    Serial.println("Object close to right sensor!");
  }

  delay(100);  // Wait 100 ms between readings
}
```

Open the **Serial Monitor** from the **Tools** menu (or the magnifying-glass icon on the top right of the IDE) and set the baud rate to **9600 baud**. Move your hand or an object in front of each sensor and watch the readings change. Verify that the left sensor changes the `L` value and the right sensor changes the `R` value to confirm which sensor is which.
Do not move on if you cannot see live distance readings from both sensors.

---

## 4. Motor Polarity Testing

A DC motor spins one way when a positive voltage is applied to its terminals, and the other way when the voltage is reversed. Before wiring the motors to the shield, you need to find out **which polarity makes each wheel drive the rover forward**.

The rovers we use have six wires, 4 for a wheel encoder sensor and 2 for powering the motor. In today's activity, we will use only the green and blue wires, which are used for driving the motor. Please leave the encoder wires disconnected.

Procedure:

1. Remove the wheels from the rover so it doesn't drive off the table during testing.
2. For each motor, one at a time, touch the motor's armature terminals (blue and green) directly to the battery terminals.
3. Observe which direction the shaft spins, and write down which wire on the positive battery terminal makes each wheel spin in the "rover forward" direction. Keep in mind that the left and right motors are mirrored, so "forward" corresponds to opposite shaft rotations on each side.

You will use these notes both for wiring the shield and for setting the direction pins in your code.

---

## 5. Motor Connection

### 5.1 How the Motor Shield works

The Arduino's digital pins can only supply about 20 mA — far too little for a motor. The **Arduino Motor Shield** solves this. It is a **dual H-bridge**: an arrangement of electronic switches that lets a small logic signal control a large current *and* reverse its polarity. The shield has two independent channels (A and B), one per motor, powered by the battery connected to the Arduino's DC jack (barrel plug).

Each channel is controlled by pins on the Arduino:

| Function | Channel A (left motor) | Channel B (right motor) |
|---|---|---|
| Direction (DIR) | 12 | 13 |
| Enable (on/off) | 3 | 11 |
| Brake | 9 | 8 |
| Current sensing | A0 | A1 |

The logic is simple:

- The **Enable** pin turns the channel on or off. When it is LOW, the motor is disconnected (all switches in the bridge open). When it is HIGH, the motor terminals are connected directly across the battery voltage and the motor runs at full power. Today we will only drive the motors fully on or fully off with `digitalWrite`, not at partial speed.
- The **DIR** pin selects polarity: positive voltage on the `+` terminal when HIGH, negative when LOW. This is what makes the motor spin forward or backward.
- When both **Brake** and **Enable** are HIGH, both motor terminals are shorted together, actively braking the motor. We won't need the brake today.

### 5.2 Wiring the motors

The motors connect to the blue **screw terminal block** on the shield (marked A+, A−, B+, B−).

1. Connect the **left motor** to terminals **A+** and **A−**: loosen the screw, insert the motor cable, and tighten. Connect the wires in the same polarity that, connected to the battery, makes the motor drive forward.
   > Please do not unscrew the terminals all the way. Screws dropped on the carpet are nearly impossible to find. If a screw is missing, ask the instructor rather than borrowing one from another shield.
2. Connect the **right motor** to terminals **B+** and **B−**, again noting the polarity that makes it drive forward.
3. Connect the **battery** to the Arduino's DC jack using the battery snap connector. The battery must be connected for the motors to spin properly. Tip: to save power and reduce electrical noise, disconnect the battery while writing code and reconnect it for testing.

### 5.3 Quick motor test

With the wheels still off, upload this short sketch and confirm that both motor shafts spin in the "forward" direction:

```cpp
void setup() {
  // Motor shield control pins
  pinMode(12, OUTPUT);  // DIRA (left motor direction)
  pinMode(13, OUTPUT);  // DIRB (right motor direction)
  pinMode(3, OUTPUT);   // ENA (left motor enable)
  pinMode(11, OUTPUT);  // ENB (right motor enable)
}

void loop() {
  // Adjust HIGH/LOW below according to your polarity notes
  digitalWrite(12, HIGH);  // Left motor forward
  digitalWrite(13, HIGH);  // Right motor forward

  digitalWrite(3, HIGH);   // Left motor on
  digitalWrite(11, HIGH);  // Right motor on
}
```

If a shaft spins the wrong way, either flip its DIR value in the code or swap the motor's wires on the screw terminal — pick one convention and stick with it. Make sure you can make both motors spin forward before moving on.

---

## 6. Closing the Loop

Now everything comes together: the sensors *sense*, your code *thinks*, and the motors *act*. Write a program that makes the rover explore the room while avoiding obstacles. A simple and effective strategy is:

- If there is an obstacle close to the **right** sensor and none close to the left, then **turn left**.
- If there is an obstacle close to the **left** sensor and none close to the right, then **turn right**.
- If there are obstacles close to **both** sensors, then **back up**.
- If there are **no** obstacles close to either sensor, then **go forward**.

To turn right in place, spin the left motor forward and the right motor backward.
The oposite motor directions will make the rover turn in place to the left.
You choose what "close" means (a threshold in centimeters, e.g. 10–20 cm). Experiment with different values and see how the rover behaves.

### Testing procedure

1. **Test with the wheels off first**, with the rover connected to the computer. Wave your hands in front of the sensors and watch the shafts respond. Use the Serial Monitor to print distances if the behavior is confusing.
2. When everything responds correctly, **disconnect the USB cable, attach the wheels, make sure the battery is connected**, and set the rover loose in a free area of the room.
3. Observe, tune, repeat: adjust `CLOSE` and the loop delay until the rover explores smoothly.

> **Pin 13 caution:** Pin 13 drives both the built-in LED *and* the channel B direction. Don't use the LED in your code, as it will interfere with the right motor.

### Ideas if you finish early

- Make the rover back up *and then turn* when both sensors see an obstacle, so it doesn't get stuck oscillating in corners.
- Slow down gradually as obstacles get closer, instead of using a single threshold.
- Print the rover's "decisions" (`FORWARD`, `TURN LEFT`, …) to the Serial Monitor while tethered, to debug the logic.

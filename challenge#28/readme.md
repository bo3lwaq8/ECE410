# Modeling and Simulating a Memristor

This project simulates a voltage-controlled memristor to demonstrate its fundamental electrical characteristics. The primary goal is to visualize the "pinched hysteresis loop" in the device's current-voltage (I-V) curve, which is the defining signature of a memristor.

---

## 1. The Memristor Model: Biolek Window Function

To accurately model the non-linear behavior of a real-world memristor, this simulation uses the model proposed by Biolek et al. This model is widely used because it effectively captures the physical boundary conditions of ion movement within the device.

The model is defined by two key equations:

**1. The Memristance Equation:** The total resistance (or "memristance," M) of the device is a function of an internal state variable, `x`. This state variable represents the normalized position of the boundary between doped (low resistance) and undoped (high resistance) regions of the material.

    M(x) = R_on * x + R_off * (1 - x)

    - `R_on`: The minimum resistance when the device is fully "ON" (`x=1`).
    - `R_off`: The maximum resistance when the device is fully "OFF" (`x=0`).

**2. The State Differential Equation:** The rate of change of the state variable `x` depends on the voltage `v(t)` applied across the device and a "window function" `f(x)` that accounts for non-linear ion drift at the boundaries.

    dx/dt = k * (v(t) - V_threshold)^α * f(x)

    - The `V_threshold` term ensures that the resistance only changes when the applied voltage exceeds a certain positive or negative threshold.
    - The window function `f(x) = 1 - (2x - 1)²` ensures that the change in resistance slows down as `x` approaches its limits of 0 or 1, realistically modeling the physical constraints of the device.

---

## 2. Simulation and Results

### How to Run
1.  Save the provided Python code as a file (e.g., `memristor_sim.py`).
2.  Ensure you have `numpy`, `scipy`, and `matplotlib` installed (`pip install numpy scipy matplotlib`).
3.  Run the script from your terminal:
    ```bash
    python memristor_sim.py
    ```
The script will generate and display the I-V curve plot.

### The Pinched Hysteresis Loop

![Memristor I-V Curve](iv_curve.png)

The simulation applies a sinusoidal voltage to the memristor model and plots the resulting current versus the voltage. The output is the characteristic **pinched hysteresis loop**.

**Analysis of the Curve:**

* **Hysteresis:** The I-V curve forms a loop, indicating that the device's resistance is not constant. For the same voltage value, the current can be different depending on the history of the voltage applied to it. This "memory" of past states is the core property of a memristor.
* **Pinched at the Origin:** The loop always passes through the origin (0V, 0A). This is a critical feature that distinguishes a memristor from other two-terminal non-linear devices. It signifies that if there is no applied voltage, there is no current, regardless of the memristor's resistance state.
* **Non-Linear Relationship:** The lobes of the curve are not simple straight lines, demonstrating the non-linear relationship between current and voltage as the internal resistance of the device changes.

This pinched hysteresis loop is the experimental "fingerprint" of a memristor. Its shape, size, and orientation provide deep insights into the device's switching thresholds, resistance range, and dynamic behavior, making it a powerful tool for characterizing these fundamental building blocks of future neuromorphic hardware.
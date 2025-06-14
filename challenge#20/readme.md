# SPICE Simulation of a 4x4 Resistive Crossbar

This project demonstrates how a resistive crossbar array can perform matrix-vector multiplication directly through its physical properties, a core concept in analog in-memory computing and neuromorphic engineering.

## 1. The Principle: Matrix-Vector Multiplication with Physics

A resistive crossbar array consists of a grid of horizontal "wordlines" and vertical "bitlines," with a resistive element at each intersection. This structure naturally performs the matrix-vector multiplication operation `I = G * V`.

-   **Input Vector (V):** Voltages are applied to the horizontal wordlines.
-   **Weight Matrix (G):** The synaptic weights are represented by the **conductance** (`G = 1/R`) of the resistor at each crosspoint.
-   **Output Vector (I):** According to **Kirchhoff's Current Law**, the total current flowing down each vertical bitline is the sum of the currents coming from each wordline through the resistors.

For a single output column `j`, the total current `I_j` is:

    I_j = I_1j + I_2j + I_3j + I_4j

According to **Ohm's Law**, the current through each resistor is `I_ij = V_i * G_ij` (since the output lines are held at 0V). Substituting this in gives:

    I_j = (V_1 * G_1j) + (V_2 * G_2j) + (V_3 * G_3j) + (V_4 * G_4j)

This is the definition of a dot product. When calculated for all four output columns, it becomes the full matrix-vector multiplication.

## 2. SPICE Implementation

The provided `crossbar.cir` file implements a 4x4 resistive crossbar in SPICE.

-   **Input Voltages:** Four DC voltage sources (`Vin1` to `Vin4`) represent the input vector.
-   **Resistor Array:** 16 resistors (`R11` to `R44`) form the weight matrix.
-   **Output Measurement:** Four 0V voltage sources (`Vout1` to `Vout4`) are used as ammeters to measure the current on each output bitline, which are held at a virtual ground.

## 3. Demonstration and Verification

To prove that the circuit works, we will perform a calculation manually and compare it to the SPICE simulation results.

### Manual Calculation

Let's define our input vector `V` and our weight matrix `G` (conductance).

**Input Vector `V`:**

    V = [1V, 2V, 0V, 1V]

**Conductance Matrix `G`:**
(Where `G=1` is a 1 Ohm resistor and `G=0` is a 1 GigaOhm resistor)

    G = [[1, 0, 1, 0],
         [0, 1, 0, 1],
         [1, 1, 0, 0],
         [0, 0, 1, 1]]

**Expected Output Current `I`:**
The current for each output column `j` is the sum of `V_i * G_ij` over all `i`.

* `I_1 = (1V*1) + (2V*0) + (0V*1) + (1V*0) = 1A`
* `I_2 = (1V*0) + (2V*1) + (0V*1) + (1V*0) = 2A`
* `I_3 = (1V*1) + (2V*0) + (0V*0) + (1V*1) = 2A`
* `I_4 = (1V*0) + (2V*1) + (0V*0) + (1V*1) = 3A`

Our expected output vector is `I = [1A, 2A, 2A, 3A]`.

### SPICE Simulation Results

To run the simulation, use a SPICE tool like LTspice or NGSPICE:

    ngspice crossbar.cir

The `.op` command will compute the DC operating point. The output will contain the currents flowing through the 0V sources on the output lines. You should see results very close to this:

    --- Operating Point ---
    I(Vout1):    1.000000e+00
    I(Vout2):    2.000000e+00
    I(Vout3):    2.000000e+00
    I(Vout4):    3.000000e+00

*(Note: Some SPICE simulators may show the current as negative due to direction conventions, but the magnitude will be the same.)*

This result confirms that the resistive crossbar has successfully performed the matrix-vector multiplication, demonstrating the power of in-memory analog computing.
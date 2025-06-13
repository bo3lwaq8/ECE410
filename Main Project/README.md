# ECE 410/510: Conv2D Hardware Accelerator Project

## Abstract / Project Summary

This repository documents the design, verification, and benchmarking of a custom hardware accelerator for a 5x5, 5-channel 2D convolutional layer. This project was undertaken for the ECE 410/510 course at Portland State University (Spring 2025) to explore the principles of HW/SW co-design in the context of modern AI/ML applications.

The project began with a software-first approach, profiling a TensorFlow/Keras-based CNN for COVID-19 X-ray classification to identify computational bottlenecks. The initial `Conv2D` layer was selected for hardware acceleration. The accelerator was designed in SystemVerilog, featuring a pipelined MAC unit, and was iteratively optimized. Verification was performed at multiple stages: initially with a Verilog testbench in Vivado and subsequently through a system-level Python `cocotb` co-simulation environment that included a custom SPI interface for communication.

The journey involved overcoming significant challenges, including Icarus Verilog compatibility issues, FPGA I/O limitations, and debugging complex FSM and clock-domain crossing logic. The final hardware, synthesized for a Xilinx Artix-7 FPGA, achieved a maximum frequency of **~101.51 MHz**. The hardware core demonstrated a **31.1x speedup** for the accelerated layer compared to a pure Python/NumPy implementation. This document details the entire workflow, from analysis and design to the final benchmarks and the valuable debugging experiences along the way.

## Development Note

The HDL code (SystemVerilog), Python testbenches (`cocotb`), and documentation in this project were developed with the significant assistance of a Large Language Model (LLM). This approach, encouraged by the course materials for rapid prototyping and "vibe coding," was instrumental in generating initial code structures, debugging complex issues, and refining the design through multiple iterations.

---

## Table of Contents
1.  [Project Goals & Success Criteria](#project-goals--success-criteria)
2.  [Repository Structure](#repository-structure)
3.  [Design Workflow & Evolution](#design-workflow--evolution)
    - [Week 2: Software Analysis](#week-2-software-analysis)
    - [Week 3-4: Initial Hardware Design & Verification](#week-3-4-initial-hardware-design--verification)
    - [Week 5: FPGA Synthesis & Implementation](#week-5-fpga-synthesis--implementation)
    - [Week 6: Iterative Design - Pipelining for Timing Closure](#week-6-iterative-design---pipelining-for-timing-closure)
    - [Week 8-9: System Integration & Co-Simulation](#week-8-9-system-integration--co-simulation)
4.  [Final Results & Benchmarks](#final-results--benchmarks)
    - [Hardware Performance Metrics](#hardware-performance-metrics)
    - [Software vs. Hardware Comparison](#software-vs-hardware-comparison)
    - [Resource Utilization](#resource-utilization)
5.  [How to Run the Simulations](#how-to-run-the-simulations)
    - [Vivado Functional Simulation (Direct DUT Test)](#vivado-functional-simulation-direct-dut-test)
    - [Cocotb Co-Simulation (Full SPI System Test)](#cocotb-co-simulation-full-spi-system-test)
6.  [Challenges & Debugging Journey](#challenges--debugging-journey)
7.  [Future Work & Potential Improvements](#future-work--potential-improvements)

---

## Project Goals & Success Criteria

This project was guided by the course's main success criteria [cite: w7_codefest.pdf], which are:

-   **Benchmark a software algorithm and identify bottlenecks.**
-   **Design, build, and test (in HDL) a custom hardware accelerator chiplet to remove the bottlenecks.**
-   **Synthesize the hardware design (FPGA or ASIC) and obtain relevant performance metrics.**
-   **Apply co-design and an iterative approach to improve the design.**
-   **Evaluate and benchmark the entire system (SW + HW + communication) and provide evidence of acceleration.**

## Repository Structure

-   **`conv5x5_core.sv`**: The core pipelined hardware module that performs a 5x5 MAC operation for a single channel. This is the computational heart of the accelerator.
-   **`conv5x5_wrapper.sv`**: A wrapper that orchestrates the `conv5x5_core` to process 5 channels sequentially.
-   **`spi_slave.sv`**: An SPI slave interface designed to receive data and control commands from a master, and to send back status and results. This module acts as the bridge between software and the hardware accelerator.
-   **`accelerator_system.sv`**: The top-level system module that integrates `spi_slave` and `conv5x5_wrapper`. This represents the final hardware system for co-simulation.
-   **`test_spi_accelerator.py`**: The `cocotb` Python testbench that acts as an SPI master to verify the entire `accelerator_system`. It handles loading stimulus, sending SPI transactions, and checking results.
-   **`Makefile`**: The makefile used to run the `cocotb` simulation with Icarus Verilog, automating the compilation and simulation process.
-   **`data/`**: A directory containing stimulus and reference files (`patch0.vec`, `weights0.mem`, `bias0.mem`, `ref0.vec`).
-   **`python_scripts/`**: A directory containing the initial Python scripts for model training, profiling (`cprofile.py`, `tfprofile.py`), and data generation (`gen_ref.py`, `image_array.py`, `weights_mem.py`).
-   **`vivado_project/`**: A directory containing the Vivado project files for synthesis and implementation, including the `constraints.xdc` file.

## Design Workflow & Evolution

The project followed the weekly codefest structure, demonstrating a complete design cycle.

### Week 2: Software Analysis
The project began by training a TensorFlow/Keras CNN model for COVID-19 X-ray classification. Using `cProfile` and TensorFlow's profiler, the initial layers, particularly the first `Conv2D` layer, were identified as computationally intensive and a suitable candidate for hardware acceleration. A specific software baseline was established by creating and timing a pure Python implementation of the 5x5 convolution (`time_sw_conv.py`), which showed a throughput of **~19,028 patches/second**.

### Week 3-4: Initial Hardware Design & Verification
The first version of the hardware accelerator was designed in SystemVerilog.
-   `conv5x5_core.sv`: A module to perform 25 sequential multiply-accumulate (MAC) operations for one channel.
-   `conv5x5_wrapper.sv`: A module to instantiate the core and manage the sequential processing of 5 channels.
-   `testbench.sv`: A SystemVerilog testbench was created to functionally verify the wrapper's logic by loading data from files and comparing the output with a pre-computed golden reference (`ref0.vec`). This was successfully simulated in Vivado's simulator.

### Week 5: FPGA Synthesis & Implementation
The verified RTL was taken through the Vivado FPGA implementation flow to get initial physical design metrics.
-   **Initial Error:** An I/O overutilization error (`[Place 30-415]`) occurred because the `conv5x5_wrapper`'s wide parallel data ports (~2365 pins) far exceeded the target FPGA's available I/O pins (106).
-   **Solution:** A temporary top-level file, `vivado_top.sv`, was created to wrap the `conv5x5_wrapper`. This new top-level had minimal I/O, with the wrapper's data inputs tied to internal constants.
-   **Second Error:** This led to a new implementation error (`[Place 30-494] The design is empty`). Vivado's logic optimizer, seeing that the outputs were not dependent on any changing inputs, trimmed away the entire datapath.
-   **Solution:** `vivado_top.sv` was modified to include outputs that were connected to the wrapper's results, signaling to the tool that the logic was "used" and preventing it from being removed. This allowed implementation to complete.

### Week 6: Iterative Design - Pipelining for Timing Closure
The first successful implementation run with dynamic stimulus failed to meet the 100 MHz timing target, with a **WNS of -1.890 ns**.
-   **Analysis:** The Vivado timing report was analyzed, revealing that the critical path was the long combinational logic path within the MAC unit of `conv5x5_core.sv` (from `mac_count_reg` to `mac_accumulator_reg`).
-   **Design Iteration:** The `conv5x5_core` was pipelined. A register (`product_reg_pipelined`) was inserted to hold the result of the `pixel * weight` multiplication. This breaks the long combinational path into two shorter, faster stages.
-   **Result:** This was a successful iteration. After re-running implementation with the pipelined core, the design met timing with a **WNS of +0.149 ns**, achieving a new, more representative Fmax of **~101.51 MHz**.

### Week 8-9: System Integration & Co-Simulation
To create a realistic test environment and benchmark system-level performance, an SPI interface was designed and integrated.
-   **Design:** `spi_slave.sv` and a new top-level `accelerator_system.sv` were created. The SPI slave was designed with a command-based protocol to handle loading weights, patch data, starting the accelerator, and reading status/results.
-   **`cocotb` Testbench:** A Python testbench (`test_spi_accelerator.py`) was developed to act as an SPI master, sending commands and data to the hardware and verifying the results.
-   **Debugging Challenges:**
    1.  **Icarus Verilog Compatibility:** Numerous compilation errors were encountered due to Icarus Verilog's strict interpretation of certain SystemVerilog constructs. This required modifying the Verilog code to: pre-declare loop variables, replace aggregate array assignments with explicit `for` loops, and change `always_comb` to `always @*`.
    2.  **`cocotb` Simulation Timeout:** The test initially failed with a timeout. Debugging with the added monitor ports showed that the `spi_slave` FSM was incorrectly aborting its "wait" states if the chip select (`cs_n`) was de-asserted. The FSM logic was corrected to ensure it would wait for `busy_from_wrapper` and `done_from_wrapper` signals regardless of `cs_n`'s state.
-   **Final Success:** After these debug cycles, the `cocotb` test passed, successfully demonstrating a full system-level operation: loading all data via SPI, triggering the accelerator, polling for status, reading back the results, and verifying their correctness against the reference file.

## Final Results & Benchmarks

The following metrics are for the final, pipelined hardware design integrated into the SPI system (`accelerator_system.sv`).

### Hardware Performance Metrics
-   **Maximum Operating Frequency (Fmax):** **101.51 MHz** (for `clk_main`)
-   **Cycles per Patch (`N_cycles`):** **172 cycles** (measured via functional simulation of the pipelined version)
-   **Hardware Core Latency:** `172 cycles / 101.51 MHz ≈ 1.69 µs`
-   **Hardware Throughput (Core only):** `101,512,500 / 172 ≈ **590,189 patches/second**`

### Software vs. Hardware Comparison
This table shows the speedup for the accelerated layer itself.

| Metric                 | Software (Python/NumPy) | Hardware (Pipelined Core) | Speedup |
| ---------------------- | ----------------------- | ------------------------- | ------- |
| Time per Patch         | 52.55 µs                | 1.69 µs                   | **31.1x** |
| Throughput (patches/s) | ~19,028                 | ~590,189                  | **31.1x** |

### Resource Utilization
The following resources were used by the `accelerator_system` on a Xilinx Artix-7 (7a35t) FPGA target:

| Hierarchy                  | Slice LUTs | Slice Registers (FFs) | DSPs |
| -------------------------- | ---------- | --------------------- | ---- |
| **`u_conv5x5_wrapper_inst`** | 766        | 841                   | 1    |
| **`u_spi_slave`** | 2185       | 2425                  | 0    |
| **Total `accelerator_system`** | **2951** | **3266** | **1** |

## How to Run the Simulations

### Vivado Functional Simulation (Direct DUT Test)
This uses `testbench.sv` to test the `conv5x5_wrapper` directly.
1.  Open the Vivado project.
2.  In the "Sources" window, set `testbench` as the top module for simulation.
3.  Ensure the data files (`patch0.vec`, `weights0.mem`, etc.) are copied to the simulation run directory (`<project>.sim/sim_1/behav/xsim/`).
4.  In the "Flow Navigator," click "Run Simulation" -> "Run Behavioral Simulation".

### Cocotb Co-Simulation (Full SPI System Test)
This uses `test_spi_accelerator.py` to test the full `accelerator_system.sv`.
1.  **Prerequisites:** Ensure you have Python, `cocotb`, and `iverilog` installed and accessible in your environment PATH. Using **Git Bash** on Windows is recommended.
2.  **Navigate to the Project Directory:** Open a terminal (like Git Bash) in the project directory containing the `Makefile`.
3.  **Run `make`:**
    ```bash
    make clean  # Recommended to clear old results
    make
    ```
    This will compile the HDL with Icarus Verilog and execute the Python testbench.

## Challenges & Debugging Journey
This project involved a significant debugging effort, which was a valuable learning experience:
-   **FPGA I/O Overutilization:** Solved by creating a minimal I/O hardware wrapper (`vivado_top.sv`) for synthesis.
-   **Logic Optimization:** The "design is empty" error was solved by adding outputs to the `vivado_top.sv` wrapper to make the internal logic "used."
-   **Timing Violations:** A WNS of -1.890 ns was fixed by identifying the critical path in the MAC unit and implementing a pipeline stage in `conv5x5_core.sv`.
-   **Icarus Verilog Compatibility:** Multiple compilation errors were resolved by changing `always_comb` to `always @*`, pre-declaring loop variables, and replacing aggregate array assignments with explicit `for` loops.
-   **Cocotb Simulation Timeout:** A `cocotb` test timeout was traced to an FSM logic error in `spi_slave.sv` where the wait states were incorrectly aborted when chip select was de-asserted. Correcting the FSM transition conditions resolved the timeout and led to a successful end-to-end test.

## Future Work & Potential Improvements
-   **Parallelism:** To further reduce `N_cycles`, the `conv5x5_wrapper` could be modified to instantiate multiple `conv5x5_core` units to process channels in parallel.
-   **Memory Architecture:** The `spi_slave`'s large storage registers could be implemented using on-chip Block RAM (BRAM) for better resource efficiency on FPGAs.
-   **Advanced Interface:** The simple SPI interface could be replaced with a higher-throughput interface like AXI4-Stream for integration into more complex SoC designs.
-   **ASIC Flow Completion:** Revisit the OpenLane 2 flow to synthesize the final design down to a GDSII layout to complete the ASIC-level success criterion.
-   **Full System Benchmarking:** Measure the performance of the accelerator when integrated with the full software application to evaluate the overall application speedup, considering data transfer overheads (Amdahl's Law).

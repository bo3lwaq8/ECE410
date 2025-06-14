##    Performance Analysis

### Observations

When the simulation runs, the resulting plot shows a clear quadratic increase in execution time as the input size grows. This is expected and highlights the key difference between a serial software simulation and a true parallel hardware implementation.

* **Software Simulation Complexity: O(n²)**
    The Python script runs on a single CPU core. It must simulate the parallel steps sequentially using nested loops. The outer loop runs `n` times (for `n` clock cycles), and the inner loops iterate through `n` elements. This results in a time complexity of **O(n²)**, which explains the rapid increase in execution time seen in the plot.

* **Hardware Systolic Array Complexity: O(n)**
    In a real systolic array, all the comparisons in the odd and even phases happen simultaneously in constant time. Since the algorithm guarantees a sorted array after `n` steps (clock cycles), the total execution time is directly proportional to the number of elements `n`. This gives the hardware implementation a highly efficient linear time complexity of **O(n)**.

This project successfully demonstrates the logical design of a systolic array for sorting and contrasts the profound performance difference between serial simulation and true parallel execution.
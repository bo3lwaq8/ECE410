import time
import random
import matplotlib.pyplot as plt
import numpy as np

def systolic_bubble_sort(arr):
    """
    Simulates an odd-even transposition sort on a 1-D systolic array.

    This function models the time complexity of the parallel hardware algorithm.
    In each full pass (representing one "tick" of a parallel clock), we perform
    all odd-pair comparisons and then all even-pair comparisons.
    
    The number of passes required to guarantee a sort is n.
    
    Args:
        arr (list): A list of numbers to sort.

    Returns:
        list: The sorted list.
    """
    n = len(arr)
    if n == 0:
        return arr

    # The algorithm requires n passes (or clock cycles) to guarantee the sort.
    for i in range(n):
        # Odd phase: Compare and swap elements at odd indices with their right neighbor
        # In hardware, all these comparisons would happen simultaneously.
        for j in range(0, n - 1, 2):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

        # Even phase: Compare and swap elements at even indices with their right neighbor
        # In hardware, all these comparisons would also happen simultaneously.
        for j in range(1, n - 1, 2):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    
    return arr

def measure_performance():
    """
    Measures the execution time of the systolic sort simulation for various
    problem sizes and generates a plot.
    """
    sizes = [10, 100, 500, 1000, 2500, 5000]
    execution_times = []

    print("Running simulations for various sorting sizes...")
    print("-" * 40)
    print(f"{'Input Size':<15} | {'Execution Time (s)':<20}")
    print("-" * 40)

    for size in sizes:
        # Generate a list of random numbers for each size
        random_list = [random.randint(0, size) for _ in range(size)]
        
        # Measure the execution time
        start_time = time.time()
        systolic_bubble_sort(random_list)
        end_time = time.time()
        
        duration = end_time - start_time
        execution_times.append(duration)
        print(f"{size:<15} | {duration:<20.6f}")

    # Visualize the results
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Using strings for x-axis labels to ensure they are treated as categories
    size_labels = [str(s) for s in sizes]
    
    bars = ax.bar(size_labels, execution_times, color='skyblue', edgecolor='black')

    ax.set_xlabel('Number of Elements to Sort', fontsize=12)
    ax.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax.set_title('Systolic Bubble Sort Simulation Performance', fontsize=14)

    # Optional: Add labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.4f}', va='bottom', ha='center')

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # --- Task 2: Test the software version ---
    print("--- Testing the sort implementation ---")
    sample_array = [6, 2, 8, 1, 9, 4, 5, 7, 3, 0]
    print(f"Original Array: {sample_array}")
    sorted_array = systolic_bubble_sort(sample_array.copy())
    print(f"Sorted Array:   {sorted_array}\n")
    
    # --- Task 3: Visualize execution times ---
    measure_performance()

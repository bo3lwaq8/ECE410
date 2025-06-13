import matplotlib.pyplot as plt
import numpy as np

# --- Paste the data from your terminal output here ---
# After running the C++ program, copy the results table
# and paste it into this dictionary.
data = {
    # Example format: "Matrix Size": {"total": TotalTime, "kernel": KernelTime}
    "2^15": {"total": 49.4308, "kernel": 47.5539},
    "2^16": {"total": 1.06496, "kernel": 0.002496},
    "2^17": {"total": 0.948256, "kernel": 0.00224},
    "2^18": {"total": 1.50214, "kernel": 0.002528},
    "2^19": {"total": 3.11917, "kernel": 0.003328},
    "2^20": {"total": 6.04771, "kernel": 0.003616},
    "2^21": {"total": 11.8603, "kernel": 0.002496},
    "2^22": {"total": 24.6436, "kernel": 0.003296},
    "2^23": {"total": 48.6031, "kernel": 0.002528},
    "2^24": {"total": 99.3924, "kernel": 0.002496},
    "2^25": {"total": 200.002, "kernel": 0.003456},
}
# ----------------------------------------------------

labels = list(data.keys())
total_times = [v['total'] for v in data.values()]
kernel_times = [v['kernel'] for v in data.values()]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 7))
rects1 = ax.bar(x - width/2, total_times, width, label='Total Time (incl. Memory Transfer)', color='skyblue')
rects2 = ax.bar(x + width/2, kernel_times, width, label='Kernel Execution Time Only', color='royalblue')

ax.set_title('CUDA Vector Addition Performance by Matrix Size')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()

# Use a logarithmic scale to better visualize the vast difference in times
ax.set_yscale('log')
ax.set_ylabel('Execution Time (ms) - Log Scale')

# Save the figure to a file
plt.savefig('performance_chart.png', dpi=300, bbox_inches='tight')

fig.tight_layout()
plt.show()

print("Plot has been saved as performance_chart.png")

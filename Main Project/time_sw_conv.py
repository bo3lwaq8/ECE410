import numpy as np
import time # Import the time module

def read_signed_hex(fname, bits=16):
    """Read a hex memory file as signed two’s-complement integers."""
    half = 1 << (bits - 1)
    full = 1 << bits
    vals = []
    with open(fname, 'r') as f:
        for line in f:
            h = line.strip()
            if not h:
                continue
            v = int(h, 16)
            if v & half: # Check if the sign bit is set
                v -= full # Convert to negative if so
            vals.append(v)
    return vals

# --- Configuration ---
NUM_OUTPUT_CHANNELS = 5
PATCH_SIZE = 5
NUM_ITERATIONS_FOR_TIMING = 10000 # Run many times for a more stable average

# --- Load Data ---
# Ensure 'weights0.mem', 'bias0.mem', and 'patch0.vec' are in the same
# directory as this script, or provide the full paths.
try:
    Wraw = read_signed_hex("weights0.mem", bits=16) # 125 weights (5 channels * 25 weights/channel)
    bq   = read_signed_hex("bias0.mem",    bits=16) # 5 biases
    
    patch_data = np.loadtxt("patch0.vec", dtype=np.int32) # Expecting 25 integer values
    if patch_data.size != (PATCH_SIZE * PATCH_SIZE):
        print(f"Error: patch0.vec should contain {PATCH_SIZE*PATCH_SIZE} values, but found {patch_data.size}.")
        exit()
    patch = patch_data.reshape(PATCH_SIZE, PATCH_SIZE)

except FileNotFoundError as e:
    print(f"Error: Could not find a required data file: {e.filename}")
    print("Please ensure weights0.mem, bias0.mem, and patch0.vec are in the current directory.")
    exit()
except ValueError as e:
    print(f"Error processing data files: {e}")
    exit()

# --- Define the core computation function ---
def compute_one_patch(current_patch, all_weights, all_biases):
    sums_list = []
    for c_idx in range(NUM_OUTPUT_CHANNELS):
        accumulator = 0
        weight_base_idx = c_idx * (PATCH_SIZE * PATCH_SIZE)
        for r_idx in range(PATCH_SIZE): # patch row
            for c_col_idx in range(PATCH_SIZE): # patch col
                pixel_val = current_patch[r_idx, c_col_idx]
                weight_val = all_weights[weight_base_idx + r_idx * PATCH_SIZE + c_col_idx]
                accumulator += pixel_val * weight_val
        accumulator += all_biases[c_idx]
        sums_list.append(accumulator)
    
    # Arithmetic shift right by 8 bits and apply ReLU
    output_values = [max(0, s_val >> 8) for s_val in sums_list]
    return output_values

# --- Timing the core operation ---

# Optional: Perform a single warm-up run (can sometimes help stabilize timings)
_ = compute_one_patch(patch, Wraw, bq)

start_time = time.perf_counter() # Use perf_counter for more precise timing

for _ in range(NUM_ITERATIONS_FOR_TIMING):
    # This is the exact operation your hardware accelerates
    calculated_outs = compute_one_patch(patch, Wraw, bq) 
    # We don't need to store 'calculated_outs' in the loop for timing purposes

end_time = time.perf_counter()

# --- Calculate and Print Results ---
total_duration = end_time - start_time
duration_per_patch = total_duration / NUM_ITERATIONS_FOR_TIMING

print(f"--- Software Performance Baseline (Python/NumPy) ---")
print(f"Operation: 5x5 Convolution, 5 Output Channels, Bias, Scale (>>8), ReLU")
print(f"Number of iterations for timing: {NUM_ITERATIONS_FOR_TIMING}")
print(f"Total time for {NUM_ITERATIONS_FOR_TIMING} iterations: {total_duration:.6f} seconds")
print(f"Average time per single patch processing: {duration_per_patch * 1e6:.3f} microseconds ({duration_per_patch:.9f} seconds)")

if duration_per_patch > 0:
    software_throughput_patches_per_sec = 1.0 / duration_per_patch
    print(f"Estimated software throughput: {software_throughput_patches_per_sec:.2f} patches/second")
else:
    print("Duration per patch too small to calculate throughput reliably, or num_iterations is zero.")
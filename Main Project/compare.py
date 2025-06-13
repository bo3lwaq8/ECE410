
import numpy as np

def read_signed_hex(fname, bits=16):
    half = 1 << (bits-1)
    full = 1 << bits
    vals = []
    with open(fname) as f:
        for line in f:
            h = line.strip()
            if not h: continue
            v = int(h, 16)
            if v & half: v -= full
            vals.append(v)
    return vals

# 1) Load signed weights & bias for channel 0
raw_w = read_signed_hex("weights0.mem", bits=16)   # 125 entries
W0 = np.array(raw_w).reshape(5,5,1,5)[...,0]       # pick channel 0

b_raw = read_signed_hex("bias0.mem", bits=16)
b0 = b_raw[0]

# 2) Load the patch
patch = np.loadtxt("patch0.vec", dtype=int).reshape(5,5)

# 3) Compute
acc = np.sum(patch * W0) + b0
print("Signed Python channel0:", acc, "ReLU→", max(acc,0))

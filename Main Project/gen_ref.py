import numpy as np

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
            if v & half:
                v -= full
            vals.append(v)
    return vals

# 1) Load raw weights (125 entries) and biases (5 entries)
Wraw = read_signed_hex("weights0.mem", bits=16)
bq   = read_signed_hex("bias0.mem",    bits=16)

# 2) Load the 5×5 patch
patch = np.loadtxt("patch0.vec", dtype=int).reshape(5, 5)

# 3) Compute fixed-point convolution + bias
sums = []
for c in range(5):
    acc = 0
    base = c * 25
    for u in range(5):
        for v in range(5):
            acc += patch[u, v] * Wraw[base + u*5 + v]
    acc += bq[c]
    sums.append(acc)

# 4) Arithmetic shift right by 8 bits (>>>8) and apply ReLU
outs = [max(0, s >> 8) for s in sums]

# 5) Write ref0.vec as 4-digit hex for $readmemh
with open("ref0.vec", "w") as f:
    for v in outs:
        f.write(f"{v & 0xFFFF:04x}\n")

print("Scaled ref0.vec (hex):", [f"{v & 0xFFFF:04x}" for v in outs])

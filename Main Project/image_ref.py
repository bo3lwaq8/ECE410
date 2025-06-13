
import numpy as np
from PIL import Image

# Configuration
IMG_PATH    = "Covid19-dataset/test/covid/2.png"   # Place your 256×256 grayscale test image here
IMG_DIM     = 256
PATCH_DIM   = 5
STRIDE      = 3
ACC_WIDTH   = 24  # bits
OUT_CH      = 5

def read_signed_hex(fname, bits=16):
    """Read hex memory file as signed two’s-complement ints."""
    half = 1 << (bits - 1)
    full = 1 << bits
    vals = []
    with open(fname, "r") as f:
        for line in f:
            h = line.strip()
            if not h:
                continue
            v = int(h, 16)
            if v & half:
                v -= full
            vals.append(v)
    return vals

def main():
    # 1) Load fixed-point weights & biases
    Wraw = read_signed_hex("weights0.mem", bits=16)   # length = OUT_CH * PATCH_DIM*PATCH_DIM
    bq   = read_signed_hex("bias0.mem",    bits=16)   # length = OUT_CH

    # Reshape weights into [OUT_CH, PATCH_DIM*PATCH_DIM]
    Wq = np.array(Wraw, dtype=int).reshape((OUT_CH, PATCH_DIM*PATCH_DIM))

    # 2) Load and prepare image
    img = Image.open(IMG_PATH).convert("L").resize((IMG_DIM, IMG_DIM))
    pix = np.array(img, dtype=int)

    # 3) Write image.mem (256×256 bytes, hex)
    with open("image.mem", "w") as f_img:
        for val in pix.flatten():
            f_img.write(f"{val:02x}\n")
    print(f"Wrote image.mem ({IMG_DIM*IMG_DIM} entries)")

    # 4) Compute channel-0 outputs for each 5×5 patch
    refs = []
    for y in range(0, IMG_DIM - PATCH_DIM + 1, STRIDE):
        for x in range(0, IMG_DIM - PATCH_DIM + 1, STRIDE):
            patch = pix[y:y+PATCH_DIM, x:x+PATCH_DIM].flatten()
            acc = int(np.dot(Wq[0], patch)) + bq[0]
            # Arithmetic shift right by 8 bits, then ReLU
            scaled = acc >> 8
            relu   = max(0, scaled)
            refs.append(relu)

    # 5) Write image_ref.mem (84×84 entries, 24-bit hex => 6 hex digits)
    with open("image_ref.mem", "w") as f_ref:
        for v in refs:
            f_ref.write(f"{v & ((1<<ACC_WIDTH)-1):06x}\n")
    print(f"Wrote image_ref.mem ({len(refs)} entries)")

    # 6) Summary
    print("First few reference values:", [f"{v:06x}" for v in refs[:5]])

if __name__ == "__main__":
    main()

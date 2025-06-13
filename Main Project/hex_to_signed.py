import numpy as np
from tensorflow.keras.models import load_model

# Load model and first conv layer
model = load_model("covid_classifier.h5")
conv = next(l for l in model.layers if l.__class__.__name__=="Conv2D")
W, b = conv.get_weights()

# Fixed-point Q8.8 as before
SCALE = 256
Wq16 = np.round(W * SCALE).astype(np.int16)

# Now map into 8-bit signed: 
# e.g. take the high 8 bits (>>8) or simply clip
Wq8 = np.clip((Wq16 + (1<<7)) >> 8, -128, 127).astype(np.int8)

# Write weights0.mem with 2-digit hex
with open("weights0.mem","w") as f:
    for c in range(Wq8.shape[3]):
        for u in range(Wq8.shape[0]):
            for v in range(Wq8.shape[1]):
                w = int(Wq8[u,v,0,c]) & 0xFF
                f.write(f"{w:02x}\n")

print("Rewritten weights0.mem as 8-bit hex")

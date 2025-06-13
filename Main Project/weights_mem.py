import numpy as np
from tensorflow.keras.models import load_model

# Load your trained model
model = load_model("covid_classifier.h5")
conv  = next(l for l in model.layers if l.__class__.__name__ == "Conv2D")
W, b  = conv.get_weights()  # W.shape==(5,5,1,5), b.shape==(5,)

# Fixed-point scale: Q8.8
SCALE = 256
Wq = np.round(W * SCALE).astype(np.int16)  # signed 16-bit
bq = np.round(b * SCALE).astype(np.int16)

# Write weights0.mem (125 entries, 4-digit hex)
with open("weights0.mem","w") as f:
    for c in range(Wq.shape[3]):
        for u in range(5):
            for v in range(5):
                w = int(Wq[u,v,0,c]) & 0xFFFF
                f.write(f"{w:04x}\n")

# Write bias0.mem (5 entries, 4-digit hex)
with open("bias0.mem","w") as f:
    for val in bq:
        f.write(f"{(int(val)&0xFFFF):04x}\n")

print("Regenerated weights0.mem & bias0.mem with Q8.8 (scale=256)")

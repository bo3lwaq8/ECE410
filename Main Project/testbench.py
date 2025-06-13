
import numpy as np
from tensorflow.keras.models import load_model

# 1) Load the 5×5 patch you already generated
patch = np.loadtxt("patch0.vec", dtype=np.int32)
patch = patch.reshape(5, 5, 1)   # shape: [H,W,channels]

# 2) Load your trained model and extract the first Conv2D layer’s weights
model = load_model("covid_classifier.h5")
# Inspect model.layers to find your first Conv2D:
for i, layer in enumerate(model.layers):
    if layer.__class__.__name__ == "Conv2D":
        conv_idx = i
        break

W, b = model.layers[conv_idx].get_weights()
# W has shape (5,5,1,5), b has shape (5,)

# 3) Compute the 5 outputs: out[k] = ReLU( sum(patch * W[...,k]) + b[k] )
outs = []
for k in range(W.shape[3]):
    filt = W[..., k]      # shape (5,5,1)
    acc  = np.sum(patch * filt) + b[k]
    outs.append(int(max(acc, 0)))  # apply ReLU and cast to integer

# 4) Save them to ref0.vec, one per line
with open("ref0.vec", "w") as f:
    for v in outs:
        f.write(f"{v}\n")

print("Generated ref0.vec:")
print(outs)

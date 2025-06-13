from PIL import Image
import numpy as np
import os

# 1) Point this at one of your test X-ray files:
img_path = os.path.join("Covid19-dataset","test","covid","2.png")

# 2) Load & preprocess to a (256×256) grayscale array
img = Image.open(img_path).convert('L')           # grayscale PIL image
img = img.resize((256,256))                       # same size your RTL expects
your_image = np.array(img, dtype=np.uint8)        # shape (256,256)

# 3) Extract the top-left 5×5 patch (or any other (i,j) window):
i0, j0 = 0, 0  # change to test other locations
patch = your_image[i0:i0+5, j0:j0+5]

# 4) Write to patch0.vec, one value per line
with open("patch0.vec","w") as f:
    for v in patch.flatten():
        f.write(f"{int(v)}\n")

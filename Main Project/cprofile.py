

import math
import cProfile
import pstats
import subprocess
import time
import webbrowser
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# --- Configuration ---
MODEL_PATH    = "covid_classifier.h5"
DATA_DIR      = "Covid19-dataset/test"  # change to your validation folder
TARGET_SIZE   = (256, 256)
BATCH_SIZE    = 32
PROF_FILE     = "inference.prof"
TEXT_PROFILE  = "inference.txt"
SV_PORT       = 5555  # SnakeViz port

def build_inference_iterator():
    """Builds an inference-only iterator (no labels)."""
    gen = ImageDataGenerator(rescale=1.0/255)
    it  = gen.flow_from_directory(
        DATA_DIR,
        target_size=TARGET_SIZE,
        color_mode="grayscale",
        class_mode=None,
        batch_size=BATCH_SIZE,
        shuffle=False
    )
    return it

def run_inference(model, iterator):
    """Runs inference on the full dataset for profiling."""
    steps = math.ceil(iterator.samples / iterator.batch_size)
    # Warm-up one batch
    batch = next(iterator)
    _ = model.predict(batch, verbose=0)
    # Full pass
    for _ in range(steps):
        batch = next(iterator)
        _ = model.predict(batch, verbose=0)

if __name__ == "__main__":
    # 1) Load model & iterator
    model = load_model(MODEL_PATH)
    inf_it = build_inference_iterator()

    # 2) Profile the inference
    profiler = cProfile.Profile()
    profiler.enable()
    run_inference(model, inf_it)
    profiler.disable()

    # 3) Dump binary stats
    profiler.dump_stats(PROF_FILE)
    print(f"Wrote raw profile data to {PROF_FILE}")

    # 4) Dump top-50 text summary
    with open(TEXT_PROFILE, "w") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs().sort_stats("cumtime").print_stats(50)
    print(f"Wrote top-50 hotspots to {TEXT_PROFILE}")

    # 5) Launch SnakeViz and open in browser
    print(f"Starting SnakeViz on port {SV_PORT}...")
    subprocess.Popen([
        "python", "-m", "snakeviz", PROF_FILE,
        "--port", str(SV_PORT)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)  # give server time to start
    url = f"http://127.0.0.1:{SV_PORT}/"
    webbrowser.open(url)
    print(f"SnakeViz should now be running at {url}")

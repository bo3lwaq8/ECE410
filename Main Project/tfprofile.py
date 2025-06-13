
"""
tfprofile_inference.py

Profiles inference using TensorFlow Profiler via tf.summary.trace, saves trace to a log directory,
starts TensorBoard server, and writes a cProfile summary to tfprofile.txt.
Uses built-in default paths so you can run without CLI args.
"""
import os
import shutil
import math
import subprocess
import webbrowser
import time
import cProfile
import pstats
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# --- Configuration (no args needed) ---
MODEL_PATH = "covid_classifier.h5"      # Make sure this file exists
DATA_DIR   = "Covid19-dataset/test"  # Make sure this folder exists
TARGET_SIZE = (256, 256)
BATCH_SIZE  = 32
LOGDIR      = "logs/tf_profile"
TB_PORT     = 6006
TXT_PROFILE = "tfprofile.txt"

# --- Build inference-only iterator (no labels) ---
def build_inference_iterator(data_dir, target_size, batch_size):
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory '{data_dir}' not found")
    gen = ImageDataGenerator(rescale=1.0/255)
    return gen.flow_from_directory(
        data_dir,
        target_size=tuple(target_size),
        color_mode='grayscale',
        class_mode=None,
        batch_size=batch_size,
        shuffle=False
    )

# --- Main Execution ---
if __name__ == '__main__':
    # 1) Load model
    print(f"Loading model from {MODEL_PATH}...")
    model = load_model(MODEL_PATH)

    # 2) Prepare inference iterator
    print(f"Building inference iterator from images in {DATA_DIR}...")
    inf_it = build_inference_iterator(DATA_DIR, TARGET_SIZE, BATCH_SIZE)

    # 3) Clean & recreate log directory
    if os.path.exists(LOGDIR):
        shutil.rmtree(LOGDIR)
    os.makedirs(LOGDIR, exist_ok=True)

    # 4) Start tf.summary.trace
    print(f"Starting TensorFlow trace, writing to {LOGDIR}...")
    writer = tf.summary.create_file_writer(LOGDIR)
    tf.summary.trace_on(graph=True, profiler=True)

    # 5) Run inference: warm-up + full pass
    steps = math.ceil(inf_it.samples / inf_it.batch_size)
    _ = model.predict(next(inf_it), verbose=0)  # warm-up
    _ = model.predict(inf_it, steps=steps, verbose=0)

    # 6) Export trace
    with writer.as_default():
        tf.summary.trace_export(
            name="inference_trace",
            step=0,
            profiler_outdir=LOGDIR
        )
    print("TensorFlow profiling trace exported.")

    # 7) Save cProfile summary
    print(f"Saving cProfile summary to {TXT_PROFILE}...")
    prof = cProfile.Profile()
    prof.enable()
    _ = model.predict(next(inf_it), verbose=0)
    prof.disable()
    with open(TXT_PROFILE, 'w') as f:
        stats = pstats.Stats(prof, stream=f)
        stats.strip_dirs().sort_stats('cumtime').print_stats(50)
    print(f"Text profile saved to {TXT_PROFILE}")

    # 8) Launch TensorBoard
    tb_cmd = [
        'tensorboard',
        f'--logdir={LOGDIR}',
        f'--port={TB_PORT}',
        '--host=localhost'
    ]
    print("Launching TensorBoard:", ' '.join(tb_cmd))
    subprocess.Popen(tb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)

    # 9) Open browser
    url = f"http://localhost:{TB_PORT}/"
    print(f"Opening browser to {url} (navigate to 'Profile' tab)")
    webbrowser.open(url)

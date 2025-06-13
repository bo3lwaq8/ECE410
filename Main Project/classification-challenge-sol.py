
"""
classification_profile.py

Standalone script to train & evaluate your COVID-19 X-ray classifier,
profile its inference with cProfile, save both binary and text outputs,
and launch an interactive SnakeViz session in your browser.
"""
import sys
import math
import time
import cProfile
import subprocess
import pstats
import webbrowser
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix

# --- Configuration ---
TRAIN_DIR = "Covid19-dataset/train"
TARGET_SIZE = (256, 256)
BATCH_SIZE = 32
EPOCHS = 20
MODEL_SAVE_PATH = "covid_classifier.h5"
PROF_FILE = "inference.prof"
TEXT_PROFILE = "inference.txt"
SNAKEVIZ_PORT = 5555

# --- Data Setup ---
train_gen = ImageDataGenerator(
    rescale=1.0/255,
    zoom_range=0.1,
    rotation_range=25,
    width_shift_range=0.05,
    height_shift_range=0.05
)
val_gen = ImageDataGenerator(rescale=1.0/255)

train_it = train_gen.flow_from_directory(
    TRAIN_DIR,
    target_size=TARGET_SIZE,
    color_mode='grayscale',
    class_mode='categorical',
    batch_size=BATCH_SIZE
)
# Iterator for inference (images only)
inf_it = val_gen.flow_from_directory(
    TRAIN_DIR,
    target_size=TARGET_SIZE,
    color_mode='grayscale',
    class_mode=None,
    batch_size=BATCH_SIZE,
    shuffle=False
)
# Iterator for evaluation (images + labels)
val_it = val_gen.flow_from_directory(
    TRAIN_DIR,
    target_size=TARGET_SIZE,
    color_mode='grayscale',
    class_mode='categorical',
    batch_size=BATCH_SIZE,
    shuffle=False
)

# --- Model Definition ---
def build_model():
    model = Sequential([
        keras.Input(shape=(TARGET_SIZE[0], TARGET_SIZE[1], 1)),
        layers.Conv2D(5, 5, strides=3, activation="relu"),
        layers.MaxPooling2D(pool_size=(2,2), strides=(2,2)),
        layers.Dropout(0.1),
        layers.Conv2D(3, 3, strides=1, activation="relu"),
        layers.MaxPooling2D(pool_size=(2,2), strides=(2,2)),
        layers.Dropout(0.2),
        layers.Flatten(),
        layers.Dense(3, activation="softmax"),
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss=tf.keras.losses.CategoricalCrossentropy(),
        metrics=[
            tf.keras.metrics.CategoricalAccuracy(name='accuracy'),
            tf.keras.metrics.AUC(name='auc')
        ]
    )
    return model

# --- Training & Evaluation ---
def train_and_evaluate():
    model = build_model()
    es = EarlyStopping(monitor='val_auc', mode='max', patience=5, verbose=1)
    history = model.fit(
        train_it,
        steps_per_epoch=train_it.samples // BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=val_it,
        validation_steps=val_it.samples // BATCH_SIZE,
        callbacks=[es]
    )
    # Plot metrics
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6,8))
    ax1.plot(history.history['accuracy'], label='train')
    ax1.plot(history.history['val_accuracy'], label='val')
    ax1.set(title='Accuracy', xlabel='Epoch', ylabel='Accuracy')
    ax1.legend()
    ax2.plot(history.history['auc'], label='train')
    ax2.plot(history.history['val_auc'], label='val')
    ax2.set(title='AUC', xlabel='Epoch', ylabel='AUC')
    ax2.legend()
    plt.tight_layout()
    plt.show()

    # Evaluate on validation set
    steps = math.ceil(val_it.samples / BATCH_SIZE)
    preds = model.predict(val_it, steps=steps)
    y_pred = np.argmax(preds, axis=1)
    y_true = val_it.classes
    print(classification_report(y_true, y_pred, target_names=list(val_it.class_indices.keys())))
    print(confusion_matrix(y_true, y_pred))
    return model

# --- Profiling Inference ---
def run_inference(model):
    steps = math.ceil(inf_it.samples / BATCH_SIZE)
    # Warm-up
    batch_images = next(inf_it)
    _ = model.predict(batch_images, verbose=0)
    # Full pass
    for _ in range(steps):
        batch_images = next(inf_it)
        _ = model.predict(batch_images, verbose=0)

# --- Main Execution ---
if __name__ == '__main__':
    # Train & evaluate
    keras_model = train_and_evaluate()

    # Save the trained model to disk
    print(f"Saving trained model to '{MODEL_SAVE_PATH}'...")
    keras_model.save(MODEL_SAVE_PATH)
    print("Model saved successfully.")

    # Profile inference (binary .prof)
    print(f"Profiling inference to '{PROF_FILE}'...")
    profiler = cProfile.Profile()
    profiler.enable()
    run_inference(keras_model)
    profiler.disable()
    profiler.dump_stats(PROF_FILE)
    print(f"Saved binary profile to '{PROF_FILE}'")

    # Also save a text summary of top 50 hot functions
    print(f"Writing text profile to '{TEXT_PROFILE}'...")
    with open(TEXT_PROFILE, 'w') as f:
        ps = pstats.Stats(profiler, stream=f)
        ps.strip_dirs().sort_stats('cumtime').print_stats(50)
    print(f"Saved text profile to '{TEXT_PROFILE}'")

    # Launch SnakeViz server
    cmd = [sys.executable, '-m', 'snakeviz', PROF_FILE, '-p', str(SNAKEVIZ_PORT)]
    print(f"Starting SnakeViz with: {' '.join(cmd)}")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("SnakeViz server running; open your browser to view the profile.")


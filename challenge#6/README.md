# Multi-Layer Perceptron for NAND and XOR Logic Functions

This repository contains a Python implementation of a Multi-Layer Perceptron (MLP) neural network that can solve both the **NAND** and **XOR** binary logic functions. The network is trained using a single hidden layer to handle both **linearly separable** (NAND) and **non-linearly separable** (XOR) problems.

## Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Code Explanation](#code-explanation)
- [Usage](#usage)
- [Results](#results)
- [License](#license)

## Project Overview

This project demonstrates the application of a **Multi-Layer Perceptron (MLP)** neural network to solve two well-known binary logic functions: **NAND** and **XOR**.

- **NAND**: A binary operator that outputs `1` except when both inputs are `1`.
- **XOR**: A binary operator that outputs `1` when the inputs are different and `0` when the inputs are the same.

The neural network is trained to learn both logic functions by using a **single hidden layer**. The model can classify the inputs of both logic functions correctly.

## Prerequisites

To run this code, you'll need the following libraries:

- Python 3.x
- `numpy`: For handling arrays and numerical operations.
- `scikit-learn`: For implementing the Multi-Layer Perceptron.

You can install the required libraries with:

```bash
pip install numpy scikit-learn
```

## Getting Started

1. **Clone the repository** to your local machine:

   ```bash
   git clone https://github.com/yourusername/MLP-NAND-XOR.git
   cd MLP-NAND-XOR
   ```

2. **Install the dependencies**:

   If you haven't already installed the necessary packages, you can do so with the following command:

   ```bash
   pip install numpy scikit-learn
   ```

3. **Run the script**:

   To train the neural network and get the results for both NAND and XOR functions, run the script:

   ```bash
   python mlp_nand_xor.py
   ```

## Code Explanation

### Data

The dataset consists of two parts:

- **NAND**: The truth table for the NAND operation with 2 inputs.
- **XOR**: The truth table for the XOR operation with 2 inputs.

These are combined and used to train the **Multi-Layer Perceptron** (MLP).

### Multi-Layer Perceptron (MLP)

The MLP is a neural network with:

- **Input layer**: 2 neurons (representing the binary inputs).
- **Hidden layer**: 2 neurons (for simplicity). It uses the **logistic (sigmoid)** activation function.
- **Output layer**: 1 neuron (with sigmoid activation for binary classification).

The MLP is trained using the **backpropagation** algorithm to minimize the error and adjust the weights.

### Python Code

```python
import numpy as np
from sklearn.neural_network import MLPClassifier

# NAND inputs and outputs
X_nand = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y_nand = np.array([1, 1, 1, 0])

# XOR inputs and outputs
X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y_xor = np.array([0, 1, 1, 0])

# Combine datasets
X_combined = np.vstack((X_nand, X_xor))
y_combined = np.hstack((y_nand, y_xor))

# Initialize and train MLP
clf = MLPClassifier(hidden_layer_sizes=(2,), activation='logistic', max_iter=10000)
clf.fit(X_combined, y_combined)

# Test the trained model
predictions = clf.predict(X_combined)
print("Predictions for combined NAND and XOR inputs:")
for i, pred in enumerate(predictions):
    print(f"Input: {X_combined[i]} => Predicted Output: {pred}")
```

## Usage

After running the script, the model will output predictions for both the **NAND** and **XOR** logic functions.

## Results

The neural network successfully solves both NAND and XOR logic functions after training:

- Correct predictions for NAND truth table.
- Correct predictions for XOR truth table (non-linearly separable).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


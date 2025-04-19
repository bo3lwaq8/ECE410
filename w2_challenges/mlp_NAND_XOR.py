import numpy as np
from sklearn.neural_network import MLPClassifier

# NAND function inputs and outputs
X_nand = np.array([[0, 0],
                   [0, 1],
                   [1, 0],
                   [1, 1]])

y_nand = np.array([1, 1, 1, 0])  # NAND outputs

# XOR function inputs and outputs
X_xor = np.array([[0, 0],
                  [0, 1],
                  [1, 0],
                  [1, 1]])

y_xor = np.array([0, 1, 1, 0])  # XOR outputs

# Combine NAND and XOR data
X_combined = np.vstack((X_nand, X_xor))
y_combined = np.hstack((y_nand, y_xor))

# Initialize and train the Multi-Layer Perceptron (MLP)
clf = MLPClassifier(hidden_layer_sizes=(2,), activation='logistic', max_iter=10000)
clf.fit(X_combined, y_combined)

# Test the trained model on both NAND and XOR
predictions = clf.predict(X_combined)
print("Predictions for combined NAND and XOR inputs:")
for i, pred in enumerate(predictions):
    print(f"Input: {X_combined[i]} => Predicted Output: {pred}")

# Testing the model individually for NAND and XOR
print("\nTesting for NAND function:")
for i in range(4):
    pred = clf.predict([X_nand[i]])
    print(f"Input: {X_nand[i]} => Predicted Output: {pred[0]}")

print("\nTesting for XOR function:")
for i in range(4):
    pred = clf.predict([X_xor[i]])
    print(f"Input: {X_xor[i]} => Predicted Output: {pred[0]}")

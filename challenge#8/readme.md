# Multi-Layer Perceptron for the XOR Problem

This project implements a simple Multi-Layer Perceptron (MLP) from scratch in Python to solve the classic XOR logical function. It demonstrates the necessity of hidden layers and the backpropagation algorithm for solving problems that are not linearly separable.

## The XOR Problem

The XOR (exclusive OR) function is a simple logical operation that outputs `1` only when its two inputs are different.

| Input 1 | Input 2 | Output |
| :-----: | :-----: | :----: |
|    0    |    0    |   0    |
|    0    |    1    |   1    |
|    1    |    0    |   1    |
|    1    |    1    |   0    |

If you plot these points, you'll see that a single straight line cannot separate the `0`s from the `1`s. This is why a single-layer perceptron fails at this task and a network with at least one hidden layer is required.

## Network Architecture

The network implemented here has a `2-2-1` architecture:
-   **Input Layer:** 2 neurons, representing the two inputs of the XOR function.
-   **Hidden Layer:** 2 neurons, which allow the network to learn a non-linear representation of the data.
-   **Output Layer:** 1 neuron, which gives the final predicted output.

The **Sigmoid function** is used as the activation function for all neurons.

## The Backpropagation Algorithm

Backpropagation is the algorithm used to train the network. It works in two main phases:

1.  **Forward Pass:** An input is passed through the network, and the final output is calculated. The activations of all neurons at each layer are stored.

2.  **Backward Pass (Error Propagation):**
    -   The error between the network's predicted output and the expected output is calculated.
    -   This error is propagated backward through the network, from the output layer to the hidden layer. At each layer, the algorithm calculates how much each neuron's weights contributed to the total error.
    -   The weights and biases are then adjusted in the direction that minimizes the error, using the calculated "deltas" and a specified learning rate.

This process is repeated for many epochs (iterations over the entire dataset) until the network's error is minimized and it can accurately predict the XOR outputs.

## How to Run

1.  Save the code as a Python file (e.g., `mlp_xor.py`).
2.  Ensure you have `numpy` installed:
    ```bash
    pip install numpy
    ```
3.  Run the script from your terminal:
    ```bash
    python mlp_xor.py
    ```

## Execution Output

When you run the script, it will print the training progress and then show the final predictions for each XOR input.



## Training the Multi-Level Perceptron 

--- Starting Training ---
Epoch 0     | Loss: 0.3081
Epoch 1000  | Loss: 0.2476
Epoch 2000  | Loss: 0.2366
Epoch 3000  | Loss: 0.2017
Epoch 4000  | Loss: 0.1731
Epoch 5000  | Loss: 0.0987
Epoch 6000  | Loss: 0.0245
Epoch 7000  | Loss: 0.0109
Epoch 8000  | Loss: 0.0067
Epoch 9000  | Loss: 0.0047
Epoch 10000 | Loss: 0.0036
Epoch 11000 | Loss: 0.0029
Epoch 12000 | Loss: 0.0024
Epoch 13000 | Loss: 0.0021
Epoch 14000 | Loss: 0.0018
Epoch 15000 | Loss: 0.0016
Epoch 16000 | Loss: 0.0014
Epoch 17000 | Loss: 0.0013
Epoch 18000 | Loss: 0.0012
Epoch 19000 | Loss: 0.0011
--- Training Complete ---

import numpy as np

class MLP_XOR:
    def __init__(self, input_size=2, hidden_size=2, output_size=1):
        """
        Initializes the weights and biases for the network with random values.
        Architecture: 2-2-1
        """
        # Weights for the hidden layer (2x2 matrix)
        self.weights_hidden = np.random.rand(input_size, hidden_size)
        # Biases for the hidden layer (1x2 matrix)
        self.bias_hidden = np.random.rand(1, hidden_size)
        
        # Weights for the output layer (2x1 matrix)
        self.weights_output = np.random.rand(hidden_size, output_size)
        # Bias for the output layer (1x1 matrix)
        self.bias_output = np.random.rand(1, output_size)

    def _sigmoid(self, x):
        """The Sigmoid activation function."""
        return 1 / (1 + np.exp(-x))

    def _sigmoid_derivative(self, x):
        """Derivative of the Sigmoid function."""
        return x * (1 - x)

    def feedforward(self, X):
        """
        Passes the input through the network to generate an output.
        Returns the activations of both the hidden and output layers.
        """
        # Input layer to hidden layer
        hidden_input = np.dot(X, self.weights_hidden) + self.bias_hidden
        hidden_activation = self._sigmoid(hidden_input)

        # Hidden layer to output layer
        output_input = np.dot(hidden_activation, self.weights_output) + self.bias_output
        output_activation = self._sigmoid(output_input)
        
        return hidden_activation, output_activation

    def backpropagate(self, X, y, hidden_activation, output_activation, learning_rate):
        """
        Performs the backpropagation algorithm to update the network's weights and biases.
        """
        # --- Calculate error and deltas for the output layer ---
        output_error = y - output_activation
        output_delta = output_error * self._sigmoid_derivative(output_activation)
        
        # --- Calculate error and deltas for the hidden layer ---
        # Propagate the output error back to the hidden layer
        hidden_error = np.dot(output_delta, self.weights_output.T)
        hidden_delta = hidden_error * self._sigmoid_derivative(hidden_activation)

        # --- Update weights and biases ---
        # Update output layer weights and bias
        self.weights_output += np.dot(hidden_activation.T, output_delta) * learning_rate
        self.bias_output += np.sum(output_delta, axis=0, keepdims=True) * learning_rate
        
        # Update hidden layer weights and bias
        self.weights_hidden += np.dot(X.T, hidden_delta) * learning_rate
        self.bias_hidden += np.sum(hidden_delta, axis=0, keepdims=True) * learning_rate

    def train(self, X, y, epochs=10000, learning_rate=0.1):
        """
        Trains the network for a specified number of epochs.
        """
        for epoch in range(epochs):
            # Perform a full feedforward and backpropagation cycle
            hidden_activation, output_activation = self.feedforward(X)
            self.backpropagate(X, y, hidden_activation, output_activation, learning_rate)

            # Print the error at certain intervals
            if epoch % 1000 == 0:
                loss = np.mean(np.square(y - output_activation))
                print(f"Epoch {epoch:<5} | Loss: {loss:.4f}")
    
    def predict(self, X):
        """Makes a prediction for a given input."""
        _, output = self.feedforward(X)
        # Round the output to get a binary prediction (0 or 1)
        return np.round(output)

# --- Main execution ---
if __name__ == "__main__":
    # Define the XOR dataset
    X_train = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y_train = np.array([[0], [1], [1], [0]])

    # Create and train the MLP
    mlp = MLP_XOR()
    print("--- Starting Training ---")
    mlp.train(X_train, y_train, epochs=20000, learning_rate=0.1)
    print("--- Training Complete ---\n")

    # Test the trained network
    print("--- Testing the Trained Network ---")
    for x_input, y_expected in zip(X_train, y_train):
        prediction = mlp.predict(x_input.reshape(1, -1))
        print(f"Input: {x_input} | Expected: {y_expected[0]} | Predicted: {int(prediction[0][0])}")

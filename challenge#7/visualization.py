import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sklearn.datasets import make_blobs

# --- 1. Perceptron Implementation ---

class Perceptron:
    """
    A simple Perceptron classifier.
    """
    def __init__(self, learning_rate=0.1, n_iters=100):
        self.lr = learning_rate
        self.n_iters = n_iters
        self.weights = None
        self.bias = None
        # History to store weights and bias for visualization
        self.history = []

    def _activation_function(self, x):
        # Heaviside step function
        return np.where(x >= 0, 1, 0)

    def fit(self, X, y):
        """
        Fit training data. The method is a generator that yields
        the state after each update for animation purposes.
        """
        n_samples, n_features = X.shape

        # Initialize weights and bias
        self.weights = np.zeros(n_features)
        self.bias = 0

        # Store initial state
        self.history.append((self.weights.copy(), self.bias))
        yield

        # Main learning loop
        for epoch in range(self.n_iters):
            updated_in_epoch = False
            for idx, x_i in enumerate(X):
                # Calculate linear combination and predict
                linear_output = np.dot(x_i, self.weights) + self.bias
                y_predicted = self._activation_function(linear_output)

                # Perceptron update rule
                if y_predicted != y[idx]:
                    update = self.lr * (y[idx] - y_predicted)
                    self.weights += update * x_i
                    self.bias += update
                    updated_in_epoch = True
                    
                    # Store state after update
                    self.history.append((self.weights.copy(), self.bias))
                    yield # Yield control for the animation to draw this step

            # If no updates were made in a full epoch, the data is separated
            if not updated_in_epoch:
                print(f"Convergence reached at epoch {epoch+1}")
                # Pad history to show the final line for a few frames
                for _ in range(20): yield
                return

        print("Reached max iterations without full convergence.")
        for _ in range(20): yield
        return


# --- 2. Data Generation and Setup ---

# Generate a linearly separable dataset with 2 features
X, y = make_blobs(n_samples=100, n_features=2, centers=2, cluster_std=1.05, random_state=42)

# Instantiate and prepare the perceptron
p = Perceptron(learning_rate=0.1, n_iters=100)

# The training process is now a generator
training_generator = p.fit(X, y)

# --- 3. Animation and Visualization ---

# Set up the plot
fig, ax = plt.subplots(figsize=(8, 6))
plt.style.use('seaborn-v0_8-whitegrid')
ax.set_title("Perceptron Learning Process")
ax.set_xlabel("Feature 1")
ax.set_ylabel("Feature 2")
ax.set_xlim(X[:, 0].min() - 1, X[:, 0].max() + 1)
ax.set_ylim(X[:, 1].min() - 1, X[:, 1].max() + 1)

# Plot the data points
ax.scatter(X[:, 0], X[:, 1], c=y, cmap='viridis', marker='o', edgecolors='k')

# Initialize an empty line object for the decision boundary
line, = ax.plot([], [], 'r-', lw=2)
info_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12)

def init():
    """Initializes the plot for the animation."""
    line.set_data([], [])
    info_text.set_text('')
    return line, info_text

def update(frame):
    """
    Update function for the animation. This function is called for each frame.
    It advances the training generator by one step and redraws the decision boundary.
    """
    try:
        # Get the next state from the training generator
        next(training_generator)
        
        # Get the current weights and bias from history
        weights, bias = p.history[-1]
        step_number = len(p.history) - 1

        # Calculate the decision boundary line
        # w1*x1 + w2*x2 + b = 0  =>  x2 = (-w1*x1 - b) / w2
        x0 = np.array([ax.get_xlim()[0], ax.get_xlim()[1]])
        if weights[1] != 0: # Avoid division by zero
            x1 = (-weights[0] * x0 - bias) / weights[1]
            line.set_data(x0, x1)
        
        info_text.set_text(f'Update Step: {step_number}')

    except StopIteration:
        # The generator is exhausted, meaning training is complete
        info_text.set_text(f'Training Complete! Steps: {len(p.history)-1}')

    return line, info_text

# Create the animation
# The interval is the delay between frames in milliseconds.
ani = FuncAnimation(fig, update, frames=p.n_iters*len(X), init_func=init, blit=True, interval=50, repeat=False)

# Display the plot
plt.show()


import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

def logistic_growth(t, y, r, K):
    """Defines the logistic differential equation."""
    return r * y * (1 - y / K)

def solve_logistic():
    # Parameters for the logistic equation
    r = 0.5        # growth rate
    K = 100        # carrying capacity
    y0 = [10]      # initial condition
    t_span = (0, 20)
    
    # Solve the differential equation using a dense output method
    sol = solve_ivp(logistic_growth, t_span, y0, args=(r, K), dense_output=True)
    
    # Create time points for plotting
    t = np.linspace(t_span[0], t_span[1], 200)
    y = sol.sol(t)[0]
    
    # Plot the solution
    plt.plot(t, y, label="Population")
    plt.xlabel("Time")
    plt.ylabel("Population")
    plt.title("Logistic Growth Model")
    plt.legend()
    plt.show()

def main():
    """Entry point for profiling / direct run."""
    solve_logistic()

if __name__ == "__main__":
    main()

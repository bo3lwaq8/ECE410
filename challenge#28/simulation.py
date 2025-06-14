import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

def biolek_memristor_model(y, t, R_on, R_off, k, alpha, V_p, V_n, V_app_func):
    """
    Defines the differential equations for the Biolek memristor model.

    Args:
        y (list): A list containing the current state variable x.
        t (float): The current time step.
        R_on (float): Resistance in the ON state.
        R_off (float): Resistance in the OFF state.
        k (float): A parameter related to the speed of ion movement.
        alpha (float): A parameter for the state variable differential equation.
        V_p (float): Positive voltage threshold.
        V_n (float): Negative voltage threshold.
        V_app_func (function): A function that returns the applied voltage at time t.

    Returns:
        float: The derivative of the state variable x (dx/dt).
    """
    x = y[0]
    v = V_app_func(t)
    
    # Biolek window function f(x)
    f_x = 1 - (2 * x - 1)**(2)

    # Differential equation for the internal state variable x
    if v > V_p:
        dx_dt = k * (v - V_p)**alpha * f_x
    elif v < V_n:
        dx_dt = k * (v - V_n)**alpha * f_x
    else:
        dx_dt = 0
        
    return dx_dt

def simulate_and_plot_iv_curve():
    """
    Simulates the memristor's response to a sinusoidal voltage
    and plots the characteristic I-V pinched hysteresis loop.
    """
    # --- Model Parameters ---
    # These are typical parameters for a TiO2-based memristor model
    R_on = 100      # Resistance when fully ON (ohms)
    R_off = 16000   # Resistance when fully OFF (ohms)
    k = 1e4         # Controls switching speed
    alpha = 1       # Controls non-linearity of ion movement
    V_p = 0.17      # Positive voltage threshold for switching
    V_n = -0.17     # Negative voltage threshold for switching
    x_0 = 0.1       # Initial state (0 <= x <= 1)

    # --- Simulation Setup ---
    frequency = 1   # Frequency of the input sine wave (Hz)
    amplitude = 0.4 # Amplitude of the input voltage (V)
    
    # Define the applied voltage as a function of time
    V_app_func = lambda t: amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Time vector for the simulation
    t = np.linspace(0, 2 / frequency, 2000) # Simulate for two cycles

    # --- Solve the ODE ---
    # Use odeint to solve the differential equation for the state variable x(t)
    solution = odeint(biolek_memristor_model, x_0, t, args=(R_on, R_off, k, alpha, V_p, V_n, V_app_func))
    x_t = solution[:, 0]
    
    # Clamp the state variable x to be between 0 and 1
    x_t = np.clip(x_t, 0, 1)

    # --- Calculate Memristance and Current ---
    # Memristance M(t) = R_on * x(t) + R_off * (1 - x(t))
    M_t = R_on * x_t + R_off * (1 - x_t)
    
    # Applied voltage V(t)
    V_t = V_app_func(t)
    
    # Current I(t) = V(t) / M(t)
    I_t = V_t / M_t

    # --- Plotting ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(V_t, I_t, color='royalblue', linewidth=2)
    
    ax.set_title('Memristor I-V Curve: Pinched Hysteresis Loop', fontsize=14)
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (A)', fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Add arrows to show the direction of the loop
    ax.arrow(V_t[500], I_t[500], V_t[501]-V_t[500], I_t[501]-I_t[500], 
             head_width=0.015, head_length=0.02, fc='black', ec='black')
    ax.arrow(V_t[1500], I_t[1500], V_t[1501]-V_t[1500], I_t[1501]-I_t[1500], 
             head_width=0.015, head_length=0.02, fc='black', ec='black')
             
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    simulate_and_plot_iv_curve()

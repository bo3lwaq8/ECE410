import numpy as np
import random

def calculate_distance_matrix(cities):
    """Calculate the Euclidean distance matrix for city coordinates."""
    n = len(cities)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = np.linalg.norm(np.array(cities[i]) - np.array(cities[j]))
    return D

def nearest_neighbor_tsp(D):
    """
    Solve the TSP using a nearest-neighbor heuristic.
    Returns the route as a list of city indices.
    """
    n = len(D)
    visited = [False] * n
    route = [0]  # Start at city 0
    visited[0] = True

    for _ in range(1, n):
        last = route[-1]
        # Find the closest unvisited city
        next_city = np.argmin([D[last][j] if not visited[j] else np.inf for j in range(n)])
        route.append(next_city)
        visited[next_city] = True

    return route

def total_distance(route, D):
    """Compute the total distance of the given route, returning to the start."""
    distance = 0
    for i in range(len(route) - 1):
        distance += D[route[i], route[i+1]]
    distance += D[route[-1], route[0]]  # Return to starting city
    return distance

def main():
    """Entry point for profiling / direct run."""
    # Generate random city coordinates (e.g., 10 cities)
    num_cities = 10
    cities = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(num_cities)]
    
    # Calculate the distance matrix
    D = calculate_distance_matrix(cities)
    
    # Solve the TSP
    route = nearest_neighbor_tsp(D)
    dist = total_distance(route, D)
    
    print("TSP route (by city indices):", route)
    print("Total distance:", dist)

if __name__ == "__main__":
    main()

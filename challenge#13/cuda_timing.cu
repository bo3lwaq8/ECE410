#include <iostream>
#include <cmath>
#include <iomanip>

// CUDA kernel to add elements of two arrays
__global__ void add(long long n, float *x, float *y) {
    int index = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;
    for (int i = index; i < n; i += stride) {
        y[i] = x[i] + y[i];
    }
}

// Helper function to handle CUDA errors
void checkCuda(cudaError_t result) {
    if (result != cudaSuccess) {
        fprintf(stderr, "CUDA Error: %s\n", cudaGetErrorString(result));
        exit(99);
    }
}

int main(void) {
    // Set up timing events
    cudaEvent_t start, stop;
    cudaEvent_t kernelStart, kernelStop;
    checkCuda(cudaEventCreate(&start));
    checkCuda(cudaEventCreate(&stop));
    checkCuda(cudaEventCreate(&kernelStart));
    checkCuda(cudaEventCreate(&kernelStop));

    std::cout << "Running vector addition for various matrix sizes...\n\n";
    std::cout << std::left << std::setw(12) << "Matrix Size"
              << std::left << std::setw(12) << "N"
              << std::left << std::setw(20) << "Total Time (ms)"
              << std::left << std::setw(20) << "Kernel Time (ms)" << std::endl;
    std::cout << "----------------------------------------------------------------\n";

    // Loop over matrix sizes from 2^15 to 2^25
    for (int i = 15; i <= 25; ++i) {
        long long N = 1LL << i;
        float *x, *y;
        float *d_x, *d_y;
        float total_time_ms, kernel_time_ms;

        // Start timing for total execution
        checkCuda(cudaEventRecord(start));

        // Allocate memory on the host (CPU)
        x = new float[N];
        y = new float[N];

        // Allocate memory on the device (GPU)
        checkCuda(cudaMalloc(&d_x, N * sizeof(float)));
        checkCuda(cudaMalloc(&d_y, N * sizeof(float)));

        // Initialize host arrays
        for (long long j = 0; j < N; j++) {
            x[j] = 1.0f;
            y[j] = 2.0f;
        }

        // Copy data from host to device
        checkCuda(cudaMemcpy(d_x, x, N * sizeof(float), cudaMemcpyHostToDevice));
        checkCuda(cudaMemcpy(d_y, y, N * sizeof(float), cudaMemcpyHostToDevice));

        // Set up execution configuration
        int blockSize = 256;
        int numBlocks = (N + blockSize - 1) / blockSize;

        // Start timing for kernel execution
        checkCuda(cudaEventRecord(kernelStart));

        // Launch the kernel
        add<<<numBlocks, blockSize>>>(N, d_x, d_y);

        // Stop timing for kernel execution
        checkCuda(cudaEventRecord(kernelStop));
        
        // Synchronize to make sure kernel is finished before getting results
        checkCuda(cudaDeviceSynchronize());

        // Copy results from device to host
        checkCuda(cudaMemcpy(y, d_y, N * sizeof(float), cudaMemcpyDeviceToHost));

        // Stop timing for total execution
        checkCuda(cudaEventRecord(stop));
        checkCuda(cudaEventSynchronize(stop));

        // Calculate elapsed times
        checkCuda(cudaEventElapsedTime(&total_time_ms, start, stop));
        checkCuda(cudaEventElapsedTime(&kernel_time_ms, kernelStart, kernelStop));
        
        // Print results for the current size
        std::cout << std::left << std::setw(12) << ("2^" + std::to_string(i))
                  << std::left << std::setw(12) << N
                  << std::left << std::setw(20) << total_time_ms
                  << std::left << std::setw(20) << kernel_time_ms << std::endl;

        // Free device and host memory
        checkCuda(cudaFree(d_x));
        checkCuda(cudaFree(d_y));
        delete[] x;
        delete[] y;
    }

    // Destroy events
    checkCuda(cudaEventDestroy(start));
    checkCuda(cudaEventDestroy(stop));
    checkCuda(cudaEventDestroy(kernelStart));
    checkCuda(cudaEventDestroy(kernelStop));

    return 0;
}

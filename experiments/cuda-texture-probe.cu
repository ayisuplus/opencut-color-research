// Source-owned CUDA texture measurement, independent of Resolve binaries.
#include <cuda_runtime.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void check(cudaError_t code) {
    if (code != cudaSuccess) {
        std::fprintf(stderr, "CUDA: %s\n", cudaGetErrorString(code));
        std::exit(1);
    }
}

__global__ void sample(cudaTextureObject_t texture, const float* coordinates,
                       float* results, unsigned count) {
    unsigned i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < count) results[i] = tex1D<float>(texture, coordinates[i]);
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    FILE* input = std::fopen(argv[1], "rb");
    if (!input) return 3;
    uint32_t header[4]; // magic, table width, table count, coordinate count
    if (std::fread(header, sizeof(header), 1, input) != 1) return 4;
    if (header[0] != 0x31585448 || header[1] != 1024 ||
        header[2] == 0 || header[2] > 8 || header[3] == 0 || header[3] > 4096) return 5;
    unsigned width = header[1], tables = header[2], count = header[3];
    std::vector<float> values(width * tables), coordinates(count), result(count * tables);
    if (std::fread(values.data(), sizeof(float), values.size(), input) != values.size() ||
        std::fread(coordinates.data(), sizeof(float), count, input) != count ||
        std::fgetc(input) != EOF) return 6;
    std::fclose(input);

    cudaDeviceProp device;
    int runtime, driver;
    check(cudaGetDeviceProperties(&device, 0));
    check(cudaRuntimeGetVersion(&runtime));
    check(cudaDriverGetVersion(&driver));
    float *gpu_coordinates, *gpu_result;
    check(cudaMalloc(&gpu_coordinates, count * sizeof(float)));
    check(cudaMalloc(&gpu_result, count * sizeof(float)));
    check(cudaMemcpy(gpu_coordinates, coordinates.data(), count * sizeof(float), cudaMemcpyHostToDevice));
    cudaChannelFormatDesc channel = cudaCreateChannelDesc<float>();
    cudaArray_t array;
    check(cudaMallocArray(&array, &channel, width));
    cudaResourceDesc resource{};
    resource.resType = cudaResourceTypeArray;
    resource.res.array.array = array;
    cudaTextureDesc descriptor{};
    descriptor.addressMode[0] = cudaAddressModeClamp;
    descriptor.filterMode = cudaFilterModeLinear;
    descriptor.readMode = cudaReadModeElementType;
    descriptor.normalizedCoords = 1;
    cudaTextureObject_t texture;
    check(cudaCreateTextureObject(&texture, &resource, &descriptor, nullptr));
    for (unsigned t = 0; t < tables; ++t) {
        check(cudaMemcpyToArray(array, 0, 0, values.data() + t * width,
                                width * sizeof(float), cudaMemcpyHostToDevice));
        sample<<<(count + 127) / 128, 128>>>(texture, gpu_coordinates, gpu_result, count);
        check(cudaGetLastError());
        check(cudaDeviceSynchronize());
        check(cudaMemcpy(result.data() + t * count, gpu_result,
                          count * sizeof(float), cudaMemcpyDeviceToHost));
    }
    check(cudaDestroyTextureObject(texture));
    check(cudaFreeArray(array));
    check(cudaFree(gpu_coordinates));
    check(cudaFree(gpu_result));
    FILE* output = std::fopen(argv[2], "wb");
    if (!output) return 7;
    if (std::fwrite(header, sizeof(header), 1, output) != 1 ||
        std::fwrite(result.data(), sizeof(float), result.size(), output) != result.size()) return 8;
    if (std::fclose(output) != 0) return 9;
    std::printf("{\"device\":\"%s\",\"compute\":[%d,%d],\"runtime\":%d,\"driver\":%d,\"tables\":%u,\"coordinates\":%u}\n",
                device.name, device.major, device.minor, runtime, driver, tables, count);
}

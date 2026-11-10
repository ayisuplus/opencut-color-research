// Source-owned float32 HDR reference probe; no target code or process access.
#include <cuda_runtime.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>

struct Pixel { float rgb[3]; uint32_t gamma; };
static_assert(sizeof(Pixel) == 16, "Pixel binary layout");

static void check(cudaError_t code) {
    if (code != cudaSuccess) {
        std::fprintf(stderr, "CUDA: %s\n", cudaGetErrorString(code));
        std::exit(1);
    }
}

__device__ float fast_exp2(float v) {
    float result;
    asm("ex2.approx.ftz.f32 %0, %1;" : "=f"(result) : "f"(v));
    return result;
}
__device__ float power(float v, float exponent) {
    return copysignf(fast_exp2(exponent * __log2f(fabsf(v))), v);
}
__device__ float decode709(float v) {
    return v <= .081f ? __fdividef(v, 4.5f)
        : power(__fdividef(v + .099f, 1.099f), 2.2222222222f);
}
__device__ float encode709(float v) {
    return v <= .018f ? v * 4.5f : fmaf(1.099f, power(v, .45f), -.099f);
}
__device__ float decode(float v, uint32_t gamma) {
    if (gamma == 0) return power(v, 2.4f);
    return v <= .04045f ? __fdividef(v, 12.92f)
        : power(__fdividef(v + .055f, 1.055f), 2.4f);
}
__device__ float encode(float v, uint32_t gamma) {
    if (gamma == 0) return power(v, .4166666667f);
    return v <= .0031308f ? v * 12.92f : fmaf(1.055f, power(v, .4166666667f), -.055f);
}
__device__ void matrix(const float* m, const float* v, float* out) {
    for (int row = 0; row < 3; ++row)
        out[row] = fmaf(m[row*3+2], v[2], fmaf(m[row*3], v[0], m[row*3+1] * v[1]));
}

__global__ void probe(cudaTextureObject_t texture, const float* table,
                      const Pixel* pixels, const float* matrices, float* output,
                      unsigned count, int matrix_mode, int interpolation) {
    unsigned i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= count) return;
    float work[3], value[3], adjusted[3], returned[3];
    for (int c = 0; c < 3; ++c)
        work[c] = decode709(power(decode(pixels[i].rgb[c], pixels[i].gamma), .4166666667f));
    float y;
    if (matrix_mode) {
        matrix(matrices, work, value);
        y = value[1];
    } else {
        for (int c = 0; c < 3; ++c) value[c] = work[c];
        y = fmaf(.0722f, work[2], fmaf(.2126f, work[0], .7152f * work[1])) * 100.f;
    }
    float q = __log2f(__fdividef(fminf(fmaxf(y, .0703125f), 4608.f), 18.f));
    float u = __fdividef(q + 8.f, 16.f);
    float t;
    if (interpolation == 0) {
        t = tex1D<float>(texture, u);
    } else {
        float position = u * 1024.f - .5f;
        int index = (int)floorf(position);
        float alpha = position - (float)index;
        int low = min(max(index, 0), 1023), high = min(max(index + 1, 0), 1023);
        t = (1.f - alpha) * table[low] + alpha * table[high];
    }
    float gain = fast_exp2(t - q);
    for (int c = 0; c < 3; ++c) adjusted[c] = value[c] * gain;
    if (matrix_mode) matrix(matrices + 9, adjusted, returned);
    else for (int c = 0; c < 3; ++c) returned[c] = adjusted[c];
    float* trace = output + i * 10;
    for (int c = 0; c < 3; ++c) {
        trace[c] = work[c];
        trace[7+c] = encode(power(encode709(returned[c]), 2.4f), pixels[i].gamma);
    }
    trace[3] = q; trace[4] = u; trace[5] = t; trace[6] = gain;
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    FILE* input = std::fopen(argv[1], "rb");
    if (!input) return 3;
    uint32_t h[5]; // magic, width, tables, pixels, trace floats
    if (std::fread(h, sizeof(h), 1, input) != 1 || h[0] != 0x32584448 ||
        h[1] != 1024 || h[2] != 2 || h[3] == 0 || h[3] > 4096 || h[4] != 10) return 4;
    unsigned count = h[3];
    std::vector<float> tables(2048), matrices(18), results(2*2*2*count*10);
    std::vector<Pixel> pixels(count);
    if (std::fread(tables.data(), sizeof(float), tables.size(), input) != tables.size() ||
        std::fread(matrices.data(), sizeof(float), 18, input) != 18 ||
        std::fread(pixels.data(), sizeof(Pixel), count, input) != count || std::fgetc(input) != EOF) return 5;
    std::fclose(input);
    for (const auto& p : pixels) if (p.gamma != 0 && p.gamma != 5) return 6;
    Pixel* gpu_pixels; float *gpu_table, *gpu_matrices, *gpu_output;
    check(cudaMalloc(&gpu_pixels, count*sizeof(Pixel)));
    check(cudaMalloc(&gpu_table, 1024*sizeof(float)));
    check(cudaMalloc(&gpu_matrices, 18*sizeof(float)));
    check(cudaMalloc(&gpu_output, count*10*sizeof(float)));
    check(cudaMemcpy(gpu_pixels, pixels.data(), count*sizeof(Pixel), cudaMemcpyHostToDevice));
    check(cudaMemcpy(gpu_matrices, matrices.data(), 18*sizeof(float), cudaMemcpyHostToDevice));
    cudaChannelFormatDesc channel = cudaCreateChannelDesc<float>();
    cudaArray_t array; check(cudaMallocArray(&array, &channel, 1024));
    cudaResourceDesc resource{}; resource.resType = cudaResourceTypeArray; resource.res.array.array = array;
    cudaTextureDesc descriptor{};
    descriptor.addressMode[0] = cudaAddressModeClamp;
    descriptor.filterMode = cudaFilterModeLinear; descriptor.readMode = cudaReadModeElementType;
    descriptor.normalizedCoords = 1;
    cudaTextureObject_t texture; check(cudaCreateTextureObject(&texture, &resource, &descriptor, nullptr));
    for (int t = 0; t < 2; ++t) {
        check(cudaMemcpyToArray(array, 0, 0, tables.data()+t*1024, 1024*sizeof(float), cudaMemcpyHostToDevice));
        check(cudaMemcpy(gpu_table, tables.data()+t*1024, 1024*sizeof(float), cudaMemcpyHostToDevice));
        for (int m = 0; m < 2; ++m) for (int a = 0; a < 2; ++a) {
            probe<<<(count+127)/128,128>>>(texture,gpu_table,gpu_pixels,gpu_matrices,gpu_output,count,m,a);
            check(cudaGetLastError()); check(cudaDeviceSynchronize());
            check(cudaMemcpy(results.data()+((t*2+m)*2+a)*count*10, gpu_output,
                             count*10*sizeof(float), cudaMemcpyDeviceToHost));
        }
    }
    check(cudaDestroyTextureObject(texture)); check(cudaFreeArray(array));
    check(cudaFree(gpu_pixels)); check(cudaFree(gpu_table)); check(cudaFree(gpu_matrices)); check(cudaFree(gpu_output));
    FILE* output = std::fopen(argv[2], "wb"); if (!output) return 7;
    if (std::fwrite(h, sizeof(h), 1, output) != 1 ||
        std::fwrite(results.data(), sizeof(float), results.size(), output) != results.size() || std::fclose(output) != 0) return 8;
    cudaDeviceProp device; int runtime, driver;
    check(cudaGetDeviceProperties(&device, 0)); check(cudaRuntimeGetVersion(&runtime)); check(cudaDriverGetVersion(&driver));
    std::printf("{\"device\":\"%s\",\"compute\":[%d,%d],\"runtime\":%d,\"driver\":%d,\"pixels\":%u,\"models\":8,\"trace_floats\":10}\n",
                device.name,device.major,device.minor,runtime,driver,count);
}

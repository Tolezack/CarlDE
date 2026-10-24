#pragma once
// BrainrotCode 1.0: header-only, C++17. Terrain/UV require only the standard library.
// To use the OpenGL window shortcut, define BRAINROT_ENABLE_GLFW and link GLFW + OpenGL.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef BRAINROT_ENABLE_GLFW
#include <GLFW/glfw3.h>
#endif

namespace br {
struct Vec2 { float u, v; };
struct Vec3 { float x, y, z; };
struct Mesh { std::vector<Vec3> vertices; std::vector<Vec2> uv; std::vector<std::uint32_t> indices; };

inline std::array<Vec2, 4> block_uv(int tile, int columns = 16, int rows = 16, float inset = 0.0005f) {
    if (columns <= 0 || rows <= 0 || tile < 0 || tile >= columns * rows || inset < 0 || inset >= .25f)
        throw std::invalid_argument("Invalid atlas tile or dimensions");
    const int x = tile % columns, y = tile / columns;
    const float u0 = (x + inset) / columns, v0 = (y + inset) / rows;
    const float u1 = (x + 1.0f - inset) / columns, v1 = (y + 1.0f - inset) / rows;
    return {{{u0, v1}, {u1, v1}, {u1, v0}, {u0, v0}}};
}

inline Mesh block_mesh(const std::array<int,6>& tiles, int columns = 16, int rows = 16, float size = 1.0f) {
    // Faces: front, back, left, right, top, bottom; outward CCW triangles.
    const float h = size / 2.0f;
    const std::array<std::array<Vec3,4>,6> faces = {{
        {{Vec3{-h,-h,h}, Vec3{h,-h,h}, Vec3{h,h,h}, Vec3{-h,h,h}}},
        {{Vec3{h,-h,-h}, Vec3{-h,-h,-h}, Vec3{-h,h,-h}, Vec3{h,h,-h}}},
        {{Vec3{-h,-h,-h}, Vec3{-h,-h,h}, Vec3{-h,h,h}, Vec3{-h,h,-h}}},
        {{Vec3{h,-h,h}, Vec3{h,-h,-h}, Vec3{h,h,-h}, Vec3{h,h,h}}},
        {{Vec3{-h,h,h}, Vec3{h,h,h}, Vec3{h,h,-h}, Vec3{-h,h,-h}}},
        {{Vec3{-h,-h,-h}, Vec3{h,-h,-h}, Vec3{h,-h,h}, Vec3{-h,-h,h}}}
    }};
    Mesh mesh;
    mesh.vertices.reserve(24); mesh.uv.reserve(24); mesh.indices.reserve(36);
    for (int f = 0; f < 6; ++f) {
        auto coords = block_uv(tiles[f], columns, rows);
        for (int j = 0; j < 4; ++j) { mesh.vertices.push_back(faces[f][j]); mesh.uv.push_back(coords[j]); }
        const auto b = static_cast<std::uint32_t>(f * 4);
        for (auto i : {0u, 1u, 2u, 0u, 2u, 3u}) mesh.indices.push_back(b + i);
    }
    return mesh;
}

inline std::uint32_t hash(int x, int y, std::uint32_t seed) {
    std::uint32_t h = seed ^ (static_cast<std::uint32_t>(x) * 0x9e3779b9U)
                           ^ (static_cast<std::uint32_t>(y) * 0x85ebca6bU);
    h ^= h >> 16; h *= 0x7feb352dU; h ^= h >> 15; h *= 0x846ca68bU; h ^= h >> 16;
    return h;
}
inline float smooth(float t) { return t*t*(3.f-2.f*t); }
inline float mix(float a, float b, float t) { return a+(b-a)*t; }
inline float value_noise(float x, float z, unsigned seed) {
    int xi = static_cast<int>(std::floor(x)), zi = static_cast<int>(std::floor(z));
    float fx = smooth(x - xi), fz = smooth(z - zi);
    auto rand = [seed](int a,int b) { return (hash(a,b,seed) & 0xffffffU) / 8388607.5f - 1.f; };
    return mix(mix(rand(xi,zi),rand(xi+1,zi),fx),
               mix(rand(xi,zi+1),rand(xi+1,zi+1),fx),fz);
}
inline std::vector<float> terrain(int width, int depth, unsigned seed = 42,
                                  float scale = 48.0f, int octaves = 4) {
    if (width <= 0 || depth <= 0 || width > 8192 || depth > 8192 || scale <= 0 || octaves < 1 || octaves > 12)
        throw std::invalid_argument("Invalid terrain dimensions or noise settings");
    std::vector<float> map(static_cast<size_t>(width) * depth);
    for (int z = 0; z < depth; ++z) for (int x = 0; x < width; ++x) {
        float amplitude = 1.f, frequency = 1.f, sum = 0.f, total = 0.f;
        for (int i = 0; i < octaves; ++i) {
            sum += value_noise(x * frequency / scale, z * frequency / scale, seed+i*137U) * amplitude;
            total += amplitude; amplitude *= .5f; frequency *= 2.f;
        }
        map[static_cast<size_t>(z) * width + x] = sum / total;
    }
    return map;
}
#ifdef BRAINROT_ENABLE_GLFW
inline void window(const std::string& title = "BrainrotCode", int width = 960, int height = 540) {
    if (width < 1 || height < 1 || !glfwInit()) throw std::runtime_error("Cannot initialize GLFW");
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR,3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR,3);
    GLFWwindow* win = glfwCreateWindow(width,height,title.c_str(),nullptr,nullptr);
    if (!win) { glfwTerminate(); throw std::runtime_error("Cannot create OpenGL window"); }
    glfwMakeContextCurrent(win); glfwSwapInterval(1);
    while (!glfwWindowShouldClose(win)) {
        if (glfwGetKey(win, GLFW_KEY_ESCAPE) == GLFW_PRESS) glfwSetWindowShouldClose(win, 1);
        int w, h; glfwGetFramebufferSize(win, &w, &h);
        glViewport(0,0,w,h); glClearColor(.09f,.13f,.19f,1.f); glClear(GL_COLOR_BUFFER_BIT);
        glfwSwapBuffers(win); glfwPollEvents();
    }
    glfwDestroyWindow(win); glfwTerminate();
}
#endif
}

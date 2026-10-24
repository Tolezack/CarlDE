// BrainrotCode 1.0: drop into a C# OpenTK project. Requires OpenTK 4.x via NuGet.
using System;
using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;

namespace BrainrotCode;

public static class Brainrot
{
    // ONE line: Brainrot.Window("Game", 960, 540);
    public static void Window(string title = "BrainrotCode", int width = 960, int height = 540)
    {
        using var game = new SimpleOpenGLWindow(title, width, height);
        game.Run();
    }

    // Values between -1 and 1; flattened map [z * width + x].
    public static float[] Terrain(int width, int depth, uint seed = 42, float scale = 48f, int octaves = 4)
    {
        if (width < 1 || depth < 1 || width > 8192 || depth > 8192 || scale <= 0 || octaves is < 1 or > 12)
            throw new ArgumentOutOfRangeException(nameof(width));
        var result = new float[checked(width * depth)];
        for (int z = 0; z < depth; z++) for (int x = 0; x < width; x++)
        {
            float amp = 1, freq = 1, sum = 0, total = 0;
            for (int i = 0; i < octaves; i++)
            {
                sum += Noise(x * freq / scale, z * freq / scale, seed + (uint)i * 137u) * amp;
                total += amp; amp *= .5f; freq *= 2;
            }
            result[z * width + x] = sum / total;
        }
        return result;
    }

    public readonly record struct UV(float U, float V);
    public readonly record struct Vertex(float X, float Y, float Z, float U, float V);
    public sealed record Mesh(Vertex[] Vertices, uint[] Indices);

    // Face order: front, back, left, right, top, bottom.
    public static UV[] BlockUV(int tile, int columns = 16, int rows = 16, float inset = .0005f)
    {
        if (columns < 1 || rows < 1 || tile < 0 || tile >= columns * rows || inset < 0 || inset >= .25f)
            throw new ArgumentOutOfRangeException(nameof(tile));
        int x = tile % columns, y = tile / columns;
        float u0 = (x + inset) / columns, v0 = (y + inset) / rows;
        float u1 = (x + 1f - inset) / columns, v1 = (y + 1f - inset) / rows;
        return new[] { new UV(u0,v1), new UV(u1,v1), new UV(u1,v0), new UV(u0,v0) };
    }

    // 24 vertices and 36 indices with per-face atlas UV.
    public static Mesh Block(int[] faceTiles, int cols = 16, int rows = 16, float size = 1)
    {
        if (faceTiles is null || faceTiles.Length != 6) throw new ArgumentException("Expected six face tiles");
        float h = size * .5f;
        float[][][] faces = {
            new[] {new[]{-h,-h,h},new[]{h,-h,h},new[]{h,h,h},new[]{-h,h,h}},
            new[] {new[]{h,-h,-h},new[]{-h,-h,-h},new[]{-h,h,-h},new[]{h,h,-h}},
            new[] {new[]{-h,-h,-h},new[]{-h,-h,h},new[]{-h,h,h},new[]{-h,h,-h}},
            new[] {new[]{h,-h,h},new[]{h,-h,-h},new[]{h,h,-h},new[]{h,h,h}},
            new[] {new[]{-h,h,h},new[]{h,h,h},new[]{h,h,-h},new[]{-h,h,-h}},
            new[] {new[]{-h,-h,-h},new[]{h,-h,-h},new[]{h,-h,h},new[]{-h,-h,h}}
        };
        var vertices = new Vertex[24]; var indices = new uint[36];
        for (int f = 0; f < 6; f++)
        {
            UV[] uv = BlockUV(faceTiles[f],cols,rows);
            for (int v = 0; v < 4; v++)
                vertices[f*4+v] = new Vertex(faces[f][v][0],faces[f][v][1],faces[f][v][2],uv[v].U,uv[v].V);
            uint b = (uint)(f*4);
            for (int i = 0; i < 6; i++) indices[f*6+i] = b + new uint[]{0,1,2,0,2,3}[i];
        }
        return new Mesh(vertices,indices);
    }

    private static uint Hash(int x, int y, uint seed)
    {
        unchecked {
            uint value = seed ^ ((uint)x * 0x9e3779b9U) ^ ((uint)y * 0x85ebca6bU);
            value ^= value >> 16; value *= 0x7feb352dU;
            value ^= value >> 15; value *= 0x846ca68bU;
            return value ^ (value >> 16);
        }
    }
    private static float Noise(float x,float z,uint seed)
    {
        int xi = (int)MathF.Floor(x), zi = (int)MathF.Floor(z);
        float a = x-xi, b = z-zi;
        a = a*a*(3-2*a); b = b*b*(3-2*b);
        float R(int i,int j) => (Hash(i,j,seed) & 0xffffffU) / 8388607.5f - 1f;
        float Mix(float m,float n,float t) => m + (n-m)*t;
        return Mix(Mix(R(xi,zi),R(xi+1,zi),a),Mix(R(xi,zi+1),R(xi+1,zi+1),a),b);
    }
}

internal sealed class SimpleOpenGLWindow : GameWindow
{
    public SimpleOpenGLWindow(string title,int width,int height)
        : base(GameWindowSettings.Default,new NativeWindowSettings {
            Title = title, ClientSize = new Vector2i(width,height) }) { }
    protected override void OnLoad()
    {
        base.OnLoad();
        VSync = VSyncMode.On;
        GL.ClearColor(.09f,.13f,.19f,1f);
    }
    protected override void OnUpdateFrame(FrameEventArgs e)
    {
        base.OnUpdateFrame(e);
        if (KeyboardState.IsKeyDown(Keys.Escape)) Close();
    }
    protected override void OnRenderFrame(FrameEventArgs e)
    {
        base.OnRenderFrame(e);
        GL.Clear(ClearBufferMask.ColorBufferBit);
        SwapBuffers();
    }
}

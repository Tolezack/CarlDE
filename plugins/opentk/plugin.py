"""OpenTK: real native OpenGL window with shaders, depth test and 3-D geometry."""
from carlde.project import Command

PROGRAM = r'''using System;
using System.IO;
using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;

internal static class Program
{
    public static void Main()
    {
        using var game = new OpenTKDemo();
        game.Run();
    }
}

internal sealed class OpenTKDemo : GameWindow
{
    private int _vao, _vbo, _shader;
    private float _angle;

    private const string VertexShader = @"#version 330 core
layout(location = 0) in vec3 aPosition;
uniform mat4 uModel;
uniform mat4 uProjection;
out vec3 vColor;
void main() {
    vColor = aPosition * 0.45 + vec3(0.55);
    gl_Position = uProjection * uModel * vec4(aPosition, 1.0);
}";
    private const string FragmentShader = @"#version 330 core
in vec3 vColor;
out vec4 FragColor;
void main() { FragColor = vec4(vColor, 1.0); }";

    // 12 triangles, 36 vertices. Rendered via OpenGL VBO/VAO (not simulated).
    private static readonly float[] Cube = {
        // front
        -1,-1, 1,  1,-1, 1,  1, 1, 1,  -1,-1, 1,  1, 1, 1, -1, 1, 1,
        // back
         1,-1,-1, -1,-1,-1, -1, 1,-1,   1,-1,-1, -1, 1,-1,  1, 1,-1,
        // left
        -1,-1,-1, -1,-1, 1, -1, 1, 1,  -1,-1,-1, -1, 1, 1, -1, 1,-1,
        // right
         1,-1, 1,  1,-1,-1, 1, 1,-1,   1,-1, 1,  1, 1,-1, 1, 1, 1,
        // top
        -1, 1, 1,  1, 1, 1,  1, 1,-1,  -1, 1, 1,  1, 1,-1, -1, 1,-1,
        // bottom
        -1,-1,-1,  1,-1,-1, 1,-1, 1,  -1,-1,-1, 1,-1, 1, -1,-1, 1
    };

    public OpenTKDemo() : base(GameWindowSettings.Default,
        new NativeWindowSettings { ClientSize = new Vector2i(960, 540),
                                   Title = "CarlDE · OpenTK / OpenGL 3D" }) { }

    private static string LoadShader(string name, string fallback)
    {
        string location = Path.Combine(AppContext.BaseDirectory, "Shaders", name);
        return File.Exists(location) ? File.ReadAllText(location) : fallback;
    }

    private static int Compile(ShaderType type, string source)
    {
        int shader = GL.CreateShader(type);
        GL.ShaderSource(shader, source);
        GL.CompileShader(shader);
        GL.GetShader(shader, ShaderParameter.CompileStatus, out int success);
        if (success == 0) throw new InvalidOperationException(GL.GetShaderInfoLog(shader));
        return shader;
    }

    protected override void OnLoad()
    {
        base.OnLoad();
        VSync = VSyncMode.On;
        GL.Enable(EnableCap.DepthTest);
        GL.ClearColor(0.09f, 0.12f, 0.16f, 1f);
        int vertex = Compile(ShaderType.VertexShader, LoadShader("cube.vert", VertexShader));
        int fragment = Compile(ShaderType.FragmentShader, LoadShader("cube.frag", FragmentShader));
        _shader = GL.CreateProgram();
        GL.AttachShader(_shader, vertex);
        GL.AttachShader(_shader, fragment);
        GL.LinkProgram(_shader);
        GL.GetProgram(_shader, GetProgramParameterName.LinkStatus, out int linked);
        if (linked == 0) throw new InvalidOperationException(GL.GetProgramInfoLog(_shader));
        GL.DetachShader(_shader, vertex); GL.DeleteShader(vertex);
        GL.DetachShader(_shader, fragment); GL.DeleteShader(fragment);
        _vao = GL.GenVertexArray(); _vbo = GL.GenBuffer();
        GL.BindVertexArray(_vao);
        GL.BindBuffer(BufferTarget.ArrayBuffer, _vbo);
        GL.BufferData(BufferTarget.ArrayBuffer, Cube.Length * sizeof(float), Cube,
                      BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(0, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
        GL.EnableVertexAttribArray(0);
        GL.BindVertexArray(0);
    }

    protected override void OnUpdateFrame(FrameEventArgs e)
    {
        base.OnUpdateFrame(e);
        if (KeyboardState.IsKeyDown(Keys.Escape)) Close();
        _angle += (float)e.Time * 0.8f;
    }

    protected override void OnRenderFrame(FrameEventArgs e)
    {
        base.OnRenderFrame(e);
        GL.Clear(ClearBufferMask.ColorBufferBit | ClearBufferMask.DepthBufferBit);
        GL.UseProgram(_shader);
        Matrix4 model = Matrix4.CreateRotationY(_angle) * Matrix4.CreateRotationX(0.4f)
                      * Matrix4.CreateTranslation(0f, 0f, -5f);
        Matrix4 projection = Matrix4.CreatePerspectiveFieldOfView(
            MathHelper.DegreesToRadians(60f), Size.X / (float)Math.Max(1, Size.Y), 0.1f, 100f);
        GL.UniformMatrix4(GL.GetUniformLocation(_shader, "uModel"), false, ref model);
        GL.UniformMatrix4(GL.GetUniformLocation(_shader, "uProjection"), false, ref projection);
        GL.BindVertexArray(_vao);
        GL.DrawArrays(PrimitiveType.Triangles, 0, Cube.Length / 3);
        SwapBuffers();
    }

    protected override void OnResize(ResizeEventArgs e)
    {
        base.OnResize(e);
        GL.Viewport(0, 0, Math.Max(1, Size.X), Math.Max(1, Size.Y));
    }

    protected override void OnUnload()
    {
        GL.DeleteBuffer(_vbo);
        GL.DeleteVertexArray(_vao);
        GL.DeleteProgram(_shader);
        base.OnUnload();
    }
}
'''


def activate(api):
    def setup(project, name):
        (project / 'Program.cs').write_text(PROGRAM, encoding='utf-8')
        shaders = project / 'Shaders'
        shaders.mkdir(exist_ok=True)
        (shaders / 'cube.vert').write_text('''#version 330 core
layout(location = 0) in vec3 aPosition;
uniform mat4 uModel;
uniform mat4 uProjection;
out vec3 vColor;
void main() {
    vColor = aPosition * 0.45 + vec3(0.55);
    gl_Position = uProjection * uModel * vec4(aPosition, 1.0);
}
''', encoding='utf-8')
        (shaders / 'cube.frag').write_text('''#version 330 core
in vec3 vColor;
out vec4 FragColor;
void main() { FragColor = vec4(vColor, 1.0); }
''', encoding='utf-8')
        # Copiar shaders para as pastas de build e publish. São arquivos editáveis.
        import xml.etree.ElementTree as ET
        csproj = project / (name + '.csproj')
        tree = ET.parse(csproj)
        itemgroup = ET.SubElement(tree.getroot(), 'ItemGroup')
        ET.SubElement(itemgroup, 'None', Update='Shaders/**', CopyToOutputDirectory='PreserveNewest', CopyToPublishDirectory='PreserveNewest')
        tree.write(csproj, encoding='utf-8', xml_declaration=True)
        (project / 'README-OpenTK.md').write_text(
            '# OpenTK / OpenGL 3D\n\nCubos 3D com VAO/VBO, shader GLSL, projeção e depth test.\n'
            'Edite Shaders/cube.vert e Shaders/cube.frag: são copiados para o executável.\n'
            'Execute pelo CarlDE. Pressione ESC para fechar. Necessita de GPU OpenGL 3.3.\n', encoding='utf-8')
        return [Command(('dotnet', 'add', str(csproj), 'package', 'OpenTK'), project,
                        'Instalar OpenTK oficial via NuGet')]
    api.register_template('opentk', 'C# · OpenTK (OpenGL 3D)',
                          'Projeto real OpenTK: cubo 3D, shaders e OpenGL 3.3',
                          'csharp_console', setup)

    from carlde.plugin_helpers import context, tool, commands
    from carlde.project import find_csproj

    def restore():
        root, _ = context(api)
        if not root or not tool(api, 'dotnet'): return
        csproj = find_csproj(root)
        if not csproj:
            api.notify('Abra um projeto C# com arquivo .csproj.', error=True)
            return
        commands(api, (('dotnet', 'add', str(csproj), 'package', 'OpenTK'), root, 'NuGet · OpenTK'),
                 (('dotnet', 'restore', str(csproj)), root, 'Restaurar dependências NuGet'))

    def open_shaders():
        root, _ = context(api)
        if not root: return
        shaders = root / 'Shaders'
        if not shaders.is_dir():
            api.notify('O projeto ainda não tem pasta Shaders. Crie um projeto OpenTK 3D.', error=True)
            return
        for filename in ('cube.vert', 'cube.frag'):
            path = shaders / filename
            if path.exists(): api.window.open_file(path)

    def run_opentk():
        root, _ = context(api)
        if not root or not tool(api, 'dotnet') or not api.save_all(): return
        csproj = find_csproj(root)
        if not csproj:
            api.notify('Abra um projeto .NET com OpenTK.', error=True)
            return
        commands(api, (('dotnet', 'run', '--project', str(csproj), '-c', 'Debug'), root,
                       'Executar OpenTK/OpenGL'))

    api.register_action('nuget', 'OpenTK · instalar/restaurar biblioteca NuGet', restore)
    api.register_action('shaders', 'OpenTK · editar shaders GLSL', open_shaders)
    api.register_action('execute', 'OpenTK · compilar e abrir janela 3D', run_opentk)

from pathlib import Path
from carlde.project import Command

PROGRAM = '''using System;
using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;

internal static class Program
{
    public static void Main()
    {
        using var window = new CarlWindow();
        window.Run();
    }
}

public sealed class CarlWindow : GameWindow
{
    public CarlWindow() : base(GameWindowSettings.Default, new NativeWindowSettings
    {
        ClientSize = new Vector2i(960, 540),
        Title = "CarlDE - OpenTK"
    }) { }

    protected override void OnRenderFrame(FrameEventArgs e)
    {
        base.OnRenderFrame(e);
        GL.ClearColor(0.12f, 0.15f, 0.20f, 1.0f);
        GL.Clear(ClearBufferMask.ColorBufferBit);
        SwapBuffers();
    }
}
'''


def activate(api):
    def setup(project, name):
        (project / 'Program.cs').write_text(PROGRAM, encoding='utf-8')
        csproj = project / (name + '.csproj')
        return [Command(('dotnet', 'add', str(csproj), 'package', 'OpenTK'), project, 'Instalar OpenTK (NuGet)')]

    api.register_template('opentk', 'C# · OpenTK (janela gráfica)',
                          'App gráfico C# / OpenGL com OpenTK via NuGet', 'csharp_console', setup)

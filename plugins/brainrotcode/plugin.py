"""BrainrotCode: convenience libraries, snippets and starter templates for real C++/OpenTK."""
from pathlib import Path
import re
import shutil
from PySide6.QtWidgets import QMessageBox
from carlde.plugin_helpers import ask_choice
from carlde.project import Command

PLUGIN_DIR = Path(__file__).resolve().parent

CPP_SNIPPETS = {
    'Janela OpenGL (GLFW)': '#include "brainrot.hpp"\n\nint main() { br::window("Meu jogo", 960, 540); }\n',
    'Terreno procedural': 'auto heights = br::terrain(128, 128, 42, 48.0f, 5);\n',
    'UV de textura em atlas': 'auto uv = br::block_uv(5, 16, 16); // 4 cantos UV\n',
    'Malha de bloco com UV': 'auto mesh = br::block_mesh({1, 1, 2, 3, 4, 5}, 16, 16);\n',
}
CS_SNIPPETS = {
    'Janela OpenGL (OpenTK)': 'BrainrotCode.Brainrot.Window("Meu jogo", 960, 540);\n',
    'Terreno procedural': 'var heights = BrainrotCode.Brainrot.Terrain(128, 128, seed: 42, scale: 48f);\n',
    'UV de textura em atlas': 'var uv = BrainrotCode.Brainrot.BlockUV(tile: 5, columns: 16, rows: 16);\n',
    'Malha de bloco com UV': 'var mesh = BrainrotCode.Brainrot.Block(new[] {1, 1, 2, 3, 4, 5});\n',
}


def install_cpp(root: Path):
    target = root / 'include' / 'brainrot.hpp'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PLUGIN_DIR / 'brainrot.hpp', target)
    return target


def install_cs(root: Path):
    if not list(root.glob('*.csproj')):
        raise ValueError('Abra um projeto .NET com .csproj para usar OpenTK.')
    target = root / 'Brainrot.cs'
    shutil.copyfile(PLUGIN_DIR / 'Brainrot.cs', target)
    return target


def cpp_glfw_setup(root: Path):
    cmake = root / 'CMakeLists.txt'
    if not cmake.is_file():
        raise ValueError('CMakeLists.txt não encontrado.')
    source = cmake.read_text(encoding='utf-8')
    marker = '# BrainrotCode: GLFW setup'
    if marker in source:
        return False
    block = '''\n# BrainrotCode: GLFW setup
find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW3 REQUIRED IMPORTED_TARGET glfw3)
find_package(OpenGL REQUIRED)
target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_SOURCE_DIR}/include)
target_compile_definitions(${PROJECT_NAME} PRIVATE BRAINROT_ENABLE_GLFW)
target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::GLFW3 OpenGL::GL)
'''
    cmake.write_text(source.rstrip() + '\n' + block, encoding='utf-8')
    return True


def post_cpp(root: Path, name: str):
    install_cpp(root)
    cpp_glfw_setup(root)
    (root / 'src' / 'main.cpp').write_text(CPP_SNIPPETS['Janela OpenGL (GLFW)'], encoding='utf-8')
    return []


def post_cs(root: Path, name: str):
    install_cs(root)
    (root / 'Program.cs').write_text(CS_SNIPPETS['Janela OpenGL (OpenTK)'], encoding='utf-8')
    proj = next(root.glob('*.csproj'))
    return [Command(('dotnet','add',str(proj),'package','OpenTK'),root,'Instalar OpenTK via NuGet')]


def activate(api):
    def root():
        project = api.project_root
        if not project:
            api.notify('Abra primeiro um projeto para instalar BrainrotCode.', error=True)
        return project

    def setup_cpp():
        project = root()
        if not project: return
        try:
            path = install_cpp(project)
            api.notify('Biblioteca C++ instalada: ' + str(path))
        except Exception as exc: api.notify(str(exc), error=True)

    def setup_glfw():
        project = root()
        if not project: return
        try:
            install_cpp(project)
            changed = cpp_glfw_setup(project)
            api.notify('CMake configurado. Instale glfw-x11 (ou glfw-wayland), pkgconf e mesa. ' +
                       ('Configuração adicionada.' if changed else 'Já configurado.'))
        except Exception as exc: api.notify(str(exc), error=True)

    def setup_cs():
        project = root()
        if not project: return
        try:
            path = install_cs(project)
            proj = next(project.glob('*.csproj'))
            api.notify('Brainrot.cs adicionado. Instalando pacote OpenTK oficial pelo NuGet...')
            api.run_commands([Command(('dotnet','add',str(proj),'package','OpenTK'),project,'OpenTK NuGet')])
        except Exception as exc: api.notify(str(exc), error=True)

    def insert_snippet():
        editor = api.window.current_editor()
        if not editor or not editor.path:
            api.notify('Abra um arquivo .cpp, .hpp ou .cs para inserir um atalho.', True)
            return
        snippets = CS_SNIPPETS if editor.path.suffix.lower() == '.cs' else CPP_SNIPPETS if editor.path.suffix.lower() in ('.cpp','.hpp','.h') else None
        if snippets is None:
            api.notify('BrainrotCode oferece atalhos para C++ e C#.', True)
            return
        label = ask_choice(api, 'BrainrotCode · inserir código', 'Código rápido:', list(snippets))
        if not label: return
        editor.textCursor().insertText(snippets[label])
        api.notify('Atalho inserido. A API normal da linguagem continua disponível.')

    api.register_template('brainrot_cpp', 'C++ · BrainrotCode / OpenGL',
                          'Janela GLFW/OpenGL e helpers de terreno, atlas UV e malha voxel.', 'cpp', post_cpp)
    api.register_template('brainrot_cs', 'C# · BrainrotCode / OpenTK',
                          'Janela OpenTK real em uma linha, noise, atlas UV e mesh.', 'csharp_console', post_cs)
    api.register_action('cpp', 'BrainrotCode · instalar biblioteca C++ (noise / UV / mesh)', setup_cpp)
    api.register_action('glfw', 'BrainrotCode · configurar janela OpenGL C++ (GLFW)', setup_glfw)
    api.register_action('cs', 'BrainrotCode · instalar no projeto C# (OpenTK)', setup_cs)
    api.register_action('snippet', 'BrainrotCode · inserir código rápido...', insert_snippet)

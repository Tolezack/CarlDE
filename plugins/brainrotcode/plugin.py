"""BrainrotCode: convenience libraries, snippets and starter templates for real C++/OpenTK."""
from pathlib import Path
import re
import shutil
from datetime import datetime
from PySide6.QtWidgets import QMessageBox
from carlde.plugin_helpers import ask_choice
from carlde.project import Command

PLUGIN_DIR = Path(__file__).resolve().parent

CPP_SNIPPETS = {
    'Janela OpenGL (GLFW) — programa completo': '#include "brainrot.hpp"\n\nint main() {\n    br::window("Meu jogo", 960, 540);\n    return 0;\n}\n',
    'Terreno procedural': 'auto heights = br::terrain(128, 128, 42, 48.0f, 5);\n',
    'UV de textura em atlas': 'auto uv = br::block_uv(5, 16, 16); // 4 cantos UV\n',
    'Malha de bloco com UV': 'auto mesh = br::block_mesh({1, 1, 2, 3, 4, 5}, 16, 16);\n',
    'Noise 3D': 'float v = br::noise3(1.2f, 2.1f, 4.3f, 42);\n',
    'Mundo voxel (trecho dentro de main)': 'br::World mundo(80, 80, 72, 42);\nmundo.generate();\nmundo.run();\n',
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
    for filename in ('brainrot.hpp', 'brainrot_world.hpp'):
        dest = root / 'include' / filename
        # C++ headers update with plugin version (no project code is replaced).
        source = PLUGIN_DIR / filename
        if not dest.exists():
            shutil.copyfile(source, dest)
        elif dest.read_bytes() != source.read_bytes():
            existing = dest.read_text(encoding='utf-8', errors='replace')
            # Upgrade known old automatically generated headers, preserve modified/custom headers.
            known_old = (filename == 'brainrot.hpp' and
                         ('// BrainrotCode 1.0:' in existing or '// BrainrotCode 1.1:' in existing))
            if known_old:
                shutil.copyfile(source, dest)
    return target


def install_cs(root: Path):
    if not list(root.glob('*.csproj')):
        raise ValueError('Abra um projeto .NET com .csproj para usar OpenTK.')
    target = root / 'Brainrot.cs'
    shutil.copyfile(PLUGIN_DIR / 'Brainrot.cs', target)
    return target


def cpp_include_setup(root: Path):
    """A biblioteca de UV/terreno deve funcionar sem exigir GLFW."""
    cmake = root / 'CMakeLists.txt'
    if not cmake.is_file():
        raise ValueError('CMakeLists.txt não encontrado.')
    source = cmake.read_text(encoding='utf-8')
    marker = '# BrainrotCode: include path'
    if marker in source or '# BrainrotCode: GLFW setup' in source:
        return False
    block = '''
# BrainrotCode: include path
target_include_directories(${PROJECT_NAME} PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
'''
    cmake.write_text(source.rstrip() + '\n' + block, encoding='utf-8')
    return True


def cpp_glfw_setup(root: Path):
    cmake = root / 'CMakeLists.txt'
    if not cmake.is_file():
        raise ValueError('CMakeLists.txt não encontrado.')
    source = cmake.read_text(encoding='utf-8')
    marker = '# BrainrotCode: GLFW setup'
    if marker in source:
        return False
    cpp_include_setup(root)
    source = cmake.read_text(encoding='utf-8')
    block = '''\n# BrainrotCode: GLFW setup
find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW3 REQUIRED IMPORTED_TARGET glfw3)
find_package(OpenGL REQUIRED)
target_compile_definitions(${PROJECT_NAME} PRIVATE BRAINROT_ENABLE_GLFW)
target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::GLFW3 OpenGL::GL)
'''
    cmake.write_text(source.rstrip() + '\n' + block, encoding='utf-8')
    return True


def post_cpp(root: Path, name: str):
    install_cpp(root)
    cpp_glfw_setup(root)
    target = root / 'src' / 'main.cpp'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(CPP_SNIPPETS['Janela OpenGL (GLFW) — programa completo'], encoding='utf-8')
    return []


def post_voxel(root: Path, name: str):
    install_cpp(root)
    cpp_glfw_setup(root)
    target = root / 'src' / 'main.cpp'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(VOXEL_MAIN, encoding='utf-8')
    return []


VOXEL_MAIN = r'''#include "brainrot.hpp"
#include <iostream>
int main() {
    try {
        br::World mundo(80, 80, 72, 42);
        mundo.biomes(true).greedyMeshing(true).chunks(16).renderDistance(5);
        mundo.generate();
        std::cout << "Voxel faces: " << mundo.face_count() << "\n";
        mundo.run("BrainrotCode | Voxel World");
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        return 1;
    }
    return 0;
}
'''


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
            cpp_include_setup(project)
            api.notify('Biblioteca C++ instalada e CMake configurado: ' + str(path))
        except Exception as exc: api.notify(str(exc), error=True)

    def setup_glfw():
        project = root()
        if not project: return
        try:
            install_cpp(project)
            changed = cpp_glfw_setup(project)
            api.notify('CMake configurado. No CachyOS: sudo pacman -S glfw mesa pkgconf. ' +
                       ('Configuração adicionada.' if changed else 'Já configurado.'))
        except Exception as exc: api.notify(str(exc), error=True)

    def fix_cpp_window():
        project = root()
        if not project: return
        target = project / 'src' / 'main.cpp'
        if target.is_file() and target.read_text(encoding='utf-8').strip():
            answer = QMessageBox.question(
                api.window, 'BrainrotCode · corrigir janela C++',
                'Isso substituirá src/main.cpp por um exemplo C++ válido com GLFW.\n'
                'O código atual será preservado em um arquivo de backup. Continuar?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            install_cpp(project)
            cpp_glfw_setup(project)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_file():
                backup = target.with_name('main.cpp.brainrot-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
                shutil.copy2(target, backup)
            target.write_text(CPP_SNIPPETS['Janela OpenGL (GLFW) — programa completo'], encoding='utf-8')
            api.notify('C++ preparado. Abra src/main.cpp novamente se estava aberto; compile em Debug/Release.')
        except Exception as exc:
            api.notify(str(exc), error=True)

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
        if editor.path.suffix.lower() != '.cs' and label.startswith('Janela OpenGL'):
            fix_cpp_window()
            return
        if editor.path.suffix.lower() != '.cs':
            try:
                install_cpp(api.project_root)
                cpp_include_setup(api.project_root)
            except Exception as exc:
                api.notify(str(exc), error=True)
                return
            if '#include "brainrot.hpp"' not in editor.toPlainText():
                from PySide6.QtGui import QTextCursor
                top = QTextCursor(editor.document())
                top.movePosition(QTextCursor.MoveOperation.Start)
                top.insertText('#include "brainrot.hpp"\n')
        editor.textCursor().insertText(snippets[label])
        api.notify('Atalho inserido. Use dentro de uma função, como main().')

    api.register_template('brainrot_cpp', 'C++ · BrainrotCode / OpenGL',
                          'Janela GLFW/OpenGL e helpers de terreno, atlas UV e malha voxel.', 'cpp', post_cpp)
    api.register_template('brainrot_voxel', 'C++ · BrainrotCode / Mundo Voxel 3D',
                          'Terreno 3D, cavernas, chunks greedy, câmera FPS, água/lava e biomas.', 'cpp', post_voxel)
    api.register_template('brainrot_cs', 'C# · BrainrotCode / OpenTK',
                          'Janela OpenTK real em uma linha, noise, atlas UV e mesh.', 'csharp_console', post_cs)
    def ensure_cpp_opened(project):
        # No CMake project: leave it untouched. No rewriting of src/main.cpp.
        if project and (project / 'CMakeLists.txt').is_file() and (
                list(project.rglob('*.cpp')) or list(project.rglob('*.hpp'))):
            install_cpp(project)
            cpp_include_setup(project)
            # When using a window or voxel renderer, add GLFW automatically.
            src = project / 'src' / 'main.cpp'
            if src.is_file():
                code = src.read_text(encoding='utf-8', errors='replace')
                if 'br::window(' in code or 'br::World' in code:
                    cpp_glfw_setup(project)

    api.register_project_hook(ensure_cpp_opened)
    api.register_action('cpp', 'BrainrotCode · instalar biblioteca C++ (noise / UV / mesh)', setup_cpp)
    api.register_action('glfw', 'BrainrotCode · configurar janela OpenGL C++ (GLFW)', setup_glfw)
    api.register_action('cs', 'BrainrotCode · instalar no projeto C# (OpenTK)', setup_cs)
    api.register_action('fix_cpp_window', 'BrainrotCode · corrigir/criar janela C++ compilável...', fix_cpp_window)
    api.register_action('snippet', 'BrainrotCode · inserir código rápido...', insert_snippet)

    def new_voxel_project():
        project = root()
        if not project: return
        target = project / 'src' / 'main.cpp'
        if target.exists():
            answer = QMessageBox.question(api.window, 'BrainrotCode - Mundo voxel',
                        'Substituir src/main.cpp pelo mundo voxel? O arquivo atual terá backup.',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes: return
        install_cpp(project);cpp_glfw_setup(project)
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            shutil.copy2(target,target.with_name('main.cpp.brainrot-backup-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')))
        target.write_text(VOXEL_MAIN,encoding='utf-8')
        api.notify('Mundo voxel pronto. Reabra src/main.cpp no editor e execute (F5).')

    api.register_action('voxel', 'BrainrotCode · criar mundo voxel de teste...', new_voxel_project)

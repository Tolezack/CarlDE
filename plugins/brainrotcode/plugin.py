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
    for filename in ('brainrot.hpp', 'brainrot_world.hpp', 'brainrot_stream.hpp', 'brainrot_biomes.hpp', 'brainrot_gl.hpp', 'brainrot_live_api.h'):
        dest = root / 'include' / filename
        # C++ headers update with plugin version (no project code is replaced).
        source = PLUGIN_DIR / filename
        if not dest.exists():
            shutil.copyfile(source, dest)
        elif dest.read_bytes() != source.read_bytes():
            existing = dest.read_text(encoding='utf-8', errors='replace')
            # Upgrade known old automatically generated headers, preserve modified/custom headers.
            known_old = ((filename == 'brainrot.hpp' and
                         ('// BrainrotCode 1.0:' in existing or '// BrainrotCode 1.1:' in existing)) or
                         (filename == 'brainrot_stream.hpp' and
                          '// BrainrotCode 3.0 alpha - Fase 01:' in existing))
            if known_old:
                backup = dest.with_suffix(dest.suffix + '.phase01.bak')
                if not backup.exists():
                    shutil.copy2(dest, backup)
                shutil.copyfile(source, dest)
    return target


def install_cs(root: Path):
    if not list(root.glob('*.csproj')):
        raise ValueError('Abra um projeto .NET com .csproj para usar OpenTK.')
    target = root / 'Brainrot.cs'
    shutil.copyfile(PLUGIN_DIR / 'Brainrot.cs', target)
    return target


def cmake_main_target(content: str) -> str | None:
    """Select exactly the main executable, not the folder or test targets."""
    project = re.search(r'project\s*\(\s*([A-Za-z_][\w-]*)', content, re.I)
    candidates = []
    for m in re.finditer(r'add_executable\s*\(\s*(\$\{PROJECT_NAME\}|[A-Za-z_][\w-]*)([^)]*)\)',content,re.I|re.S):
        target = project.group(1) if m.group(1) == '${PROJECT_NAME}' and project else m.group(1)
        candidates.append((target,m.group(2)))
    if len(candidates)==1:
        return candidates[0][0]
    main=[target for target,files in candidates if 'src/main.cpp' in files.replace('\\','/')]
    if len(main)==1:return main[0]
    return None


def cpp_include_setup(root: Path):
    """A biblioteca de UV/terreno deve funcionar sem exigir GLFW."""
    cmake = root / 'CMakeLists.txt'
    if not cmake.is_file():
        raise ValueError('CMakeLists.txt não encontrado.')
    source = cmake.read_text(encoding='utf-8')
    marker = '# BrainrotCode: include path'
    if marker in source or '# BrainrotCode: GLFW setup' in source:
        return False
    target = cmake_main_target(source)
    if not target:
        raise ValueError('CMake com múltiplos alvos ambíguos; selecione o alvo principal manualmente.')
    block = f'''\n# BrainrotCode: include path
    target_include_directories({target} PRIVATE "${{CMAKE_CURRENT_SOURCE_DIR}}/include")
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
    target=cmake_main_target(source)
    if not target:
        raise ValueError('Não foi possível determinar o executável principal do CMake.')
    block = f'''\n# BrainrotCode: GLFW setup
find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW3 REQUIRED IMPORTED_TARGET glfw3)
find_package(OpenGL REQUIRED)
target_compile_definitions({target} PRIVATE BRAINROT_ENABLE_GLFW)
target_link_libraries({target} PRIVATE PkgConfig::GLFW3 OpenGL::GL)
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



def post_stream(root: Path, name: str):
    """Copy a complete, standalone GL 3.3 streaming example into a new project."""
    install_cpp(root)
    template = PLUGIN_DIR / 'stream_template'
    for source in template.rglob('*'):
        if not source.is_file():
            continue
        dst = root / source.relative_to(template)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dst)
        if dst.suffix == '.sh':
            dst.chmod(dst.stat().st_mode | 0o111)
    cmake = root / 'CMakeLists.txt'
    source = cmake.read_text(encoding='utf-8')
    source = source.replace('project(BrainrotCode_StreamDemo VERSION 0.1', f'project({name} VERSION 0.1')
    cmake.write_text(source, encoding='utf-8')
    return []

def post_stream_config(root: Path, name: str, api):
    post_stream(root, name)
    target = root / 'src' / 'main.cpp'
    code = target.read_text(encoding='utf-8')
    worker_setting = int(api.get_setting('worker_threads', 2))
    code = code.replace('settings.workers=std::clamp(int(std::thread::hardware_concurrency()/2),2,4);',
                        f'settings.workers={max(1,min(worker_setting,8))};')
    if api.get_setting('show_debug', False):
        code = code.replace('debug=false;', 'debug=true;')
    target.write_text(code, encoding='utf-8')
    path = root / 'controls.cfg'
    content = path.read_text(encoding='utf-8')
    content = content.replace('view_chunks=3', 'view_chunks='+str(max(1,min(12,int(api.get_setting('view_chunks',3))))))
    path.write_text(content, encoding='utf-8')
    return []


def activate(api):
    api.register_settings({
        'worker_threads': {'type': 'int', 'label': 'Workers (novos projetos)', 'default': 2, 'min': 1, 'max': 8},
        'view_chunks': {'type': 'int', 'label': 'Distância em chunks (novos projetos)', 'default': 3, 'min': 1, 'max': 12},
        'show_debug': {'type': 'bool', 'label': 'Iniciar com debug visual', 'default': False}
    })
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
    api.register_template('brainrot_stream', 'C++ · BrainrotCode 3.1 / Biomas + Streaming Voxel',
                          'Workers/chunks, geologia, cavernas, biomas, OpenGL 3.3 e hot reload.',
                          'cpp', lambda project,name: post_stream_config(project,name,api))
    api.register_template('brainrot_cs', 'C# · BrainrotCode / OpenTK',
                          'Janela OpenTK real em uma linha, noise, atlas UV e mesh.', 'csharp_console', post_cs)
    def ensure_cpp_opened(project):
        # Do not inject BrainrotCode into unrelated C++/Qt/SDL projects.
        # Only projects that explicitly use BrainrotCode are upgraded.
        src = project / 'src' / 'main.cpp' if project else None
        identified = bool(project and (
            (project / 'include' / 'brainrot.hpp').exists() or
            (src and src.is_file() and ('brainrot.hpp' in src.read_text(encoding='utf-8',errors='replace') or
                                      'br::World' in src.read_text(encoding='utf-8',errors='replace')))
        ))
        if identified and (project / 'CMakeLists.txt').is_file():
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

    api.register_action('voxel', 'BrainrotCode · criar mundo voxel de teste (legado)...', new_voxel_project)
    api.register_action('stream_setup', 'BrainrotCode · instalar headers da Engine 3 (sem alterar main.cpp)', setup_cpp)

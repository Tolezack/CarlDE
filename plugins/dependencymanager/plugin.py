from carlde.plugin_helpers import context,ask_choice,tool,confirm
from carlde.dependencies import package_manager
from carlde.project import Command,find_csproj
from carlde.runner import open_konsole

PACKAGES={
 'SDL2':{'pacman':'sdl2','apt-get':'libsdl2-dev','dnf':'SDL2-devel'},
 'SDL3':{'pacman':'sdl3','apt-get':'libsdl3-dev','dnf':'SDL3-devel'},
 'SFML':{'pacman':'sfml','apt-get':'libsfml-dev','dnf':'SFML-devel'},
 'GLFW':{'pacman':'glfw','apt-get':'libglfw3-dev','dnf':'glfw-devel'},
 'OpenGL / Mesa':{'pacman':'mesa','apt-get':'libgl1-mesa-dev','dnf':'mesa-libGL-devel'},
 'Boost':{'pacman':'boost','apt-get':'libboost-all-dev','dnf':'boost-devel'},
 'Vulkan':{'pacman':'vulkan-headers','apt-get':'libvulkan-dev','dnf':'vulkan-headers'},
}

def activate(api):
    def install():
        root,_=context(api)
        if not root:return
        choice=ask_choice(api,'Dependency Manager','Biblioteca:',[*PACKAGES,'OpenTK (NuGet)','Conan (gerenciador)','vcpkg (gerenciador)'])
        if not choice:return
        if choice=='OpenTK (NuGet)':
            csproj=find_csproj(root)
            if not csproj:api.notify('Abra um projeto .NET com arquivo .csproj.',error=True);return
            if tool(api,'dotnet'):api.run_commands([Command(('dotnet','add',str(csproj),'package','OpenTK'),root,'Instalar OpenTK via NuGet')]);return
        if choice.startswith('Conan') or choice.startswith('vcpkg'):
            api.notify('Instale Conan via pipx install conan ou vcpkg seguindo a documentação oficial. Não serão executados scripts remotos automaticamente.')
            return
        manager=package_manager()
        if not manager:api.notify('Pacman, apt ou dnf não detectado.',error=True);return
        package=PACKAGES[choice][manager]
        if not confirm(api,'Dependência do sistema',f'Executar instalação de {package} via sudo {manager} no Konsole?'):return
        if manager=='pacman':argv=('sudo','pacman','-S','--needed',package)
        elif manager=='apt-get':argv=('sudo','apt-get','install',package)
        else:argv=('sudo','dnf','install',package)
        open_konsole(root,Command(argv,root,'Instalar biblioteca'))
    api.register_action('install','Dependency Manager · instalar bibliotecas',install)

from carlde.plugin_helpers import context,tool,commands,ask_choice,confirm
from carlde.project import find_csproj

def activate(api):
    def format_code():
        root,path=context(api,True)
        if not root:return
        suffix=path.suffix.lower()
        toolname={'.cpp':'clang-format','.cc':'clang-format','.h':'clang-format','.hpp':'clang-format',
                  '.py':'ruff','.sh':'shfmt','.cs':'dotnet'}.get(suffix)
        if not toolname or not tool(api,toolname):return
        if not api.save_all():return
        if toolname=='clang-format':
            if not (root/'.clang-format').exists():
                style=ask_choice(api,'Code Formatter','Estilo C++',['LLVM','Google','Chromium','Mozilla','WebKit'])
                if style and confirm(api,'Configurar estilo','Criar .clang-format (BasedOnStyle: '+style+')?'):
                    (root/'.clang-format').write_text('BasedOnStyle: '+style+'\nIndentWidth: 4\n',encoding='utf-8')
            argv=('clang-format','-i',str(path))
        elif toolname=='ruff':argv=('ruff','format',str(path))
        elif toolname=='shfmt':argv=('shfmt','-w',str(path))
        else:
            proj=find_csproj(root)
            if not proj:api.notify('Projeto .csproj ausente.',error=True);return
            argv=('dotnet','format',str(proj),'--include',str(path))
        commands(api,(argv,root,'Code Formatter Pro'),refresh=True)
    api.register_action('format','Code Formatter Pro · formatar arquivo',format_code)

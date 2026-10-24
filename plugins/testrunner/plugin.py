from carlde.plugin_helpers import context,tool,commands,ask_choice
from carlde.project import find_csproj

def activate(api):
    def test():
        root,_=context(api)
        if not root:return
        opts=[]
        if find_csproj(root):opts.append('dotnet test')
        if (root/'CMakeLists.txt').exists():opts.append('CTest Debug')
        if list(root.glob('test_*.py')) or (root/'tests').exists() or (root/'pyproject.toml').exists():opts.append('pytest')
        if not opts:opts=['pytest','CTest Debug','dotnet test']
        choice=ask_choice(api,'Test Runner','Executar testes:',opts)
        if not choice:return
        if choice.startswith('dotnet'):
            if not tool(api,'dotnet'):return
            argv=('dotnet','test',str(root),'-c','Debug','--logger','console;verbosity=normal')
        elif choice.startswith('CTest'):
            if not tool(api,'ctest'):return
            b=root/'build'/'Debug'
            if not b.is_dir():api.notify('Configure e compile Debug antes de CTest.',error=True);return
            argv=('ctest','--test-dir',str(b),'--output-on-failure')
        else:
            if not tool(api,'pytest'):return
            argv=('pytest','-v',str(root))
        commands(api,(argv,root,choice))
    api.register_action('test','Test Runner · executar testes',test)

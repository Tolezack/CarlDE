from carlde.plugin_helpers import context,tool,commands
from carlde.project import load_metadata

def activate(api):
    def inspect():
        root,_=context(api)
        if not root or not tool(api,'valgrind'):return
        exe=root/'build'/'Debug'/load_metadata(root).get('name',root.name)
        if not exe.is_file():api.notify('Compile em Debug primeiro: '+str(exe),error=True);return
        commands(api,(('valgrind','--leak-check=full','--track-origins=yes','--show-leak-kinds=all',str(exe)),root,'Valgrind Memcheck / leaks'))
    api.register_action('check','Memory Inspector · verificar leaks',inspect)

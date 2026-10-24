from carlde.plugin_helpers import context,tool,commands,confirm
from carlde.project import Command

def activate(api):
    def docs():
        root,_=context(api)
        if not root or not tool(api,'doxygen'):return
        file=root/'Doxyfile'
        if not file.exists():
            if not confirm(api,'Doxygen','Criar Doxyfile padrão no projeto?'):return
            file.write_text('PROJECT_NAME = "'+root.name+'"\nOUTPUT_DIRECTORY = docs\nGENERATE_HTML = YES\nGENERATE_LATEX = NO\nINPUT = src .\nRECURSIVE = YES\nQUIET = YES\n',encoding='utf-8')
        commands(api,(('doxygen',str(file)),root,'Gerar documentação Doxygen'))
    api.register_action('docs','Documentation Generator · Doxygen',docs)

from carlde.plugin_helpers import context,tool,ask_choice,ask_text,commands,confirm
import re

def activate(api):
    def manage():
        root,_=context(api)
        if not root or not tool(api,'docker'):return
        choice=ask_choice(api,'Docker Manager','Operação',['Listar imagens','Build de Dockerfile','Executar imagem (sem privilégios adicionais)'])
        if not choice:return
        if choice=='Listar imagens':argv=('docker','images')
        elif choice.startswith('Build'):
            if not (root/'Dockerfile').is_file():api.notify('Crie um Dockerfile na pasta do projeto.',error=True);return
            name=ask_text(api,'Docker Build','Tag da imagem:','carlde-app:latest')
            if not name or not re.fullmatch('[A-Za-z0-9_./:-]+',name):return
            argv=('docker','build','-t',name,str(root))
        else:
            name=ask_text(api,'Docker Run','Imagem Docker:','carlde-app:latest')
            if not name or not re.fullmatch('[A-Za-z0-9_./:-]+',name):return
            if not confirm(api,'Docker run','Executar o container '+name+'?'):return
            argv=('docker','run','--rm',name)
        commands(api,(argv,root,'Docker Manager'))
    api.register_action('docker','Docker Manager · imagens e containers',manage)

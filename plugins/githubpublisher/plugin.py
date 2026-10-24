from carlde.plugin_helpers import context,tool,select_file,ask_text,confirm,commands
import re

def activate(api):
    def publish():
        root,_=context(api)
        if not root or not tool(api,'gh','GitHub CLI (gh)'):return
        tag=ask_text(api,'GitHub Publisher','Tag da release (ex.: v1.0.0):','v1.0.0')
        if not tag:return
        if not re.fullmatch(r'v?[0-9]+\.[0-9]+\.[0-9]+(?:[-.][A-Za-z0-9.-]+)?',tag):
            api.notify('Use uma tag SemVer como v1.2.3.',error=True);return
        artifact=select_file(api,'Arquivo a publicar na release',root/'dist')
        if not artifact:return
        if not confirm(api,'Publicar no GitHub','Criar release '+tag+' e enviar '+str(artifact)+'?\nÉ uma publicação online.'):return
        commands(api,(('gh','release','create',tag,str(artifact),'--generate-notes'),root,'Publicar GitHub Release'))
    api.register_action('publish','GitHub Publisher · criar release',publish)

import shutil,subprocess
from carlde.plugin_helpers import context,ask_choice,tool

def activate(api):
    def terminal():
        root,_=context(api)
        if not root or not tool(api,'konsole'):return
        opts={'Bash':['bash'],'Fish':['fish'],'Zsh':['zsh'],'PowerShell':['pwsh'],'Wine CMD':['wineconsole','cmd']}
        choice=ask_choice(api,'Terminal Profiles','Shell a abrir no Konsole:',list(opts))
        if not choice:return
        cmd=opts[choice]
        if not tool(api,cmd[0]):return
        subprocess.Popen(['konsole','--workdir',str(root),'-e',*cmd],start_new_session=True)
    api.register_action('terminal','Terminal Profiles · escolher shell',terminal)

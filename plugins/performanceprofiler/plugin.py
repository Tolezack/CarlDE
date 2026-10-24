from carlde.plugin_helpers import context,tool,commands,ask_choice
from carlde.project import load_metadata

def activate(api):
    def run():
        root,_=context(api)
        if not root or not tool(api,'perf'):return
        exe=root/'build'/'Release'/load_metadata(root).get('name',root.name)
        if not exe.is_file():api.notify('Compile em Release antes do perfil de CPU.',error=True);return
        choice=ask_choice(api,'Perf Profiler','Operação',['Contadores perf stat','Gravar amostras perf record','Ler relatório perf report'])
        if not choice:return
        data=root/'.carlde-perf.data'
        if choice.startswith('Contadores'):argv=('perf','stat','--',str(exe))
        elif choice.startswith('Gravar'):argv=('perf','record','-g','-o',str(data),'--',str(exe))
        else:
            if not data.exists():api.notify('Ainda não gravou um perfil.',error=True);return
            argv=('perf','report','--stdio','-i',str(data))
        commands(api,(argv,root,'Performance Profiler'))
    api.register_action('perf','Performance Profiler · CPU',run)

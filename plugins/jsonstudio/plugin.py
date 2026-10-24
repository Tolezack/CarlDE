import json
from carlde.plugin_helpers import context,tool,show_text,select_file,confirm,ask_choice

def activate(api):
    def validate():
        root,path=context(api,True)
        if not root:return
        if path.suffix.lower()!='.json':api.notify('Selecione um arquivo .json.',error=True);return
        if not api.save_all():return
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            api.notify(f'JSON inválido na linha {exc.lineno}, coluna {exc.colno}: {exc.msg}',error=True);return
        choice=ask_choice(api,'JSON Studio','Operação',['Formatar com indentação','Validar com JSON Schema','Ver estrutura resumida'])
        if choice=='Formatar com indentação':
            if not confirm(api,'Formatar JSON','Sobrescrever arquivo após criar .bak?'):return
            import shutil
            shutil.copy2(path,str(path)+'.bak')
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            api.reload_open_files();api.notify('JSON válido e formatado.')
        elif choice=='Validar com JSON Schema':
            try:import jsonschema
            except ImportError:api.notify('Instale python-jsonschema ou pip install jsonschema.',error=True);return
            schema=select_file(api,'Selecionar esquema .json',root,'JSON (*.json)')
            if not schema:return
            try:jsonschema.validate(data,json.loads(schema.read_text('utf-8')));api.notify('JSON válido conforme schema.')
            except Exception as exc:api.notify(str(exc),error=True)
        elif choice=='Ver estrutura resumida':
            out=[]
            def walk(obj,prefix='',depth=0):
                if depth>6 or len(out)>=450:return
                out.append(prefix+': '+type(obj).__name__)
                if isinstance(obj,dict):
                    for k,v in list(obj.items())[:80]:walk(v,prefix+'/'+str(k),depth+1)
                elif isinstance(obj,list):
                    for i,v in enumerate(obj[:30]):walk(v,prefix+'/'+str(i),depth+1)
            walk(data,'$')
            show_text(api,'JSON Studio · estrutura','\n'.join(out))
    api.register_action('json','JSON Studio · validar/formatar',validate)

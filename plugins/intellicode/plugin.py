import shutil
from pathlib import Path
from carlde.lsp_client import LSPClient
from carlde.plugin_helpers import context, ask_choice, show_text

SERVERS = {'.c':('clangd', ['clangd'], 'c'), '.cpp':('clangd',['clangd'],'cpp'),
           '.cc':('clangd',['clangd'],'cpp'), '.h':('clangd',['clangd'],'cpp'),
           '.hpp':('clangd',['clangd'],'cpp'), '.cs':('csharp-ls',['csharp-ls'],'csharp'),
           '.py':('basedpyright-langserver',['basedpyright-langserver','--stdio'],'python')}
clients = {}

def activate(api):
    def prepare():
        root, path = context(api, True)
        if not root: return None
        server = SERVERS.get(path.suffix.lower())
        if not server:
            api.notify('LSP disponível para C/C++, C# e Python.', error=True); return None
        if not shutil.which(server[0]):
            api.notify('Instale o servidor LSP: '+server[0], error=True); return None
        key = (str(root.resolve()), server[0])
        try:
            if key not in clients or clients[key].process.poll() is not None:
                clients[key] = LSPClient(server[1], root)
            editor = api.window.current_editor()
            uri = clients[key].sync(path, editor.toPlainText(), server[2])
            cursor = editor.textCursor()
            return clients[key], editor, path, uri, {'line':cursor.blockNumber(), 'character':cursor.positionInBlock()}
        except Exception as exc:
            api.notify('Erro LSP: '+str(exc), error=True); return None

    def complete():
        result = prepare()
        if not result: return
        client, editor, path, uri, pos = result
        try:
            payload = client.request('textDocument/completion', {'textDocument':{'uri':uri},'position':pos}, timeout=8)
            items = payload if isinstance(payload,list) else (payload or {}).get('items',[])
            items = [p for p in items if isinstance(p,dict)][:150]
            if not items:
                api.notify('O servidor LSP não retornou sugestões.'); return
            options = [i.get('label', '(sem nome)') for i in items]
            choice = ask_choice(api,'IntelliCode · LSP','Sugestões reais do servidor:',options)
            if choice is None:return
            item = items[options.index(choice)]
            insert = item.get('insertText', choice)
            if isinstance(insert,str) and '${' not in insert:
                cursor = editor.textCursor()
                # Substituir o prefixo identifier antes do cursor.
                text = editor.toPlainText()[:cursor.position()]
                import re
                match = re.search(r'[a-zA-Z_][\w]*$',text)
                if match:
                    cursor.setPosition(match.start(),cursor.MoveMode.KeepAnchor)
                cursor.insertText(insert)
                editor.setTextCursor(cursor)
            else:
                api.notify('Sugestão com snippet: '+choice)
        except Exception as exc: api.notify('Falha autocomplete: '+str(exc),error=True)

    def definition():
        result=prepare()
        if not result:return
        client, editor, path, uri, pos=result
        try:
            found=client.request('textDocument/definition',{'textDocument':{'uri':uri},'position':pos})
            targets=found if isinstance(found,list) else [found] if found else []
            if not targets: api.notify('Definição não encontrada.');return
            ref=targets[0]; uri2=ref.get('uri') or ref.get('targetUri')
            if uri2 and uri2.startswith('file://'):
                from urllib.parse import urlparse, unquote
                dest=Path(unquote(urlparse(uri2).path))
                api.window.open_file(dest)
                cursor=api.window.current_editor().textCursor()
                target_range=ref.get('range') or ref.get('targetSelectionRange') or {}
                line=target_range.get('start',{}).get('line',0)
                from PySide6.QtGui import QTextCursor
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.movePosition(QTextCursor.MoveOperation.Down,QTextCursor.MoveMode.MoveAnchor,line)
                api.window.current_editor().setTextCursor(cursor)
            else: api.notify('Definição remota não suportada.')
        except Exception as exc:api.notify('Erro definição: '+str(exc),error=True)

    def diagnostics():
        result=prepare()
        if not result:return
        client, _, _, uri, _=result
        from PySide6.QtWidgets import QApplication
        import time
        limit=time.monotonic()+1.2
        while uri not in client.diagnostics and time.monotonic()<limit:
            QApplication.processEvents(); time.sleep(.04)
        records=client.diagnostics.get(uri,[])
        details=['Linha %d: %s'%(d.get('range',{}).get('start',{}).get('line',0)+1,d.get('message','')) for d in records]
        show_text(api,'IntelliCode · diagnósticos LSP','\n\n'.join(details) if details else 'Nenhum diagnóstico recebido. Aguarde o servidor indexar o projeto e tente novamente.')

    api.register_action('complete','IntelliCode · sugestões (Ctrl+Espaço)',complete,shortcut='Ctrl+Space')
    api.register_action('definition','IntelliCode · ir para definição (F12)',definition,shortcut='F12')
    api.register_action('diagnostics','IntelliCode · diagnósticos do arquivo',diagnostics)

def deactivate():
    for client in clients.values():client.close()
    clients.clear()

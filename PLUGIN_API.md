# API de plugins CarlDE 0.4

O código dos plugins fica **apenas no repositório GitHub** (`plugins/<id>`). Ao instalar, o usuário autoriza a execução Python do plugin. Em `plugin.py`:

```python
from carlde.plugin_helpers import context, tool, commands

def activate(api):
    def example():
        root, current_file = context(api)
        if root:
            api.notify(f"Projeto aberto: {root}")
    api.register_action('example', 'Meu Plugin · ação', example, shortcut='Ctrl+Alt+M')

def deactivate():
    pass
```

- `api.project_root`, `api.current_file`, `api.window` são o projeto e UI atual.
- `api.register_action(key, label, callback, shortcut=None)` cria ação no menu Ferramentas; ao desativar é removida.
- `api.register_template(id, label, description, base, post_create)` adiciona template na janela Novo Projeto. `base` pode ser `cpp`, `cpp_library`, `python` ou `csharp_console`. O callback recebe `(project_root, project_name)` e retorna lista de `Command` opcionais. Para .NET ele é executado depois do `dotnet new`; para C++/Python executa após criar a pasta.
- `api.run_commands(list[Command], refresh=False)` chama TaskRunner com argumentos como tuplas, sem shell.
- `api.save_all()`, `api.reload_open_files()`, `api.notify(message,error=False)`.
- `carlde.plugin_helpers` fornece `context`, `tool`, `commands`, `ask_text`, `ask_choice`, `select_file`, `select_dir`, `confirm` e `show_text`.
- `carlde.lsp_client.LSPClient` fornece conexão LSP stdio JSON-RPC com `initialize`, `sync`, `request`, `notify`, `close`.

`plugin.json` deve declarar `id`, `name`, `version`, `description`, `image`, `category` (nome mostrado na loja), e conter um `cover.png`. Gere `index.json` com `python3 build_catalog.py` antes do push. O catálogo inclui SHA-256 de todos os arquivos.

Atenção: scripts dos plugins não são executados em sandbox e têm acesso aos arquivos do usuário. Não use `shell=True`, não tente elevar permissões sem confirmação e não embarque credenciais no catálogo.

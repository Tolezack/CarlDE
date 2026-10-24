from pathlib import Path
from carlde.project import Command, find_csproj


def activate(api):
    def fix():
        path = api.current_file
        root = api.project_root or (path.parent if path else None)
        if not path or not root:
            api.notify('Abra um arquivo para corrigir.', error=True)
            return
        if not api.save_all():
            return
        if path.suffix.lower() == '.py':
            steps = [Command(('ruff', 'check', '--fix', str(path)), root, 'Ruff · corrigir Python'),
                     Command(('ruff', 'format', str(path)), root, 'Ruff · formatar Python')]
        elif path.suffix.lower() == '.cs':
            proj = find_csproj(root)
            if not proj:
                api.notify('Abra a pasta que contém o arquivo .csproj.', error=True)
                return
            steps = [Command(('dotnet', 'format', str(proj), '--include', str(path)), root, 'dotnet format')]
        else:
            api.notify('AutoCorrigir aceita .py e .cs. O formatador atende outros formatos.')
            return
        api.run_commands(steps, refresh=True)

    api.register_action('fix', 'AutoCorrigir arquivo  (Ruff / dotnet format)', fix)

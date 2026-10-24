"""Procura anotações de desenvolvimento sem modificar arquivos."""
import re

PATTERN = re.compile(r'\b(TODO|FIXME|HACK)\b', re.I)
EXT = {'.cpp', '.hpp', '.h', '.c', '.cs', '.py', '.sh', '.js', '.ts', '.gd', '.java'}
SKIP = {'build', 'dist', '.git', '.venv', '__pycache__', 'node_modules'}


def activate(api):
    def scan():
        root = api.project_root
        if root is None:
            api.notify('Abra uma pasta de projeto primeiro.', error=True)
            return
        results = []
        for path in root.rglob('*'):
            if path.suffix.lower() not in EXT or any(x in SKIP for x in path.relative_to(root).parts):
                continue
            if not path.is_file() or path.stat().st_size > 1_000_000:
                continue
            for i, line in enumerate(path.read_text('utf-8', errors='replace').splitlines(), 1):
                if PATTERN.search(line):
                    results.append(f'{path.relative_to(root)}:{i}: {line.strip()[:140]}')
            if len(results) >= 300:
                results.append('... resultado limitado a 300 linhas ...')
                break
        api.window.append_output('\nTODO Explorer\n' + ('\n'.join(results) if results else 'Nenhuma anotação encontrada.') + '\n')

    api.register_action('scan', 'TODO Explorer · Buscar TODO/FIXME', scan)

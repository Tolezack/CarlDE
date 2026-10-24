import json
from carlde.project import Command


def activate(api):
    def format_file():
        path = api.current_file
        if not path:
            api.notify('Abra um arquivo antes de formatar.', error=True)
            return
        if not api.save_all():
            return
        ext = path.suffix.lower()
        if ext in ('.c', '.cpp', '.h', '.hpp'):
            cmd = ('clang-format', '-i', str(path))
        elif ext in ('.sh', '.bash'):
            cmd = ('shfmt', '-w', str(path))
        elif ext == '.json':
            try:
                obj = json.loads(path.read_text(encoding='utf-8'))
                path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                api.reload_open_files()
                api.notify('JSON formatado.')
            except (OSError, json.JSONDecodeError) as exc:
                api.notify(str(exc), error=True)
            return
        else:
            api.notify('Formatador suporta C/C++, shell e JSON.', error=True)
            return
        api.run_commands([Command(cmd, path.parent, 'Formatar arquivo')], refresh=True)

    api.register_action('format', 'Formatar arquivo  (clang-format / shfmt / JSON)', format_file)

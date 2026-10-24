from carlde.project import Command


def activate(api):
    def execute(args, label):
        project = api.project_root
        if not project:
            api.notify('Abra a pasta de um projeto Git.', error=True)
            return
        api.run_commands([Command(tuple(['git', *args]), project, label)])

    api.register_action('status', 'Git · Status', lambda: execute(['status', '--short', '--branch'], 'Git status'))
    api.register_action('diff', 'Git · Diff', lambda: execute(['diff', '--'], 'Git diff'))

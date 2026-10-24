"""Limpa apenas diretórios gerados pelo CMake dentro do projeto."""
import shutil
from PySide6.QtWidgets import QMessageBox


def activate(api):
    def clean():
        root = api.project_root
        if root is None:
            api.notify('Abra um projeto CMake.', error=True)
            return
        if not (root / 'CMakeLists.txt').is_file():
            api.notify('Este projeto não contém CMakeLists.txt.', error=True)
            return
        build = root / 'build'
        if build.is_symlink():
            api.notify('Pasta build é um link simbólico. Operação cancelada por segurança.', error=True)
            return
        candidates = [build / 'Debug', build / 'Release']
        existing = [p for p in candidates if p.is_dir() and not p.is_symlink()]
        if not existing:
            api.notify('Nenhuma pasta de compilação Debug/Release encontrada.')
            return
        if QMessageBox.question(api.window, 'CMake Cleaner',
                                'Excluir os arquivos de compilação em build/Debug e build/Release?\n'
                                'Seu código e a pasta dist/ não serão alterados.',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        for folder in existing:
            shutil.rmtree(folder)
        api.notify('Build CMake limpo. Compile novamente para reconstruir.')

    api.register_action('clean', 'CMake Cleaner · Limpar builds', clean)

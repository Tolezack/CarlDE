from pathlib import Path
import shutil
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QListWidget,QLabel,QPushButton,QFileDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from carlde.plugin_helpers import context,select_file,confirm

EXTS={'.png','.jpg','.jpeg','.webp','.svg','.bmp','.ttf','.otf','.wav','.ogg','.mp3','.obj','.glb','.gltf','.fbx'}

def activate(api):
    def browse():
        root,_=context(api)
        if not root:return
        dlg=QDialog(api.window);dlg.setWindowTitle('Resource Explorer · assets');dlg.resize(900,610)
        layout=QVBoxLayout(dlg);left=QHBoxLayout()
        files=QListWidget();files.setMinimumWidth(300);left.addWidget(files)
        preview=QLabel('Escolha um recurso');preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left.addWidget(preview,1);layout.addLayout(left,1)
        for f in sorted(root.rglob('*')):
            if f.is_file() and f.suffix.lower() in EXTS and len(files)<1000 and '.git' not in f.parts:
                files.addItem(str(f.relative_to(root)))
        def selected():
            item=files.currentItem()
            return root/item.text() if item else None
        def show():
            path=selected()
            if not path:return
            pix=QPixmap(str(path))
            if pix.isNull():preview.setText(str(path.name)+'\n'+str(path.stat().st_size)+' bytes')
            else:preview.setPixmap(pix.scaled(500,450,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        files.currentRowChanged.connect(lambda *_:show())
        btn=QPushButton('IMPORTAR RECURSO PARA assets/')
        def import_asset():
            file=select_file(api,'Selecionar recurso',root)
            if not file or file.suffix.lower() not in EXTS:return
            target=root/'assets'/file.name;target.parent.mkdir(exist_ok=True)
            if target.exists() and not confirm(api,'Sobrescrever','Recurso existe. Substituir?'):return
            shutil.copy2(file,target);files.addItem(str(target.relative_to(root)))
        btn.clicked.connect(import_asset);layout.addWidget(btn)
        dlg.exec()
    api.register_action('assets','Resource Explorer · imagens/fontes/modelos',browse)

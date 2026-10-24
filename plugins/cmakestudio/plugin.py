import re
from pathlib import Path
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QLabel,QPushButton,QLineEdit
from carlde.plugin_helpers import context,confirm

def activate(api):
    def edit():
        root,_=context(api)
        if not root:return
        cmake=root/'CMakeLists.txt'
        if not cmake.exists():api.notify('Não há CMakeLists.txt neste projeto.',error=True);return
        old=cmake.read_text(encoding='utf-8')
        dlg=QDialog(api.window);dlg.setWindowTitle('CMake Studio · Configurações');layout=QVBoxLayout(dlg)
        form=QFormLayout();standard=QComboBox();standard.addItems(['11','14','17','20','23','26'])
        m=re.search(r'set\(CMAKE_CXX_STANDARD\s+(\d+)\)',old)
        if m and m.group(1) in ['11','14','17','20','23','26']:standard.setCurrentText(m.group(1))
        flag=QLineEdit();flag.setPlaceholderText('Ex.: -Wall -Wextra (opcional)')
        form.addRow('Padrão C++',standard);form.addRow('Flags extras',flag);layout.addLayout(form)
        layout.addWidget(QLabel('O CarlDE preservará o arquivo anterior em CMakeLists.txt.bak'))
        save=QPushButton('SALVAR CONFIGURAÇÃO');layout.addWidget(save)
        def apply():
            if not confirm(api,'Alterar CMakeLists.txt','Salvar estas alterações no projeto?'):return
            text=old
            replacement='set(CMAKE_CXX_STANDARD '+standard.currentText()+')'
            if m:text=re.sub(r'set\(CMAKE_CXX_STANDARD\s+\d+\)',replacement,text,count=1)
            else:text+='\n'+replacement+'\n'
            if flag.text().strip():
                allowed=set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_- =.+:/')
                if not set(flag.text())<=allowed:api.notify('Flags têm caracteres não permitidos.',error=True);return
                text+='\nadd_compile_options('+flag.text() +')\n'
            (root/'CMakeLists.txt.bak').write_text(old,encoding='utf-8')
            cmake.write_text(text,encoding='utf-8');api.reload_open_files();dlg.accept()
        save.clicked.connect(apply);dlg.exec()
    api.register_action('edit','CMake Studio · configurações visuais',edit)

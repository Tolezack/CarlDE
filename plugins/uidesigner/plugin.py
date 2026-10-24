from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QSpinBox,QPushButton,QLabel
from carlde.plugin_helpers import context,confirm,tool,commands

def activate(api):
    def design():
        root,_=context(api)
        if not root:return
        dlg=QDialog(api.window);dlg.setWindowTitle('UI Designer · gerar interface');dlg.resize(590,370)
        layout=QVBoxLayout(dlg);form=QFormLayout()
        framework=QComboBox();framework.addItems(['Qt Widgets (.ui)','Avalonia XAML (.axaml)'])
        title=QLineEdit(root.name);buttons=QSpinBox();buttons.setRange(0,12);buttons.setValue(2)
        inputs=QSpinBox();inputs.setRange(0,12);inputs.setValue(2)
        form.addRow('Framework',framework);form.addRow('Título',title)
        form.addRow('Botões',buttons);form.addRow('Entradas de texto',inputs)
        layout.addLayout(form);layout.addWidget(QLabel('Gera interface editável. Para Qt use Qt Designer; para Avalonia edite o XAML.'))
        save=QPushButton('GERAR INTERFACE');layout.addWidget(save)
        def make():
            is_qt=framework.currentIndex()==0
            path=root/('mainwindow.ui' if is_qt else 'MainWindow.axaml')
            if path.exists() and not confirm(api,'Substituir interface','Arquivo existente. Sobrescrever?'):return
            if is_qt:
                ui=Element('ui',version='4.0');SubElement(ui,'class').text='MainWindow'
                w=SubElement(ui,'widget',{'class':'QMainWindow','name':'MainWindow'})
                props=SubElement(w,'property',name='windowTitle');SubElement(props,'string').text=title.text()
                central=SubElement(w,'widget',{'class':'QWidget','name':'centralwidget'})
                vertical=SubElement(central,'layout',{'class':'QVBoxLayout','name':'verticalLayout'})
                for n in range(inputs.value()):
                    item=SubElement(vertical,'item');widget=SubElement(item,'widget',{'class':'QLineEdit','name':f'input{n+1}'})
                    prop=SubElement(widget,'property',name='placeholderText');SubElement(prop,'string').text=f'Campo {n+1}'
                for n in range(buttons.value()):
                    item=SubElement(vertical,'item');widget=SubElement(item,'widget',{'class':'QPushButton','name':f'button{n+1}'})
                    prop=SubElement(widget,'property',name='text');SubElement(prop,'string').text=f'Botão {n+1}'
                SubElement(ui,'resources');SubElement(ui,'connections');indent(ui)
                ElementTree(ui).write(path,encoding='utf-8',xml_declaration=True)
            else:
                from xml.sax.saxutils import escape
                elements='\n'.join('        <TextBox Name="Input%d" Watermark="Campo %d" />'%(i+1,i+1) for i in range(inputs.value()))
                elements+='\n'+'\n'.join('        <Button Name="Button%d" Content="Botão %d" />'%(i+1,i+1) for i in range(buttons.value()))
                text='<Window xmlns="https://github.com/avaloniaui" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Class="CarlDEProject.MainWindow" Title="'+escape(title.text(),{'"':'&quot;'})+'" Width="800" Height="520">\n  <StackPanel Margin="24" Spacing="10">\n'+elements+'\n  </StackPanel>\n</Window>\n'
                path.write_text(text,encoding='utf-8')
            api.window.open_file(path);dlg.accept()
        save.clicked.connect(make);dlg.exec()
    api.register_action('designer','UI Designer · gerar Qt/Avalonia',design)

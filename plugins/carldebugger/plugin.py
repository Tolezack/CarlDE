from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QDialog,QVBoxLayout,QPlainTextEdit,QPushButton,QHBoxLayout,QLineEdit,QLabel
from carlde.plugin_helpers import context,tool

def activate(api):
    def debug():
        root,path=context(api)
        if not root or not tool(api,'gdb'):return
        from carlde.project import load_metadata
        name=load_metadata(root).get('name',root.name)
        exe=root/'build'/'Debug'/name
        if not exe.is_file():api.notify('Compile o projeto em Debug antes de depurar. Esperado: '+str(exe),error=True);return
        dlg=QDialog(api.window);dlg.setWindowTitle('CarlDebugger · GDB/MI2');dlg.resize(950,650)
        layout=QVBoxLayout(dlg);output=QPlainTextEdit();output.setReadOnly(True)
        layout.addWidget(output,1)
        row=QHBoxLayout()
        process=QProcess(dlg);process.setProgram('gdb');process.setArguments(['--interpreter=mi2','--quiet','--args',str(exe)])
        process.setWorkingDirectory(str(root));process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(lambda: output.insertPlainText(bytes(process.readAllStandardOutput()).decode('utf-8','replace')))
        process.start()
        def send(command):
            if process.state()==QProcess.ProcessState.Running:process.write((command+'\n').encode())
        for label,cmd in [('INICIAR','-exec-run'),('CONTINUAR','-exec-continue'),('PRÓXIMA LINHA','-exec-next'),('ENTRAR','-exec-step'),('PILHA','-stack-list-frames'),('VARIÁVEIS','-stack-list-variables --all-values')]:
            button=QPushButton(label);button.clicked.connect(lambda _,c=cmd:send(c));row.addWidget(button)
        layout.addLayout(row)
        row2=QHBoxLayout();br=QLineEdit();br.setPlaceholderText('breakpoint: arquivo.cpp:linha')
        val=QLineEdit();val.setPlaceholderText('Expressão C++')
        b1=QPushButton('BREAKPOINT');b1.clicked.connect(lambda:send('-break-insert '+br.text().strip()) if ':' in br.text() else None)
        b2=QPushButton('INSPECIONAR');b2.clicked.connect(lambda:send('-data-evaluate-expression '+__import__('json').dumps(val.text().strip())))
        for w in [br,b1,val,b2]:row2.addWidget(w)
        layout.addLayout(row2)
        dlg.exec()
        process.kill();process.waitForFinished(2000)
    api.register_action('gdb','CarlDebugger · depuração GDB/MI',debug)

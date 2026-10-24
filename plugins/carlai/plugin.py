import json, threading
from urllib.request import Request, urlopen
from carlde.plugin_helpers import context, ask_choice
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QPlainTextEdit,QComboBox,QLabel)

HOST='http://127.0.0.1:11434'

def available_models():
    with urlopen(HOST+'/api/tags',timeout=3) as r:
        return [m['name'] for m in json.load(r).get('models',[]) if m.get('name')]

def generate(model,prompt):
    data=json.dumps({'model':model,'prompt':prompt,'stream':False}).encode('utf-8')
    with urlopen(Request(HOST+'/api/generate',data=data,headers={'Content-Type':'application/json'}),timeout=180) as r:
        return json.load(r).get('response','')

class Bridge(QObject):
    done=Signal(str)

def activate(api):
    def run():
        root,path=context(api,True)
        if not root:return
        try:models=available_models()
        except Exception as exc:
            api.notify('Ollama offline. Execute ollama serve e baixe um modelo com ollama pull. '+str(exc),error=True);return
        if not models:
            api.notify('Nenhum modelo instalado. Exemplo: ollama pull qwen2.5-coder:1.5b',error=True);return
        editor=api.window.current_editor()
        selection=editor.textCursor().selectedText().replace('\u2029','\n')
        source=selection or editor.toPlainText()[:14000]
        if len(source)>20000:
            api.notify('Selecione um trecho menor (máximo 20.000 caracteres).',error=True);return
        dlg=QDialog(api.window);dlg.setWindowTitle('CarlAI Local · Ollama (offline)');dlg.resize(870,670)
        layout=QVBoxLayout(dlg)
        row=QHBoxLayout();combo=QComboBox();combo.addItems(models);row.addWidget(QLabel('Modelo local'));row.addWidget(combo)
        layout.addLayout(row)
        prompt=QPlainTextEdit();prompt.setFixedHeight(100)
        prompt.setPlainText('Explique este código, encontre problemas e sugira melhorias sem alterar seu comportamento:')
        layout.addWidget(prompt)
        answer=QPlainTextEdit();answer.setReadOnly(True);answer.setPlaceholderText('Resposta do Ollama aparecerá aqui...')
        layout.addWidget(answer,1)
        row2=QHBoxLayout();ask=QPushButton('PERGUNTAR');insert=QPushButton('INSERIR NA POSIÇÃO DO CURSOR');insert.setEnabled(False)
        row2.addWidget(ask);row2.addWidget(insert);layout.addLayout(row2)
        bridge=Bridge(dlg)
        def finish(value):
            answer.setPlainText(value);ask.setEnabled(True);insert.setEnabled(not value.startswith('ERRO:'))
        bridge.done.connect(finish)
        def submit():
            ask.setEnabled(False);answer.setPlainText('Consultando Ollama local...')
            question=prompt.toPlainText()+'\n\nArquivo: '+str(path)+'\n```\n'+source+'\n```'
            model=combo.currentText()
            def worker():
                try: value=generate(model,question)
                except Exception as e:value='ERRO: '+str(e)
                bridge.done.emit(value)
            threading.Thread(target=worker,daemon=True).start()
        ask.clicked.connect(submit)
        insert.clicked.connect(lambda: editor.textCursor().insertText(answer.toPlainText()))
        dlg.exec()
    api.register_action('ask','CarlAI Local · explicar/revisar código',run)

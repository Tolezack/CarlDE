"""CarlAI Local v2: assistant, hardware model advisor, explicit download opt-in."""
import json
import shutil
import threading
from urllib.request import Request, urlopen
from carlde.plugin_helpers import context
from carlde.hardware import detect_linux_hardware, recommend_model
from carlde.project import Command
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QPlainTextEdit,
                                QComboBox,QLabel,QMessageBox)

HOST = 'http://127.0.0.1:11434'
MODELS=('qwen2.5-coder:1.5b','qwen2.5-coder:3b','qwen2.5-coder:7b','qwen2.5-coder:14b')

def available_models():
    with urlopen(HOST + '/api/tags', timeout=3) as r:
        return [str(m['name']) for m in json.load(r).get('models', []) if m.get('name')]

def generate(model, prompt):
    data=json.dumps({'model':model,'prompt':prompt,'stream':False}).encode()
    with urlopen(Request(HOST+'/api/generate',data=data,
                         headers={'Content-Type':'application/json'}),timeout=180) as r:
        return json.load(r).get('response','')

class Bridge(QObject):
    done=Signal(str)

def activate(api):
    api.register_settings({
        'model': {'type':'choice','label':'Modelo preferido', 'choices':list(MODELS), 'default':'qwen2.5-coder:1.5b'},
        'prefer_selection': {'type':'bool','label':'Priorizar seleção do editor','default':True},
        'max_chars': {'type':'int','label':'Máximo de caracteres','min':1000,'max':20000,'default':12000},
    })

    def advisor():
        hw=detect_linux_hardware()
        model,reason=recommend_model(hw)
        dlg=QDialog(api.window)
        dlg.setWindowTitle('CarlAI · análise do computador e modelo local')
        dlg.resize(590,310)
        layout=QVBoxLayout(dlg)
        layout.addWidget(QLabel(f'RAM: {hw.total_gib:.1f} GiB  |  disponível: {hw.available_gib:.1f} GiB'))
        layout.addWidget(QLabel(f'GPU: {hw.gpu}  |  VRAM informada: {hw.vram_gib:.1f} GiB  |  threads: {hw.cpu_threads}'))
        layout.addWidget(QLabel('Sugestão: '+model+' — '+reason))
        layout.addWidget(QLabel('Estimativa heurística; não mede o desempenho nem garante espaço em disco.'))
        row=QHBoxLayout()
        combo=QComboBox();combo.addItems(MODELS);combo.setCurrentText(model)
        row.addWidget(combo);layout.addLayout(row)
        download=QPushButton('BAIXAR MODELO SELECIONADO')
        remember=QPushButton('USAR COMO PADRÃO (SEM BAIXAR)')
        layout.addWidget(remember);layout.addWidget(download)
        def persist():
            api.set_setting('model',combo.currentText())
            api.notify('Modelo selecionado: '+combo.currentText())
            dlg.accept()
        remember.clicked.connect(persist)
        def pull():
            if not shutil.which('ollama'):
                QMessageBox.warning(dlg,'CarlAI','Instale primeiro Ollama no Linux.');return
            chosen=combo.currentText()
            if QMessageBox.question(dlg,'Download do modelo',
               f'Baixar {chosen} usando Ollama? O download pode ocupar vários GB e usar internet.\nContinuar?',
               QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
               QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            api.set_setting('model',chosen)
            root=api.project_root or __import__('pathlib').Path.home()
            api.run_commands([Command(('ollama','pull',chosen),root,'Baixando modelo Ollama')])
            dlg.accept()
        download.clicked.connect(pull)
        dlg.exec()

    def ask():
        root,path=context(api,True)
        if not root:return
        try:
            models=available_models()
        except Exception as exc:
            api.notify('Ollama offline. Inicie o serviço e baixe um modelo: '+str(exc),error=True);return
        if not models:
            advisor();return
        editor=api.window.current_editor()
        selection=editor.textCursor().selectedText().replace('\u2029','\n')
        source=selection if selection and api.get_setting('prefer_selection',True) else editor.toPlainText()
        source=source[:int(api.get_setting('max_chars',12000))]
        dlg=QDialog(api.window);dlg.setWindowTitle('CarlAI Local · revisão');dlg.resize(850,640)
        layout=QVBoxLayout(dlg);row=QHBoxLayout()
        combo=QComboBox();combo.addItems(models)
        desired=api.get_setting('model','qwen2.5-coder:1.5b')
        if desired in models:combo.setCurrentText(desired)
        row.addWidget(QLabel('Modelo'));row.addWidget(combo);layout.addLayout(row)
        prompt=QPlainTextEdit('Explique o código, identifique problemas e sugira melhorias mantendo o comportamento.')
        prompt.setFixedHeight(90);layout.addWidget(prompt)
        answer=QPlainTextEdit();answer.setReadOnly(True);layout.addWidget(answer,1)
        ask_btn=QPushButton('ANALISAR');layout.addWidget(ask_btn)
        bridge=Bridge(dlg)
        def finish(value):
            answer.setPlainText(value);ask_btn.setEnabled(True)
        bridge.done.connect(finish)
        def submit():
            ask_btn.setEnabled(False);answer.setPlainText('Processando no Ollama local...')
            question=prompt.toPlainText()+'\nArquivo: '+str(path)+'\n```\n'+source+'\n```'
            model=combo.currentText()
            def worker():
                try:value=generate(model,question)
                except Exception as error:value='ERRO: '+str(error)
                bridge.done.emit(value)
            threading.Thread(target=worker,daemon=True).start()
        ask_btn.clicked.connect(submit)
        dlg.exec()
    api.register_action('ask','CarlAI Local · revisar código',ask)
    api.register_action('hardware','CarlAI Local · analisar PC / baixar modelo',advisor)

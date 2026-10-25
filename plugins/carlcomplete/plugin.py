"""CarlComplete: inline Ollama completions with debounce, cancellation and Tab acceptance.
No remote API. Requires a running Ollama instance on 127.0.0.1:11434.
"""
import json
import re
import threading
import subprocess
import shutil
import time
from contextlib import suppress
from urllib.request import Request, urlopen
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox

HOST = 'http://127.0.0.1:11434'
MAX_CHARS = 1400

class LocalModelServer:
    """Starts Ollama only if locally installed and port is not already served.
    Never kills an Ollama service it did not start.
    Model weights are NOT bundled; user explicitly pulls a model once.
    """
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
        self.stopped = False

    def start(self):
        try:
            get_models()
            return 'Serviço Ollama existente encontrado; será reutilizado.'
        except Exception:
            pass
        binary = shutil.which('ollama')
        if not binary:
            return 'Ollama não instalado. Ghost Text usa modelo local: instale Ollama e baixe um modelo.'
        with self.lock:
            if self.stopped:
                return 'Início cancelado: a IDE está encerrando.'
            self.process = subprocess.Popen([binary, 'serve'], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
        return 'Servidor Ollama iniciado pelo CarlComplete (será encerrado ao sair).'

    def stop(self):
        with self.lock:
            self.stopped = True
            proc, self.process = self.process, None
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                with suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=1)



def get_models():
    with urlopen(HOST + '/api/tags', timeout=3) as response:
        data = json.load(response)
    return [v['name'] for v in data.get('models', []) if isinstance(v.get('name'), str)]


def make_prompt(before, after, filename):
    # Only a small bounded excerpt of code is sent to LOCAL Ollama.
    return (f'You are a code completion engine. Language inferred from {filename}. '
            'Complete at the cursor, returning ONLY raw source code to insert. '
            'Do not repeat the prefix or suffix. No markdown, no explanations. '
            'Prefer a short continuation (1-5 lines).\n'
            f'<BEFORE>\n{before[-MAX_CHARS:]}\n</BEFORE>\n'
            f'<AFTER>\n{after[:240]}\n</AFTER>\n'
            'Output the missing continuation:')


def builtin_predict(before, after, filename):
    """Tiny fully local pattern predictor. Not an LLM, needs no model weights.
    Suggests continuation of similar lines from the current document.
    """
    line = before.rsplit('\n', 1)[-1]
    if len(line.strip()) < 3 or after.startswith(line):
        return ''
    lines = before[:-len(line)].splitlines() if line else before.splitlines()
    for i in range(len(lines)-1, -1, -1):
        old = lines[i]
        if old.startswith(line) and len(old) > len(line):
            result = old[len(line):]
            if i + 1 < len(lines) and lines[i+1].strip() and len(result) < 100:
                result += '\n' + lines[i+1]
            return result[:240]
    return ''

def cleanup_output(result):
    text = result.replace('\r', '')
    text = re.sub(r'^\s*```(?:\w+)?\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    text = text.strip('\n')
    if text.lower().startswith(('here is ', 'sure,', 'explanation:')):
        return ''
    return text[:1000]


def completion(model, prompt):
    request = Request(HOST + '/api/generate',
                      data=json.dumps({'model': model, 'prompt': prompt, 'stream': False,
                                       'options': {'temperature': 0.1, 'num_predict': 160}}).encode(),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=60) as response:
        answer = json.load(response)
    if answer.get('error'):
        raise RuntimeError(answer['error'])
    return cleanup_output(answer.get('response', ''))


class Channel(QObject):
    finished = Signal(object, int, int, str)
    error = Signal(str)


class CompletionService(QObject):
    def __init__(self, api):
        super().__init__(api.window)
        self.api = api
        self.channel = Channel(self)
        self.channel.finished.connect(self.receive)
        self.channel.error.connect(self.error)
        self.timers = {}
        self.connections = {}
        self.requests = {}
        self.active = True
        self.model = api.get_setting('model', api.window.settings.get('carlcomplete_model', ''))
        self.enabled = api.get_setting('enabled', api.window.settings.get('carlcomplete_enabled', True))
        self._reported_error = False
        self.server = LocalModelServer()
        # GUI remains responsive: checking/starting local inference is background work.
        self._server_thread = threading.Thread(target=self._start_server, daemon=True)
        self._server_thread.start()

    def _start_server(self):
        try:
            self.server.start()
            # If no model was configured yet, choose one already installed.
            for _ in range(10):
                if not self.active: return
                try:
                    models = get_models()
                    if self.active and models and self.model not in models:
                        self.model = models[0]
                        self.api.window.settings.set('carlcomplete_model', self.model)
                    return
                except Exception:
                    time.sleep(.3)
        except Exception:
            return

    def attach(self, editor):
        if editor in self.timers:
            return
        timer = QTimer(editor)
        timer.setSingleShot(True)
        timer.setInterval(950)
        timer.timeout.connect(lambda e=editor: self.send(e))
        on_text = lambda e=editor: self.schedule(e)
        on_cursor = lambda e=editor: self.moved(e)
        editor.textChanged.connect(on_text)
        editor.cursorPositionChanged.connect(on_cursor)
        self.connections[editor] = (on_text, on_cursor)
        self.timers[editor] = timer
        editor.destroyed.connect(lambda _=None, e=editor: self.forget(e))

    def forget(self, editor):
        self.timers.pop(editor, None)
        self.connections.pop(editor, None)
        self.requests.pop(editor, None)

    def moved(self, editor):
        # When user moves cursor, old suggestion is no longer valid.
        editor.clear_ghost_text()
        self.requests[editor] = self.requests.get(editor, 0) + 1

    def schedule(self, editor):
        editor.clear_ghost_text()
        self.requests[editor] = self.requests.get(editor, 0) + 1
        if not self.active or not self.enabled or editor.isReadOnly():
            return
        if editor.toPlainText().strip() and editor.textCursor().position() > 0:
            self.timers[editor].start()

    def send(self, editor):
        if not self.active or not self.enabled or not editor.path:
            return
        cursor = editor.textCursor()
        if cursor.hasSelection():
            return
        body = editor.toPlainText()
        position = cursor.position()
        before, after = body[:position], body[position:]
        if not before.strip() or len(before) > 1_000_000:
            return
        serial = self.requests.get(editor, 0)
        prompt = make_prompt(before, after, editor.path.name)
        model = self.model
        fallback = builtin_predict(before, after, editor.path.name)
        if not model:
            self.receive(editor, serial, position, fallback)
            return
        def worker():
            try:
                answer = completion(model, prompt)
                if self.active:
                    self.channel.finished.emit(editor, serial, position, answer)
            except Exception as exc:
                if self.active:
                    try:
                        if fallback:
                            self.channel.finished.emit(editor, serial, position, fallback)
                        self.channel.error.emit(str(exc))
                    except RuntimeError:
                        pass
        threading.Thread(target=worker, daemon=True).start()

    def receive(self, editor, serial, position, result):
        if not self.active or not self.enabled:
            return
        if editor not in self.timers or self.requests.get(editor) != serial:
            return
        try:
            if editor.textCursor().position() != position:
                return
            if self.api.window.current_editor() is not editor:
                return
            editor.set_ghost_text(result)
        except RuntimeError:
            self.forget(editor)

    def error(self, text):
        if not self._reported_error and self.active:
            self.api.window.append_output('CarlComplete: ' + text + '\n')
            self._reported_error = True

    def select_model(self):
        try:
            models = get_models()
        except Exception as exc:
            QMessageBox.warning(self.api.window, 'CarlComplete',
                'Ollama local indisponível. Rode ollama serve e ollama pull qwen2.5-coder:1.5b\n\n' + str(exc))
            return
        if not models:
            self.api.notify('Nenhum modelo Ollama instalado. Exemplo: ollama pull qwen2.5-coder:1.5b', True)
            return
        model, ok = QInputDialog.getItem(self.api.window, 'CarlComplete', 'Modelo local de código:',
                                          models, max(0, models.index(self.model)) if self.model in models else 0, False)
        if ok:
            self.model = model
            self.api.set_setting('model',model)
            self.api.window.settings.set('carlcomplete_model', model)
            self.api.notify('CarlComplete: ' + model)

    def toggle(self):
        self.enabled = not self.enabled
        self.api.set_setting('enabled',self.enabled)
        self.api.window.settings.set('carlcomplete_enabled', self.enabled)
        if not self.enabled:
            for editor in tuple(self.timers):
                self.timers[editor].stop()
                editor.clear_ghost_text()
        self.api.notify('CarlComplete ' + ('ligado' if self.enabled else 'desligado'))

    def stop(self):
        self.active = False
        self.server.stop()
        self.channel.finished.disconnect(self.receive)
        self.channel.error.disconnect(self.error)
        for editor, timer in list(self.timers.items()):
            timer.stop()
            editor.clear_ghost_text()
            try:
                on_text, on_cursor = self.connections[editor]
                editor.textChanged.disconnect(on_text)
                editor.cursorPositionChanged.disconnect(on_cursor)
            except (RuntimeError, TypeError, KeyError):
                pass
        self.timers.clear()
        self.connections.clear()


service = None


def activate(api):
    global service
    service = CompletionService(api)
    def apply_settings(values):
        service.model = values.get('model', service.model)
        service.enabled = bool(values.get('enabled', service.enabled))
        if not service.enabled:
            for e,t in list(service.timers.items()):
                t.stop()
                e.clear_ghost_text()
    api.register_settings({
        'enabled': {'type':'bool', 'label':'Ativar sugestões automáticas', 'default':True},
        'model': {'type':'str','label':'Modelo instalado (Ollama)', 'default':'qwen2.5-coder:1.5b'},
    },apply_settings)
    api.register_editor_hook(service.attach)
    api.register_action('model', 'CarlComplete · escolher modelo Ollama...', service.select_model)
    def pull_model():
        import shutil
        from PySide6.QtWidgets import QMessageBox
        choice = QMessageBox.question(api.window, 'CarlComplete · modelo local',
                    'Baixar qwen2.5-coder:1.5b para autocomplete?\n'
                    'A instalação usa a internet apenas para baixar o modelo e ocupa espaço em disco.\n'
                    'O processamento das sugestões ocorrerá localmente. Continuar?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
        if choice != QMessageBox.StandardButton.Yes:return
        if not shutil.which('ollama'):
            api.notify('Instale Ollama para baixar o modelo local.',error=True)
            return
        if not shutil.which('konsole'):
            api.notify('Konsole não encontrado. Execute: ollama pull qwen2.5-coder:1.5b',error=True)
            return
        subprocess.Popen(['konsole','--hold','-e','ollama','pull','qwen2.5-coder:1.5b'])
    api.register_action('install_model', 'CarlComplete · baixar modelo local (sob confirmação)...', pull_model)
    api.register_action('enabled', 'CarlComplete · ativar/desativar sugestões', service.toggle)
    api.register_action('manual', 'CarlComplete · sugerir agora',
                        lambda: service.send(api.window.current_editor()) if api.window.current_editor() else None,
                        shortcut='Ctrl+Alt+Space')
    if not service.model:
        api.window.append_output('CarlComplete: iniciando modelo local, se instalado. '
                                 'Caso não tenha pesos, use Ferramentas → CarlComplete → baixar modelo.\n')


def deactivate():
    global service
    if service:
        service.stop()
        service.deleteLater()
        service = None

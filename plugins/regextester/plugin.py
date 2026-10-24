import re
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLineEdit,QPlainTextEdit,QPushButton,QLabel
from carlde.plugin_helpers import show_text

def activate(api):
    def tester():
        dlg=QDialog(api.window);dlg.setWindowTitle('Regex Tester · Python re');dlg.resize(750,570)
        layout=QVBoxLayout(dlg)
        expr=QLineEdit();expr.setPlaceholderText('Expressão regular');layout.addWidget(expr)
        sample=QPlainTextEdit();sample.setPlaceholderText('Texto de teste...');layout.addWidget(sample)
        result=QPlainTextEdit();result.setReadOnly(True);layout.addWidget(result)
        btn=QPushButton('TESTAR');layout.addWidget(btn)
        def test():
            try:
                matches=list(re.finditer(expr.text(),sample.toPlainText()))[:200]
                lines=[f'{len(matches)} correspondência(s) (máximo 200):']
                for m in matches:lines.append(f'{m.span()}: {m.group(0)!r} | grupos={m.groups()!r}')
                result.setPlainText('\n'.join(lines))
            except re.error as exc:result.setPlainText('ERRO: '+str(exc))
        btn.clicked.connect(test);dlg.exec()
    api.register_action('regex','Regex Tester · testar expressões regulares',tester)

import sqlite3,csv
from pathlib import Path
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QPlainTextEdit,QPushButton,QLabel,QHBoxLayout,QTableWidget,QTableWidgetItem)
from carlde.plugin_helpers import context,select_file,ask_choice,ask_text,tool,commands,confirm

def activate(api):
    def open_db():
        root,_=context(api)
        if not root:return
        kind=ask_choice(api,'Database Explorer','Banco de dados',['SQLite (.db/.sqlite)','PostgreSQL (psql)'])
        if kind is None:return
        if kind.startswith('PostgreSQL'):
            if not tool(api,'psql'):return
            database=ask_text(api,'PostgreSQL','Banco (usa variáveis PGHOST/PGUSER/PGSERVICE):','postgres')
            if database and database.replace('_','').isalnum():
                commands(api,(('psql','--dbname',database,'--command',r'\dt'),root,'Listar tabelas PostgreSQL'))
            return
        path=select_file(api,'Abrir SQLite',root,'SQLite (*.db *.sqlite *.sqlite3);;Todos (*.*)')
        if not path:return
        dlg=QDialog(api.window);dlg.setWindowTitle('Database Explorer · '+path.name);dlg.resize(960,650)
        layout=QVBoxLayout(dlg)
        query=QPlainTextEdit();query.setFixedHeight(110)
        query.setPlainText("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        layout.addWidget(QLabel('SQL: SELECT / PRAGMA ou alterações confirmadas'));layout.addWidget(query)
        table=QTableWidget();layout.addWidget(table,1)
        buttons=QHBoxLayout();run=QPushButton('EXECUTAR');export=QPushButton('EXPORTAR CSV');buttons.addWidget(run);buttons.addWidget(export);layout.addLayout(buttons)
        cache=[]
        def execute():
            sql=query.toPlainText().strip()
            if not sql:return
            write=not sql.lstrip().lower().startswith(('select','pragma','explain','with'))
            if write and not confirm(api,'SQL modificador','Este SQL pode alterar o banco. Executar?'):return
            try:
                with sqlite3.connect(str(path)) as db:
                    cur=db.execute(sql)
                    if cur.description:
                        columns=[d[0] for d in cur.description]
                        rows=cur.fetchmany(2000)
                    else:
                        db.commit();columns=['Linhas alteradas'];rows=[(cur.rowcount,)]
                cache[:]=[columns,rows]
                table.setColumnCount(len(columns));table.setHorizontalHeaderLabels(columns);table.setRowCount(len(rows))
                for i,row in enumerate(rows):
                    for j,value in enumerate(row):table.setItem(i,j,QTableWidgetItem(str(value)))
            except sqlite3.Error as exc:api.notify(str(exc),error=True)
        def save():
            if not cache:return
            from PySide6.QtWidgets import QFileDialog
            file,_=QFileDialog.getSaveFileName(dlg,'Exportar CSV',str(root/'results.csv'),'CSV (*.csv)')
            if file:
                with open(file,'w',newline='',encoding='utf-8') as f:
                    writer=csv.writer(f);writer.writerow(cache[0]);writer.writerows(cache[1])
        run.clicked.connect(execute);export.clicked.connect(save);execute();dlg.exec()
    api.register_action('database','Database Explorer · SQLite / PostgreSQL',open_db)

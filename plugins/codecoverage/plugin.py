from carlde.plugin_helpers import context,tool,commands,ask_choice

def activate(api):
    def cover():
        root,_=context(api)
        if not root:return
        kind=ask_choice(api,'Code Coverage','Tecnologia',['Python · coverage+pytest','C++ · gcovr/CTest'])
        if kind is None:return
        if kind.startswith('Python'):
            if not tool(api,'coverage') or not tool(api,'pytest'):return
            steps=[(('coverage','run','-m','pytest'),root,'Executar testes instrumentados'),
                   (('coverage','report','-m'),root,'Relatório cobertura'),
                   (('coverage','html','-d',str(root/'dist'/'coverage-html')),root,'Gerar HTML')]
        else:
            if not tool(api,'cmake') or not tool(api,'ctest') or not tool(api,'gcovr'):return
            b=root/'build'/'Coverage'
            steps=[(('cmake','-S',str(root),'-B',str(b),'-DCMAKE_BUILD_TYPE=Debug','-DCMAKE_CXX_FLAGS=--coverage','-DCMAKE_EXE_LINKER_FLAGS=--coverage'),root,'Configurar Coverage'),
                   (('cmake','--build',str(b)),root,'Compilar instrumentado'),
                   (('ctest','--test-dir',str(b),'--output-on-failure'),root,'Testes C++'),
                   (('gcovr','-r',str(root),'--html-details','-o',str(root/'coverage.html')),root,'Relatório C++ HTML')]
        commands(api,*steps)
    api.register_action('coverage','Code Coverage · relatório',cover)

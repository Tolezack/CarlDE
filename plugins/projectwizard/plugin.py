def activate(api):
    def cpplib(project,name):
        (project/'include').mkdir(exist_ok=True);(project/'src').mkdir(exist_ok=True)
        (project/'include'/f'{name}.hpp').write_text('#pragma once\nint add(int a, int b);\n',encoding='utf-8')
        (project/'src'/f'{name}.cpp').write_text(f'#include "{name}.hpp"\nint add(int a, int b) {{ return a + b; }}\n',encoding='utf-8')
        (project/'CMakeLists.txt').write_text(f'cmake_minimum_required(VERSION 3.16)\nproject({name} LANGUAGES CXX)\nadd_library({name} STATIC src/{name}.cpp)\ntarget_include_directories({name} PUBLIC include)\n',encoding='utf-8')
        (project/'README.md').write_text('Biblioteca estática C++ criada pelo Project Wizard+.\n',encoding='utf-8')
    def pythonpkg(project,name):
        package=name.replace('-','_').lower();(project/package).mkdir(exist_ok=True)
        (project/package/'__init__.py').write_text('def add(a, b):\n    return a + b\n',encoding='utf-8')
        (project/'pyproject.toml').write_text('[build-system]\nrequires = ["setuptools>=68"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "'+package+'"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n',encoding='utf-8')
        (project/'main.py').write_text(f'from {package} import add\nprint(add(2, 3))\n',encoding='utf-8')
    def pythontest(project,name):
        (project/'tests').mkdir(exist_ok=True)
        (project/'main.py').write_text('def add(a,b):\n    return a + b\n\nif __name__ == "__main__":\n    print(add(2,3))\n',encoding='utf-8')
        (project/'tests'/'test_main.py').write_text('from main import add\n\ndef test_add():\n    assert add(2,3)==5\n',encoding='utf-8')
        (project/'pytest.ini').write_text('[pytest]\npythonpath = .\n',encoding='utf-8')
    api.register_template('cpplib','C++ · Biblioteca estática','Biblioteca C++ .a com CMake','cpp_library',cpplib)
    api.register_template('pythonpkg','Python · Pacote / biblioteca','Pacote Python com pyproject.toml','python',pythonpkg)
    api.register_template('pythontest','Python · Projeto com pytest','App com suíte de testes automatizados','python',pythontest)

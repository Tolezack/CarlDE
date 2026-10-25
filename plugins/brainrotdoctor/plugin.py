import ast
import re
from datetime import datetime
from pathlib import Path
import shutil
from carlde.plugin_helpers import context,show_text,confirm


def inspect(root:Path):
    problems=[]
    files=[p for p in root.rglob('*') if p.is_file() and len(p.parts)-len(root.parts)<=7 and not set(p.parts).intersection({'build','.git','.venv','dist'})]
    files=files[:1500]
    cmake=root/'CMakeLists.txt'
    if cmake.is_file():
        data=cmake.read_text(errors='replace')
        targets=set(re.findall(r'add_(?:executable|library)\s*\(\s*([A-Za-z_][\w-]*)',data,re.I))
        project=re.search(r'project\s*\(\s*([A-Za-z_][\w-]*)',data,re.I)
        for n,line in enumerate(data.splitlines(),1):
            match=re.search(r'\btarget_include_directories\s*\(\s*\$\{PROJECT_NAME\}',line,re.I)
            if match and project and project.group(1) not in targets:
                problems.append(('ERRO',str(cmake.relative_to(root)),n,'target_include_directories(${PROJECT_NAME}) usa alvo inexistente. Corrigir após conferir add_executable().'))
    for p in files:
        if p.suffix=='.py':
            try:ast.parse(p.read_text(encoding='utf-8'))
            except (SyntaxError,UnicodeDecodeError) as e:
                problems.append(('ERRO',str(p.relative_to(root)),getattr(e,'lineno',0) or 0,'Python: '+str(e)))
        elif p.suffix=='.json':
            try:__import__('json').loads(p.read_text(encoding='utf-8'))
            except (ValueError,UnicodeDecodeError) as e:
                problems.append(('ERRO',str(p.relative_to(root)),0,'JSON inválido: '+str(e)))
        elif p.suffix in ('.cpp','.hpp','.h','.cs'):
            try:s=p.read_text(encoding='utf-8')
            except UnicodeDecodeError:continue
            # Heurísticas não são provas; jamais alterar controle automaticamente.
            for n,line in enumerate(s.splitlines(),1):
                if re.search(r'glBegin\s*\(',line) and '#version 330' in s:
                    problems.append(('AVISO',str(p.relative_to(root)),n,'GL immediate mode não funciona em OpenGL Core 3.3.'))
                if re.search(r'camera\.yaw\s*[-+]?=',line) or 'raycast(' in line:
                    if len([f for f in problems if f[0]=='DICA'])<7:
                        problems.append(('DICA',str(p.relative_to(root)),n,'Teste o vetor frontal, os eixos e a normal de face ao interagir (não é erro confirmado).'))
    return problems

def activate(api):
    api.register_settings({'scan_limit':{'type':'int','label':'Limite de diagnósticos exibidos','default':150,'min':10,'max':500}})
    def scan():
        root,_=context(api)
        if not root:return
        issues=inspect(root)
        report='BrainrotDoctor / análise estática (ALPHA)\n\n'
        report+='Nenhum erro detectado pelas verificações simples. Isso NÃO garante programa sem bugs.' if not issues else '\n'.join(f'[{lvl}] {file}:{line} — {msg}' for lvl,file,line,msg in issues[:api.get_setting('scan_limit',150)])
        report+='\n\nControles/raycast e visuais precisam de testes em execução para confirmar problemas.'
        show_text(api,'BrainrotDoctor / Diagnóstico',report)
    def fix_cmake():
        root,_=context(api)
        if not root:return
        cmake=root/'CMakeLists.txt'
        if not cmake.is_file():api.notify('CMakeLists.txt ausente.',True);return
        source=cmake.read_text()
        if '${PROJECT_NAME}' not in source:api.notify('Não existe referência ${PROJECT_NAME} nesse CMake.');return
        # Replace only if there is one uniquely determined compiled target.
        targets=set(re.findall(r'add_(?:executable|library)\s*\(\s*([A-Za-z_][\w-]*)',source,re.I))
        project=re.search(r'project\s*\(\s*([A-Za-z_][\w-]*)',source,re.I)
        if not project or project.group(1) in targets or len(targets)!=1:
            api.notify('Alvos não são inequívocos; analise o CMake manualmente.',True);return
        target=next(iter(targets))
        fixed=re.sub(r'(target_(?:include_directories|compile_definitions|link_libraries)\s*\()\s*\$\{PROJECT_NAME\}',lambda m:m.group(1)+target,source,flags=re.I)
        if fixed==source:return
        if not confirm(api,'BrainrotDoctor / CMake',f'Substituir alvo ${{PROJECT_NAME}} inexistente por {target}?\nSerá criado um backup; revise a alteração.'):
            return
        backup=cmake.with_name('CMakeLists.txt.backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
        shutil.copy2(cmake,backup)
        cmake.write_text(fixed)
        api.notify('CMake corrigido. Backup: '+str(backup))
    api.register_action('scan','BrainrotDoctor · analisar projeto',scan)
    api.register_action('cmake','BrainrotDoctor · reparar alvo CMake (com backup)',fix_cmake)

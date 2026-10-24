import os,shutil,re,json
from pathlib import Path
from carlde.plugin_helpers import context,ask_choice,ask_text,confirm,tool,commands
from carlde.project import load_metadata

ICON='''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><rect width="128" height="128" fill="#273949"/><rect x="26" y="26" width="76" height="76" fill="#5797bd"/><path d="M43 65l15 15 28-34" stroke="#fff" fill="none" stroke-width="7"/></svg>'''

def activate(api):
    def export():
        root,_=context(api)
        if not root:return
        cfg=ask_choice(api,'Export Manager','Perfil de build',['Release','Debug'])
        if not cfg:return
        name=load_metadata(root).get('name',root.name)
        if not re.fullmatch('[a-zA-Z][a-zA-Z0-9_-]*',name):api.notify('Nome de projeto inválido.',error=True);return
        binaries=[root/'dist'/cfg/name,root/'build'/cfg/name]
        binary=next((x for x in binaries if x.is_file()),None)
        if not binary:api.notify('Exporte o executável Linux no CarlDE em '+cfg+' antes de empacotar.',error=True);return
        fmt=ask_choice(api,'Export Manager','Pacote Linux',['AppImage','DEB','RPM','Flatpak (manifesto)'])
        if not fmt:return
        version=ask_text(api,'Export Manager','Versão (ex.: 1.0.0):','1.0.0')
        if not version or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',version):api.notify('Versão inválida.',error=True);return
        dist=root/'dist'/'packages';dist.mkdir(parents=True,exist_ok=True)
        key=name.lower().replace('_','-')
        if fmt=='AppImage':
            if not tool(api,'appimagetool'):return
            stage=dist/(name+'.AppDir');bindir=stage/'usr'/'bin';bindir.mkdir(parents=True,exist_ok=True)
            shutil.copy2(binary,bindir/name);(bindir/name).chmod(0o755)
            (stage/'AppRun').write_text('#!/bin/sh\nHERE="$(dirname "$(readlink -f "$0")")"\nexec "$HERE/usr/bin/'+name+'" "$@"\n',encoding='utf-8')
            (stage/'AppRun').chmod(0o755)
            (stage/(name+'.svg')).write_text(ICON,encoding='utf-8')
            (stage/(name+'.desktop')).write_text('[Desktop Entry]\nType=Application\nName='+name+'\nExec='+name+'\nIcon='+name+'\nCategories=Development;\n',encoding='utf-8')
            commands(api,(('appimagetool',str(stage),str(dist/(name+'-'+version+'-x86_64.AppImage'))),root,'Empacotar AppImage'))
        elif fmt=='DEB':
            if not tool(api,'dpkg-deb'):return
            stage=dist/(key+'_'+version+'_amd64');(stage/'DEBIAN').mkdir(parents=True,exist_ok=True)
            target=stage/'usr'/'bin';target.mkdir(parents=True,exist_ok=True);shutil.copy2(binary,target/name)
            (stage/'DEBIAN'/'control').write_text('Package: '+key+'\nVersion: '+version+'\nSection: utils\nPriority: optional\nArchitecture: amd64\nMaintainer: CarlDE User <user@localhost>\nDescription: Aplicativo '+name+' empacotado com CarlDE\n',encoding='utf-8')
            commands(api,(('dpkg-deb','--build',str(stage)),root,'Criar pacote DEB'))
        elif fmt=='RPM':
            if not tool(api,'rpmbuild'):return
            top=dist/'rpmbuild';(top/'SOURCES').mkdir(parents=True,exist_ok=True);(top/'SPECS').mkdir(parents=True,exist_ok=True)
            for d in ['BUILD','RPMS','SRPMS','BUILDROOT']: (top/d).mkdir(exist_ok=True)
            shutil.copy2(binary,top/'SOURCES'/name)
            spec=('Name: '+key+'\nVersion: '+version+'\nRelease: 1\nSummary: Aplicativo '+name+'\nLicense: MIT\n'
                  'BuildArch: x86_64\n%description\nAplicativo empacotado pelo CarlDE\n'
                  '%prep\n%build\n%install\nmkdir -p %{buildroot}/usr/bin\n'
                  'install -m 0755 %{_sourcedir}/'+name+' %{buildroot}/usr/bin/'+name+'\n'
                  '%files\n/usr/bin/'+name+'\n')
            specfile=top/'SPECS'/(key+'.spec');specfile.write_text(spec,encoding='utf-8')
            commands(api,(('rpmbuild','--define','_topdir '+str(top),'--define','_sourcedir '+str(top/'SOURCES'),'-bb',str(specfile)),root,'Criar pacote RPM'))
        else:
            runtime=ask_text(api,'Flatpak','Versão do runtime org.freedesktop.Platform (instalado no sistema):','24.08')
            if not runtime or not re.fullmatch(r'[0-9]{2}\.[0-9]{2}',runtime):return
            stage=dist/'flatpak';stage.mkdir(exist_ok=True)
            shutil.copy2(binary,stage/name)
            appid='io.github.carlde.'+''.join(ch for ch in name.lower() if ch.isalnum())
            manifest={'app-id':appid,'runtime':'org.freedesktop.Platform','runtime-version':runtime,
                'sdk':'org.freedesktop.Sdk','command':name,
                'modules':[{'name':name,'buildsystem':'simple','build-commands':['install -D '+name+' /app/bin/'+name],
                            'sources':[{'type':'file','path':name}]}]}
            (stage/(appid+'.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
            api.notify('Manifesto Flatpak gerado em '+str(stage)+'; instale runtime e execute flatpak-builder manualmente.')
    api.register_action('package','Export Manager · pacotes Linux',export)

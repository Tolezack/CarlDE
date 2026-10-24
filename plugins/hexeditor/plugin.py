import re
from carlde.plugin_helpers import context,select_file,show_text,ask_text,confirm

def activate(api):
    def hexview():
        root,_=context(api)
        if not root:return
        path=select_file(api,'Abrir binário',root)
        if not path:return
        if path.stat().st_size>2_000_000:api.notify('Limite: 2 MB por arquivo.',error=True);return
        data=path.read_bytes()
        lines=[]
        for n in range(0,min(len(data),8192),16):
            chunk=data[n:n+16]
            lines.append(f'{n:08X}  '+ ' '.join(f'{b:02X}' for b in chunk).ljust(48)+'  '+''.join(chr(b) if 32<=b<127 else '.' for b in chunk))
        show_text(api,'Hex Editor · '+path.name,'\n'.join(lines)+'\n\nPrévia limitada aos primeiros 8 KB.')
        value=ask_text(api,'Hex Editor','Alterar offset (hexadecimal, deixe vazio para não editar):','')
        if not value:return
        try:offset=int(value,16)
        except ValueError:api.notify('Offset inválido.',error=True);return
        if not 0<=offset<len(data):api.notify('Offset fora do arquivo.',error=True);return
        byte=ask_text(api,'Hex Editor',f'Novo byte em {offset:X} (00-FF):',f'{data[offset]:02X}')
        if not byte or not re.fullmatch('[a-fA-F0-9]{2}',byte):api.notify('Valor precisa ser 2 dígitos hex.',error=True);return
        if not confirm(api,'Alteração binária',f'Gravar {byte} no offset {offset:08X} de {path.name}?'):return
        import shutil
        shutil.copy2(path,str(path)+'.bak')
        buf=bytearray(data);buf[offset]=int(byte,16);path.write_bytes(buf);api.notify('Byte salvo e backup .bak criado.')
    api.register_action('hex','Hex Editor · inspecionar/editar binário',hexview)

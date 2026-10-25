"""CarlTorture: tiny reproducible esolang sandbox; no filesystem/network commands."""
from pathlib import Path
from carlde.plugin_helpers import context,select_file,show_text

ALPHABET='¤§¶±×÷¿¡'
STEPS=100000

def run(program:str, user_input:str='',limit:int=STEPS):
    """Eight glyphs. Effective operation = (glyph index+pointer+cell) % 8.
    Index 6/7 are reserved conditional jumps; code rotates after 17 steps.
    Output UTF-8-ish bytes represented by unicode Latin1, bounded steps.
    """
    tape=[0]*256;pointer=0;pc=0;steps=0;out=[];inp=iter(user_input)
    code=[c for c in program if c in ALPHABET]
    if not code:return '(código sem instruções)',steps
    while pc<len(code) and steps<limit and len(out)<2048:
        idx=ALPHABET.index(code[pc])
        op=(idx+pointer+tape[pointer])%8
        if op==0:pointer=(pointer+1)%256
        elif op==1:pointer=(pointer-1)%256
        elif op==2:tape[pointer]=(tape[pointer]+1)%256
        elif op==3:tape[pointer]=(tape[pointer]-1)%256
        elif op==4:out.append(chr(tape[pointer]))
        elif op==5:tape[pointer]=ord(next(inp,'\0'))%256
        elif op==6 and tape[pointer]==0:pc+=1+(tape[(pointer+7)%256]%7)
        elif op==7 and tape[pointer]!=0:pc=max(-1,pc-1-(tape[(pointer+11)%256]%7))
        if (steps+1)%17==0:
            code[pc%len(code)] = ALPHABET[(idx+steps//17)%8]
        steps+=1;pc+=1
    return ''.join(out)+(f'\n[Limite: {limit} instruções]' if steps>=limit else ''),steps

def post_create(root,name):
    (root/'main.ctort').write_text('¤§¶±×÷¿¡\n',encoding='utf-8')
    (root/'README.md').write_text('CarlTorture: operações alteradas pelo estado; execute via Ferramentas > CarlTorture.\n')
    return []

def activate(api):
    api.register_settings({'limit':{'type':'int','label':'Máximo de instruções','default':50000,'min':100,'max':100000}})
    api.register_template('carltorture','CarlTorture · Esolang','Linguagem absurda, interpretada no CarlDE, sem compilador externo.','empty',post_create)
    def execute():
        root,path=context(api)
        if not root:return
        source=path if path and path.suffix=='.ctort' else select_file(api,'Arquivo CarlTorture',root,'CarlTorture (*.ctort)')
        if not source:return
        output,steps=run(source.read_text(encoding='utf-8'),limit=api.get_setting('limit',50000))
        show_text(api,'CarlTorture / execução',f'Passos executados: {steps}\n\nSaída:\n{output or "(vazia)"}')
    api.register_action('run','CarlTorture · executar .ctort',execute)

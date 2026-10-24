# CarlComplete: ghost text local

1. Instale Ollama: https://ollama.com/ e inicie `ollama serve` (se não estiver rodando).
2. Instale um modelo com `ollama pull qwen2.5-coder:1.5b` (pode usar outro).
3. Na loja do CarlDE instale e ATIVE **CarlComplete**.
4. **Ferramentas > CarlComplete · escolher modelo Ollama...** e selecione o modelo disponível.
5. Abra C++/C#/Python, digite e pare ~1 segundo; verá sugestões cinzas. `Tab` aceita; `Esc` ignora. `Ctrl+Alt+Space` tenta sugerir agora.
6. **Ferramentas > CarlComplete · ativar/desativar** permite pausar.

O plugin consulta **somente** `127.0.0.1:11434` e manda até 1400 caracteres anteriores e 240 posteriores ao cursor. Não acessa provedores de IA na nuvem, porém o modelo local pode sugerir trechos inválidos; revise antes de executar. Sem Ollama/modelo disponível as sugestões não aparecem; o CarlDE continua funcionando.

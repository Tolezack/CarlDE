# CarlComplete 1.1 — Ghost Text local

- `Tab`: aceita o texto cinza; `Esc`: descarta; `Ctrl+Alt+Espaço`: gera sugestão manualmente.
- Requer **Ollama instalado localmente** e um modelo já baixado. O plugin **não embute os pesos de uma IA**.
- Na ativação (inclusive início do CarlDE, se o plugin estiver habilitado), tenta acessar o servidor Ollama em `127.0.0.1:11434`. Se indisponível e `ollama` existir, inicia seu próprio processo `ollama serve`.
- No fechamento da IDE/desativação do plugin, encerra **somente o processo que iniciou**. Nunca encerra um Ollama já existente de outro aplicativo.
- Se houver modelos instalados, seleciona o primeiro automaticamente. Para trocar: `Ferramentas → CarlComplete · escolher modelo`.
- Para obter pesos: use a ação de download **com confirmação** ou execute `ollama pull qwen2.5-coder:1.5b` no terminal. A primeira aquisição exige internet.
- A inferência fica no seu computador; não há API paga. Modelos pequenos dão sugestões mais simples que os grandes; desempenho depende da máquina.

A IA gera sugestões em background. Se não houver Ollama ou modelo disponível, o plugin mostra a dependência faltante em SAÍDA, e não gera sugestões falsas.

Sem Ollama ou modelo, um preditor **estatístico simples integrado ao plugin** reutiliza padrões do próprio arquivo para sugerir texto em cinza. Não é um LLM e não gera funções inteiras inéditas.

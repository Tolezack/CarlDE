# CarlDE — Catálogo de plugins v8

Publique o CONTEÚDO deste ZIP na raiz de [Tolezack/CarlDE](https://github.com/Tolezack/CarlDE). O arquivo `index.json` deve ficar na raiz.

- **BrainrotCode 3.1 alpha**: geração procedural Fase 02, biomas, geologia e cavernas determinísticas, mantém streaming da fase 01. O template C++ inclui cabeçalhos e shader.
- **CarlAI Local 2.0**: analisa memória, CPU/GPU Linux, recomenda modelo Ollama e baixa somente com confirmação. Ferramentas → CarlAI → analisar PC.
- **CarlComplete 1.2**: Ghost Text, Tab para aceitar, opção de configurar modelo pela loja.
- **BrainrotDoctor alpha**: inspeção estática de projetos e reparo específico de CMake com backup; NÃO conserta automaticamente todos os bugs visuais ou físicos.
- **CarlTorture alpha**: linguagem esotérica experimental com interpretador limitado.

As capas ficam `plugins/<id>/cover.png` no GitHub; nenhuma extensão é instalada automaticamente na IDE.

Após mudanças, execute `python3 build_catalog.py` e `python3 verify_plugins.py` antes do push.

Atenção: os plugins executam código Python do usuário; hashes SHA-256 do catálogo verificam integridade relativa à branch, não provam autoria.

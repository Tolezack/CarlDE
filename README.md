# CarlDE — plugins oficiais (catálogo v6)

Publicar o **conteúdo** deste pacote na raiz de `https://github.com/Tolezack/CarlDE`, branch `main`.

O repositório contém **33 plugins** e suas capas `plugins/<id>/cover.png`. `index.json` e `build_catalog.py` ficam na raiz. A IDE vem sem plugins instalados: as capas são carregadas pela loja e os códigos só são baixados depois de escolher **BAIXAR / ATIVAR**.

## Atualizações

- **BrainrotCode 2.0.0**: mundo voxel de teste em C++ com noise 3D/cavernas, biomas, árvores, chunks greedy, renderizador GLFW/OpenGL, câmera FPS, colisão simples, atlas procedural, água e lava com níveis. A IDE inclui automaticamente cabeçalhos em projetos C++ quando este plugin está ativado.
- **CarlComplete 1.1.0**: tenta iniciar Ollama local quando a IDE inicia (se instalado) e encerra apenas o processo iniciado por ele ao sair. Um preditor estatístico básico já vem embutido; pesos de IA generativa são baixados somente com confirmação.
- **CarlDE 0.6.0**: hooks de projetos para extensões e correção da execução quando o nome do alvo CMake difere da pasta.

Consulte `plugins/brainrotcode/README.md` e `plugins/carlcomplete/README.md` para uso e limitações.

## Publicação

```bash
python3 build_catalog.py
python3 verify_plugins.py
```

Faça commit/push e atualize o catálogo dentro da IDE. Plugins executam Python com as permissões do usuário; SHA-256 apenas compara com o catálogo remoto, não é uma assinatura independente. Publique somente código revisado.

### Atualização BrainrotCode 3.0 alpha

O novo template Streaming Voxel contém arquivos `.sh`, `.cfg`, `.vert` e `.frag`,
portanto recomenda-se usar **CarlDE IDE v7** ou posterior para o gerenciador de
plugins reconhecer todas as dependências do template. As imagens continuam neste
repositório GitHub, e os plugins só são baixados após a escolha do usuário.

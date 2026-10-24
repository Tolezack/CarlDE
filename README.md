# CarlDE — Loja de plugins

Repositório de plugins e imagens para **CarlDE no Linux**, acessado automaticamente em:

https://github.com/Tolezack/CarlDE

## Estrutura

- `index.json` — catálogo (nome, versão, SHA-256 e arquivo PNG por plugin)
- `build_catalog.py` — gera novamente os hashes após mudanças
- `plugins/<id>/plugin.json` — metadados
- `plugins/<id>/plugin.py` — código da extensão
- `plugins/<id>/cover.png` — **imagem mostrada na loja diretamente pelo GitHub**

O pacote inclui 6 extensões: OpenTK, AutoCorrigir Código, Formatador, Git Tools, TODO Explorer e CMake Cleaner. Os dois últimos são novos nesta versão.

## Publicar atualização

Extraia o ZIP **diretamente na raiz** de `Tolezack/CarlDE` na branch `main` (substitua o catálogo antigo). Sempre que editar um arquivo ou PNG, rode:

```bash
python3 build_catalog.py
```

Depois faça commit/push do `index.json` e do conteúdo de `plugins/`.

**Não é necessário enviar o código-fonte da IDE a este repositório** para carregar os plugins. O CarlDE só usa o catálogo e as imagens até você clicar BAIXAR, e nenhum plugin é ativado automaticamente.

> Segurança: uma extensão é código Python executado sob sua conta local. Instale e ative apenas conteúdo confiável. A verificação SHA-256 evita dados adulterados em trânsito em relação ao próprio catálogo, mas não substitui assinaturas ou revisão de código.

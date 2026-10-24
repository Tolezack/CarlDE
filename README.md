# CarlDE — repositório de plugins (com imagens)

Publicar **estes arquivos na raiz de um repositório GitHub público**, branch `main`:

```
index.json
build_catalog.py
README.md
plugins/
  opentk/cover.png, plugin.json, plugin.py
  autofix/cover.png, plugin.json, plugin.py
  formatter/cover.png, plugin.json, plugin.py
  gittools/cover.png, plugin.json, plugin.py
```

No CarlDE abra **Loja de plugins**, escreva `seu-usuario/carlde-plugins` e `main`, clique **CONECTAR / ATUALIZAR** e depois **BAIXAR**. Os PNGs são exibidos em cada card; os downloads são conferidos por SHA-256. Após baixar, clique **ATIVAR** se decidir executar o plugin.

Para criar novos plugins, faça uma pasta em `plugins/`, contendo `plugin.json`, `plugin.py` e, opcionalmente, `cover.png`. No `plugin.json`, inclua `"image": "cover.png"` para a capa. Após qualquer edição de arquivos, execute:

```bash
python3 build_catalog.py
```

Faça commit/push do catálogo regenerado e de todos os arquivos. **A IDE não contém estes códigos de plugins pré-instalados**; este ZIP é o material para o seu futuro repositório.

**Segurança:** plugin é código Python executado com permissão do usuário. Os hashes não provam a identidade do autor.

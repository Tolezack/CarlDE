# CarlDE — repositório oficial de plugins

Publicar estes arquivos na **raiz** de `https://github.com/Tolezack/CarlDE`, branch `main`. Exemplo:

```
Tolezack/CarlDE
├── index.json
├── build_catalog.py
├── PLUGIN_API.md
└── plugins/
    ├── opentk/{plugin.json, plugin.py, cover.png}
    ├── intellicode/{plugin.json, plugin.py, cover.png}
    ├── carlai/{plugin.json, plugin.py, cover.png}
    └── ... 28 outros plugins ...
```

A IDE CarlDE 0.4 consulta o catálogo e as capas do GitHub, mas **não baixa o código dos plugins** até você clicar BAIXAR. Depois é necessário ATIVAR. O repositório contém **31 extensões** com implementações iniciais reais ou integração com ferramentas existentes; elas não substituem nem incluem as ferramentas externas (Ollama, clangd, GDB, .NET, Vulkan etc.).

## Como publicar

1. Extraia `CarlDE_Plugins_GitHub_v4.zip`.
2. Suba **o conteúdo** da pasta para a raiz do seu repositório (não suba a pasta envolvendo esses arquivos).
3. Execute `python3 build_catalog.py` após editar qualquer plugin ou capa.
4. Faça commit/push dos arquivos e acesse a loja no CarlDE.

## Principais recursos

- **OpenTK 3D**: integração .NET/OpenTK oficial via NuGet; ações para restaurar, editar shaders externos e rodar cubo 3D com OpenGL 3.3, GLSL e buffers gráficos.
- **IntelliCode LSP**: sugestões sob demanda, diagnósticos e ir para definição via servidores LSP reais; C++ com clangd, C# com csharp-ls, Python com basedpyright.
- **CarlAI Local**: conecta a um modelo Ollama rodando apenas em `127.0.0.1:11434`; não chama serviços de IA externos.
- **CarlDebugger**: GUI inicial sobre GDB/MI2, permite breakpoints e inspeção.
- **CMake Studio, SDL Studio e Vulkan Tools**: edição de CMake, projetos gráficos/SDK e compilação de shaders SPIR-V.
- **Test Runner, Code Coverage, Valgrind e perf**: executam os sistemas Linux existentes, não simulam resultados.
- **Export Manager**: cria pacotes AppImage/DEB/RPM se as ferramentas estiverem instaladas; Flatpak gera um manifesto para finalização manual.
- **GitHub Publisher**: usa `gh release create` e pede confirmação explícita.
- **Outros**: UI Designer, Resource/Database Explorer, Docker Manager, Hex Editor, Regex Tester, JSON Studio, Documentation Generator, Project Wizard+, Terminal Profiles, e os plugins anteriores.

## Segurança

Plugins são scripts Python com permissões de usuário. Os hashes SHA-256 verificam correspondência com o catálogo, **não** identidade ou assinatura criptográfica. Ative apenas plugins de fontes confiáveis e proteja a branch principal do repositório.

## Validar o catálogo

```bash
python3 build_catalog.py
python3 verify_plugins.py
```

Observação: algumas integrações dependem de distribuições, versões de SDK, permissões e ferramentas instaladas. Veja `README.md` do ZIP da IDE para detalhes e limitações.

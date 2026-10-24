# BrainrotCode

API de conveniência opcional; **não altera a linguagem** C++ ou C#. O pacote OpenTK é instalado pelo NuGet para projetos C#, e GLFW/OpenGL (pacotes do Linux) são necessários somente para janelas C++. A versão 1.0 não cobre literalmente todas as APIs de C++/OpenTK; oferece atalhos iniciais para operações recorrentes.

## Criar um projeto novo

Após instalar e ativar o plugin, use **Novo projeto** → **C# · BrainrotCode / OpenTK** ou **C++ · BrainrotCode / OpenGL**.

## C++17 (sem dependência externa para terreno/UV)

```cpp
#include "brainrot.hpp"
auto map = br::terrain(128,128,1234,48.0f,5); // 16384 alturas
// Ordem das faces: frente, trás, esquerda, direita, cima, baixo
auto block = br::block_mesh({1,1,2,2,3,4},16,16);
auto uv = br::block_uv(5,16,16);
```

Janela OpenGL real usando GLFW (requer `#define BRAINROT_ENABLE_GLFW`, CMake configurado e pacotes glfw / pkgconf / OpenGL):

```cpp
#include "brainrot.hpp"
int main(){ br::window("Meu Jogo",960,540); }
```

## C# / OpenTK 4

```csharp
BrainrotCode.Brainrot.Window("Meu Jogo",960,540); // abre e executa janela OpenGL
var terrain = BrainrotCode.Brainrot.Terrain(128,128,42);
var cube = BrainrotCode.Brainrot.Block(new[]{1,1,2,2,3,4});
var uv = BrainrotCode.Brainrot.BlockUV(5,16,16);
```

`Block` retorna vértices e índices; **não chama o renderer automaticamente**. Renderize com seus próprios shaders e VBO/VAO. As alturas são determinísticas em ambas as versões, mas não garantimos resultados bit a bit idênticos entre C++ e C#.


## Corrigir o erro `br does not name a type`

C++ não executa funções soltas na raiz de um `.cpp`. **É obrigatório** ter `#include "brainrot.hpp"` e colocar a chamada em `int main()`. No CarlDE, **Ferramentas → BrainrotCode → corrigir/criar janela C++ compilável...** cria um `src/main.cpp` pronto, coloca o header em `include/`, configura o CMake e faz backup do código antigo (com confirmação).

No CachyOS/Arch atual:

```bash
sudo pacman -S --needed glfw mesa pkgconf cmake gcc
```

O `C# BrainrotCode.Brainrot.Window(...)` funciona **somente** em projetos C# com OpenTK e `.csproj`, não em `main.cpp`.

Para compilar manualmente C++:

```bash
cmake -S . -B build/Debug -DCMAKE_BUILD_TYPE=Debug
cmake --build build/Debug
./build/Debug/NOME_DO_PROJETO
```

> A biblioteca `br::terrain`/`br::block_uv` pode funcionar sem GLFW. A janela `br::window` precisa de GLFW e OpenGL configurados no CMake.

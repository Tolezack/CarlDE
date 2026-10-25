# BrainrotCode 2.0 — API C++17 e OpenTK C#

## Instalação automática

Após **BAIXAR + ATIVAR** no CarlDE v0.6, ao criar ou abrir um projeto C++ com `CMakeLists.txt`, o plugin:

- Gera `include/brainrot.hpp` e `include/brainrot_world.hpp` se faltarem;
- Adiciona o caminho de inclusão no `CMakeLists.txt` sem substituir o código do usuário;
- Se encontrar `br::World` ou `br::window` em `src/main.cpp`, configura GLFW/OpenGL no CMake;
- Só substitui `src/main.cpp` na ação explícita de geração de exemplo, com backup/confirmação.

Cabeçalhos antigos originais BrainrotCode 1.x podem ser atualizados automaticamente. Cabeçalhos editados pelo usuário não são substituídos à força.

No CachyOS:

```bash
sudo pacman -S --needed glfw mesa pkgconf gcc cmake
```

## Novo template — C++ · BrainrotCode / Mundo Voxel 3D

Crie pelo assistente de projetos ou use `Ferramentas → BrainrotCode · criar mundo voxel de teste...` (confirmação e backup).

```cpp
#include "brainrot.hpp"
#include <iostream>
int main() {
    br::World mundo(80, 80, 72, 42); // largura, profundidade, altura, seed
    mundo.biomes(true).greedyMeshing(true).chunks(16).renderDistance(5);
    mundo.generate();
    std::cout << mundo.face_count() << " faces\n";
    mundo.run("BrainrotCode | Mundo voxel");
}
```

Controles do exemplo: mouse olha, **WASD** anda, **Espaço** pula, **F** voa, **Ctrl** corre, **Esc** solta/captura mouse, **Q** sai, **LMB** quebra, **RMB** coloca, teclas **1–4** alternam bloco/pedra/água/lava/madeira.

### API de mundo voxel realmente implementada (protótipo)

| API | Efeito |
|---|---|
| `br::noise3(x,y,z,seed)` e `br::fbm3(...)` | Noise 3D interpolado / fractal |
| `World::generate()` | Mundo de dimensões finitas, heightmap com escarpas, cavernas internas, água rasa e árvores |
| `World::biomes(bool)` | Biomas simplificados: neve, areia, grama |
| `World::greedyMeshing(bool)` | Une faces de blocos coplanares iguais por chunk |
| `World::chunks(size)` | Altera tamanho dos chunks de malha |
| `World::renderDistance(chunks)` | Distância de desenho dos líquidos (sólidos do protótipo são desenhados globalmente) |
| `World::place_liquid(...)` e `step_fluids(budget)` | Água/lava em células com níveis 1–7 e fluxo simples |
| `World::collides(...)` | Colisão AABB básica |
| `World::set/get/surface` | Acesso direto aos blocos |
| `World::run()` | Janela GLFW OpenGL 2.1 (compatibility), câmera FPS, voo, pulo, mouse, blocos e renderização |
| `block_uv`, `block_mesh`, `terrain` | APIs anteriores mantidas |

O renderizador usa **atlas procedural gerado na memória** com pixel art, **neblina linear**, **iluminação por face** e ciclo de brilho. **Ainda não possui** sombras projetadas, iluminação voxel propagada, shaders GLSL configuráveis, chunks assíncronos, geração infinita, física avançada de líquidos, salvamento de mundos ou desempenho e mecânicas no nível de Vintage Story. A renderização usa OpenGL de compatibilidade por simplicidade e precisa de teste numa máquina Linux com GLFW/OpenGL real.

## C# / OpenTK

O helper `Brainrot.cs` continua permitindo:

```csharp
using BrainrotCode;
Brainrot.Window("Meu jogo", 1280, 720);
var heights = Brainrot.Terrain(64,64,42);
var mesh = Brainrot.Block(new []{1,1,2,3,4,5});
```

O **mundo voxel 2.0** foi implementado em **C++**, não foi portado ainda para C#/OpenTK. São bibliotecas opcionais: C++ tradicional e OpenTK tradicional continuam disponíveis.

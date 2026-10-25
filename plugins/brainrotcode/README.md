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

## 3.0 alpha — Novo template Streaming Voxel (Fase 01)

Selecione **C++ · BrainrotCode 3 / Streaming Voxel** no criador de projetos do CarlDE.
O novo template copia `brainrot_stream.hpp`, `brainrot_gl.hpp`, `brainrot_live_api.h`,
`src/main.cpp`, `src/live_rules.cpp`, `shaders/world.vert/frag`, `controls.cfg`,
`CMakeLists.txt` e scripts de execução/hot reload. A versão antiga de `br::World`
continua disponível sem modificações.

O núcleo `br::stream::World` inclui geração em workers, meshing greedy por chunk,
limite de jobs, streaming, salvamento incremental e raycast DDA. O demo usa
OpenGL 3.3 VAO/VBO e shaders GLSL externos. Controles, sensibilidade, alcance
do raycast e render distance são recarregáveis a partir de `controls.cfg`.
Alterações a `src/live_rules.cpp` são compiladas automaticamente e carregadas
pelo jogo usando uma interface C (veja `include/brainrot_live_api.h`).

No Linux CachyOS: `sudo pacman -S --needed gcc cmake glfw pkgconf mesa`.
Leia o README que acompanha o template. **Não implementa ainda as fases 02–06
nem é uma engine equivalente ao Vintage Story.**


## 3.1 Alpha / Fase 02

Adicionado `brainrot_biomes.hpp` (incluído por `brainrot_stream.hpp`):
noise3/fbm3, domínio deformado, continentalidade, erosão, montanhas e rios esculpidos, 8 biomas baseados em clima, geologia em camadas, minério de cobre e árvores determinísticas entre chunks.

**Limites:** não há água renderizada, iluminação voxel ou erosão física; rios são depressões procedurais. Biomas e geologia são estáticos na seed. Não é equivalente ao Vintage Story. `brainrot_saves_phase02` isola o mundo novo dos saves v7.

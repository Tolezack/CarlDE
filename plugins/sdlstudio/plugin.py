from carlde.project import initial_files

SDL_MAIN='''#include <SDL3/SDL.h>\n#include <stdio.h>\nint main(){ if(!SDL_Init(SDL_INIT_VIDEO)){fprintf(stderr,"%s\\n",SDL_GetError());return 1;}\nSDL_Window* w=SDL_CreateWindow("CarlDE SDL3",960,540,0); if(!w)return 2;\nSDL_Renderer* r=SDL_CreateRenderer(w,NULL); if(!r)return 3;\nint running=1; SDL_Event ev;while(running){while(SDL_PollEvent(&ev)){if(ev.type==SDL_EVENT_QUIT)running=0;}\nSDL_SetRenderDrawColor(r,28,45,65,255);SDL_RenderClear(r);SDL_RenderPresent(r);SDL_Delay(16);}\nSDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();return 0;}\n'''
SDL2_MAIN='''#include <SDL.h>\n#include <stdio.h>\nint main(){if(SDL_Init(SDL_INIT_VIDEO)!=0){fprintf(stderr,"%s\\n",SDL_GetError());return 1;}\nSDL_Window *w=SDL_CreateWindow("CarlDE SDL2",SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,960,540,0);\nif(!w)return 2; SDL_Renderer *r=SDL_CreateRenderer(w,-1,SDL_RENDERER_ACCELERATED);if(!r)return 3;\nint running=1;SDL_Event ev;while(running){while(SDL_PollEvent(&ev)){if(ev.type==SDL_QUIT)running=0;}\nSDL_SetRenderDrawColor(r,28,45,65,255);SDL_RenderClear(r);SDL_RenderPresent(r);SDL_Delay(16);}\nSDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();return 0;}\n'''

def activate(api):
    def setup(kind):
        def create(project,name):
            (project/'src').mkdir(exist_ok=True)
            (project/'src/main.cpp').write_text(SDL_MAIN if kind=='SDL3' else SDL2_MAIN,encoding='utf-8')
            cmake=('cmake_minimum_required(VERSION 3.20)\nproject('+name+' LANGUAGES CXX)\n'
                   'set(CMAKE_CXX_STANDARD 17)\nfind_package('+kind+' REQUIRED CONFIG)\n'
                   'add_executable('+name+' src/main.cpp)\n'
                   'target_link_libraries('+name+' PRIVATE '+kind+'::'+kind+')\n')
            (project/'CMakeLists.txt').write_text(cmake,encoding='utf-8')
            (project/'README-SDL.md').write_text('Necessário '+kind+' e desenvolvimento CMake instalados no sistema.\n',encoding='utf-8')
        return create
    api.register_template('sdl2','C++ · SDL2', 'Projeto SDL2 C++ com CMake e janela', 'cpp',setup('SDL2'))
    api.register_template('sdl3','C++ · SDL3', 'Projeto SDL3 C++ com CMake e janela', 'cpp',setup('SDL3'))

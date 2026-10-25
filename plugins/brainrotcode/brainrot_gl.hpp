#pragma once
// Minimal OpenGL 3.3 function loader via GLFW. No glad/glew requirement.
// This is exclusively called from the GLFW render thread.
#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
namespace br::gl {
using GLuint=unsigned int;using GLenum=unsigned int;using GLint=int;using GLsizei=int;
using GLboolean=unsigned char;using GLsizeiptr=std::ptrdiff_t;using GLfloat=float;
constexpr GLenum VERTEX_SHADER=0x8B31, FRAGMENT_SHADER=0x8B30,COMPILE_STATUS=0x8B81,LINK_STATUS=0x8B82,INFO_LOG_LENGTH=0x8B84;
constexpr GLenum ARRAY_BUFFER=0x8892,STATIC_DRAW=0x88E4,FLOAT=0x1406,TRIANGLES=0x0004,LINES=0x0001,COLOR_BUFFER_BIT=0x00004000,DEPTH_BUFFER_BIT=0x00000100,DEPTH_TEST=0x0B71,CULL_FACE=0x0B44;
#define GL_FN(name,Ret,...) using name##T = Ret (*)(__VA_ARGS__); inline name##T name=nullptr
GL_FN(CreateShader,GLuint,GLenum);GL_FN(ShaderSource,void,GLuint,GLsizei,const char* const*,const GLint*);
GL_FN(CompileShader,void,GLuint);GL_FN(GetShaderiv,void,GLuint,GLenum,GLint*);GL_FN(GetShaderInfoLog,void,GLuint,GLsizei,GLsizei*,char*);GL_FN(DeleteShader,void,GLuint);
GL_FN(CreateProgram,GLuint);GL_FN(AttachShader,void,GLuint,GLuint);GL_FN(LinkProgram,void,GLuint);GL_FN(GetProgramiv,void,GLuint,GLenum,GLint*);GL_FN(GetProgramInfoLog,void,GLuint,GLsizei,GLsizei*,char*);GL_FN(DeleteProgram,void,GLuint);GL_FN(UseProgram,void,GLuint);
GL_FN(GetUniformLocation,GLint,GLuint,const char*);GL_FN(UniformMatrix4fv,void,GLint,GLsizei,GLboolean,const GLfloat*);GL_FN(Uniform3f,void,GLint,GLfloat,GLfloat,GLfloat);GL_FN(Uniform1f,void,GLint,GLfloat);
GL_FN(GenVertexArrays,void,GLsizei,GLuint*);GL_FN(BindVertexArray,void,GLuint);GL_FN(DeleteVertexArrays,void,GLsizei,const GLuint*);
GL_FN(GenBuffers,void,GLsizei,GLuint*);GL_FN(BindBuffer,void,GLenum,GLuint);GL_FN(BufferData,void,GLenum,GLsizeiptr,const void*,GLenum);GL_FN(DeleteBuffers,void,GLsizei,const GLuint*);
GL_FN(EnableVertexAttribArray,void,GLuint);GL_FN(VertexAttribPointer,void,GLuint,GLint,GLenum,GLboolean,GLsizei,const void*);
GL_FN(DrawArrays,void,GLenum,GLint,GLsizei);GL_FN(Viewport,void,GLint,GLint,GLsizei,GLsizei);GL_FN(Clear,void,GLenum);GL_FN(ClearColor,void,GLfloat,GLfloat,GLfloat,GLfloat);GL_FN(Enable,void,GLenum);GL_FN(Disable,void,GLenum);
#undef GL_FN
inline void load() {
#define LOAD(fn) fn=reinterpret_cast<fn##T>(glfwGetProcAddress("gl" #fn));if(!fn)throw std::runtime_error("OpenGL 3.3: gl" #fn " unavailable")
LOAD(CreateShader);LOAD(ShaderSource);LOAD(CompileShader);LOAD(GetShaderiv);LOAD(GetShaderInfoLog);LOAD(DeleteShader);
LOAD(CreateProgram);LOAD(AttachShader);LOAD(LinkProgram);LOAD(GetProgramiv);LOAD(GetProgramInfoLog);LOAD(DeleteProgram);LOAD(UseProgram);
LOAD(GetUniformLocation);LOAD(UniformMatrix4fv);LOAD(Uniform3f);LOAD(Uniform1f);
LOAD(GenVertexArrays);LOAD(BindVertexArray);LOAD(DeleteVertexArrays);LOAD(GenBuffers);LOAD(BindBuffer);LOAD(BufferData);LOAD(DeleteBuffers);
LOAD(EnableVertexAttribArray);LOAD(VertexAttribPointer);LOAD(DrawArrays);LOAD(Viewport);LOAD(Clear);LOAD(ClearColor);LOAD(Enable);LOAD(Disable);
#undef LOAD
}
inline GLuint compile(GLenum type,const std::string& code) {
    GLuint sh=CreateShader(type);const char* src=code.c_str();ShaderSource(sh,1,&src,nullptr);CompileShader(sh);
    GLint ok=0;GetShaderiv(sh,COMPILE_STATUS,&ok);
    if(!ok){GLint len=0;GetShaderiv(sh,INFO_LOG_LENGTH,&len);std::string log(std::size_t(std::max(1,len)),' ');GetShaderInfoLog(sh,len,nullptr,log.data());DeleteShader(sh);throw std::runtime_error("GLSL: "+log);}
    return sh;
}
inline GLuint link(const std::string& vertex,const std::string& fragment) {
    GLuint v=compile(VERTEX_SHADER,vertex),f=0;
    try {f=compile(FRAGMENT_SHADER,fragment);}catch(...){DeleteShader(v);throw;}
    GLuint p=CreateProgram();AttachShader(p,v);AttachShader(p,f);LinkProgram(p);
    DeleteShader(v);DeleteShader(f);
    GLint ok=0;GetProgramiv(p,LINK_STATUS,&ok);
    if(!ok){GLint len=0;GetProgramiv(p,INFO_LOG_LENGTH,&len);std::string log(std::size_t(std::max(1,len)),' ');GetProgramInfoLog(p,len,nullptr,log.data());DeleteProgram(p);throw std::runtime_error("GLSL link: "+log);}
    return p;
}
} // namespace br::gl

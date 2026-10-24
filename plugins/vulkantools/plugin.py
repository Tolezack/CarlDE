from carlde.plugin_helpers import context,tool,commands

PROGRAM=r'''#include <vulkan/vulkan.h>
#include <iostream>
#include <vector>
int main(){
 VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.pApplicationName="CarlDE Vulkan";
 app.apiVersion=VK_API_VERSION_1_0;
 VkInstanceCreateInfo create{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};create.pApplicationInfo=&app;
 VkInstance instance{};
 VkResult result=vkCreateInstance(&create,nullptr,&instance);
 if(result!=VK_SUCCESS){std::cerr<<"vkCreateInstance falhou: "<<result<<"\n";return 1;}
 uint32_t count=0;vkEnumeratePhysicalDevices(instance,&count,nullptr);
 std::vector<VkPhysicalDevice> devices(count);
 if(count)vkEnumeratePhysicalDevices(instance,&count,devices.data());
 std::cout<<"Dispositivos Vulkan: "<<count<<"\n";
 for(auto d:devices){VkPhysicalDeviceProperties p{};vkGetPhysicalDeviceProperties(d,&p);
 std::cout<<" - "<<p.deviceName<<"\n";}
 vkDestroyInstance(instance,nullptr);return 0;
}'''

def activate(api):
    def create(project,name):
        (project/'src').mkdir(exist_ok=True)
        (project/'src/main.cpp').write_text(PROGRAM,encoding='utf-8')
        (project/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject('+name+' LANGUAGES CXX)\nfind_package(Vulkan REQUIRED)\nadd_executable('+name+' src/main.cpp)\ntarget_link_libraries('+name+' PRIVATE Vulkan::Vulkan)\n',encoding='utf-8')
    def spirv():
        root,path=context(api,True)
        if not root or not tool(api,'glslangValidator'):return
        if not api.save_all():return
        commands(api,(('glslangValidator','-V',str(path),'-o',str(path)+'.spv'),root,'Compilar SPIR-V'))
    api.register_template('vulkan','C++ · Vulkan SDK','Enumeração real de GPUs com Vulkan e CMake','cpp',create)
    api.register_action('spirv','Vulkan · compilar shader SPIR-V',spirv)

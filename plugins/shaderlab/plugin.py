from carlde.plugin_helpers import context,tool,commands,ask_choice

def activate(api):
    def validate():
        root,path=context(api,True)
        if not root or not tool(api,'glslangValidator'):return
        stage={'.vert':'vert','.frag':'frag','.comp':'comp','.geom':'geom','.tesc':'tesc','.tese':'tese'}
        profile=stage.get(path.suffix.lower())
        if not profile:
            profile=ask_choice(api,'ShaderLab','Etapa GLSL',['vert','frag','comp','geom','tesc','tese'])
        if not profile:return
        if not api.save_all():return
        commands(api,(('glslangValidator','-S',profile,str(path)),root,'Validar GLSL com glslangValidator'))
    def preview():
        root,path=context(api,True)
        if not root or not tool(api,'glslViewer','glslViewer (prévia GLSL)'):return
        if path.suffix.lower() != '.frag':api.notify('Prévia aceita shader fragment .frag.',error=True);return
        commands(api,(('glslViewer',str(path)),root,'Prévia GLSL em glslViewer'))
    api.register_action('validate','ShaderLab · compilar/verificar GLSL',validate)
    api.register_action('preview','ShaderLab · prévia .frag (glslViewer)',preview)

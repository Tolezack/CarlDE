#version 330 core
in vec2 v_uv;
flat in float v_mat;
in float v_shade;
in float v_distance;
uniform vec3 u_sky;
uniform float u_fog_distance;
out vec4 frag_color;
vec3 palette(int mat) {
    if(mat==1) return vec3(.30,.65,.22); // Grass
    if(mat==2) return vec3(.47,.32,.20); // Dirt
    if(mat==3) return vec3(.49,.50,.53); // Stone
    if(mat==4) return vec3(.77,.70,.45); // Sand
    if(mat==5) return vec3(.90,.92,.94); // Snow
    if(mat==6) return vec3(.43,.27,.13); // Trunk
    if(mat==7) return vec3(.21,.48,.20); // Leaves
    return vec3(.7,.2,.8);
}
void main() {
    vec2 tile=fract(v_uv);
    float grain=fract(sin(dot(floor(v_uv*8.0+tile*16.0),vec2(127.1,311.7)))*43758.5453);
    float bright = .91 + .16 * grain;
    vec3 color = palette(int(v_mat+.5))*v_shade*bright;
    float haze = smoothstep(u_fog_distance*.54,u_fog_distance,v_distance);
    frag_color=vec4(mix(color,u_sky,haze),1.0);
}

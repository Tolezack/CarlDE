#version 330 core
layout(location=0) in vec3 in_position;
layout(location=1) in vec2 in_uv;
layout(location=2) in float in_material;
layout(location=3) in float in_shade;
uniform mat4 u_mvp;
uniform vec3 u_eye;
out vec2 v_uv;
flat out float v_mat;
out float v_shade;
out float v_distance;
void main() {
    gl_Position = u_mvp * vec4(in_position,1.0);
    v_uv = in_uv;
    v_mat = in_material;
    v_shade = in_shade;
    v_distance = distance(in_position,u_eye);
}

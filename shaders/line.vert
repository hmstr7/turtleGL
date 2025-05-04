#version 330

in vec2 in_pos;
in vec3 in_color;
in float in_visibility;

void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
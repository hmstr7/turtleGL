#version 330

in vec2 in_pos;
in vec3 in_color;
in float in_alpha;

out vec3 color;
out float alpha;

void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
    color = in_color;
    alpha = in_alpha;
}
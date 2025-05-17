#version 330

flat in vec3 color;
flat in float alpha;

out vec4 fragColor;

void main() {
    fragColor = vec4(color, alpha);

}
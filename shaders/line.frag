#version 330

flat in vec3 color;
flat in float alpha;
flat in float timing;
out vec4 fragColor;

uniform float time;

void main() {
    if (time <= timing) {
        discard;
    }
    fragColor = vec4(color, alpha);

}
# TurtleGL

TurtleGL is a Python-based graphics library made purely for fun (please do not use it for any serious purposes). It is a small stupid experiment I did because I thought normal turtle lacks parallelism (no, I did not implement parallelism and multithreading yet). If you wish to fill your GPU VRAM with garbage and waste your system's resources, TurtleGL is definitely for you. 

## Features

- **Overengineering** Using ModernGL OpenGL wrapper + pyglet to write the most delicious spaghetti code ever.
- **1 % of actual turtle functionality** As for now
- **Turtle on a GPU!** 

## Installation
(No PyPI package yet)

1. Clone the repository:
   ```bash
   git clone https://github.com/hmstr7/turtleGL.git
   cd turtleGL
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```   

3. (Optional) Install a compatible OpenGL driver if not already installed.

## Usage

### Basic Example

Here is a simple example to get started with TurtleGL:

```python
from turtlegl import Window, Turtle, run, start

# Create a window
window = Window()

# Create a turtle
turtle = Turtle(window)

# Define the main loop
@run(window)
def main():
    turtle.goto((100, -200))
    turtle.goto((200, 200))
    turtle.goto((67, 0))
    turtle.goto((-37, -50))

# Start the application
start(debug=True)
```
See wiki (WIP) for more details

## Development

### Contributing

TODO

### License

This project isn't licensed yet. 

## Acknowledgments

- [ModernGL](https://github.com/moderngl/moderngl) for providing a Pythonic interface to OpenGL.
- [Pyglet](https://github.com/pyglet/pyglet) for windowing and event handling.



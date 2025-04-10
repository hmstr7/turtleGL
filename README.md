# TurtleGL

TurtleGL is a Python-based graphics library that combines the simplicity of the classic Turtle module with the power of OpenGL for rendering. It allows users to create graphical applications with modern rendering techniques while maintaining an easy-to-use interface.

## Features

- **Modern OpenGL Rendering**: Leverages `moderngl` for efficient and high-quality rendering.
- **Turtle-like API**: Provides a familiar interface for users who have worked with the Turtle module.
- **Customizable Graphics**: Supports custom colors, line thickness, and more.
- **Event Handling**: Built on `pyglet`, enabling advanced event handling and window management.
- **Debugging Support**: Includes logging and debugging tools for easier development.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd turtleGL
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Ensure you have the following Python packages installed:
   - `moderngl`
   - `pyglet`
   - `numpy`

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

### Key Classes and Functions

- **`Window`**: Represents the main application window. Handles OpenGL context and event management.
- **`Turtle`**: Represents a drawable object. Provides methods like `goto` for moving and drawing.
- **`run`**: A decorator to set the main loop function.
- **`start`**: Starts the application and enters the main event loop.

## Development

### Project Structure

```
turtleGL/
├── shaders/             # Directory for custom shaders
├── turtlegl.py          # Main library file
├── utils.py             # Small global utilitary functions
├── example.py           # Example usage and testing file
└── README.md            # Project documentation
```

### Logging

Logging is handled using Python's `logging` module. To enable debug logs, set the `DEBUG` variable to `True` in `turtlegl.py` or call `start(debug=True)`.

### Contributing

TODO

## License

This project isn't licensed yet. 

## Acknowledgments

- [ModernGL](https://github.com/moderngl/moderngl) for providing a Pythonic interface to OpenGL.
- [Pyglet](https://github.com/pyglet/pyglet) for windowing and event handling.


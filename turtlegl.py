import moderngl
import pyglet

from utils import load_shader
import numpy as np

import logging
""" import timeit """

DEBUG = False
logger = logging.getLogger(__name__)

if DEBUG:
    logger.setLevel(logging.DEBUG)

class Window(pyglet.window.Window):
    def __init__(self, width=500,height=500, title="TurtleGL", resizable=True, vsync=False,**kwargs):
        # OpenGL and pyglet setup
        logging.debug(f"Initializing window {self}")
        super().__init__(width=width,height=height,caption=title,resizable=resizable, **kwargs)
        self.ctx = moderngl.create_context()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.turtles = []

        self.clock = pyglet.clock.Clock()
        self.set_vsync(vsync)  # Set vsync to True or False based on the parameter


        self.mainloop = None
        self.needs_redraw = True  # Flag to indicate if a redraw is needed
   
    def on_draw(self):
        self.clear()
        self.ctx.clear(0.1, 0.1, 0.1, 1.0)
        self.clock.tick()
        if self.needs_redraw:  # Only call mainloop if redraw is needed
            try:
                logger.debug("Calling mainloop")
                if not self.mainloop:
                    raise NotImplementedError("No mainloop set. Did you forget to call run() on your main function?")
                self.mainloop()
                self.needs_redraw = False  # Reset the flag after drawing
            except Exception as e:
                logger.error(f"Error while rendering frame: {e}")
        else:
            try:
                for turtle in self.turtles:
                    turtle._Turtle__draw()
            except Exception as e:
                logger.error(f"Turtle draw call error: {e}")

    def request_redraw(self):
        """Call this method to request a rerun of the mainloop."""
        logger.debug("Redraw requested")
        self.needs_redraw = True
    
    # Some correct changes handling (nothing important)
    def on_resize(self, width, height):
        self.ctx.viewport = (0, 0, width, height)
    def on_close(self):
        for turtle in self.turtles:
            turtle._Turtle__vbo.release()
            turtle._Turtle__vao.release()
            turtle._Turtle__prog.release()
        return super().on_close()

class Turtle:
    def __init__(self, window: Window):
        logger.debug(f"Initializing turtle {self}")
        # Window binding
        self.window = window
        self.ctx = window.ctx
        self.window.turtles.append(self)

        # High level props
        self.position = (0.0, 0.0)
        """
        The position is a tuple of (x,y) coordinates in the range [-screen_width/2, screen_width/2] and [-screen_height/2, screen_height/2] respectively.
        However, OpenGL uses a different coordinate system (in the range -1, 1), so we need to convert the coordinates to OpenGL coordinates.
        Use the __pointTurtleToGL method to convert the coordinates from turtle-like to the ones used by OpenGL.
        Vice versa for __pointGLToTurtle.
        """
        self.color = (1.0, 0.0, 0.0)
        self.thickness = 1.0

        # OpenGL setup
        self.__setupOpenGL() 
        
    def __setupOpenGL(self):
        """
        Simply a macros-like function to setup OpenGL 
        with the sole reason of being separated from the constructor 
        being readability.
        What it does:
        - Setup default OpenGL render mode to LINE_STRIP (connected lines);
        - TODO
        """
        logger.debug("Setting up OpenGL")
        self.__render_mode = self.ctx.LINE_STRIP
        self.__vertices = np.array(
            [*self.__pointTurtleToGL(self.position)],
            dtype='f4'
        )
        self.__prog = self.ctx.program(
            vertex_shader=load_shader("shaders/line.vert"),
            fragment_shader=load_shader("shaders/line.frag"),
        )# Shader prog 
        self.__vbo = self.ctx.buffer(self.__vertices.tobytes()) #  Vertex buffer (in VRAM)
        self.__vao = self.ctx.vertex_array(
            self.__prog, 
            self.__vbo, 
            # Varyings
            "in_pos"
        )
        
        # Bind uniforms       
        self.__prog['color']=self.color
        
        logger.debug("OpenGL setup complete") # Add stuff here to debug

    def __updateOpenGL(self):
        logger.debug(f"""Updating OpenGL
- vertices: \n {self.__vertices.reshape(-1,2)}\n""")
        
        # Buffer update
        self.__vbo.clear()
        self.__vbo.orphan(size=self.__vertices.nbytes)
        self.__vbo.write(self.__vertices.tobytes())

        # Update uniforms
        self.ctx.line_width = self.thickness
        self.__prog['color'] = self.color

    def __pointGLToTurtle(self, a: tuple):
        """
        Converts a point from OpenGL coordinates to turtle-like coordinates.
        Args:
            a (tuple): A tuple (x, y) representing the point in OpenGL coordinates (range of both x and y is [-1.0, 1.0]).
        Returns:
            tuple: A tuple (x, y) representing the point in turtle-like coordinates.
        Raises:
            ValueError: If the input point is not a tuple of length 2.
        """
        if len(a) != 2:
            raise ValueError("Point must be a tuple of length 2")
        denormalized_x = a[0] * (self.window.width / 2)
        denormalized_y = a[1] * (self.window.height / 2)
        return (denormalized_x, denormalized_y)
    
    def __pointTurtleToGL(self, a: tuple):
        """
        Converts a point from turtle-like coordinates to OpenGL coordinates.
        Args:
            a (tuple): A tuple (x, y) representing the point in turtle-like coordinates.
        Returns:
            tuple: A tuple (x, y) representing the point in OpenGL coordinates.
        Raises:
            ValueError: If the input point is not a tuple of length 2.
        """
        if len(a) != 2:
            raise ValueError("Point must be a tuple of length 2")
        normalized_x = a[0] / (self.window.width / 2)
        normalized_y = a[1] / (self.window.height / 2)
        return (normalized_x, normalized_y)
    

    def __draw(self):
        """
        Renders all vertices using current OpenGL render mode. This function should be called after any impactful method call.
        """
        #print("draw call")
        self.__vao.render(mode=self.__render_mode, vertices=len(self.__vertices)//2) # Draw the line using the current render mode
        
    def goto(self, point, color=(1.0, 0.0, 0.0)):
        """
        Moves the turtle to a specified position and draws a line to it.
        Args:
            point (tuple): A tuple (x, y) representing the new position in 
                           turtle-like coordinates. The x and y values should 
                           be within the range [-screen_width/2, screen_width/2] 
                           and [-screen_height/2, screen_height/2], respectively.
            color (tuple, optional): A tuple (r, g, b) representing the color 
                                     of the line. Each value should be in the 
                                     range [0.0, 1.0]. Defaults to (1.0, 0.0, 0.0) 
                                     (red).
        Returns:
            None
        """

        print("goto", point)
        
        # High level stuff
        self.color = color
        self.position = point

        # Convert the current position to OpenGL coordinates
        current_pos = self.__pointTurtleToGL(self.position)

        # Check if the current position is already the last vertex
        if len(self.__vertices) < 2 or not np.array_equal(self.__vertices[-2:], current_pos):
            #self.__vertices = np.append(self.__vertices, current_pos)
            self.__vertices = np.concatenate((self.__vertices, np.array([*current_pos], dtype='f4')))



        self.__updateOpenGL() # Update buffer to include new point

        self.__draw() # Render 
            
def run(window: Window):
    def decorator(function):
        window.mainloop = function
        logging.debug(f"Mainloop set to {function.__name__} at {hex(id(function))}")
        return function
    return decorator

def start(debug=False):
    """Run the TurtleGL application."""
    global DEBUG
    DEBUG = debug
    pyglet.app.run()

if __name__ == "__main__":
    window = Window()
    turtle = Turtle(window)

    @run(window)
    def main():
        turtle.goto((100, -200))
        turtle.goto((200, 200))
        turtle.goto((67, 0))
        turtle.goto((-37, -50))


    start(True)

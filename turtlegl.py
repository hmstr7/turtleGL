import moderngl
import pyglet

from utils import load_shader
import numpy as np

import logging
import sys
from typing import Callable
""" import timeit """

DEBUG = False

logger = logging.getLogger("turtlegl")

class Window(pyglet.window.Window):
    def __init__(self, width=500,height=500, title="TurtleGL", resizable=True, vsync=False,**kwargs):
        # OpenGL and pyglet setup
        self.__debug(f"Initializing window {self}")
        super().__init__(width=width,height=height,caption=title,resizable=resizable, **kwargs)
        self.ctx = moderngl.create_context()
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.turtles = []

        self.clock = pyglet.clock.Clock()
        self.set_vsync(vsync)  # Set vsync to True or False based on the parameter


        self.mainloop = None
        self.needs_redraw = True  # Flag to indicate if a redraw is needed
    def __debug(self, msg:str):
        """Debugging wrapper for DEBUG level logs"""
        logger.debug(msg)
    def on_draw(self):
        self.clear()
        self.ctx.clear(0.1, 0.1, 0.1, 1.0)
        self.clock.tick()
        if self.needs_redraw:  # Only call mainloop if redraw is needed
            try:
                self.__debug("Calling mainloop")
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
                logging.error(f"Turtle draw call error: {e}")

    def request_redraw(self):
        """Call this method to request a rerun of the mainloop."""
        self.__debug("Redraw requested")
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
    def __init__(self, window: Window, color=(1.0, 0.0,0.0), init_pos=(0.0, 0.0)):
        self.__debug(f"Initializing turtle {self}")
        # Window binding
        self.window = window
        self.ctx = window.ctx
        self.window.turtles.append(self)

        # High level props
        self.position = init_pos
        """
        The position is a tuple of (x,y) coordinates in the range [-screen_width/2, screen_width/2] and [-screen_height/2, screen_height/2] respectively.
        However, OpenGL uses a different coordinate system (in the range -1, 1), so we need to convert the coordinates to OpenGL coordinates.
        Use the __pointTurtleToGL method to convert the coordinates from turtle-like to the ones used by OpenGL.
        Vice versa for __pointGLToTurtle.
        """
        self.color = color
        self.thickness = 1.0
        
        self.__sleeptime = 0.0 # Time to sleep in seconds (used for scheduling)


        # OpenGL setup
        self.__setupOpenGL() 
    
    def __debug(self, msg:str):
        """Debugging wrapper for DEBUG level logs"""
        logger.debug(msg)#, extra={"turtlename", self.__qualname__})

    # OpenGL magic
    def __setupOpenGL(self):
        """
        Simply a macros-like function to setup OpenGL 
        with the sole reason of being separated from the constructor 
        being readability.
        What it does:
        - Setup default OpenGL render mode to LINE_STRIP (connected lines);
        - TODO
        """
        self.__debug("Setting up OpenGL")
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
        
        self.__debug("OpenGL setup complete") # Add stuff here to debug

    def __updateOpenGL(self):
        self.__debug(f"""Updating OpenGL
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
        self.__vao.render(mode=self.__render_mode, vertices=len(self.__vertices)//2) # Draw the line using the current render mode

    # Scheduling
    def __schedule(self, func: Callable):
        delay = self.__sleeptime
        self.window.clock.schedule_once(func, delay=delay)
        self.__debug(f"Function {func.__name__} will be called in {delay}")
        self.__sleeptime = 0.0 # Reset the sleep time after scheduling
    @staticmethod
    def __active(func):
        """
        A decorator for methods that have an effect on this object and must be scheduled.
        """
        def wrapper(self, *args, **kwargs):
            # Schedule the function to run after a short delay
            self.__debug(f"Scheduling {func.__name__} with args: {args}, kwargs: {kwargs}")
            def scheduled_call(dt):
                func(self, *args, **kwargs)

            self.__schedule(scheduled_call)
            return None  # Return None since the function is scheduled
        return wrapper

    
    @__active
    def goto(self, point:tuple, color=None):
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
        self.__debug(f"Goto {point}")
        
        """ self.__demandExecution(self.goto, point=point, color=color) """ # Schedule the call to goto

        # High level stuff
        if color:
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

    @__active
    def setColor(self, color:tuple):
        """
        Sets the color of the turtle.
        Args:
            color (tuple): A tuple (r, g, b) representing the color in RGB format.
                           Each value should be in the range [0.0, 1.0].
        Returns:
            None
        """
        self.__debug(f"Setting color to {color}")
        self.color = color
        
        self.__updateOpenGL()
        self.__draw()

    def sleep(self, seconds: int | float):
        """
        Pauses the execution for a specified number of seconds without blocking the event loop.
        Args:
            seconds (float): The number of seconds to sleep.
        Returns:
            None
        """
        self.__debug(f"Sleeping for {seconds} seconds")

        self.__sleeptime = seconds # Set the sleep time

def run(window: Window):
    def decorator(function):
        window.mainloop = function
        logger.debug(f"Mainloop set to {function.__name__} at {hex(id(function))}")
        return function
    return decorator

def start(debug=False):
    """Run the TurtleGL application."""
    global DEBUG, logger
    DEBUG = debug

    logger.propagate = False  # Prevent logs from being passed to the root logger

    # Remove any existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    if DEBUG:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
    else:
        logger.setLevel(logging.WARNING)


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

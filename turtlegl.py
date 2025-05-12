import moderngl
import pyglet

from utils import load_shader
import numpy as np

import logging
import sys
from typing import Callable
from timeit import timeit

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
                for turtle in self.turtles:
                    turtle._Turtle__appendix()
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
    def __init__(self, window: Window, color=(1.0, 0.0,0.0), init_pos:tuple[int,int]=(0,0), max_vertices=10_000):
        self.__debug(f"Initializing turtle {self}")
        # Window binding
        self.window = window
        self.ctx = window.ctx
        self.window.turtles.append(self)
        self.wwidth = window.width
        self.wheight = window.height

        # High level props
        self.position = init_pos
        """
        The position is a tuple of (x,y) coordinates in the range [-screen_width/2, screen_width/2] and [-screen_height/2, screen_height/2] respectively.
        However, OpenGL uses a different coordinate system (in the range -1, 1), so we need to convert the coordinates to OpenGL coordinates.
        Use the __pointTurtleToGL method to convert the coordinates from turtle-like to the ones used by OpenGL.
        Vice versa for __pointGLToTurtle.
        """
        self.color = color
        self.alpha = 1.0
        #self.thickness = 1.0

        # Other
        self.__sleeptime = 0.0 # Time to sleep in seconds (used for scheduling)

        # OpenGL setup
        self.__setupOpenGL(max_vertices=max_vertices)

        self.__debug(f"OpenGL setup complete for turtle {self}")
    
    # Utility methods
    def __debug(self, msg:str):
        """Debugging wrapper for DEBUG level logs"""
        logger.debug(msg)#, extra={"turtlename", self.__qualname__})


    # OpenGL magic
    def __setupOpenGL(self, max_vertices:int):
        """
        Simply a macros-like function to setup OpenGL 
        with the sole reason of being separated from the constructor 
        being readability.
        What it does:
        - Setup default OpenGL render mode to LINE_STRIP (connected lines);
        - TODO
        """
        self.__debug("Setting up OpenGL...")

        self.__render_mode = self.ctx.LINE_STRIP

        # Preallocate array of fixed size for vertices
        self.__max_vertices = max_vertices
        
        self.__raw_vertices = np.zeros((self.__max_vertices,6), dtype='f4') # Raw vertices (in turtle-like coordinates). Must be in the form (x,y,r,g,b,a), implying (N,6) shape
        self.__raw_vertices[0] = np.array([*self.position, *self.color, self.alpha]).reshape(-1,6) # Never pass this to the GPU, only the __vertices! (The only actual difference is the coordinates which are in turtle-like coordinates here)
        
        self.__raw_vertex_count = 1

        self.__vertices = np.zeros((self.__max_vertices, 2+3+1), dtype='f4') # Actual stuff to be passed to the GPU. Must be in the form (x,y,r,g,b,a), implying (N,6) shape
        self.__vertices[0] = np.array([*self.__pointTurtleToGL(self.position), *self.color, self.alpha]).reshape(-1,6)

        self.__vertex_count = 1

        self.__debug(f"__vertices shape check 1: raw:{self.__raw_vertices.shape}; vertices:{self.__vertices.shape}")

        self.__prog = self.ctx.program(
            vertex_shader=load_shader("shaders/line.vert"),
            fragment_shader=load_shader("shaders/line.frag"),
        ) # Shader prog 

        self.__vbo = self.ctx.buffer(self.__vertices[:self.__vertex_count].tobytes()) #  Vertex buffer (in VRAM)
        self.__vao = self.ctx.vertex_array(
            self.__prog, 
            self.__vbo, 
            # Varyings
            "in_pos","in_color", "in_alpha"
        ) 
        
        
        self.__debug("OpenGL setup complete")

    def __updateOpenGL(self):
        self.__debug(f"""Updating OpenGL
- vertices: \n {self.__vertices[:self.__vertex_count]}\n""")
        
        # Buffer update
        self.__vbo.orphan(size=self.__vertices[:self.__vertex_count].nbytes)
        self.__vbo.write(self.__vertices[:self.__vertex_count].tobytes())

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
        Warning: this is slow and should not be used with arrays
        Args:
            a (tuple): A tuple (x, y) representing the point in turtle-like coordinates.
        Returns:
            tuple: A tuple (x, y) representing the point in OpenGL coordinates.
        Raises:
            ValueError: If the input point is not a tuple of length 2.
        """
        if len(a) != 2:
            raise ValueError("Point must be a tuple of length 2")
        normalized_x = a[0] / (self.wwidth / 2)
        normalized_y = a[1] / (self.wheight / 2)
        return (normalized_x, normalized_y)
    
    def __draw(self):
        """
        Renders all vertices using current OpenGL render mode. This function should be called after any impactful method call.
        """
        self.__vao.render(mode=self.__render_mode, vertices=self.__vertex_count) # Draw the line using the current render mode


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
            
            if self.__sleeptime > 0.0:
                # If sleep time is set, schedule the function with the delay
                
                
                def scheduled_call():
                    func(self, *args, **kwargs)
                self.__debug(f"Scheduling {func.__name__} with delay {self.__sleeptime}")
                self.window.clock.schedule_once(scheduled_call, delay=self.__sleeptime)
                self.__schedule(scheduled_call)
                return None  # Return None since the function is scheduled
            else:
                return func(self, *args, **kwargs) # Possible speed boost
        return wrapper



    # High level methods
    @__active
    def old_goto(self, point:tuple, color=None):
        """
        **(Deprecated, do not use)**

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

        # High level stuff
        if color:
            self.color = color
        self.position = point

        # Convert the current position to OpenGL coordinates
        gl_pos = self.__pointTurtleToGL(self.position)

        if self.__vertex_count >= self.__max_vertices:
            logger.warning("Vertex buffer full — cannot add more points")
            return

        self.__raw_vertices[self.__vertex_count] = gl_pos
        self.__vertex_count += 1

        self.__updateOpenGL() # Update buffer to include new point

        self.__draw() # Render 
    
    @__active
    def bulk(self, points: np.ndarray):
        '''
        Draws a path of points.
        Requirements:
        - a NumPy array of shape (N, 6) (x,y,r,g,b,a)
        - each point has TURTLE coordinates! (ranged from -(WINDOW/2) to (WINDOW/2))
        Args:
            points (np.ndarray): A NumPy array of shape (N, 6) representing the points to draw.
        Returns:
            None
        '''
        self.__debug(f"Bulk {points}")
        
        points = points.reshape(-1, 6) # Reshape to (N, 6)

        if points.dtype != 'f4':
            points = points.astype('f4')
        # if points.shape[1] != 6:
        #     raise ValueError("Points must be of shape (N, 6) - x,y,r,g,b,a")

        # Convert the points to OpenGL coordinates
        points[:, :2] /= np.array([self.wwidth / 2, self.wheight / 2])
    
        count = len(points)

        # Safety check
        if self.__vertex_count + count > self.__max_vertices:
            self.__debug(f"Turtle vertex buffer overflow: trying to add {count} points while already having {self.__vertex_count} (limit {self.__max_vertices})")
            count = self.__max_vertices - self.__vertex_count # Calculate the number of points that can be added
            points = points[:count] # Crop points

        # Bulk insert
        self.__vertices[self.__vertex_count:self.__vertex_count + count] = points
        self.__vertex_count += count

        self.__updateOpenGL() # Update buffer to include new points
        self.__draw() # Render
    
    def goto(self, point:tuple[float,float], color:tuple[float,float,float]=None):
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
        if color:
            self.color = color
        if self.__raw_vertex_count + 1 >= self.__max_vertices:
            self.__debug(f"Turtle vertex buffer overflow: trying to add a point while already having {self.__raw_vertex_count} (limit {self.__max_vertices})")
        else:
            self.__raw_vertex_count += 1
            self.__raw_vertices[self.__raw_vertex_count - 1] = [*point, *self.color, self.alpha] # Insert the new point at the end of the path. WARNING: point coordinates are in turtle-like coordinates!! Call bulk() in the end!
            

    #@__active
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
        
        # self.__updateOpenGL()
        # self.__draw()
    
    def penup(self):
        """
        Lifts the pen up, so that moving the turtle does not draw a line.
        Returns:
            None
        """
        self.__debug("Pen up")
        self.alpha = 0.0 # Set alpha to 0.0 to make the line invisible
    
    def pendown(self):
        """
        Puts the pen down, so that moving the turtle draws a line.
        Returns:
            None
        """
        self.__debug("Pen down")
        self.alpha = 1.0


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


    # Extra methods
    def __appendix(self):
        """
        Must be called after the execution of the main loop.
        """
        # To improve later


        # Cumulative ending 
        if self.__raw_vertices.size > 1:
            self.bulk(self.__raw_vertices)


    # Debug 
    def get_vertex_count(self, real=False):
        """
        Returns the number of vertices in the vertex buffer.
        Returns:
            int: The number of vertices in the vertex buffer.
        """
        if not real:
            return self.__vertex_count
        else:
            return self.__raw_vertices.size / 2

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

    try:
        pyglet.app.run()
    except KeyboardInterrupt:
        close()

def close():
    """Close the application."""
    logger.debug("Closing application")
    pyglet.app.exit()

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

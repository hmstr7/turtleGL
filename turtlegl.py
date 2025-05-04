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
    def __init__(self, window: Window, color=(1.0, 0.0,0.0), init_pos=(0.0, 0.0), max_vertices=10_000):
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
        self.thickness = 1.0
        
        self.__cumulative_path:np.ndarray = np.array([*self.position], dtype='f4') # Cumulative path of the turtle (used for goto_path)

        self.__sleeptime = 0.0 # Time to sleep in seconds (used for scheduling)


        # OpenGL setup
        self.__setupOpenGL(max_vertices=max_vertices)
    
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
        self.__debug("Setting up OpenGL")

        self.__render_mode = self.ctx.LINE_STRIP

        # Preallocate array of fixed size for vertices
        self.__max_vertices = max_vertices
        self.__vertices = np.zeros((self.__max_vertices, 2+3+1), dtype='f4') # 2D points with 3D color and 1D visibility (x,y,r,g,b,v)
        self.__vertex_count = 0

        # Add initial position
        self.__vertices[0] = self.__pointTurtleToGL(self.position)
        self.__vertex_count = 1


        self.__prog = self.ctx.program(
            vertex_shader=load_shader("shaders/line.vert"),
            fragment_shader=load_shader("shaders/line.frag"),
        )# Shader prog 
        self.__vbo = self.ctx.buffer(self.__vertices[:self.__vertex_count].tobytes()) #  Vertex buffer (in VRAM)
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
- vertices: \n {self.__vertices[:self.__vertex_count]}\n""")
        
        # Buffer update
        self.__vbo.orphan(size=self.__vertices[:self.__vertex_count].nbytes)
        self.__vbo.write(self.__vertices[:self.__vertex_count].tobytes())

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

        self.__vertices[self.__vertex_count] = gl_pos
        self.__vertex_count += 1

        self.__updateOpenGL() # Update buffer to include new point

        self.__draw() # Render 
    
    @__active
    def goto_path(self, points:list[tuple[float,float]] | np.ndarray, cleanCoords:bool=False, color:tuple[float,float]=None):
        '''
        Draws a path of points.
        It is a more efficient way to draw large structures (say, a million points) than calling goto() a million times.
        Also speeds up drasrically if supplied directly with 'clean' coordinates that are:
        - a NumPy array of shape (N, 2) 
        - of datatype float32 (f4)
        - each point already in OpenGL coordinates (ranged from -1.0 to 1.0)
        Args:
            points (list or np.ndarray): A list of tuples or a NumPy array of shape (N, 2) representing the points to draw.
            cleanCoords (bool): When False (by default), it means that the coordinates must be sanitized and transformed properly before rendering. If True, coords are assumed clean (see requirements above) and can be used in a more direct, faster way. Put True only if you are sure about data provided being correct, else unexpected and unhandled behavior may occur.
        Returns:
            None
        '''
        self.__debug(f"Goto bulk {points}")
        
        if color:
            self.color = color
        
        self.position = points[-1]  # Update the position to the last point in the list
        
        if not cleanCoords:
            # Tedious cleaning and conversion to OpenGL coords
            if isinstance(points, np.ndarray):
                # Validate shape and dtype
                if len(points.shape) < 2 or points.shape[1] != 2:
                    raise ValueError("NumPy array must be of shape (N, 2)")
                if points.dtype != np.float32:
                    points = points.astype('f4')

                # Assume turtle-like coords, convert. TODO: replace later with a bulk GPU-based conversion
                """ gl_points = np.empty_like(points)
                for i, p in enumerate(points):
                    gl_points[i] = self.__pointTurtleToGL(tuple(p)) """
                
                # Faster conversion (allegedly)
                gl_points = np.divide(points, np.array([(self.wwidth/2, self.wheight/2)],dtype='f4'))
            else:
                # Assume list of tuples
                gl_points = np.array([self.__pointTurtleToGL(p) for p in points], dtype='f4')
        else:
            # Coords are already clean and nice
            gl_points = points if isinstance(points, np.ndarray) else np.array(points, dtype='f4')

        count = len(gl_points)

        # Safety check
        if self.__vertex_count + count > self.__max_vertices:
            logger.warning(f"Turtle vertex buffer overflow: trying to add {count} points at {self.__vertex_count}")
            count = self.__max_vertices - self.__vertex_count
            gl_points = gl_points[:count]

        # Bulk insert
        self.__vertices[self.__vertex_count:self.__vertex_count + count] = gl_points
        self.__vertex_count += count
        self.__vertices

        self.__updateOpenGL() # Update buffer to include new points
        self.__draw() # Render
    
    def goto(self, point:tuple[float,float]):
        """
        Cumulative goto is a convenience wrapper method to build a path out of points one by one (see goto_path function)
        
        As for now, the color change is not supported. The color used will be the last one set by setColor.
        Furthermore, sleeping/scheduling is not supported either (yet)
        """
        self.__cumulative_path = np.append(self.__cumulative_path, point).reshape(-1, 2) # Insert the new point at the end of the path
    
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


    # Extra methods
    def __appendix(self):
        """
        Must be called after the execution of the main loop.
        """
        # To improve later


        # Cumulative ending 
        if self.__cumulative_path.size > 1:
            self.goto_path(self.__cumulative_path, cleanCoords=False)


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
            return self.__vertices.size / 2

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

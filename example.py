from turtlegl import Window, Turtle, run, start, close
from random import random as rfloat
from random import randint as rint
import time
import numpy as np
mywindow = Window(title="TurtleGL Window", width=800, height=600)

""" turtle2 = Turtle(mywindow, color=(0.0, 1.0, 0.0))
turtle3 = Turtle(mywindow, color=(0.0, 0.0, 1.0)) """


@run(mywindow)
def main():
    """ st = time.time()
    turtles = []
    numturtles = 200
    numsteps = 200
    for i in range(numturtles):
        turtles.append(Turtle(mywindow, color=(rfloat(), rfloat(), rfloat()), init_pos=(rint(-100, 100), rint(-100, 100))))
    mt = time.time()
    print("init time", mt-st)
    for k in range(numsteps):
        for turtle in turtles:
            turtle.goto((rint(-400, 400), rint(-300, 300)))
    et = time.time()
    print("draw time", et-mt)
    print("total time", et-st) """
    st = time.time()
    turtles = []
    paths = []
    numturtles = 10
    pathLen=1_000_000
    for i in range(numturtles):
        turtles.append(Turtle(mywindow, color=(rfloat(), rfloat(), rfloat()), init_pos=(rint(-100, 100), rint(-100, 100)), max_vertices=10_000_000))
        paths.append((2 * np.random.rand(pathLen, 2) - 1) * np.array([800, 600])) 
    mt = time.time()
    print("init time", mt-st)
    for i, turtle in enumerate(turtles):
        turtle.goto_path(paths[i])
    et = time.time()
    print("draw time", et-mt)
    print("total time", et-st)

    
    
start(debug=False)




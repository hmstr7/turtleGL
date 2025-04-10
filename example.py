from turtlegl import Window, Turtle, run,start
import time 

mywindow = Window(title="TurtleGL Window")
turtle = Turtle(mywindow)

@run(mywindow)
def main():
    turtle.goto((100,-60))
    time.sleep(10)
    turtle.goto((-100,-60))


start(mywindow)

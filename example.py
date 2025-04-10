from turtlegl import Window, Turtle, run,start 

mywindow = Window(title="TurtleGL Window")
turtle = Turtle(mywindow)
turtle2 = Turtle(mywindow, color=(0.0, 1.0, 0.0))
turtle3 = Turtle(mywindow, color=(0.0, 0.0, 1.0))

@run(mywindow)
def main():
    turtle.goto((100,-60))
    turtle2.goto((-50,0))
    turtle3.goto((300,300))
    
    turtle.sleep(3)
    turtle2.sleep(1)
    turtle3.sleep(5.5)
    
    turtle.goto((-100,-60))
    turtle2.goto((-50,100))
    turtle3.setColor((1.0, 0.0, 0.0))


start(debug=False)

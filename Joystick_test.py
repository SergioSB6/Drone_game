from Joystick import *
from Dron import Dron
dron1 = Dron ()
dron1.connect ('tcp:127.0.0.1:5763', 115200)
j1 = Joystick (0, dron1)
# dron2 = Dron ()
# dron2.connect ('tcp:127.0.0.1:5773', 115200)
# j2 = Joystick (1, dron2)
# print ("Joystick 1 y 2 funcionando")
while True:
    pass
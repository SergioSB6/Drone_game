import threading

import pygame
import time
from pymavlink import mavutil
from Dron import Dron

class Joystick:
    def __init__(self, num, dron):
        print ("NUM. ", num)
        self.num = num

        self.dron = dron

        print ("empezamos")

        threading.Thread(target=self.control_loop).start()

    def control_loop (self):
        pygame.init()
        pygame.joystick.init()
        # Obtener el primer joystick
        self.joystick = pygame.joystick.Joystick(self.num)
        self.joystick.init()
        print(self.joystick.get_name())
        if self.joystick.get_name() == 'USB Gamepad':
            self.pitch = 2
        elif self.joystick.get_name() == 'Generic USB Joystick':
            self.pitch = 4

        while True:
            pygame.event.pump()
            # Leer estado de botones

            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
            print("Botones:", buttons)
            # Leer valores de los ejes
            axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
            print("Ejes:", ["{:.2f}".format(a) for a in axes])

            print ("miro")
            if self.dron.state == "connected":
                # con dron armado, neutro para Loiter
                throttle = 1000
            else:
                # sin armar, mínimo para permitir el arm
                throttle = 1500
            roll = self.map_axis(self.joystick.get_axis(3))  # RC1: Roll
            pitch = self.map_axis(self.joystick.get_axis(self.pitch))  # RC2: Pitch
            yaw = self.map_axis(self.joystick.get_axis(0))  # RC4: Yaw
            self.dron.send_rc( roll, pitch, throttle, yaw)
            print(self.dron.state)
            print(throttle)
            if self.joystick.get_button(8) == 1:
                self.dron.arm()
                print("Armado")
            if self.joystick.get_button(9) == 1:
                self.dron.takeOff(5, blocking = False)
                print("En el aire")
            if self.joystick.get_button(0) == 1:
                self.dron.RTL(blocking = False)
                print("Retornado")
            if self.joystick.get_button(1) == 1:
                self.dron.set_mode('GUIDED')
                print("Modo Guided")
            if self.joystick.get_button(2) == 1:
                self.dron.Land(blocking = False)
                print("Aterrizado")
            if self.joystick.get_button(3) == 1:
                self.dron.set_mode('LOITER')
                print("Modo Loiter")

            time.sleep(0.1)

    def map_axis(self, value):
        """Convierte valor del eje (-1 a 1) a rango RC (1000 a 2000)"""
        return int(1500 + value *value*value*value*value*value*value*value*value*value*value*value*value* 500)
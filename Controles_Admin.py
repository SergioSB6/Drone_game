import time
import customtkinter as ctk
from Dron import Dron
from tkinter import messagebox
from modules import dron_nav

class ControlesAdmin:
    def __init__(self, dron, drone_label="Dron 1", button_color="dark orange"):
        self.dron = dron
        self.drone_label = drone_label
        self.button_color = button_color
        self.armBtn = None
        self.takeOffBtn = None
        self.RTLBtn = None
        self.speedSldr = None

    def arm(self):
        """
        Arma el dron de forma no bloqueante y actualiza el botón.
        """
        try:
            if self.armBtn:
                self.armBtn.configure(fg_color='yellow', text='Armando...')
            self.dron.arm(blocking=False, callback=self.informar, params='ARMED')
        except Exception as e:
            print("Error al armar el dron:", e)
            if self.armBtn:
                self.armBtn.configure(fg_color=self.button_color, text='Armar')

    def takeoff(self):
        """
        Despega el dron a una altura predefinida (5 metros) en modo no bloqueante.
        """
        try:
            alt = 5
            if self.takeOffBtn:
                self.takeOffBtn.configure(fg_color='yellow', text='Despegando...')
            self.dron.takeOff(alt, blocking=False, callback=self.informar, params='VOLANDO')
        except Exception as e:
            print("Error al despegar:", e)
            messagebox.showerror("Error", "Introduce una altura válida para el despegue.")

    def informar(self, mensaje):
        """
        Callback para actualizar la interfaz cuando una acción asíncrona (arm, takeOff, RTL) finaliza.
        """
        messagebox.showinfo("Información", "Mensaje del dron: " + mensaje)

        if mensaje == 'ARMED':
            if self.armBtn:
                self.armBtn.configure(fg_color='green', text='Armado')

        elif mensaje == 'VOLANDO':
            if self.takeOffBtn:
                self.takeOffBtn.configure(fg_color='green', text='En el aire')

        elif mensaje == "EN CASA":
            if self.RTLBtn:
                self.RTLBtn.configure(fg_color='green', text='En casa')
            if self.armBtn:
                self.armBtn.configure(fg_color=self.button_color, text='Armar')
            if self.takeOffBtn:
                self.takeOffBtn.configure(fg_color=self.button_color, text='Despegar')
            if self.RTLBtn:
                self.RTLBtn.configure(fg_color=self.button_color, text='RTL')
            self.dron.disconnect()

    def RTL(self):
        """
        Ejecuta el retorno a casa (RTL) de forma no bloqueante.
        """
        self.dron.setNavSpeed(1)
        if self.dron.going:
            self.dron.stopGo()
        self.dron.RTL(blocking=False, callback=self.informar, params='EN CASA')
        if self.RTLBtn:
            self.RTLBtn.configure(fg_color='yellow', text='Retornando...')

    def change_speed(self, speed):
        """
        Cambia la velocidad de navegación según el valor del slider.
        """
        try:
            self.dron.changeNavSpeed(float(speed))
        except Exception as e:
            print("Error al cambiar la velocidad:", e)

    def go(self, direction):
        """
        Envía el comando de navegación en la dirección especificada.
        """
        if not self.dron.going:
            self.dron.startGo()
        self.dron.go(direction)

    def crear_ventana(self):
        """
        Crea y configura la ventana de control con todos los botones y el slider.
        """
        ventana = ctk.CTkToplevel()
        ventana.title(f"Controles - {self.drone_label}")
        ventana.rowconfigure(0, weight=1)
        ventana.columnconfigure(0, weight=1)
        ventana.columnconfigure(1, weight=1)

        # Frame principal de controles
        controlFrame = ctk.CTkFrame(ventana)
        controlFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        for i in range(6):
            controlFrame.rowconfigure(i, weight=1)
        controlFrame.columnconfigure(0, weight=1)

        # Botón Armar
        self.armBtn = ctk.CTkButton(controlFrame, text="Armar", fg_color=self.button_color, command=self.arm)
        self.armBtn.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Botón Despegar
        self.takeOffBtn = ctk.CTkButton(controlFrame, text="Despegar", fg_color=self.button_color, command=self.takeoff)
        self.takeOffBtn.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # Botón RTL
        self.RTLBtn = ctk.CTkButton(controlFrame, text="RTL", fg_color=self.button_color, command=self.RTL)
        self.RTLBtn.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

        # Slider de velocidad
        self.speedSldr = ctk.CTkSlider(controlFrame, from_=0, to=20, number_of_steps=20, command=self.change_speed)
        self.speedSldr.set(1)  # Velocidad por defecto de 1 m/s
        self.speedSldr.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

        # Frame para botones de navegación
        navFrame = ctk.CTkFrame(controlFrame)
        navFrame.grid(row=5, column=0, padx=50, pady=5, sticky="nsew")
        for i in range(3):
            navFrame.rowconfigure(i, weight=1)
            navFrame.columnconfigure(i, weight=1)

        # Especificaciones: (texto del botón, dirección, fila, columna)
        btn_specs = [
            ("NW", "NorthWest", 0, 0),
            ("No", "North", 0, 1),
            ("NE", "NorthEast", 0, 2),
            ("We", "West", 1, 0),
            ("St", "Stop", 1, 1),
            ("Ea", "East", 1, 2),
            ("SW", "SouthWest", 2, 0),
            ("So", "South", 2, 1),
            ("SE", "SouthEast", 2, 2),
        ]

        for text, direction, row, col in btn_specs:
            btn = ctk.CTkButton(
                navFrame,
                text=text,
                fg_color=self.button_color,
                command=lambda d=direction: self.go(d)
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        return ventana

    def abrir_ventana(self):
        """
        Abre la ventana de controles.
        """
        return self.crear_ventana()

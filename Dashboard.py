from tkinter import Menubutton
import customtkinter as ctk
from Dron import Dron
from Editor_Mapa import MapFrameClass
from Checkpoint_screen import CheckpointScreen
import platform
import sys
import shutil
from Controles_Admin import ControlesAdmin
import subprocess
import time
import stat
import os
import ctypes
from AnimatedGif import *
from screeninfo import get_monitors
import pyglet
import pywinstyles
from pymavlink import mavutil

pyglet.options.win32_gdi_font = True
pyglet.font.add_file('assets/m04fatal_fury/m04.ttf')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("Directorio base:", base_dir)

    # Rutas a los ejecutables
    sitl_exe = os.path.join(base_dir, "Mission Planner", "sitl", "ArduCopter.exe")
    defaults  = os.path.join(base_dir, "Mission Planner", "sitl", "default_params", "copter.parm")
    mp_exe    = os.path.join(base_dir, "Mission Planner", "Mission Planner", "MissionPlanner.exe")

    # Verificaciones
    for path,name in [(sitl_exe,"SITL"), (defaults,"copter.parm"), (mp_exe,"Mission Planner")]:
        if not os.path.isfile(path):
            print(f"ERROR: No encontrado {name} en:\n  {path}")
            return

    flags = subprocess.CREATE_NEW_CONSOLE

    # SITL 1 → puerto TCP 5762
    cmd_sitl1 = [
        sitl_exe,
        "--model", "+",
        "--speedup", "3",
        "--instance", "0",
        "--defaults", defaults,
        "--home", "41.276358174374515, 1.988269781384222,3,0",
        "-P", "SYSID_THISMAV=1",

    ]
    print("Lanzando SITL #1:", " ".join(cmd_sitl1))
    subprocess.Popen(cmd_sitl1, cwd=base_dir, creationflags=flags)
    time.sleep(2)

    # SITL 2 → puerto TCP 5772
    cmd_sitl2 = [
        sitl_exe,
        "--model", "+",
        "--speedup", "3",
        "--instance", "1",
        "--defaults", defaults,
        "--home", "41.27622147922305, 1.9883288804776904,3,0",
        "-P", "SYSID_THISMAV=2",

    ]
    print("Lanzando SITL #2:", " ".join(cmd_sitl2))
    subprocess.Popen(cmd_sitl2, cwd=base_dir, creationflags=flags)
    time.sleep(2)

    # Una sola Mission Planner → conectar al puerto 5762 (puedes cambiarlo a 5772 si quieres)
    cmd_mp = [
        mp_exe,
        "/connect", "tcp:127.0.0.1:5762"
    ]
    print("Lanzando Mission Planner:", " ".join(cmd_mp))
    subprocess.Popen(cmd_mp, cwd=os.path.dirname(mp_exe), creationflags=flags)

    print("¡Todo levantado correctamente!")

if __name__ == "__main__":
    main()

def install_dependencies():
    # Instala las bibliotecas necesarias si no están instaladas
    try:
        import customtkinter
        import numpy
        import PIL
    except ImportError:
        print("Instalando dependencias necesarias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "numpy", "pillow","  shapely"])

    # Instala la fuente personalizada
    install_custom_font()

def install_custom_font():
    # Ruta a la fuente en la carpeta assets

    font_path = os.path.join(os.getcwd(), 'assets', 'm04fatal_fury', 'm04.ttf')
    print(f"font_path: {font_path}")

    if platform.system() == 'Windows':
        # Copia la fuente a la carpeta de fuentes de Windows
        try:
            windows_fonts_dir = os.path.join(os.environ['WINDIR'], "Fonts")
            font_dest_path = os.path.join(windows_fonts_dir, 'm04.ttf')
            print(f"font_dest_path: {font_dest_path}")
            print(f"windows_font_dir: {windows_fonts_dir}")


            if not os.path.isfile(windows_fonts_dir):  # Evita copiar si ya está instalada

                print(os.access(font_path, os.F_OK))
                print(os.access(windows_fonts_dir, os.X_OK))
                try:
                    try:
                        os.chmod(windows_fonts_dir, stat.S_ISUID)
                        shutil.copy(font_path, windows_fonts_dir)
                    except Exception as e:
                        print(f"Error al copiar: {e}")
                    try:
                        ctypes.windll.gdi32.AddFontResourceEx(font_dest_path, 0, 0)
                    except Exception as e:
                        print(f"Error al añadir el recurso: {e}")
                    print("Fuente instalada correctamente en Windows.")
                except Exception as e:
                    print(f"Acceso denegado: {e}")
            else:
                print("La fuente ya está instalada.")
        except Exception as e:
            print(f"No se pudo instalar la fuente: {e}")

    else:
        # Para sistemas operativos diferentes a Windows, muestra un mensaje informativo
        print("Para otros sistemas, instala la fuente manualmente desde la carpeta assets/fonts.")
for m in get_monitors():
    print(str(m))

install_custom_font()

# ================= DASHBOARD INICIAL =================
dron = Dron()    # Dron 1
dron2 = Dron()   # Dron 2
ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("blue")  # Tema por defecto

# Función para cambiar de marco
def mostrar_frame(frame):
    frame.tkraise()  # Mueve el marco especificado al frente, ocultando los otros

# Función para activar/desactivar pantalla completa
def toggle_fullscreen(event=None):
    is_fullscreen = ventana.attributes("-fullscreen")
    ventana.attributes("-fullscreen", not is_fullscreen)

# Función para salir de pantalla completa
def end_fullscreen(event=None):
    ventana.attributes("-fullscreen", False)

# Crear la ventana principal
ventana = ctk.CTk()  # Crear la ventana
ventana.geometry("1280x720")  # Tamaño de la ventana
ventana.title("Ventana principal")


# Configurar para que la ventana comience en pantalla completa
ventana.attributes("-fullscreen", True)

# Vincular la tecla ESC para salir de pantalla completa
ventana.bind("<Escape>", end_fullscreen)

# =================== MARCOS (PANTALLAS) ===================

# Crear dos marcos (pantallas) que se alternarán
frame_titulo = ctk.CTkFrame(master=ventana)  # Primer marco (titulo)
frame_titulo.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_menu = ctk.CTkFrame(master=ventana)  # Segundo marco (Juego)
frame_menu.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_tag = ctk.CTkFrame(master=ventana)  # Segundo marco (Tag)
frame_tag.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_CheckPoint = ctk.CTkFrame(master=ventana)  # Segundo marco (CheckPoint)
frame_CheckPoint.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

frame_Editor_mapas = ctk.CTkFrame(master=ventana)  # Segundo marco (Editor de mapas)
frame_Editor_mapas.place(relx=0, rely=0, relwidth=1, relheight=1)  # Ocupa toda la ventana

img = Image.open('assets/Animacion_2.gif')
img = img.resize((1280,720))
photoImg = ImageTk.PhotoImage(img)
gif_label = AnimatedGif(frame_titulo,'assets/Animacion_2.gif', 0.04)
gif_label.place(relx=0, rely=0, relwidth=1, relheight=1)

# ================== FUNCIONES DE NAVEGACIÓN ==================

# Función para volver al menú principal
def volver_menu():
    mostrar_frame(frame_menu)

# Función para volver al título principal
def volver_titulo():
    mostrar_frame(frame_titulo)

# ================== CONTENIDO DEL TITULO ==================
mostrar_frame(frame_titulo)
label = ctk.CTkLabel(master=frame_titulo, text="DroneLab", font=("M04_FATAL FURY", 80),bg_color="#000001")
label.place(anchor="n", rely=0.1, relx=0.5)
pywinstyles.set_opacity(label, value=1, color="#000001")

# Botón con efecto de rebote
increase = True
current_size = 50

def bounce_button():
    global increase, current_size

    if increase:
        current_size += 1
        if current_size >= 60:
            increase = False
    else:
        current_size -= 1
        if current_size <= 50:
            increase = True

    boton_play.configure(font=("M04_FATAL FURY", current_size))
    ventana.after(50, bounce_button)


# Agregar un botón a la ventana
def boton_click():
    mostrar_frame(frame_menu)

boton_play = ctk.CTkButton(master=frame_titulo, text="Play!", font=("M04_FATAL FURY", 50), fg_color="transparent", bg_color= "#000001",  hover=False, command=boton_click, width=300, height=50)
boton_play.pack(pady=100, padx=0, side="bottom")
pywinstyles.set_opacity(boton_play, value=1, color="#000001")

# Iniciar rebote
bounce_button()
gif_label.start()
# ================== CONTENIDO DEL MENÚ PRINCIPAL ==================

# Agregar una etiqueta y botón en el marco del juego
label_select = ctk.CTkLabel(master=frame_menu, text="Select game", font=("M04_FATAL FURY", 70))
label_select.pack(pady=20, side="top")


def abrir_configuracion_avanzada():
    print("Abrir configuración avanzada para Dron 1")
    controlador_dron1 = ControlesAdmin(dron, drone_label="Dron 1")
    ventana_dron1 = controlador_dron1.abrir_ventana()


# Función para abrir la botonera del dron 2
def abrir_configuracion_avanzada_dron2():
    print("Abrir configuración avanzada para Dron 2")
    controlador_dron2 = ControlesAdmin(dron2, drone_label="Dron 2")
    ventana_dron2 = controlador_dron2.abrir_ventana()



def mostrar_menu():
    menu_frame = ctk.CTkFrame(frame_menu, width=150, height=150, corner_radius=10)
    menu_frame.place(x=10, y=50)

    boton_configuracion = ctk.CTkButton(menu_frame, text="Config Dron 1", command=abrir_configuracion_avanzada,
                                        width=130, height=30)
    boton_configuracion.pack(pady=5)

    boton_configuracion2 = ctk.CTkButton(menu_frame, text="Config Dron 2", command=abrir_configuracion_avanzada_dron2,
                                         width=130, height=30)
    boton_configuracion2.pack(pady=5)

    boton_sonido = ctk.CTkButton(menu_frame, text="Sonido", command=ajustar_sonido, width=130, height=30)
    boton_sonido.pack(pady=5)

    # Para ocultar el menú al hacer clic en cualquier parte del frame
    def ocultar_menu(event):
        menu_frame.place_forget()

    frame_menu.bind("<Button-1>", ocultar_menu)


def ajustar_sonido():
    print("Ajustar sonido")

# Crear el botón con forma de engranaje
icono_engrane = ctk.CTkButton(frame_menu, text="⚙", width=30, height=30, command=mostrar_menu)
icono_engrane.place(x=10, y=10)  # Posicionar en la esquina superior izquierda

# Seleccionar juegos
def tag():
    mostrar_frame(frame_tag)

boton_tag = ctk.CTkButton(master=frame_menu, text="Tag", font=("M04_FATAL FURY", 35), fg_color="transparent", hover=False, command=tag)
boton_tag.place(relx=0.3, rely=0.4, anchor="center")
def showcheckpoint():
    global dron

    # Limpiar frame actual
    for widget in frame_CheckPoint.winfo_children():
        widget.destroy()

    # Crear CheckpointScreen en frame_CheckPoint
    checkpoint_screen = CheckpointScreen(dron, dron2, frame_CheckPoint)
    boton_volver4 = ctk.CTkButton(master=frame_CheckPoint, text="Return", font=("M04_FATAL FURY", 20),
                                  fg_color="transparent", hover=False, command=volver_menu)
    boton_volver4.place(relx=0.01, rely=0.95, anchor="sw")
    # Mostrar el frame del checkpoint
    mostrar_frame(frame_CheckPoint)
    mostrar_frame(frame_CheckPoint)

def CheckPoint():
    mostrar_frame(frame_CheckPoint)

boton_tag = ctk.CTkButton(master=frame_menu, text="CheckPoints race", font=("M04_FATAL FURY", 35), fg_color="transparent", hover=False, command=showcheckpoint)
boton_tag.place(relx=0.7, rely=0.4, anchor="center")
boton_tag._text_label.configure(wraplength=400)


# Editor de mapas
# Abrimos el mapa
def showmap():
    global dron

    # ================== CONTENIDO DEL EDITOR DE MAPAS ==================
    # Inicializamos la clase del mapa con el dron y el frame_Editor_mapas como fatherFrame
    map_frame_class = MapFrameClass(dron, frame_Editor_mapas)

    # Construimos el frame del mapa dentro del frame_Editor_mapas
    map_frame = map_frame_class.buildFrame()

    # Lo ajustamos para que ocupe todo el espacio
    map_frame.pack(fill="both", expand=True)

    boton_volver3 = ctk.CTkButton(master=frame_Editor_mapas, text="Return", font=("M04_FATAL FURY", 20),
                                  fg_color="transparent", hover=False, command=volver_menu)
    boton_volver3.place(relx=0.01, rely=0.95, anchor="sw")

    # Mostrar el frame del editor de mapas
    mostrar_frame(frame_Editor_mapas)

def Editor_mapas():
    mostrar_frame(frame_Editor_mapas)

boton_editorMap = ctk.CTkButton(master=frame_menu, text="Map Editor", font=("M04_FATAL FURY", 35), fg_color="transparent", hover=False, command=showmap)
boton_editorMap.place(relx=0.85, rely=0.95, anchor="s")
boton_editorMap._text_label.configure(wraplength=400)

# Botón para volver al título
boton_volver = ctk.CTkButton(master=frame_menu, text="Return", font=("M04_FATAL FURY", 20), fg_color="transparent", hover=False, command=volver_titulo)
boton_volver.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL TAG ==================
label_tag = ctk.CTkLabel(master=frame_tag, text="Welcome to Tag mode!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

boton_volver1 = ctk.CTkButton(master=frame_tag, text="Return", font=("M04_FATAL FURY", 20), fg_color="transparent", hover=False, command=volver_menu)
boton_volver1.place(relx=0.01, rely=0.95, anchor="sw")

# ================== CONTENIDO DEL CHECKPOINT ==================
label_tag = ctk.CTkLabel(master=frame_CheckPoint, text="Welcome to CheckPoint Race mode!", font=("M04_FATAL FURY", 35))
label_tag.pack(pady=20)

# Ejecutar la ventana principal
ventana.mainloop()
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import json
import math
from AnimatedGif import *
import pywinstyles
from PIL import Image, ImageTk
import time
import threading
import winsound
import pygame
from Joystick import Joystick
import subprocess
import win32con
import tkinter.simpledialog as sd
from screeninfo import get_monitors


class CheckpointScreen:
    def __init__(self, dron, dron2, parent_frame):
        self.dron = dron
        self.dron2 = dron2
        self.map_data = None
        self.connected_drones = []
        self.player_positions = {}
        self.frame = parent_frame
        self.is_on_obstacle = False
        self.is_on_obstacle2 = False
        self.drone1_image_full = None
        self.drone2_image_full = None
        # Vida de cada dron (0.0 .. 1.0)
        self.life1 = 1.0
        self.life2 = 1.0
        # “facil” resta un 5%, “medio” 10%, “dificil” 25% al chocar.
        self.difficulty = "medium"
        self.damage_map = {"easy": 0.05, "medium": 0.1, "hard": 0.25}
        self.hitbox_map = {"easy": 2, "medium": 1, "hard": 0.5}
        self.raw_checkpoints = []  # lista completa de {id, original:{col,row}, mirror:{col,row}}
        self.queue_j1 = []  # checkpoints pendientes para jugador 1 (original)
        self.queue_j2 = []  # idem para jugador 2 (mirror)
        self.current_cp_j1 = None  # {col,row, item_id}
        self.current_cp_j2 = None
        self.cp1_count = 0  # recogidos por J1
        self.cp2_count = 0
        self.cp1_label = None
        self.cp2_label = None
        self.num = []
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.sitl_procs = []  # aquí guardamos los Popen de los SITL
        self.mp_proc = None
        self.monitors = get_monitors()
        self.width = self.monitors[0].width
        self.height = self.monitors[0].height
        # ---------------- CONFIGURAR GRID PRINCIPAL ----------------
        self.frame.rowconfigure(0, weight=0)  # título
        self.frame.rowconfigure(1, weight=0)  # headers
        self.frame.rowconfigure(2, weight=1)  # listas / canvas
        self.frame.rowconfigure(3, weight=0)  # info_label / “Modo:” label
        self.frame.rowconfigure(4, weight=0)  # desplegable
        self.frame.rowconfigure(5, weight=0)  # botones
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        # ---------------- TÍTULO ----------------
        label_title = ctk.CTkLabel(self.frame, text="CHECKPOINT RACE MODE", font=("M04_FATAL FURY", 50))
        # Lo ponemos en la primera fila, ocupando 2 columnas
        label_title.grid(row=0, column=0, columnspan=2, pady=20, sticky="n")

        # ---------------- LISTA DE JUGADORES (Columna 0) ----------------
        label_players = ctk.CTkLabel(self.frame, text="CONNECTED PLAYERS", font=("M04_FATAL FURY", 20))
        label_players.grid(row=1, column=0, padx=10, pady=50, sticky="n")

        self.player_listbox = ctk.CTkTextbox(self.frame, width=250, height=300)
        self.player_listbox.grid(row=2, column=0, padx=10, pady=80, sticky="n")


        self.info_label = ctk.CTkLabel(
            self.frame,
            text="Press L1 in your Joystick to connect!",
            font=("M04_FATAL FURY", 12)
        )
        self.info_label.grid(row=3, column=0, padx=10, pady=5, sticky="n")

        # ---------------- PREVIEW MAPA (Columna 1) ----------------
        self.preview_label = ctk.CTkLabel(self.frame, text="MAP PREVIEW", font=("M04_FATAL FURY", 20))
        self.preview_label.grid(row=1, column=1, padx=10, pady=50, sticky="n")

        self.map_canvas = ctk.CTkCanvas(self.frame, width=500, height=500, bg="gray")
        self.map_canvas.grid(row=2, column=1, padx=10, pady=80, sticky="n")

        ctk.CTkLabel(self.frame, text="Modo:", font=("M04_FATAL FURY", 15)) \
            .grid(row=3, column=1, sticky="w", padx=(0, 5), pady=(5, 0))

        # -------------- DESPLEGABLE (row 4) --------------
        self.mode_var = ctk.StringVar(value="Simulation")
        self.mode_menu = ctk.CTkOptionMenu(
            self.frame,
            values=["Simulation", "Production"],
            variable=self.mode_var,
            command=self.on_mode_change,
            width=150
        )
        self.mode_menu.grid(row=4, column=1, sticky="w", padx=0, pady=0)

        self.control_var = ctk.StringVar(value="Joystick")
        self.control_menu = ctk.CTkOptionMenu(
            self.frame,
            values=["Joystick", "RC Transmitter"],
            variable=self.control_var,
            command=self.on_control_change,
            width=150
        )
        self.control_menu.grid(row=4, column=1, sticky="w", padx=200, pady=0)
        # ocultamos hasta que el modo sea Production
        self.control_menu.grid_remove()

        # ---------------- FILA DE BOTONES AL FINAL ----------------
        botones_frame = ctk.CTkFrame(self.frame)
        botones_frame.grid(row=5, column=0, columnspan=2, pady=(20, 10))

        # Selector de dificultad
        self.difficulty_var = ctk.StringVar(value=self.difficulty.capitalize())
        ctk.CTkLabel(botones_frame, text="Dificultad:", font=("M04_FATAL FURY", 18)).pack(side="left", padx=(10, 5))
        self.diff_menu = ctk.CTkOptionMenu(
            botones_frame,
            values=["Easy", "Medium", "Hard"],
            variable=self.difficulty_var,
            command=self.on_difficulty_change
        )
        self.diff_menu.pack(side="left", padx=(0, 20))

        # Botones de acción
        self.boton_select_map = ctk.CTkButton(botones_frame, text="Select map", command=self.select_map)
        self.boton_select_map.pack(side="left", padx=10)

        self.boton_connect = ctk.CTkButton(botones_frame, text="Connect player", command=self.connect_player)
        self.boton_connect.pack(side="left", padx=10)

        self.boton_jugar = ctk.CTkButton(botones_frame, text="Play", command=self.start_game)
        self.boton_jugar.pack(side="left", padx=10)

        self.boton_volver = ctk.CTkButton(self.frame, text="Return", font=("M04_FATAL FURY", 30),
                                          fg_color="transparent", hover=False, command=self.callback_volver)

        # ─── Variables para el temporizador ────────────────────────────────────
        # Para evitar varios finales de partida
        self.game_over = False

        # Dentro de botones_frame, justo tras self.diff_menu.pack(...)
        ctk.CTkLabel(botones_frame, text="Time:", font=("M04_FATAL FURY", 18)) \
            .pack(side="left", padx=(10, 5))
        self.time_entry = ctk.CTkEntry(botones_frame, width=50)
        self.time_entry.insert(0, "2")  # valor por defecto (minutos)
        self.time_entry.pack(side="left", padx=(0, 20))
        self.update_player_list()
    def launch_sitl_servers(self):
        # si ya hay 2 SITL vivos, no hacer nada
        alive = [p for p in self.sitl_procs if p.poll() is None]
        if len(alive) >= 2:
            return

        sitl_exe = os.path.join(self.base_dir, "Mission Planner1", "sitl", "ArduCopter.exe")
        defaults = os.path.join(self.base_dir, "Mission Planner1", "sitl", "default_params", "copter.parm")

        flags = subprocess.CREATE_NEW_CONSOLE
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # SW_SHOWMINNOACTIVE abre minimizado y sin robar foco
        si.wShowWindow = win32con.SW_SHOWMINNOACTIVE

        # arranco SITL #1
        cmd1 = [
            sitl_exe, "--model", "+", "--speedup", "3", "--instance", "0",
            "--defaults", defaults,
            "--home", "41.276358174374515,1.988269781384222,3,0",
            "-P", "SYSID_THISMAV=1",
        ]
        p1 = subprocess.Popen(cmd1, cwd=self.base_dir,
                              creationflags=flags, startupinfo=si)
        time.sleep(2)

        # arranco SITL #2
        cmd2 = [
            sitl_exe, "--model", "+", "--speedup", "3", "--instance", "1",
            "--defaults", defaults,
            "--home", "41.27622147922305,1.9883288804776904,3,0",
            "-P", "SYSID_THISMAV=2",
        ]
        p2 = subprocess.Popen(cmd2, cwd=self.base_dir,
                              creationflags=flags, startupinfo=si)
        time.sleep(2)

        # guardamos solo los vivos
        self.sitl_procs = [p for p in (p1, p2) if p.poll() is None]
        print(f"→ SITL arrancados ({len(self.sitl_procs)})")

    def launch_mission_planner(self):
        # si ya tenemos uno vivo, no hacemos nada
        if self.mp_proc and self.mp_proc.poll() is None:
            return

        mp_exe = os.path.join(self.base_dir, "Mission Planner1", "Mission Planner2", "MissionPlanner.exe")
        flags = subprocess.CREATE_NEW_CONSOLE

        self.mp_proc = subprocess.Popen(
            [mp_exe],
            cwd=os.path.dirname(mp_exe),
            creationflags=flags
        )
        print("→ Mission Planner arrancado")

    def shutdown_sitl_servers(self):
        # termina todos los procesos SITL vivos
        for p in self.sitl_procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill()
        self.sitl_procs = []
        print("→ SITL detenidos")

    def on_mode_change(self, nuevo_modo):
        if nuevo_modo == "Simulation":
            self.dron.disconnect()
            self.dron2.disconnect()
            self.update_player_list()
            self.info_label.grid()
            self.control_menu.grid_remove()
            pygame.init()
            pygame.joystick.init()
            # arrancamos el listener de mandos
            threading.Thread(target=self._listen_for_joy4, daemon=True).start()
            # 1) arrancar los SITL (si no están ya)…
            self.launch_sitl_servers()
            # 2) arrancar Mission Planner (si no está ya)
            self.launch_mission_planner()
        else:  # Production
            self.dron.disconnect()
            self.dron2.disconnect()
            self.update_player_list()
            self.control_menu.grid()
            # cerrar los SITL
            self.shutdown_sitl_servers()
            self.launch_mission_planner()

        print("Modo cambiado a", nuevo_modo)

    def on_control_change(self, source):
        if source == "Joystick":
            pygame.init()
            pygame.joystick.init()
            # arrancamos el listener de mandos
            threading.Thread(target=self._listen_for_joy4, daemon=True).start()
        else:

            self.info_label.grid_remove()


    # ─── Método para formatear segundos a M:SS ──────────────────────────────


    def _format_time(self, total_seconds):
        """
        Devuelve 'M:SS' donde M es minutos (sin cero inicial) y SS segundos con dos dígitos.
        """
        mins = total_seconds // 60
        secs = total_seconds % 60
        return f"{mins}:{secs:02d}"

        # ─── Método para mostrar la ventana de fin de partida ───────────────────


    def _show_game_over(self, winner_forced=None, death_message=None):
        """
        Se ejecuta una sola vez al acabar tiempo o al recoger todos los checkpoints.
        Muestra puntos, tiempo empleado y ganador.
        """
        if self.game_over:
            return
        self.game_over = True

        threading.Thread(target=self.dron.stopGo, daemon=True).start()
        threading.Thread(target=self.dron2.stopGo, daemon=True).start()
        pygame.mixer.music.stop()
        total = len(self.raw_checkpoints)
        elapsed = self.timer_duration - self.remaining_time
        time_str = self._format_time(elapsed)

        if winner_forced:
            winner = winner_forced
        else:
            if self.cp1_count == self.cp2_count:
                winner = "Draw"
            elif self.cp1_count == total:
                winner = "Player 1"
            elif self.cp2_count == total:
                winner = "Player 2"
            else:
                # fin por tiempo: el que más checkpoints tenga
                if self.cp1_count > self.cp2_count:
                    winner = "Player 1"
                elif self.cp2_count > self.cp1_count:
                    winner = "Player 2"

        # Crear ventana de resumen
        self.over = ctk.CTkToplevel(self.game_window)
        self.over.title("Game over")
        self.over.geometry("600x400")

        self.over.transient(self.game_window)
        self.over.grab_set()
        self.over.lift(aboveThis=self.game_window)
        self.over.focus_force()

        if death_message:
            ctk.CTkLabel(
                self.over,
                text=death_message,
                font=("M04_FATAL FURY", 24, "bold"),
                text_color="red"
            ).pack(pady=(10, 0))

        title_lbl = ctk.CTkLabel(self.over, text="GAME OVER",font=("M04_FATAL FURY", 40, "bold"), text_color="red")
        title_lbl.pack(pady=(20, 10))
        # Contenedor interior para centrar y ajustar márgenes
        frame = ctk.CTkFrame(self.over, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        for c in range(3):
            frame.grid_columnconfigure(c, weight=1)
        # --- Encabezados de tabla ---
        header_font = ("M04_FATAL FURY", 18, "bold")
        ctk.CTkLabel(frame, text="Player", font=header_font).grid(row=0, column=0, padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text="Points", font=header_font).grid(row=0, column=1, padx=10, pady=(0, 5))
        ctk.CTkLabel(frame, text="Time", font=header_font).grid(row=0, column=2, padx=10, pady=(0, 5))

        # --- Fila Jugador 1 ---
        body_font = ("M04_FATAL FURY", 16)
        ctk.CTkLabel(frame, text="Player 1", font=body_font).grid(row=1, column=0, padx=10, pady=2)
        ctk.CTkLabel(frame, text=f"{self.cp1_count} of {total}", font=body_font).grid(row=1, column=1, padx=10, pady=2)
        ctk.CTkLabel(frame, text=time_str, font=body_font).grid(row=1, column=2, padx=10, pady=2)

        # --- Fila Jugador 2 ---
        ctk.CTkLabel(frame, text="Player 2", font=body_font).grid(row=2, column=0, padx=10, pady=2)
        ctk.CTkLabel(frame, text=f"{self.cp2_count} of {total}", font=body_font).grid(row=2, column=1, padx=10, pady=2)
        ctk.CTkLabel(frame, text=time_str, font=body_font).grid(row=2, column=2, padx=10, pady=2)

        # --- Mensaje de ganador ---
        winner_font = ("M04_FATAL FURY", 20)

        if winner in ("Player 1", "Player 2"):
            ctk.CTkLabel(
                self.over,
                text=f"The winner is: {winner}",
                font=winner_font,
                text_color="green"
            ).pack(pady=(0, 10))

        elif winner == "Draw":
            ctk.CTkLabel(
                self.over,
                text="Draw",
                font=winner_font,
                text_color="green"
            ).pack(pady=(0, 10))

        def on_finalize():
            # Lanza RTL en hilos separados
            threading.Thread(target=self.dron.RTL, daemon=True).start()
            threading.Thread(target=self.dron2.RTL, daemon=True).start()

            # Reinicia los contadores
            self.cp1_count = 0
            self.cp2_count = 0

            self.cp1_label.configure(text=f"Checkpoints: {self.cp1_count}")
            self.cp2_label.configure(text=f"Checkpoints: {self.cp2_count}")

            self.life1 = 1.0
            self.life2 = 1.0

            self.hp1_bar.set(self.life1)
            self.hp2_bar.set(self.life2)

            # Cierra ventanas
            self.over.destroy()
            self.game_window.destroy()

        ctk.CTkButton(
            self.over,
            text="End",
            command=on_finalize
        ).pack(pady=10)

    def stop_drones(self):
        """
        Para ambos drones en un hilo para no bloquear la UI.
        """
        try:
            self.dron.stopGo()
        except Exception as e:
            print(f"Error al parar dron1: {e}")
        try:
            self.dron2.stopGo()
        except Exception as e:
            print(f"Error al parar dron2: {e}")

    def rtl_drones(self):
        """
        Envía RTL a ambos drones en un hilo.
        """
        try:
            self.dron.RTL()
        except Exception as e:
            print(f"Error enviando RTL dron1: {e}")
        try:
            self.dron2.RTL()
        except Exception as e:
            print(f"Error enviando RTL dron2: {e}")

    def _spawn_next_checkpoint(self, canvas, queue, which):
        if not queue:
            setattr(self, f"current_cp_{which}", None)
            self._show_game_over()
            return
        cell = queue.pop(0)
        size = self.map_data["map_size"]["cell_size"]
        x = cell["col"] * size + size / 2
        y = cell["row"] * size + size / 2

        # si usas imagen:
        item = canvas.create_image(x, y, image=self.checkpoint_img, tag=f"cp_{which}")

        # o si prefieres óvalo:
        # r = size*0.4
        # item = canvas.create_oval(x-r, y-r, x+r, y+r, fill="yellow", outline="black", tag=f"cp_{which}")

        setattr(self, f"current_cp_{which}", {
            "col": cell["col"],
            "row": cell["row"],
            "item": item,
            "x": x,
            "y": y
        })

    def on_difficulty_change(self, selection):
        # convierte a minúsculas para usar el damage_map
        key = selection.lower()
        if key in self.damage_map:
            self.difficulty = key
        print(f"Dificultad → {self.difficulty}, daño por obstáculo = {self.damage_map[self.difficulty] * 100:.0f}%")

    # ----------------------------------------------------------------------
    # Seleccionar Mapa y mostrar preview
    # ----------------------------------------------------------------------
    def select_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r") as file:
                self.map_data = json.load(file)
            self.render_map_preview()
            messagebox.showinfo("Mapa Cargado", "Mapa cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el mapa: {e}")

    # ----------------------------------------------------------------------
    # Conectar Jugador y activar telemetría
    # ----------------------------------------------------------------------
    def _listen_for_joy4(self):
        # asumimos que sólo hay hasta 2 mandos conectados
        while len(self.connected_drones) < 2:
            pygame.event.pump()
            for idx in range(pygame.joystick.get_count()):
                if idx in self.num:
                    continue
                joy = pygame.joystick.Joystick(idx)
                joy.init()
                if joy.get_button(4) == 1:
                    # intento conectar; sólo si devuelve True, bloqueo este joystick
                    player = len(self.connected_drones) + 1
                    success = self._connect_single(self.dron if player == 1 else self.dron2,
                                                   idx,
                                                   player=player)
                    if success:
                        self.num.append(idx)
                    # espero a que suelte el botón para evitar rebotes
                    while joy.get_button(4) == 1:
                        pygame.event.pump()
                        time.sleep(0.05)
            time.sleep(0.1)

    def _connect_single(self, drone, joy_index, player) -> bool:
        """
        Conecta un solo dron con timeout de 10s.
        Si no conecta en ese tiempo, aborta y permite reintentar.
        """
        TIMEOUT = 10  # segundos

        if self.mode_var.get() == "Production" and self.control_var.get() == "Joystick":
            # Pedir COM SIEMPRE
            self._resultado_com = None

            def pedir_com():
                texto = f"Introduce el puerto COM de Player {player} (ej. COM3):"
                com = sd.askstring(
                    title=f"Puerto COM Player {player}",
                    prompt=texto,
                    parent=self.frame
                )
                self._resultado_com = com

            self.frame.after(0, pedir_com)
            while self._resultado_com is None:
                time.sleep(0.05)

            com = self._resultado_com
            if not com or not com.strip():
                messagebox.showwarning(
                    "Advertencia",
                    "Debes introducir un puerto COM válido."
                )
                return False

            conn_str = com.strip()
            baud = 57600

        elif self.mode_var.get() == "Simulation":
            port = 5762 if player == 1 else 5772
            conn_str = f"tcp:127.0.0.1:{port}"
            baud = 115200

        else:
            return False

        # 2) Intentar la conexión, con timeout
        try:
            print(f"🔌 Player {player}: intentando conectar a {conn_str} @ {baud}…")
            # NO BLOQUEANTE para poder aplicar timeout
            drone.connect(conn_str, baud, blocking=False)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error conectando Player {player}: {e}"
            )
            return False

        # 3) Esperar hasta TIMEOUT a que drone.state == "connected"
        start = time.time()
        while time.time() - start < TIMEOUT:
            if getattr(drone, "state", None) == "connected":
                break
            time.sleep(0.1)
        else:
            messagebox.showerror(
                "Error",
                f"No se pudo conectar Player {player} en {TIMEOUT} segundos. Abortando."
            )
            # Intenta desconectar por si acaso
            try:
                drone.disconnect()
            except Exception:
                pass
            return False

        # 4) Confirmar estado una vez más
        if getattr(drone, "state", None) != "connected":
            messagebox.showerror(
                "Error",
                f"Player {player} no pasó a estado 'connected'."
            )
            try:
                drone.disconnect()
            except Exception:
                pass
            return False

        # 5) Si conecta, sigue igual
        print(f"✅ Player {player} connected.")
        self.connected_drones.append(drone)
        if self.mode_var.get() == "Production" and self.control_var.get() == "Joystick":
            drone.setLoiterSpeed(1.0)
            time.sleep(1)
            drone.setRTLSpeed(1.0)
        elif self.mode_var.get() == "Simulation":
            drone.setLoiterSpeed(3.0)
            time.sleep(1)
            drone.setRTLSpeed(1.0)

        Joystick(joy_index, drone)
        if player == 1:
            drone.send_telemetry_info(self.process_telemetry_info)
        else:
            drone.send_telemetry_info(self.process_telemetry_info_second)
        self.update_player_list()
        return True

    def connect_player(self):
        """
        Conecta primero a Player 1 y, si Player 1 se conecta correctamente,
        pide el COM de Player 2 y lo conecta. Cada intento tiene un timeout
        para no quedarse bloqueado indefinidamente.
        """

        # Solo válido en Production + RC Transmitter
        if not (self.mode_var.get() == "Production" and self.control_var.get() == "RC Transmitter"):
            messagebox.showerror("Error", "Este método solo sirve para modo Production con RC Transmitter.")
            return

        baud = 57600
        timeout_secs = 10  # segundos máximos a esperar por cada dron

        # ─── 1) Conexión de Player 1 ──────────────────────────────────────────────

        # 1.1) Pedimos COM para Player 1
        com1 = sd.askstring(
            "Puerto COM Player 1",
            "Introduce el puerto COM de Player 1 (ej. COM3):",
            parent=self.frame
        )
        if not com1 or not com1.strip():
            # El usuario canceló o dejó en blanco
            return

        com1 = com1.strip()
        # 1.2) Intentamos la conexión en modo no bloqueante
        try:
            print(f"🔌 Iniciando conexión Player 1 a {com1} @ {baud}…")
            # blocking=False: regresa inmediatamente y _connect() corre en hilos internos
            conectado1 = self.dron.connect(com1, baud, blocking=False)
            if not conectado1:
                # Si connect(...) devolvió False, significa que ya estaba conectado o hubo error
                messagebox.showerror("Error", "No se pudo iniciar la conexión para Player 1.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando la conexión de Player 1:\n{e}")
            return

        # 1.3) Esperamos hasta timeout_secs a que self.dron.state == "connected"
        start = time.time()
        while time.time() - start < timeout_secs:
            if getattr(self.dron, "state", None) == "connected":
                break
            time.sleep(0.1)
        else:
            # Timeout: no se conectó a tiempo
            messagebox.showerror(
                "Error",
                f"Player 1 no se conectó en {timeout_secs} segundos. Abortando."
            )
            # Nos aseguramos de cerrar cualquier intento residual
            try:
                self.dron.disconnect()
            except:
                pass
            return

        # 1.4) Verificamos estado “connected” una vez más
        if getattr(self.dron, "state", None) != "connected":
            messagebox.showerror("Error", "Player 1 no alcanzó estado 'connected'.")
            try:
                self.dron.disconnect()
            except:
                pass
            return

        # Player 1 conectado con éxito
        print("✅ Player 1 connected.")
        self.connected_drones.append(self.dron)
        # Ajustes de velocidad
        time.sleep(1)
        self.dron.setLoiterSpeed(1.0)
        time.sleep(1)
        self.dron.setRTLSpeed(1.0)
        # Arrancamos telemetría (si lo deseas)
        self.dron.send_telemetry_info(self.process_telemetry_info)
        self.update_player_list()

        # ─── 2) Conexión de Player 2 ──────────────────────────────────────────────

        # 2.1) Pedimos COM para Player 2
        com2 = sd.askstring(
            "Puerto COM Player 2",
            "Introduce el puerto COM de Player 2 (ej. COM4):",
            parent=self.frame
        )
        if not com2 or not com2.strip():
            # Si el usuario canceló o dejó en blanco, dejamos a Player 1 conectado y salimos
            return

        com2 = com2.strip()
        # 2.2) Intentamos la conexión en modo no bloqueante
        try:
            print(f"🔌 Iniciando conexión Player 2 a {com2} @ {baud}…")
            conectado2 = self.dron2.connect(com2, baud, blocking=False)
            if not conectado2:
                messagebox.showerror("Error", "No se pudo iniciar la conexión para Player 2.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando la conexión de Player 2:\n{e}")
            return

        # 2.3) Esperamos hasta timeout_secs a que self.dron2.state == "connected"
        start = time.time()
        while time.time() - start < timeout_secs:
            if getattr(self.dron2, "state", None) == "connected":
                break
            time.sleep(0.1)
        else:
            # Timeout: Player 2 no se conectó a tiempo
            messagebox.showerror(
                "Error",
                f"Player 2 no se conectó en {timeout_secs} segundos. Abortando."
            )
            try:
                self.dron2.disconnect()
            except:
                pass
            return

        # 2.4) Verificamos estado “connected” una vez más
        if getattr(self.dron2, "state", None) != "connected":
            messagebox.showerror("Error", "Player 2 no alcanzó estado 'connected'.")
            try:
                self.dron2.disconnect()
            except:
                pass
            return

        # Player 2 conectado con éxito
        print("✅ Player 2 connected.")
        self.connected_drones.append(self.dron2)
        time.sleep(1)
        self.dron2.setLoiterSpeed(1.0)
        time.sleep(1)
        self.dron2.setRTLSpeed(1.0)
        self.dron2.send_telemetry_info(self.process_telemetry_info_second)
        self.update_player_list()

    # ----------------------------------------------------------------------
    def get_gps_from_canvas_coordinates(self, x, y):
            """
            Converts canvas coordinates (x, y) back to GPS coordinates (lat, lon).
            Uses 'top_left' as a reference and 'cell_size' as px/m.
            """
            x_old = x
            y_old = y
            angulo = math.radians(72)
            x = x_old * math.cos(angulo) - y_old * math.sin(angulo)
            y = x_old * math.sin(angulo) + y_old * math.cos(angulo)

            if not self.map_data or "top_left" not in self.map_data:
                print("🚨 Mapa sin 'top_left'.")
                return None, None

            top_left_lat = self.map_data["top_left"]["lat"]
            top_left_lon = self.map_data["top_left"]["lon"]
            scale = self.map_data["map_size"]["cell_size"]

            # Convert back from pixels to meters
            delta_lon_m = x / scale
            delta_lat_m = y / scale

            # Convert back from meters to degrees
            lat = top_left_lat - (delta_lat_m / 111320.0)
            lon = top_left_lon + (delta_lon_m / (111320.0 * math.cos(math.radians(top_left_lat))))

            print(f"📌 Canvas → GPS: x={x:.2f}, y={y:.2f} → lat={lat:.6f}, lon={lon:.6f}")
            return lat, lon
    def get_canvas_coordinates_from_gps(self, lat, lon):
        """
        Usa 'top_left' como referencia y 'cell_size' como px/m.
        """
        try:
            if not self.map_data or "top_left" not in self.map_data:
                print("🚨 Mapa sin 'top_left'.")
                return None, None

            top_left_lat = self.map_data["top_left"]["lat"]
            top_left_lon = self.map_data["top_left"]["lon"]
            scale = self.map_data["map_size"]["cell_size"]

            delta_lat_m = (top_left_lat - lat) * 111320.0
            delta_lon_m = (lon - top_left_lon) * (111320.0 * math.cos(math.radians(top_left_lat)))
            x = delta_lon_m * scale
            y = delta_lat_m * scale
            x_old = x
            y_old = y
            angulo = math.radians(-72)
            x = x_old * math.cos(angulo) - y_old * math.sin(angulo)
            y = x_old * math.sin(angulo) + y_old * math.cos(angulo)
            print(f"📌 GPS → Canvas: lat={lat}, lon={lon} → x={x:.2f}, y={y:.2f}")
            return x, y
        except Exception as e:
            print(f"❌ Error en get_canvas_coordinates_from_gps: {e}")
            return None, None

    def check_if_on_obstacle_cell(self, x, y):
        cell_size = self.map_data["map_size"]["cell_size"]
        col = int(x / cell_size)
        row = int(y / cell_size)
        print("Dron 1 en celda:", (col, row))

        obstacle_cells = set()
        for obs in self.map_data.get("obstacles", []):
            obstacle_cells.add((obs["original"]["col"], obs["original"]["row"]))
            obstacle_cells.add((obs["mirror"]["col"], obs["mirror"]["row"]))
        print("Celdas de obstáculo:", obstacle_cells)

        if (col, row) in obstacle_cells:
            if not self.is_on_obstacle:
                damage = self.damage_map[self.difficulty]
                self.life1 = max(0.0, self.life1 - damage)
                self.hp1_bar.set(self.life1)
                if self.life1 <= 0.0:
                    winsound.PlaySound("assets/death.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
                    time.sleep(1)
                    self._show_game_over(winner_forced="Player 2", death_message="Player 1 died!")
                    return True
                print(f"J1 choca: vida ahora {self.life1:.2f}")
                print("¡Alerta! Dron 1 sobre obstáculo en celda", (col, row))
                winsound.PlaySound("assets/hurt.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_on_obstacle = True
            return True
        self.is_on_obstacle=False
        return False

    def check_if_on_checkpoint_j1(self, x, y, canvas):
        size = self.map_data["map_size"]["cell_size"]
        cp = self.current_cp_j1
        if not cp:
            return False

        # hitbox en celdas → hitbox en píxeles
        hb_cells = self.hitbox_map.get(self.difficulty, 0)
        # tomamos la mitad de la celda + las celdas extra de tolerancia
        radius = size * (0.5 + hb_cells)

        # si estamos dentro del cuadrado de detección:
        if abs(x - cp["x"]) <= radius and abs(y - cp["y"]) <= radius:
            winsound.PlaySound("assets/ring.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            canvas.delete(cp["item"])
            self.cp1_count += 1
            self.cp1_label.configure(text=f"Checkpoints: {self.cp1_count}")
            self._spawn_next_checkpoint(canvas, self.queue_j1, "j1")

            return True
        if self.cp1_count == len(self.raw_checkpoints): self._show_game_over()
        return False

    def check_if_on_obstacle_cell_2(self, x, y):
        cell_size = self.map_data["map_size"]["cell_size"]
        col = int(x / cell_size)
        row = int(y / cell_size)
        print("Dron 2 en celda:", (col, row))

        obstacle_cells = set()
        for obs in self.map_data.get("obstacles", []):
            obstacle_cells.add((obs["original"]["col"], obs["original"]["row"]))
            obstacle_cells.add((obs["mirror"]["col"], obs["mirror"]["row"]))
        print("Celdas de obstáculo:", obstacle_cells)

        if (col, row) in obstacle_cells:

            if not self.is_on_obstacle2:
                damage = self.damage_map[self.difficulty]
                self.life2 = max(0.0, self.life2 - damage)
                self.hp2_bar.set(self.life2)
                if self.life2 <= 0.0:
                    winsound.PlaySound("assets/death.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
                    time.sleep(1)
                    self._show_game_over(winner_forced="Player 1", death_message="Player 2 died!")
                    return True
                print(f"J2 choca: vida ahora {self.life2:.2f}")
                print("¡Alerta! Dron 2 sobre obstáculo en celda", (col, row))
                winsound.PlaySound("assets/hurt.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_on_obstacle2 = True
            return True
        self.is_on_obstacle2 = False
        return False

    def check_if_on_checkpoint_j2(self, x, y, canvas):
        size = self.map_data["map_size"]["cell_size"]
        cp = self.current_cp_j2
        if not cp:
            return False

        # hitbox en celdas → hitbox en píxeles
        hb_cells = self.hitbox_map.get(self.difficulty, 0)
        # tomamos la mitad de la celda + las celdas extra de tolerancia
        radius = size * (0.5 + hb_cells)

        # si estamos dentro del cuadrado de detección:
        if abs(x - cp["x"]) <= radius and abs(y - cp["y"]) <= radius:
            winsound.PlaySound("assets/ring.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            canvas.delete(cp["item"])
            self.cp2_count += 1
            self.cp2_label.configure(text=f"Checkpoints: {self.cp2_count}")
            self._spawn_next_checkpoint(canvas, self.queue_j2, "j2")

            return True
        if self.cp2_count == len(self.raw_checkpoints): self._show_game_over()
        return False

    def _arm_flag(self, drone, event):
        """Arma al dron y señala cuando termina."""
        while drone.state == "connected":
            print(f"→ Intentando armar dron (estado actual: {drone.state})")
            drone.arm()
            time.sleep(1)
        print("✔️ Dron armado")
        event.set()

    def _takeoff_flag(self, drone, event):
        """Despega al dron y señala cuando termina."""
        while drone.state != "flying":
            print(f"→ Intentando takeoff (estado actual: {drone.state})")
            drone.takeOff(5)
            time.sleep(1)
        print("✔️ Dron en vuelo")
        event.set()

    def _on_ready(self):
        """Se pulsa Ready: destruye la carga y arranca el juego."""
        self.ready_btn.destroy()
        self.loading.destroy()
        self._init_game()

    def _show_loading_screen(self):

        pygame.mixer.music.stop()

        for drone in (self.dron, self.dron2):
            params0 = json.dumps([{"ID": "PILOT_THR_BHV", "Value": 1.0}])
            drone.setParams(params0, blocking=True)

        # 1. Eventos para saber cuando acaba cada operación
        self.arm_done1 = threading.Event()
        self.arm_done2 = threading.Event()
        self.takeoff_done1 = threading.Event()
        self.takeoff_done2 = threading.Event()
        self.stage = 1

        root = self.frame.winfo_toplevel()
        self.loading = ctk.CTkToplevel(root, fg_color="#000001")
        self.loading.attributes("-fullscreen", True)
        self.loading.transient(root)
        self.loading.grab_set()
        self.loading.bind("<Escape>", lambda e: self.loading.attributes("-fullscreen", False))

        img = Image.open('assets/loading_screen.gif')
        photoImg = ImageTk.PhotoImage(img)
        self.gif_label = AnimatedGif(self.loading, 'assets/loading_screen.gif', 0.04)
        self.gif_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.gif_label.start_thread()

        self.msg_label = ctk.CTkLabel(
            self.loading,
            text="Starting...",
            font=("M04_FATAL FURY", 12),
            text_color="white",  # ← CAMBIA AQUÍ
            anchor="w",
            fg_color="transparent"
        )

        self.msg_label.place(in_=self.loading, relx=0.02, rely=0.9, anchor="w")


        self.bar = ctk.CTkProgressBar(self.loading, orientation= "horizontal", height= 30, progress_color="green")
        self.bar.set(0.0)
        self.bar.pack(side="bottom", fill="x", padx=0, pady=10)

        self.pct_label = ctk.CTkLabel(
            self.loading,
            text="0 %",
            font=("Arial", 16),
            text_color="white",  # ← CAMBIA AQUÍ
            fg_color="transparent"
        )

        self.pct_label.place(in_=self.loading, relx=0.98, rely=0.9, anchor="e")

        self.ready_btn = ctk.CTkButton(
            self.loading,
            text="Ready",
            font=("M04_FATAL FURY", 18),
            text_color="white",  # ← CAMBIA AQUÍ
            fg_color="transparent",
            command=self._on_ready,
            state="disabled"
        )

        self.ready_btn.place(relx=0.5, rely=0.85, anchor="center")

        # 3. Arranca sólo ARM
        threading.Thread(target=self._arm_flag, args=(self.dron, self.arm_done1), daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self._takeoff_flag, args=(self.dron, self.takeoff_done1), daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self._arm_flag, args=(self.dron2, self.arm_done2), daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self._takeoff_flag, args=(self.dron2, self.takeoff_done2), daemon=True).start()
        # 4. Primer bucle de actualización
        self.loading.after(100, self._update_loading)

    def _update_loading(self):
        """Actualiza la barra y pasa de etapa según eventos o tiempos."""
        if self.stage == 1:
            self.msg_label.configure(text="Arming...")

            if self.arm_done1.is_set() and self.arm_done2.is_set():
                self.stage = 2
                self.bar.set(0.25)
                self.pct_label.configure(text="25 %")
                self.loading.update_idletasks()
            self.loading.after(2000, self._update_loading)

        elif self.stage == 2:
            self.msg_label.configure(text="warming up engines...")
            self.bar.set(0.50)
            self.pct_label.configure(text="50 %")
            self.loading.update_idletasks()
            self.stage = 3
            self.loading.after(5000, self._update_loading)

        elif self.stage == 3:
            self.msg_label.configure(text="Taking off...")
            self.bar.set(0.75)
            self.pct_label.configure(text="75 %")
            self.loading.update_idletasks()

            self.stage = 4
            self.loading.after(2000, self._update_loading)

        elif self.stage == 4:
            if self.takeoff_done1.is_set() and self.takeoff_done2.is_set():
                TARGET_HEADING = 72
                YAW_RATE = 20  # °/s
                # direction=1 (clockwise), relative=False (absoluto)
                self.dron.condition_yaw(TARGET_HEADING, YAW_RATE, direction=1, relative=False)
                self.dron2.condition_yaw(TARGET_HEADING, YAW_RATE, direction=1, relative=False)
                time.sleep(6)
                for drone in (self.dron, self.dron2):
                    drone.set_mode('LOITER')
                    time.sleep(1)
                    params1 = json.dumps([{"ID": "PILOT_THR_BHV", "Value": 0.0}])
                    drone.setParams(params1, blocking=True)
                self.bar.set(1.0)
                self.msg_label.configure(text="Loading progress finished")
                self.pct_label.configure(text="100 %")
                self.loading.update_idletasks()
                self.ready_btn.configure(state="normal")
            else:
                self.loading.after(100, self._update_loading)

    def _init_game(self):

        pygame.mixer.music.load('assets/track_1.wav')
        pygame.mixer.music.play(-1, 0.0)
        pygame.mixer.music.set_volume(0.2)

        map_width = self.map_data["map_size"]["width"]
        map_height = self.map_data["map_size"]["height"]
        cell_size = self.map_data["map_size"]["cell_size"]
        self.gif_label.stop_thread()
        # --- ventana en fullscreen ---
        def end_fullscreen(event=None):
            self.game_window.attributes("-fullscreen", False)

        self.game_window = ctk.CTkToplevel(fg_color="white")
        self.game_window.title("Checkpoint Race - Mapa")
        self.game_window.attributes("-fullscreen", True)
        self.game_window.bind("<Escape>", end_fullscreen)
        self.game_window.grid_rowconfigure(0, weight=1)
        self.game_window.grid_columnconfigure(0, weight=0)
        self.game_window.grid_columnconfigure(1, weight=1)
        self.game_window.grid_columnconfigure(2, weight=0)
        img = Image.open('assets/FONDO_JUEGO.png')
        img = img.resize((self.width,self.height), Image.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(img)
        fondo_label = ctk.CTkLabel(self.game_window, image=self.bg_image, text="")
        fondo_label.place(relx=0, rely=0, relwidth=1, relheight=1)


        # --- Barra de vida horizontal J1 ---

        life_frame1 = ctk.CTkFrame(self.game_window, fg_color="#000001", bg_color="#000001")
        life_frame1.grid(row=0, column=0, sticky="nw", padx=20, pady=10)
        life_frame1.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(life_frame1, text="PLAYER 1", font=("M04_FATAL FURY", 20), bg_color="transparent",
                     text_color="black") \
            .grid(row=0, column=0, pady=(0, 5))
        pywinstyles.set_opacity(life_frame1, 1, color="#000001")

        self.hp1_bar = ctk.CTkProgressBar(
            life_frame1,
            orientation="horizontal",
            width=200,
            height=20,
            progress_color="green",
            fg_color="white"
        )
        self.hp1_bar.set(self.life1)
        self.hp1_bar.grid(row=1, column=0, sticky="ew", pady=(20, 0))

        # label de recuento de checkpoints J1
        self.cp1_label = ctk.CTkLabel(life_frame1,
                                      text=f"Checkpoints: {self.cp1_count}",
                                      font=("M04_FATAL FURY", 16),
                                      text_color="black")
        self.cp1_label.grid(row=2, column=0, pady=(5, 10), sticky="n")

        # Temporizador Para Jugador 1
        self.timer1_label = ctk.CTkLabel(life_frame1,
                                         text=self._format_time(self.timer_duration),
                                         font=("M04_FATAL FURY", 16),
                                         text_color="black")
        self.timer1_label.grid(row=3, column=0, pady=(0, 10), sticky="n")

        btn_land1 = ctk.CTkButton(
            life_frame1,
            text="Land Drone 1",
            command=lambda: threading.Thread(
                target=self.dron.Land, kwargs={"blocking": False}, daemon=True
            ).start()
        )
        btn_land1.grid(row=4, column=0, pady=(5, 0))

        # --- contenedor central expandible ---
        center_container = ctk.CTkFrame(self.game_window, fg_color="#000001", bg_color="#000001")
        center_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        center_container.grid_rowconfigure(0, weight=1)
        center_container.grid_columnconfigure(0, weight=1)
        pywinstyles.set_opacity(center_container, 1, color="#000001")

        # --- canvas central TAMAÑO FIJO y centrado ---
        # usa map_width/map_height tal como ya los calculas un poco más arriba
        game_canvas = ctk.CTkCanvas(
            center_container,
            width=map_width,
            height=map_height,
            bg="gray"
        )
        # en lugar de grid, lo colocamos en el medio:
        game_canvas.place(relx=0.5, rely=0.5, anchor="center")

        # Fondo
        background_path = self.map_data.get("background")
        if background_path and os.path.exists(background_path):
            try:
                background_image = Image.open(background_path).resize((map_width, map_height), Image.LANCZOS)
                self.background_image_full = ImageTk.PhotoImage(background_image)
                game_canvas.create_image(0, 0, anchor="nw", image=self.background_image_full)
            except Exception as e:
                print(f"Error cargando el fondo: {e}")

        # Dibujar geofence
        for cell in self.map_data.get("geofence", []):
            col, row = cell["col"], cell["row"]
            x1 = col * cell_size
            y1 = row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            game_canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="red", tag="geofence")

        # lista_geo = [[[0, 0], [0, 0], [0, 980], [224, 980], [224, 0]], [[224, 0], [224, 980], [448, 980], [448, 0]]]
        # lista_geo = [[[14,14], [14, 14], [14, 966], [210, 966], [210, 14]], [[238,14],[238,966],[434,966],[434,14]]]
        # for poligono in lista_geo:
        #     for coordenada in poligono:
        #         lata, longanisa = self.get_gps_from_canvas_coordinates(coordenada[0],coordenada[1])
        #         coordenada[0] = lata
        #         coordenada[1] = longanisa
        #         print(self.get_canvas_coordinates_from_gps(lata, longanisa))
        # self.dron.setGEOFence(lista_geo)
        # self.dron2.setGEOFence(lista_geo)
        # print(lista_geo)
        # lista original en píxeles
        pixel_polygons = [
            [[14, 14], [14, 14], [14, 966], [210, 966], [210, 14]],
            [[238, 14], [238, 966], [434, 966], [434, 14]]
        ]

        # convierte cada (x,y) en [lat, lon]
        lista_geo = []
        for poly in pixel_polygons:
            geo_poly = []
            for x_px, y_px in poly:
                lat, lon = self.get_gps_from_canvas_coordinates(x_px, y_px)
                geo_poly.append([lat, lon])
            lista_geo.append(geo_poly)

        # aplica el geofence
        self.dron.setGEOFence(lista_geo, 0.9)
        self.dron2.setGEOFence(lista_geo, 0.9)

        print("Geofence enviado:", lista_geo)

        # Dibujar obstáculos
        obstacle_image_path = self.map_data.get("obstacle_image")
        obstacle_image = None
        if obstacle_image_path and os.path.exists(obstacle_image_path):
            try:
                obstacle_image = Image.open(obstacle_image_path).resize((cell_size, cell_size), Image.LANCZOS)
                self.obstacle_image_full = ImageTk.PhotoImage(obstacle_image)
            except Exception as e:
                print(f"Error cargando la imagen del obstáculo: {e}")

        for obstacle in self.map_data.get("obstacles", []):
            col, row = obstacle["original"]["col"], obstacle["original"]["row"]
            x1 = col * cell_size
            y1 = row * cell_size
            if obstacle_image:
                game_canvas.create_image(x1, y1, anchor="nw", image=self.obstacle_image_full)
            else:
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                game_canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", outline="black", tag="obstacle")

            mirror_col, mirror_row = obstacle["mirror"]["col"], obstacle["mirror"]["row"]
            mx1 = mirror_col * cell_size
            my1 = mirror_row * cell_size
            if obstacle_image:
                game_canvas.create_image(mx1, my1, anchor="nw", image=self.obstacle_image_full)
            else:
                mx2 = mx1 + cell_size
                my2 = my1 + cell_size
                game_canvas.create_rectangle(mx1, my1, mx2, my2, fill="yellow", outline="black", tag="obstacle")

        # Cargar la imagen del dron
        try:
            drone1_image_path = "assets/dron.png"
            if not os.path.exists(drone1_image_path):
                raise FileNotFoundError(f"No se encontró la imagen del dron en {drone1_image_path}")
            drone1_image = Image.open(drone1_image_path).resize((cell_size*2, cell_size*2), Image.LANCZOS)
            self.drone1_image_full = ImageTk.PhotoImage(drone1_image)
        except Exception as e:
            print(f"Error al cargar la imagen del dron: {e}")

            # --- Barra de vida horizontal J2 ---
        life_frame2 = ctk.CTkFrame(self.game_window, fg_color="#000001", bg_color="#000001")
        life_frame2.grid(row=0, column=2, sticky="ne", padx=20, pady=10)
        life_frame2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(life_frame2, text="PLAYER 2", font=("M04_FATAL FURY", 20), fg_color="transparent",
                     text_color="black") \
            .grid(row=0, column=0, pady=(0, 5))
        pywinstyles.set_opacity(life_frame2, 1, color="#000001")

        self.hp2_bar = ctk.CTkProgressBar(
            life_frame2,
            orientation="horizontal",
            width=200,
            height=20,
            progress_color="green",
            fg_color="white"
        )
        self.hp2_bar.set(self.life2)
        self.hp2_bar.grid(row=1, column=0, sticky="ew", pady=(20, 0))

        # label de recuento de checkpoints J1
        self.cp2_label = ctk.CTkLabel(life_frame2,
                                      text=f"Checkpoints: {self.cp2_count}",
                                      font=("M04_FATAL FURY", 16),
                                      text_color="black")
        self.cp2_label.grid(row=2, column=0, pady=(5, 10), sticky="n")
        # timer j2
        self.timer2_label = ctk.CTkLabel(life_frame2,
                                         text=self._format_time(self.timer_duration),
                                         font=("M04_FATAL FURY", 16),
                                         text_color="black")
        self.timer2_label.grid(row=3, column=0, pady=(0, 10), sticky="n")

        btn_land2 = ctk.CTkButton(
            life_frame2,
            text="Land Drone 2",
            command=lambda: threading.Thread(
                target=self.dron2.Land, kwargs={"blocking": False}, daemon=True
            ).start()
        )
        btn_land2.grid(row=4, column=0, pady=(0, 5))

        self.checkpoint_img = ImageTk.PhotoImage(
            Image.open("assets/checkpoint.png")
            .resize((cell_size*2, cell_size*2), Image.LANCZOS)
        )
        self._spawn_next_checkpoint(game_canvas, self.queue_j1, "j1")
        self._spawn_next_checkpoint(game_canvas, self.queue_j2, "j2")
        # ─── Iniciar temporizador ────────────────────────────────────────────
        self.remaining_time = self.timer_duration

        def update_timer():

            if self.game_over:
                return 

            texto = self._format_time(self.remaining_time)
            self.timer1_label.configure(text=texto)
            self.timer2_label.configure(text=texto)

            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.game_window.after(1000, update_timer)
            else:
                # tiempo agotado
                self._show_game_over()

        update_timer()

        self.start_telemetry_sync(game_canvas)
        self.start_telemetry_sync_second(game_canvas)

    def start_game(self):

        self.game_over = False

        if not self.map_data:
            messagebox.showwarning("Advertencia", "Selecciona un mapa antes de jugar.")
            return

        if not self.connected_drones:
            messagebox.showwarning(
                "Advertencia",
                "No hay jugadores conectados. Conecta al menos un dron antes de empezar."
            )
            return

        # ─── Leer y validar tiempo en minutos (mínimo 2) ───────────────────────
        try:
            mins = int(self.time_entry.get())
        except ValueError:
            mins = 2
        if mins < 2:
            mins = 2
        self.timer_duration = mins * 60   # en segundos

        self.raw_checkpoints = self.map_data.get("checkpoints", [])
        self.queue_j1 = [{"col": cp["original"]["col"], "row": cp["original"]["row"], "id": cp["id"]}
                         for cp in self.raw_checkpoints]
        self.queue_j2 = [{"col": cp["mirror"]["col"], "row": cp["mirror"]["row"], "id": cp["id"]}
                         for cp in self.raw_checkpoints]

        self._show_loading_screen()

    # ----------------------------------------------------------------------
    # 4) Telemetría y coordenadas
    # ----------------------------------------------------------------------
    def process_telemetry_info(self, telemetry_info):
        print(f"📡 Telemetría Jugador 1: {telemetry_info}")

    def process_telemetry_info_second(self, telemetry_info):
        print(f"📡 Telemetría Jugador 2: {telemetry_info}")

    def start_telemetry_sync(self, canvas):
        def update():
            lat, lon = self.dron.lat, self.dron.lon
            if lat != 0.0 or lon != 0.0:
                # 1) coords LÓGICAS (sin clamp, ya rotadas por get_canvas_coordinates_from_gps)
                x_logic, y_logic = self.get_canvas_coordinates_from_gps(lat, lon)

                # 2) detecciones en coords LÓGICAS
                self.check_if_on_checkpoint_j1(x_logic, y_logic, canvas)
                self.check_if_on_obstacle_cell(x_logic, y_logic)

                # 3) coords PARA DIBUJAR (clamp + centrar)
                map_w = self.map_data["map_size"]["width"]
                map_h = self.map_data["map_size"]["height"]
                hw = self.drone1_image_full.width() / 2
                hh = self.drone1_image_full.height() / 2

                x_draw = min(max(x_logic, hw), map_w - hw)
                y_draw = min(max(y_logic, hh), map_h - hh)

                # 4) dibujar con anchor="center"
                tag = "player_drone"
                canvas.delete(tag)
                canvas.create_image(
                    x_draw, y_draw,
                    anchor="center",  
                    image=self.drone1_image_full,
                    tag=tag
                )

                print(f"✅ Dron 1 en canvas: lógico=({x_logic:.1f},{y_logic:.1f})  dibujado=({x_draw:.1f},{y_draw:.1f})")

            canvas.after(100, update)

        update()

    def start_telemetry_sync_second(self, canvas):
        """
        Dibuja el dron 2 cada ~35 ms, separando lógica de detección de dibujo.
        """

        def update():
            lat, lon = self.dron2.lat, self.dron2.lon
            if lat != 0.0 or lon != 0.0:
                # 1) coords LÓGICAS (sin clamp ni rotación extra)
                x_logic, y_logic = self.get_canvas_coordinates_from_gps(lat, lon)

                # 2) detecciones en coords LÓGICAS
                self.check_if_on_checkpoint_j2(x_logic, y_logic, canvas)
                self.check_if_on_obstacle_cell_2(x_logic, y_logic)

                # 3) coords PARA DIBUJAR (clamp + centrar el sprite)
                map_w = self.map_data["map_size"]["width"]
                map_h = self.map_data["map_size"]["height"]
                hw = self.drone1_image_full.width() / 2
                hh = self.drone1_image_full.height() / 2

                x_draw = min(max(x_logic, hw), map_w - hw)
                y_draw = min(max(y_logic, hh), map_h - hh)

                # 4) dibujar con anchor="center" y tag propio
                tag = "player_drone_2"
                canvas.delete(tag)
                canvas.create_image(
                    x_draw, y_draw,
                    anchor="center",
                    image=self.drone1_image_full,
                    tag=tag
                )

                print(f"✅ Dron 2 en canvas: lógico=({x_logic:.1f},{y_logic:.1f})  dibujado=({x_draw:.1f},{y_draw:.1f})")

            canvas.after(100, update)

        update()

    # ----------------------------------------------------------------------
    # 5) Utilidades de la interfaz
    # ----------------------------------------------------------------------
    def update_player_list(self):
        self.player_listbox.delete("1.0", "end")

        # Comprueba el estado del primer dron
        if hasattr(self, "dron") and self.dron:
            self.player_listbox.insert("end", f"Player 1: {self.dron.state}\n")
        else:
            self.player_listbox.insert("end", "Player 1: No conectado\n")

        # Comprueba el estado del segundo dron
        if hasattr(self, "dron2") and self.dron2:
            self.player_listbox.insert("end", f"Player 2: {self.dron2.state}\n")
        else:
            self.player_listbox.insert("end", "Player 2: No conectado\n")

    def render_map_preview(self):
        """
        Muestra un preview de 300x300 del mapa en self.map_canvas.
        """
        self.map_canvas.delete("all")
        if not self.map_data:
            return

        map_width = self.map_data["map_size"]["width"]
        map_height = self.map_data["map_size"]["height"]
        cell_size = self.map_data["map_size"]["cell_size"]

        if cell_size <= 0:
            print("⚠ cell_size inválido en map_data.")
            return
        map_width_cells = map_width // cell_size
        map_height_cells = map_height // cell_size
        scale_x = 500 / map_width_cells if map_width_cells else 1
        scale_y = 500 / map_height_cells if map_height_cells else 1
        scale = min(scale_x, scale_y)
        offset_x = (500 - (map_width_cells * scale)) / 2
        offset_y = (500 - (map_height_cells * scale)) / 2

        background_path = self.map_data.get("background")
        if background_path and os.path.exists(background_path):
            try:
                background_image = Image.open(background_path)
                resized_image = background_image.resize(
                    (int(map_width_cells * scale), int(map_height_cells * scale)), Image.LANCZOS
                )
                self.background_image_preview = ImageTk.PhotoImage(resized_image)
                self.map_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.background_image_preview)
            except Exception as e:
                print(f"Error cargando el fondo: {e}")

        # Pintar geofence
        for fence in self.map_data.get("geofence", []):
            col, row = fence["col"], fence["row"]
            x1 = offset_x + col * scale
            y1 = offset_y + row * scale
            x2 = x1 + scale
            y2 = y1 + scale
            self.map_canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="red")

        # Pintar obstáculos
        obstacle_image_path = self.map_data.get("obstacle_image")
        obstacle_image = None
        if obstacle_image_path and os.path.exists(obstacle_image_path):
            try:
                obstacle_image = Image.open(obstacle_image_path).resize((int(scale), int(scale)), Image.LANCZOS)
                self.obstacle_image_preview = ImageTk.PhotoImage(obstacle_image)
            except Exception as e:
                print(f"Error cargando la imagen del obstáculo: {e}")

        for obstacle in self.map_data.get("obstacles", []):
            col, row = obstacle["original"]["col"], obstacle["original"]["row"]
            x = offset_x + col * scale
            y = offset_y + row * scale
            if obstacle_image:
                self.map_canvas.create_image(x, y, anchor="nw", image=self.obstacle_image_preview)
            else:
                self.map_canvas.create_rectangle(x, y, x + scale, y + scale, fill="yellow", outline="yellow")

            mirror_col, mirror_row = obstacle["mirror"]["col"], obstacle["mirror"]["row"]
            mx = offset_x + mirror_col * scale
            my = offset_y + mirror_row * scale
            if obstacle_image:
                self.map_canvas.create_image(mx, my, anchor="nw", image=self.obstacle_image_preview)
            else:
                self.map_canvas.create_rectangle(mx, my, mx + scale, my + scale, fill="yellow", outline="yellow")

    def callback_volver(self):
        self.frame.tkraise()

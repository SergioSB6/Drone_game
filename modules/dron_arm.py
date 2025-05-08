import threading
import time
from pymavlink import mavutil


def _arm(self, callback=None, params=None):
    print("Estado actual:", self.state)
    self.state = "arming"

    # Cambiar a modo GUIDED
    mode = 'GUIDED'
    mode_id = self.vehicle.mode_mapping()[mode]
    self.vehicle.mav.set_mode_send(
        self.vehicle.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )

    # Esperar el ACK para el cambio de modo con timeout (5 segundos)
    ack = self.vehicle.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
    if ack is None:
        print("No se recibió ACK para el cambio a GUIDED en tiempo esperado.")
    else:
        print("ACK recibido para cambio de modo:", ack)

    # Enviar comando para armar
    self.vehicle.mav.command_long_send(
        self.vehicle.target_system,
        self.vehicle.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0
    )

    # Implementar espera manual para que los motores se armen con timeout
    timeout_duration = 5  # segundos
    start_time = time.time()
    armed = False
    while time.time() - start_time < timeout_duration:
        # Se asume que self.vehicle.motors_armed() devuelve True o False.
        if self.vehicle.motors_armed():
            armed = True
            break
        time.sleep(0.1)

    if not armed:
        print("Los motores no se armieron en el tiempo esperado.")
        self.state = "connected"
    else:
        self.state = "armed"
    print("Estado final:", self.state)

    if callback is not None:
        if self.id is None:
            if params is None:
                callback()
            else:
                callback(params)
        else:
            if params is None:
                callback(self.id)
            else:
                callback(self.id, params)


def arm(self, blocking=True, callback=None, params=None):
    print("Estado antes de armar:", self.state)
    if self.state == 'connected':
        if blocking:
            self._arm(callback, params)
        else:
            armThread = threading.Thread(target=self._arm, args=(callback, params))
            armThread.start()
        return True
    else:
        return False

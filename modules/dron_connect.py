import json
import math
import threading
import time

from pymavlink import mavutil

''' Esta función sirve exclusivamente para detectar cuándo el dron se desarma porque 
ha pasado mucho tiempo desde que se armó sin despegar'''
# QUIZA HAY OTRA FORMA MAS SIMPLE DE DETECTAR ESO
def _handle_heartbeat(self):
    while self.state != 'disconnected':
        msg = self.vehicle.recv_match(
            type='HEARTBEAT', blocking=True)
        if msg.base_mode == 89 and self.state == 'armed' :
            self.state = 'connected'
        time.sleep (0.25)


# Some more small functions
def _connect(self, connection_string, baud, callback=None, params=None):
    self.vehicle = mavutil.mavlink_connection(connection_string, baud)
    self.vehicle.wait_heartbeat()
    self.state = "connected"
    # pongo en marcha el thread para detectar el desarmado por innacción
    handleThread = threading.Thread (target = self._handle_heartbeat)
    handleThread.start()


    # lo que viene a continuación es para pedir que nos envíe periodicamente datos de telemetría global
    # y datos de telemetría local
    # LAS FRECUENCIAS PODRIAN SER PARÁMETROS DE LA CONEXIÓN
    # A VECES SOSPECHO QUE EL SIMULADOR SE SATURA AL ENVIAR TANTO DATO Y LLEGAN CON RETRASO A LA APLICACIÓN
    # HABRÍA QUE VER SI EN PRODUCCIÓN PASA LO MISMO
    # CREO QUE ESO PASA CUANDO LA FRECUENCIA CON LA QUE PIDO QUE ENVIE DATOS NO COINCIDE CON LA FRECUENCIA CON LA QUE LOS LEO
    # TAMBIEN TENGO DUDAS EN ESTO: PODRIA INICIAR AQUI EN ENVIO DE DATOS DE TELEMETRIA. PARA ELLO TENDRÍA
    # QUE RECIBIR COMO PARAMETROS LOS CALLBACKS. TAL Y COMO ESTÁ AHORA, EL USUARIO TIENE QUE PEDIR LOS
    # DATOS DE TELEMETRIA DESPUES DE CONECTARSE, SI ES QUE LOS QUIERE, USANDO LAS FUNCIONES APROPIADAS.
    # NO SE QUÉ ES MEJOR

    # Pido datos globales
    frequency_hz = 4
    self.vehicle.mav.command_long_send(
        self.vehicle.target_system, self.vehicle.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,  # The MAVLink message ID
        1e6 / frequency_hz,
        # The interval between two messages in microseconds. Set to -1 to disable and 0 to request default rate.
        0, 0, 0, 0,  # Unused parameters
        0,
        # Target address of message stream (if message has target address fields). 0: Flight-stack default (recommended), 1: address of requestor, 2: broadcast.
    )
    self.vehicle.mav.command_long_send(
        self.vehicle.target_system, self.vehicle.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,  # The MAVLink message ID
        1e6 / frequency_hz,
        # The interval between two messages in microseconds. Set to -1 to disable and 0 to request default rate.
        0, 0, 0, 0,  # Unused parameters
        0,
        # Target address of message stream (if message has target address fields). 0: Flight-stack default (recommended), 1: address of requestor, 2: broadcast.
    )


    if callback != None:
        if self.id == None:
            if params == None:
                callback()
            else:
                callback(params)
        else:
            if params == None:
                callback(self.id)
            else:
                callback(self.id, params)


def connect(self,
            connection_string,
            baud,
            id= None,
            blocking=True,
            callback=None,
            params = None):
    if self.state == 'disconnected':
        self.id = id
        if blocking:
            self._connect(connection_string, baud)
        else:
            connectThread = threading.Thread(target=self._connect, args=[connection_string, baud, callback, params, ])
            connectThread.start()
        return True
    else:
        return False

def disconnect (self):
    if self.state == 'connected':
        self.state = "disconnected"
        # AQUI PARO EL ENVIO DE LOS DATOS DE TELEMETRIA
        self.stop_sending_telemetry_info()
        self.stop_sending_local_telemetry_info()
        time.sleep (5)
        self.vehicle.close()
        return True
    else:
        return False
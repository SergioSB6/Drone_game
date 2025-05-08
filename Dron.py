class Dron(object):
    def __init__(self):

        self.state = "disconnected"
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        ''' los otros estados son:
            connected
            arming
            armed
            takingOff
            flying
            returning
            landing
        '''

        self.going = False # se usa en dron_nav
        self.navSpeed = 1 # se usa en dron_nav
        self.direction = 'Stop' # se usa en dron_nav
        self.id = None
        self.sendTelemetryInfo = False #usado en dron_telemetry

        self.sendLocalTelemetryInfo = False  # usado en dron_local_telemetry

        self.step = 1 # se usa en dron_mov. Son los metros que mueve en cada paso
        self.localGeofence = None # se usa en dron_mov para evitar que el dron se salga del espacio
        self.position = [0,0,0] # se usa en dron_mov para identificar la posición del dron dentro del espacio
        self.heading = None


    # aqui se importan los métodos de la clase Dron, que están organizados en ficheros.
    # Así podría orgenizarse la aportación de futuros alumnos que necesitasen incorporar nuevos servicios
    # para sus aplicaciones. Crearían un fichero con sus nuevos métodos y lo importarían aquí
    # Lo que no me gusta mucho es que si esa contribución nueva requiere de algún nuevo atributo de clase
    # ese atributo hay que declararlo aqui y no en el fichero con los métodos nuevos.
    # Ese es el caso del atributo going, que lo tengo que declarar aqui y preferiría poder declararlo en el fichero dron_goto

    from modules.dron_connect import connect, _connect, disconnect, _handle_heartbeat
    from modules.dron_arm import arm, _arm
    from modules.dron_takeOff import takeOff, _takeOff
    from modules.dron_RTL_Land import  RTL, Land, _goDown
    from modules.dron_nav import _prepare_command, startGo, stopGo, go, _startGo, changeHeading, fixHeading, unfixHeading, changeNavSpeed
    from modules.dron_goto import goto, _goto, _distanceToDestinationInMeters
    from modules.dron_parameters import getParams, _getParams, setParams, _setParams
    from modules.dron_setGeofence import setGEOFence, _setGEOFence
    from modules.dron_telemetry import send_telemetry_info, _send_telemetry_info, stop_sending_telemetry_info

    from modules.dron_local_telemetry import send_local_telemetry_info, _send_local_telemetry_info, stop_sending_local_telemetry_info
    from modules.dron_mov import move, _move, _prepare_command_mov, setStep, moveto, _moveto, _prepare_command_movto, inGeofence, setLocalGeofence
    from modules.dron_mov import inGeofence, _futurePosition, check, _distance, _destination,setNavSpeed
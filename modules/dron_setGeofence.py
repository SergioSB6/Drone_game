# dron_setGeofence.py
import json
from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect

def _setGEOFence(self, polygons, margin):
    """
    Configura geofences en forma de múltiples polígonos en ArduPilot y
    ajusta también la distancia de seguridad (FENCE_MARGIN).
    :param polygons: Lista de polígonos, donde cada polígono es una lista de [lat, lon].
    :param margin:   Distancia de seguridad al fence en metros (FENCE_MARGIN).
    """
    try:
        # 1) Activa geofence
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_ENABLE",
            float(1),
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # 2) Acción al violar fence (4 = HOLD_INSIDE, por ejemplo)
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_ACTION",
            float(4),
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # 3) Tipo de fence (7 = INCLUSION)
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_TYPE",
            float(7),
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # 4) Distancia de seguridad al fence
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_MARGIN",
            float(margin),
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )
        print(f"→ FENCE_MARGIN seteado a {margin} m")

        # 5) Prepara todos los puntos (cierra cada polígono)
        all_points = []
        for polygon in polygons:
            if len(polygon) < 3:
                raise ValueError("Cada polígono debe tener al menos 3 puntos.")
            closed = polygon + [polygon[0]]
            all_points.extend(closed)

        total = len(all_points)
        if total > 255:
            raise ValueError("El número total de puntos no puede exceder 255.")

        # 6) Envia FENCE_TOTAL
        self.vehicle.mav.param_set_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            b"FENCE_TOTAL",
            float(total),
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        # 7) Envia cada punto
        for idx, (lat, lon) in enumerate(all_points):
            self.vehicle.mav.send(
                mavutil.mavlink.MAVLink_fence_point_message(
                    self.vehicle.target_system,
                    self.vehicle.target_component,
                    idx,
                    total,
                    float(lat),
                    float(lon),
                )
            )

        print(f"Geofence aplicado correctamente con {total} puntos y margen {margin} m.")
    except Exception as e:
        raise RuntimeError(f"Error al configurar el geofence: {e}")

def setGEOFence(self, polygons, margin):
    """
    Configura un geofence basado en múltiples polígonos, incluyendo FENCE_MARGIN.
    :param polygons: Lista de polígonos, donde cada polígono es una lista de [lat, lon].
    :param margin:   Distancia de seguridad al fence en metros.
    """
    try:
        print("Configurando geofence con los polígonos proporcionados y margen de seguridad...")
        _setGEOFence(self, polygons, margin=margin)
    except Exception as e:
        raise RuntimeError(f"Error al aplicar el geofence: {e}")

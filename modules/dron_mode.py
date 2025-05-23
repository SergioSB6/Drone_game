# modules/dron_mode.py
import time
from pymavlink import mavutil

def set_mode (self,mode):
    # Get mode ID
    mode_id = self.vehicle.mode_mapping()[mode]
    self.vehicle.mav.set_mode_send(
        self.vehicle.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)
    msg = self.vehicle.recv_match(type='COMMAND_ACK', timeout=3)

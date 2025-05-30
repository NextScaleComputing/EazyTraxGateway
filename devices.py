from datetime import datetime
from ble_device import BLEDevice
import gc
import logging

# Dictionary to store BLE devices
ble_devices_array = {}

def get_recent_devices(max_second=60):
    """Returns a sorted list of BLE devices seen within the last `max_second` seconds."""
    current_time = int(datetime.now().timestamp())

    return sorted(
        [
            device
            for device in ble_devices_array.values()
            if (current_time - device.last_seen) <= max_second
        ],
        key=lambda d: d.last_seen,
        reverse=True,
    )

def cleanup_old_devices(max_seconds=30):
    """Removes BLE devices that have not been seen in the last `max_seconds` seconds."""
    current_time = int(datetime.now().timestamp())
    devices_to_remove = []
    
    # ??????????????????????????????? max_seconds ???????????????
    for addr, device in ble_devices_array.items():
        if (current_time - device.last_seen) > max_seconds:
            devices_to_remove.append(addr)
    
    # ????????????????????
    for addr in devices_to_remove:
        del ble_devices_array[addr]
    
    if devices_to_remove:
        logging.info(f"scanner:: Removed {len(devices_to_remove)} stale BLE devices older than {max_seconds} seconds. Remaining: {len(ble_devices_array)}")
        gc.collect()
    
    return len(devices_to_remove)
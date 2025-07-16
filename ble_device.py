from datetime import datetime
from math import fabs
import struct
import json
from bleak import BleakClient
import sys
import os


class BLEDevice:
    """Represents a single BLE device."""
    def __init__(self, address: str, name: str, rssi: int):
        self.address = address
        self.name = name
        self.rssi = rssi
        self.battery = None
        self.temperature = None
        self.humidity = None
        self.co2 = None
        self.formaldehyde = None
        self.tvoc = None
        self.pm25 = None
        self.pm10 = None
        self.ibeacon_uuid = None
        self.ibeacon_major = None
        self.ibeacon_minor = None
        self.ibeacon_rssi_1m = None
        self.ibeacon_rssi = None
        self.last_seen = int(datetime.now().timestamp())
        self.service_uuids = []  # List to track unique service UUIDs
        self.service_data_keys = []  # List to track unique service data keys
        self.manufacture_data_keys = []  # List to track unique manufacturer data keys
        self.services = None  # Cache services

    def add_service_uuid(self, uuid):
        """Add a new service UUID if it's not already in the list."""
        if uuid not in self.service_uuids:
            self.service_uuids.append(uuid)

    def add_service_data_key(self, key):
        """Add a new service data key if it's not already in the list."""
        if key not in self.service_data_keys:
            self.service_data_keys.append(key)

    def add_manufacture_data_key(self, key):
        """Add a new manufacturer data key if it's not already in the list."""
        if key not in self.manufacture_data_keys:
            self.manufacture_data_keys.append(key)

    def update(self, name: str, rssi: int):
        ALPHA = 0.6
        """Update device info with an EMA smoothing technique."""
        self.name = name
        self.rssi = int(ALPHA * rssi + (1 - ALPHA) * self.rssi) if self.rssi else rssi
        self.last_seen = int(datetime.now().timestamp())

    def update_battery(self, battery: int):
        """Update the battery level."""
        self.battery = battery

    def update_temperature(self, temperature: float):
        """Update the temperature."""
        self.temperature = temperature

    def update_humidity(self, humidity: float):
        """Update the humidity."""
        self.humidity = humidity

    def update_co2(self, value: int):
        self.co2 = value

    def update_formaldehyde(self, value: int):
        self.formaldehyde = value

    def update_tvoc(self, value: int):
        self.tvoc = value

    def update_pm25(self, value: float):
        self.pm25 = value

    def update_pm10(self, value: float):
        self.pm10 = value

    def update_ibeacon(
        self, uuid: str, major: int, minor: int, rssi_1m: int, rssi: int
    ):
        """Update the iBeacon data."""
        self.ibeacon_uuid = uuid
        self.ibeacon_major = major
        self.ibeacon_minor = minor
        self.ibeacon_rssi_1m = rssi_1m
        self.ibeacon_rssi = rssi

    def to_json(self, include_service_manufacture_data=False):
        """Converts the BLEDevice object into a JSON-serializable dictionary."""
    
        json_data = {
            "address": self.address,
            "name": self.name,
            "rssi": self.rssi,
            "last_seen": self.last_seen,
            "sensors": {k: v for k, v in {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "battery": self.battery,
                "co2": self.co2,
                "formaldehyde": self.formaldehyde,
                "tvoc": self.tvoc,
                "pm25": self.pm25,
                "pm10": self.pm10,
            }.items() if v is not None},
            "ibeacon": {k: v for k, v in {
                "uuid": self.ibeacon_uuid,
                "major": self.ibeacon_major,
                "minor": self.ibeacon_minor,
                "rssi": self.ibeacon_rssi,
                "rssi_1m": self.ibeacon_rssi_1m,
            }.items() if v is not None},
        }

        if include_service_manufacture_data:
            json_data.update({
                "service_uuids": self.service_uuids,  
                "service_data_keys": self.service_data_keys,  
                "manufacture_data_keys": self.manufacture_data_keys,  
            })

        return json_data


    def parse_ibeacon(self, data):
        if len(data) >= 46 and data[0:4] == "0215":
            uuid = data[4:36]
            major = int(data[36:40], 16)
            minor = int(data[40:44], 16)
            rssi_1m = struct.unpack("b", bytes.fromhex(data[44:46]))[0]

            if False:
                print("########## iBeacon Advertisement ##########")
                print(f"Address: {address}")
                print(f"Name: {device.name}")
                print(f"RSSI: {advertisement_data.rssi}")
                print(f"iBeacon UUID: {uuid}")
                print(f"iBeacon Major: {major}")
                print(f"iBeacon Minor: {minor}")
                print(f"iBeacon RSSI at 1m: {rssi_1m}")
                print("###########################################\n")

            return uuid, major, minor, rssi_1m
        return None, None, None, None

        async def read_characteristic(self, service_uuid, char_uuid):
            """Reads a specific BLE characteristic from a given service UUID."""
            try:
                async with BleakClient(self.address) as client:
                    if not client.is_connected:
                        return {"error": "Failed to connect to BLE device"}
                
                    # Retrieve services and check for the characteristic
                    services = await client.get_services()
                    found = False
                    for service in services:
                        if service.uuid.lower() == service_uuid.lower():
                            for char in service.characteristics:
                                if char.uuid.lower() == char_uuid.lower():
                                    found = True
                                    try:
                                        value = await client.read_gatt_char(char_uuid)
                                        return {
                                            "mac_address": self.address,
                                            "service_uuid": service_uuid,
                                            "char_uuid": char_uuid,
                                            "value": value.hex(),  # Return as HEX
                                            "ascii_value": value.decode(errors='ignore')
                                        }
                                    except Exception as e:
                                        return {"error": f"Failed to read characteristic: {str(e)}"}
                
                    if not found:
                        return {"error": "Service or characteristic not found"}

            except Exception as e:
                return {"error": str(e)}

    def process_service_uuids(self, advertisement_data):
        """Processes service UUIDs from advertisement data."""
        for uuid in advertisement_data.service_uuids:
            self.add_service_uuid(uuid)



    def process_service_data(self, advertisement_data):
        """Processes service data from advertisement data."""

        for key, value in advertisement_data.service_data.items():
            self.add_service_data_key(key)
            #print(f"> value: {value}") 
            
            # Check for specific data formats (e.g., custom sensor data)
            if key == "0000ffe1-0000-1000-8000-00805f9b34fb" and value.hex().startswith("a101"):
                self.update_battery(int(value.hex()[4:6], 16))
                self.update_temperature(int(value.hex()[6:10], 16) / 256.0)
                self.update_humidity(int(value.hex()[10:14], 16) / 256.0)

            if key == "0000ffe1-0000-1000-8000-00805f9b34fb" and value.hex().startswith("a701"):
                payload = value[2:]  # Skip 0xA7 + 0x01

                #print("------------------------------------")
                ##print(payload.hex())
                #print(len(payload))
                if len(payload) >= 14:
                    eco2 = int.from_bytes(payload[0:2])
                    ech2o = int.from_bytes(payload[2:4])
                    tvoc = int.from_bytes(payload[4:6])
                    pm25 = int.from_bytes(payload[6:8])
                    pm10 = int.from_bytes(payload[8:10])
                    temperature = payload[10] + payload[11] / 100
                    humidity = payload[12] + payload[13] / 100

                    self.update_co2(eco2)
                    self.update_formaldehyde(ech2o)
                    self.update_tvoc(tvoc)
                    self.update_pm25(pm25)
                    self.update_pm10(pm10)
                    self.update_temperature(temperature)
                    self.update_humidity(humidity)

                    #print(f"✅ Parsed Air Sensor — CO₂:{eco2}, HCHO:{ech2o}, TVOC:{tvoc}, PM2.5:{pm25}, PM10:{pm10}, Temp:{temperature:.2f}°C, RH:{humidity:.2f}%")

            elif False:
                print(f">---------process_service_data----------------")
                #print(f"> process_service_data: {advertisement_data}")
                print(f"> value: {value}")
                print(f"> key: {key}")
                print(f"> value.hex(): {value.hex()}")

    def process_manufacturer_data(self, advertisement_data):
        """Processes manufacturer data from advertisement data."""
        for key, value in advertisement_data.manufacturer_data.items():
            self.add_manufacture_data_key(key)
            # Apple iBeacon
            if key == 76:
                uuid, major, minor, rssi_1m = self.parse_ibeacon(value.hex())
                if uuid:
                    self.update_ibeacon(uuid, major, minor, rssi_1m, advertisement_data.rssi)

            # Custom Sensor Data
            elif  key == 1593:
                hex_value = value.hex()
                if hex_value.startswith("ca05"):
                    self.update_temperature(int(hex_value[10:14], 16) / 256.0)
                    self.update_humidity(int(hex_value[14:18], 16) / 256.0)
                elif hex_value.startswith("ca00"):
                    self.update_battery(int(hex_value[16:18], 16))

            else:
                # Process other manufacturer data silently
                pass

    def debug_print(self, advertisement_data):
        """Prints debug information for the BLE device."""
        if False:  # Change to True to enable debugging
            print("  _________________________________________________")
            print(f"  Address: {self.address}")
            print(f"  Name: {self.name}")
            print(f"  RSSI: {self.rssi}")
            print(f"  Advertisement Data: {advertisement_data}")
            if advertisement_data.tx_power is not None:
                print(f"  TX Power: {advertisement_data.tx_power}")
            print("  _________________________________________________")

    async def get_services_and_characteristics(self):
        """Retrieves all services and characteristics from BLE device. Uses cached data if available."""
        #if self.services:  # Return cached services if available
            #return {"services": self.services}
        try:
            async with BleakClient(self.address) as client:
                if not client.is_connected:
                    return {"error": "Failed to connect to BLE device"}
                else:
                    print(f"> {self.address} Connected")

                services = await client.get_services()
                service_list = []
                
                for service in services:
                    service_uuid = service.uuid.lower()  # Normalize UUID format
                    service_dict = {
                        "service_uuid": service_uuid,
                        "characteristics": [],
                        "Data": ""
                    }
                    for char in service.characteristics:
                        char_uuid = char.uuid.lower()
                        char_dict = {
                            "char_uuid": char.uuid,
                            "properties": char.properties
                        }
                        service_dict["characteristics"].append(char_dict)

                    service_list.append(service_dict)

                self.services = service_list  # Cache services

                print(f">Return result: ")
                print(f"{json.dumps(self.services, indent=2)}")

                return {"services": service_list}

        except Exception as e:
            return {"error": str(e)}

    async def read_all_characteristics(self):
        """Reads all characteristics from the cached services and stores values."""
        if not self.services:
            return {"error": "No services available. Scan first."}

        try:
            async with BleakClient(self.address) as client:
                if not client.is_connected:
                    return {"error": "Failed to connect to BLE device"}

                for service in self.services:
                    service["Data"] = ""
                    service["Data_Ascii"] = ""

                    for char in service["characteristics"]:
                        try:
                            value = await client.read_gatt_char(char["char_uuid"])
                            hex_value = value.hex()
                            try:
                                ascii_value = value.decode("utf-8").strip()  # Try decoding as UTF-8
                            except UnicodeDecodeError:
                                ascii_value = "".join(
                                    chr(b) if 32 <= b < 127 else "." for b in value
                                )  # Replace non-printable characters

                            service["Data"] += f"{char['char_uuid']}: {hex_value} | "
                            service["Data_Ascii"] += f"{char['char_uuid']}: {ascii_value} | "
                        except Exception as e:
                            error_msg = f"Error ({str(e)})"
                            service["Data"] += f"{char['char_uuid']}: {error_msg} | "
                            service["Data_Ascii"] += f"{char['char_uuid']}: {error_msg} | "

            return {"services": self.services}

        except Exception as e:
            return {"error": str(e)}


    def __repr__(self):
        return (
            f"BLEDevice(address={self.address}, name={self.name}, rssi={self.rssi}, "
            f"battery={self.battery}, temperature={self.temperature}, "
            f"humidity={self.humidity}, ibeacon_uuid={self.ibeacon_uuid}, "
            f"ibeacon_major={self.ibeacon_major}, ibeacon_minor={self.ibeacon_minor}, "
            f"rssi_1m={self.ibeacon_rssi_1m}, ibeacon_rssi={self.ibeacon_rssi}, "
            f"last_seen={self.last_seen})"
        )

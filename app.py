import asyncio
import pandas as pd
import struct
import json
import os
import gc
import logging
import sys
import psutil
import requests
import socket
import netifaces
import platform
import netifaces
import paho.mqtt.client as mqtt

from paho.mqtt.client import CallbackAPIVersion
from dotenv import load_dotenv
load_dotenv(override=True)

from bleak import BleakScanner
from ble_device import BLEDevice
from flask import Flask, jsonify, render_template, request
from datetime import datetime
from devices import ble_devices_array, get_recent_devices, cleanup_old_devices
from device_info import get_device_info
import hostname
import auth

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

time_start = int(datetime.now().timestamp())
mqtt_server_ip = "172.19.2.11"
mqtt_client_instance = None
proxy_url = os.getenv("PROXY")
publish_count = 0
app = Flask(__name__)
scan_count = 0
gateway_mac = None

@app.route("/")
def index():
    return "EazyTrax Gateway"

@app.route("/api")
def get_payload():
    payLoad = prepare_payload()
    return jsonify(payLoad)

@app.route("/api/Telemetry/Gateway/token", methods=["GET"])
def get_token():
    """API endpoint to get a new bearer token based on the device MAC address"""
    global gateway_mac
    
    # Default to using the gateway_mac if it's available
    mac_address = gateway_mac
    
    # Check if a MAC address was provided in the request
    if request.args.get('mac'):
        mac_address = request.args.get('mac').replace(':', '').upper()
    
    # If we don't have a MAC address, return an error
    if not mac_address:
        return jsonify({
            "success": False,
            "message": "No MAC address available"
        }), 400
    
    # Generate a token
    token = auth.generate_token(mac_address)
    
    return jsonify({
        "success": True,
        "token": token,
        "mac": mac_address,
        "expires_in": auth.TOKEN_EXPIRY
    })

@app.route("/api/Telemetry/Gateway/hostname", methods=["GET"])
@auth.token_required
def get_hostname():
    """API endpoint to get the current hostname (requires authentication)"""
    return jsonify({
        "hostname": hostname.get_current_hostname(),
        "success": True
    })

@app.route("/api/Telemetry/Gateway/hostname/update", methods=["POST"])
@auth.token_required
def set_hostname():
    """API endpoint to change the hostname (requires authentication)"""
    data = request.get_json()
    
    if not data or 'hostname' not in data:
        return jsonify({
            "success": False,
            "message": "Missing hostname parameter"
        }), 400
    
    new_hostname = data['hostname']
    success, message = hostname.change_hostname(new_hostname)
    
    return jsonify({
        "success": success,
        "message": message,
        "hostname": hostname.get_current_hostname()
    }), 200 if success else 400

async def send_report_payload():
        try:
            payload = prepare_payload()
            publish_to_mqtt(payload)
            
            export_devices = get_recent_devices()
            publish_each_device_to_mqtt(export_devices)

            # ?????????????????????????????????????? 30 ??????
            logging.info(f"mqtt:: Cleaning up old device data (older than 30 seconds)")
            removed_count = cleanup_old_devices(30)
            
            # ??????????????????????????????
            del payload
            del export_devices

        except Exception as e:
            logging.info(f"Error sending payload: {e}")
        gc.collect()
        
def get_active_interface():
    """
    Detects the active network interface (Wi-Fi prioritized on Linux).
    Returns (interface_name, ip_address, mac_address)
    """
    system = platform.system().lower()

    def get_ip_mac(interface):
        try:
            ip = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [{}])[0].get("addr")
            mac = netifaces.ifaddresses(interface).get(netifaces.AF_LINK, [{}])[0].get("addr")
            return ip, mac
        except (KeyError, IndexError, ValueError):
            return None, None

    # First pass: prioritize wlan* on Linux
    if system == "linux":
        for iface in netifaces.interfaces():
            if iface.startswith("wlan"):
                ip, mac = get_ip_mac(iface)
                if ip and mac:
                    return iface, ip, mac

    # Second pass: accept any interface with valid IP/MAC
    for iface in netifaces.interfaces():
        ip, mac = get_ip_mac(iface)
        if ip and mac:
            return iface, ip, mac

def get_recent_devices(max_second=90):
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

def prepare_payload(max_second=60):
    global publish_count
    hostname_value = hostname.get_current_hostname()  # Use the hostname module
    interface, ip, mac = get_active_interface()
    export_devices = get_recent_devices(max_second)
    device_info = get_device_info()
    token = os.getenv("TOKEN")
    publish_count = publish_count + 1

    payload: str = {
        "meta": {
            "access_token": token,
            "topic": "telemetry",
            "api_version": "2.0",
            "gateway_mac": "NA"
        },
        "reporter": {
            "name": hostname_value,
            "mac": mac if mac else "N/A",
            "hw_type": f"{device_info['Hardware']} {device_info['Model']}", 
            "revision": device_info["Revision"],
            "model": device_info["Model"],
            "sw_version": "1.0.50",
            "ipv4": ip if ip else "N/A",
            "uptime": int(psutil.boot_time()),
            "time": int(datetime.now().timestamp()),
            "publish_count": publish_count,
        },
        "reported": [device.to_json() for device in export_devices],
    }
 
    return payload

def init_mqtt_client():

    global mqtt_client_instance, gateway_mac, mqtt_server_ip
    mqtt_client_instance = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, gateway_mac)
    mqtt_client_instance.connect(mqtt_server_ip, 1883, 60)
    mqtt_client_instance.loop_start()

def ensure_mqtt_connection():
    global mqtt_client_instance, gateway_mac
    if mqtt_client_instance is None:
        init_mqtt_client()
    elif not mqtt_client_instance.is_connected():
        mqtt_client_instance.reconnect()

def publish_to_mqtt(payload):
    global gateway_mac
    try:
        ensure_mqtt_connection()

        topic = f"Gateways/{gateway_mac}/Telemetry"
        message = json.dumps(payload)
        message_size = len(message.encode("utf-8"))

        mqtt_client_instance.publish(topic, message, qos=0)

        logging.info(f"mqtt:: Published payload to MQTT topic: {topic}")
        logging.info(f"mqtt:: Payload size: {message_size} bytes")
    except Exception as e:
        logging.error(f"mqtt:: MQTT publish error: {e}")

def publish_each_device_to_mqtt(devices):
    global gateway_mac

    props = mqtt.Properties(mqtt.PacketTypes.PUBLISH)
    props.MessageExpiryInterval = 10  

    try:
        ensure_mqtt_connection()

        for device in devices:
            topic = f"Bles/{device.address}/Gateways/{gateway_mac}/Telemetry"
            message = json.dumps(device.to_json())
            mqtt_client_instance.publish(topic, message, qos=0, retain=True, properties=props)

        logging.info(f"mqtt:: Published {len(devices)} individual devices to MQTT.")
    except Exception as e:
        logging.error(f"mqtt:: MQTT individual publish error: {e}")

async def scan_ble_devices():
    """Continuously scans for BLE devices with periodic pauses."""
    logging.info("Continuous BLE scanning started.")

    def callback(device, advertisement_data):
       device.address = device.address.replace(":", "")
       # Scan all BLE devices without filtering
       if device.address not in ble_devices_array:
           ble_devices_array[device.address] = BLEDevice(device.address, device.name, advertisement_data.rssi)
       else:
           ble_devices_array[device.address].update(device.name, advertisement_data.rssi)
       ble_devices_array[device.address].process_manufacturer_data(advertisement_data)
       ble_devices_array[device.address].process_service_uuids(advertisement_data)
       ble_devices_array[device.address].process_service_data(advertisement_data)

    scanner = BleakScanner(callback)

    try:
        while True:
            await scanner.start()
            logging.info("scanner:: Scanning started")
            await asyncio.sleep(10)  # Scan for 10 seconds
            await scanner.stop()
            await send_report_payload()
            gc.collect()  # Run garbage collection to free up memory

    except asyncio.CancelledError:
        logging.info("scanner:: BLE scanning task cancelled.")
        await scanner.stop()
    except Exception as e:
        logging.info(f"scanner:: Error in BLE scanning: {e}")
        await scanner.stop()

def run_flask_app():
     app.run(host="0.0.0.0", port=os.getenv("PORT"))

async def main():
    global gateway_mac, mqtt_server_ip
    
    interface, ip, mac = get_active_interface()
    gateway_mac = mac.replace(':', '').upper() if mac else "defaultClientId"
    
    # Set the MAC address in the auth module to use it as SECRET_KEY
    auth.set_mac_address(mac)
    
    mqtt_server_ip = os.getenv("MQTT_SERVER")

    print(f"---------------------------------------------------------")
    print(f"EazyTrax Gateway")
    print(f"---------------------------------------------------------")
    print(f"TOKEN: {os.getenv('ACCESS_TOKEN')}")
    print(f"PORT: {os.getenv('PORT')}")
    print(f"MAC: {gateway_mac}")
    print(f"IP: {ip}")
    print(f"Interface: {interface}")
    print(f"MQTT_SERVER_IP: {mqtt_server_ip}")
    print(f"Hostname: {hostname.get_current_hostname()}")
    print(f"---------------------------------------------------------")

    # Start the BLE scanning task
    asyncio.create_task(scan_ble_devices())

    # Run Flask in a separate thread
    loop = asyncio.get_event_loop()
    flask_thread = loop.run_in_executor(None, run_flask_app)
    await flask_thread  # Wait for Flask to keep running

if __name__ == "__main__":
    asyncio.run(main())
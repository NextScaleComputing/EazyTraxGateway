# EazyTrax Gateway (PiScanner)

🚀 **EazyTrax Gateway** is a Python-based BLE (Bluetooth Low Energy) scanning application that discovers, monitors, and reports IoT device data through MQTT communication.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Docker Deployment](#docker-deployment)
- [Service Management](#service-management)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🔍 Overview

EazyTrax Gateway acts as a bridge between BLE IoT devices and MQTT infrastructure. It continuously scans for BLE devices, processes their advertising data (including sensor readings, iBeacon data, and device information), and publishes this data to an MQTT broker for further processing and analysis.

### Key Components

- **BLE Scanner**: Discovers and monitors BLE devices in range
- **Data Processor**: Extracts sensor data from BLE advertisements
- **MQTT Publisher**: Sends device data to MQTT broker
- **Web API**: RESTful API for device management and configuration
- **Authentication**: Token-based authentication system
- **Device Management**: Tracks device history and status

## ✨ Features

### BLE Device Support
- 📡 **Continuous BLE scanning** with real-time device discovery
- 📊 **Multi-sensor data extraction**: Temperature, Humidity, CO2, PM2.5, PM10, TVOC, Formaldehyde
- 📶 **Signal strength monitoring** (RSSI) with moving average filtering
- 🔋 **Battery level monitoring** for supported devices
- 📍 **iBeacon detection** with UUID, Major, Minor, and RSSI@1m
- 🔍 **Service discovery** and manufacturer data parsing

### Connectivity & Communication
- 🌐 **MQTT integration** with automatic reconnection
- 🔒 **Secure authentication** using MAC-based token generation
- 📤 **Real-time data publishing** with configurable intervals
- 🌍 **Network auto-detection** with interface prioritization
- 📡 **HTTP proxy support** for restricted networks

### Device Management
- 🖥️ **System information reporting** (Hardware, Model, IP, Uptime)
- 🏷️ **Hostname management** with dynamic updates
- 🧹 **Automatic cleanup** of old device records
- 📈 **Performance monitoring** with memory management
- 🔄 **Device state tracking** with last-seen timestamps

### Web API
- 🌐 **RESTful API endpoints** for integration
- 🔐 **Token-based authentication** with MAC address binding
- 📊 **Device data export** in JSON format
- ⚙️ **Configuration management** through API calls

## 🛠️ System Requirements

### Hardware
- **Platform**: Raspberry Pi 3/4, Linux SBC, or x86 machine
- **Bluetooth**: BLE 4.0+ adapter required
- **Memory**: Minimum 512MB RAM
- **Storage**: 1GB+ available space

### Software
- **OS**: Linux (Ubuntu 18.04+, Raspberry Pi OS)
- **Python**: 3.8 or higher
- **Bluetooth**: BlueZ stack enabled
- **Network**: WiFi or Ethernet connectivity

### Supported Architectures
- ARM64 (Raspberry Pi 4)
- ARM32 (Raspberry Pi 3)
- x86_64 (Linux PCs)

## 📦 Installation

### Quick Setup (Linux/Raspberry Pi)

```bash
# 1. Clone the repository
git clone <repository-url>
cd PiScanner

# 2. Run the installation script
chmod +x EazyTraxGateway_Install.sh
./EazyTraxGateway_Install.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Run the application
python3 app.py
```

### Manual Installation

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev
sudo apt install -y bluez libbluetooth-dev build-essential

# 2. Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Dependencies

The application requires the following Python packages:

```
pandas          # Data manipulation and analysis
requests        # HTTP library
netifaces       # Network interface information
bleak           # BLE library for Python
flask           # Web framework
pyyaml          # YAML parser
python-dotenv   # Environment variable management
psutil          # System and process utilities
paho-mqtt       # MQTT client library
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# MQTT Configuration
MQTT_SERVER=172.19.2.11
MQTT_PORT=1883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password

# Authentication
TOKEN=your_access_token
AUTH_SECRET_KEY=your_secret_key
AUTH_TOKEN_EXPIRY=86400

# Proxy Settings (if needed)
PROXY=http://proxy.company.com:8080

# Application Settings
LOG_LEVEL=INFO
SCAN_INTERVAL=5
DEVICE_TIMEOUT=30
```

### MQTT Topics

The gateway publishes data to the following MQTT topics:

```
# Gateway telemetry data
Gateways/{gateway_mac}/Telemetry

# Individual device data
Bles/{device_mac}/Gateways/{gateway_mac}/Telemetry
```

### Device Configuration

Configure BLE scanning parameters in `app.py`:

```python
# Scanning interval (seconds)
SCAN_INTERVAL = 5

# Device timeout (seconds)
DEVICE_TIMEOUT = 30

# Data reporting interval (seconds)
REPORT_INTERVAL = 60
```

## 🌐 API Endpoints

### Authentication

```http
GET /api/token?mac=AA:BB:CC:DD:EE:FF
```

Generates a bearer token for API authentication.

**Response:**
```json
{
  "success": true,
  "token": "generated_token_here",
  "mac": "AABBCCDDEEFF",
  "expires_in": 86400
}
```

### Device Data

```http
GET /api
Authorization: Bearer <token>
```

Returns current BLE device data.

**Response:**
```json
{
  "meta": {
    "access_token": "token",
    "topic": "telemetry",
    "api_version": "2.0",
    "gateway_mac": "AA:BB:CC:DD:EE:FF"
  },
  "reporter": {
    "name": "eazytrax-gateway",
    "mac": "AA:BB:CC:DD:EE:FF",
    "hw_type": "Raspberry Pi 4",
    "ipv4": "192.168.1.100",
    "time": 1640995200,
    "publish_count": 42
  },
  "reported": [
    {
      "address": "11:22:33:44:55:66",
      "name": "IoT Sensor",
      "rssi": -65,
      "temperature": 23.5,
      "humidity": 60.2,
      "battery": 85,
      "last_seen": 1640995180
    }
  ]
}
```

### Hostname Management

```http
GET /api/hostname
Authorization: Bearer <token>
```

```http
POST /api/hostname
Authorization: Bearer <token>
Content-Type: application/json

{
  "hostname": "new-hostname"
}
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the Docker image
docker build -t eazytrax-gateway .

# Run the container
docker run -d \
  --name eazytrax-gateway \
  --privileged \
  --net=host \
  -v /var/run/dbus:/var/run/dbus \
  -e MQTT_SERVER=172.19.2.11 \
  -e TOKEN=your_token \
  eazytrax-gateway
```

### Docker Compose

```yaml
version: '3.8'
services:
  eazytrax-gateway:
    build: .
    container_name: eazytrax-gateway
    privileged: true
    network_mode: host
    volumes:
      - /var/run/dbus:/var/run/dbus
    environment:
      - MQTT_SERVER=172.19.2.11
      - TOKEN=your_token
    restart: unless-stopped
```

### Docker Requirements

- **Privileged mode**: Required for BLE access
- **Host networking**: Needed for BLE communication
- **D-Bus access**: Required for BlueZ interaction

## 🔧 Service Management

### Install as System Service

```bash
# Install the service
sudo ./EazyTraxGateway_Service.sh --install

# Check service status
sudo ./EazyTraxGateway_Service.sh --verify

# Uninstall the service
sudo ./EazyTraxGateway_Service.sh --uninstall
```

### Manual Service Control

```bash
# Start the service
sudo systemctl start EazyTraxGateway

# Stop the service
sudo systemctl stop EazyTraxGateway

# Check service status
sudo systemctl status EazyTraxGateway

# View service logs
sudo journalctl -u EazyTraxGateway -f
```

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BLE Devices   │    │  EazyTrax       │    │  MQTT Broker    │
│                 │◄──►│  Gateway        │───►│                 │
│  • Sensors      │    │                 │    │  • Data Storage │
│  • Beacons      │    │  • BLE Scanner  │    │  • Analytics    │
│  • IoT Devices  │    │  • Data Parser  │    │  • Dashboards   │
└─────────────────┘    │  • MQTT Client  │    └─────────────────┘
                       │  • Web API      │              │
                       └─────────────────┘              │
                                │                       │
                       ┌─────────────────┐              │
                       │  Web Dashboard  │◄─────────────┘
                       │                 │
                       │  • Device List  │
                       │  • Real-time    │
                       │  • Config       │
                       └─────────────────┘
```

### Data Flow

1. **BLE Scanning**: Continuous discovery of BLE devices
2. **Data Extraction**: Parse advertising data for sensor values
3. **Device Management**: Track device state and history
4. **MQTT Publishing**: Send data to MQTT broker
5. **API Serving**: Provide REST API for external access

### Class Structure

```python
BLEDevice           # Represents individual BLE device
├── Device data     # MAC, Name, RSSI, Last seen
├── Sensor data     # Temperature, Humidity, etc.
├── iBeacon data    # UUID, Major, Minor
└── Methods         # Update, JSON export

DeviceManager       # Manages device collection
├── Device storage  # In-memory device array
├── Cleanup logic   # Remove old devices
└── Data export     # Recent devices query

MQTTClient          # MQTT communication
├── Connection      # Auto-reconnect logic
├── Publishing      # Topic-based publishing
└── Error handling  # Retry mechanisms
```

## 🔍 Troubleshooting

### Common Issues

#### BLE Permission Issues
```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Set BLE permissions
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)
```

#### Bluetooth Service Issues
```bash
# Restart Bluetooth service
sudo systemctl restart bluetooth

# Check Bluetooth status
sudo systemctl status bluetooth

# Reset Bluetooth adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up
```

#### MQTT Connection Issues
```bash
# Test MQTT connectivity
mosquitto_pub -h 172.19.2.11 -t test -m "hello"

# Check network connectivity
ping 172.19.2.11

# Verify firewall settings
sudo ufw status
```

#### Memory Issues
```bash
# Monitor memory usage
free -h

# Check application memory
ps aux | grep python

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### Debug Mode

Enable debug logging:

```python
# In app.py
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

```bash
# Application logs
tail -f /var/log/eazytrax-gateway.log

# System logs
sudo journalctl -u EazyTraxGateway -f

# Bluetooth logs
sudo journalctl -u bluetooth -f
```

## 📊 Performance Optimization

### Memory Management
- Automatic cleanup of old device records
- Garbage collection after each scan cycle
- Efficient data structures for device storage

### Network Optimization
- MQTT connection pooling
- Batch publishing of device data
- Automatic reconnection handling

### BLE Optimization
- Adaptive scan intervals
- RSSI filtering for signal quality
- Service UUID caching

## 🔒 Security Considerations

### Authentication
- MAC address-based token generation
- Configurable token expiration
- Secure secret key management

### Network Security
- MQTT authentication support
- TLS encryption available
- Proxy support for corporate networks

### Data Privacy
- Local data processing
- Configurable data retention
- No personal data collection

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd PiScanner

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black .
flake8 .
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings for public methods
- Include unit tests for new features

### Submitting Changes
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**EazyTrax Gateway** - Bridging IoT devices to the cloud through intelligent BLE scanning and MQTT communication.

#!/bin/bash
set -e

echo "Installing EazyTrax App..."

# Install required packages
echo "install python3 python3-venv python3-pip wget python3-dev ..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip wget python3-dev

# Download the latest app archive
echo "Downloading latest version..."
#wget -O eazytrax-gateway.tar.gz https://eazytrax.com/downloads/eazytrax-gateway-latest.tar.gz


# Extract app
#tar xzf eazytrax-gateway.tar.gz EazyTraxGateway/
cd /home/EazyTrax/EazyTraxGateway

# Set up virtual environment
echo "Create Virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Install dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "-----------------------------------------------------------"
echo "EazyTrax Setup Clomplete... "
echo "to run execute..."
echo ""
echo "source venv/bin/activate"
echo "python3 app.py"
echo ""
echo "-----------------------------------------------------------"
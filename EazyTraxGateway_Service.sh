su #!/bin/bash
set -e

SERVICE_NAME=EazyTraxGateway
APP_DIR=/home/EazyTrax/EazyTraxGateway
ENV_FILE=${APP_DIR}/.env
PYTHON=${APP_DIR}/venv/bin/python
APP_FILE=${APP_DIR}/app.py
SERVICE_FILE=/etc/systemd/system/${SERVICE_NAME}.service

print_usage() {
    echo "Usage: $0 [--install | --uninstall | --verify]"
    echo "  --install    Register and start the EazyTrax service"
    echo "  --uninstall  Stop and remove the EazyTrax service"
    echo "  --verify     Check if the EazyTrax service exists and is active"
}

# ---------------------
# VERIFY MODE
# ---------------------
if [[ "$1" == "--verify" ]]; then
    echo "🔍 Verifying service '${SERVICE_NAME}'..."
    
    if systemctl list-units --type=service --all | grep -q "${SERVICE_NAME}.service"; then
        STATUS=$(systemctl is-active ${SERVICE_NAME})
        echo "✅ Service '${SERVICE_NAME}' exists. Status: ${STATUS}"
    else
        echo "❌ Service '${SERVICE_NAME}' does not exist."
        exit 1
    fi

    exit 0
fi

# ---------------------
# UNINSTALL MODE
# ---------------------
if [[ "$1" == "--uninstall" ]]; then
    echo "🧹 Uninstalling service '${SERVICE_NAME}'..."

    sudo systemctl stop ${SERVICE_NAME} || true
    sudo systemctl disable ${SERVICE_NAME} || true
    sudo rm -f ${SERVICE_FILE}
    sudo systemctl daemon-reload

    echo "✅ Service '${SERVICE_NAME}' uninstalled."
    exit 0
fi

# ---------------------
# INSTALL MODE (default if no argument or --install)
# ---------------------
if [[ -z "$1" || "$1" == "--install" ]]; then
    echo "🔧 Registering EazyTrax as a systemd service..."

    sudo tee ${SERVICE_FILE} > /dev/null <<EOF
[Unit]
Description=EazyTrax Gateway Service
After=network.target

[Service]
User=EazyTrax
WorkingDirectory=${APP_DIR}
ExecStart=${PYTHON} ${APP_FILE}
EnvironmentFile=${ENV_FILE}
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    sudo systemctl restart ${SERVICE_NAME}

    echo "✅ Service '${SERVICE_NAME}' registered and started!"
    echo "📄 Environment loaded from: ${ENV_FILE}"
    echo "📢 To check logs: sudo journalctl -u ${SERVICE_NAME} -f"
    exit 0
fi

# ---------------------
# Unknown Option
# ---------------------
echo "❌ Unknown option: $1"
print_usage
exit 1

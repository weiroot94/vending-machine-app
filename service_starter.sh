#!/bin/bash

# Your Flask application details
APP_NAME="vendingapp"
APP_USER=$(whoami)
APP_PATH=$(pwd)
REQUIREMENTS_FILE="${APP_PATH}/requirements.txt"
APP_SCRIPT="main.py"
LOG_FILE="${APP_PATH}/app.log"
VENV_PATH="${APP_PATH}/myworkenv"

# Activate the virtual environment
source ${VENV_PATH}/bin/activate

# Create the systemd service file
sudo tee "/etc/systemd/system/${APP_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Vending app
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_PATH}
Environment="PATH=${VENV_PATH}/bin:${PATH}"
ExecStartPre=/bin/bash -c 'source ${VENV_PATH}/bin/activate; pip install -r ${REQUIREMENTS_FILE}'
ExecStart=/bin/bash -c 'source ${VENV_PATH}/bin/activate; python ${APP_SCRIPT}'
StandardOutput=file:${LOG_FILE}
StandardError=file:${LOG_FILE}
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to read the new service file
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable ${APP_NAME}.service
sudo systemctl start ${APP_NAME}.service

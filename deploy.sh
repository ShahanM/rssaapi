#!/usr/bin/bash

SERVICE_USER=
APP_ROOT=
POETRY_EXEC=
SERVICE_NAME=

cat deploy/templates/rssa-api.service.template | envsubst \
    | sudo tee /etc/systemd/system/${SERVICE_NAME} > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo "Service deployed and started successfully."

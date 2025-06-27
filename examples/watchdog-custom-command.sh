#!/bin/bash

# The root (installation) directory of the server
SERVER_DIR="$HOME/servers/ets2-server"
# Server log file, assuming the 'Euro Truck Simulator 2' home directory is inside the server root directory
LOG_FILE="$SERVER_DIR/Euro Truck Simulator 2/server.log.txt"

# Example with Docker container named 'ets2-server'
python3 ets2_server_watchdog.py --command 'docker restart ets2-server' "$LOG_FILE"

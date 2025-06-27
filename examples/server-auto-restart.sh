#!/bin/bash

# The root (installation) directory of the server
SERVER_DIR="$HOME/servers/ets2-server"
cd "$SERVER_DIR"

export LD_LIBRARY_PATH="$SERVER_DIR/linux64"
# The server will generate the 'Euro Truck Simulator 2' home directory inside the server root directory
export XDG_DATA_HOME="$SERVER_DIR"

while true; do
    ./bin/linux_x64/eurotrucks2_server
    echo 'Restarting the server in 3 seconds, press Ctrl-C to abort'
    sleep 3
done

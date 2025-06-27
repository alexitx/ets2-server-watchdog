# ETS2 Server Watchdog

Monitoring script for a [Euro Truck Simulator 2 dedicated server][ets2-dedicated-server] that detects and stops the
server in rare cases where it hangs during startup or loses connection to Steam, allowing it to be restarted
automatically. Currently supports Linux only.


## Table of contents

- [Installation](#installation)
- [Usage](#usage)
    - [Watchdog script](#watchdog-script)
    - [ETS2 server](#ets2-server)
    - [CLI arguments](#cli-arguments)
- [License](#license)


## Installation

Requirements:
- Python 3.9+
- Any modern Linux distribution

1. Clone or download the repository

    ```sh
    git clone https://github.com/alexitx/ets2-server-watchdog
    cd ets2-server-watchdog
    ```

2. Create a virtual environment using [virtualenv][virtualenv] or [venv][venv]

    ```sh
    python3 -m virtualenv venv
    source ./venv/bin/activate
    ```

3. Install dependencies

    ```sh
    pip install -r requirements.txt
    ```


## Usage

Run the server and watchdog script in separate terminals, screen/tmux sessions, or however is most convenient. The
watchdog must be run as the same user as the server, or as root, to allow it to find the process of the server.

If the server is running inside Docker or any other sandboxed environment, you can pass custom command to the watchdog
script using `--command` to be run whenever the server should be restarted. Make sure the server log file is accessible
on disk and that the watchdog has appropriate permissions to read it.

See [example scripts][examples].

### Watchdog script

```sh
python3 ets2_server_watchdog.py <server log file>
```

The server log file is in the `Euro Truck Simulator 2` home directory, which is automatically created on server start in
`$HOME` or `$XDG_DATA_HOME`.

### ETS2 server

1.  Create a start script for the ETS2 server that ensures the correct working directory for the server, has all
    environment variables set, such as `$LD_LIBRARY_PATH` or `$XDG_DATA_HOME` (to set the location of the `Euro Truck
    Simulator 2` config directory), and runs the server executable.

    Example:
    ```sh
    #!/bin/bash

    SERVER_DIR="$HOME/servers/ets2-server"
    cd "$SERVER_DIR"

    export LD_LIBRARY_PATH="$SERVER_DIR/linux64"
    export XDG_DATA_HOME="$SERVER_DIR"

    ./bin/linux_x64/eurotrucks2_server
    ```

2.  Wrap the executable call in a loop instead and add a small timeout after the server stops but before it restarts to
    allow exiting the script with Ctrl-C.

    Before:
    ```sh
    ./bin/linux_x64/eurotrucks2_server
    ```

    After:
    ```sh
    while true; do
        ./bin/linux_x64/eurotrucks2_server
        echo 'Restarting the server in 3 seconds, press Ctrl-C to abort'
        sleep 3
    done
    ```

### CLI arguments

| Argument              | Default | Required | Description                                                                                         |
|-----------------------|---------|----------|-----------------------------------------------------------------------------------------------------|
| `--debug`             |         | No       | Log debug messages                                                                                  |
| `--debug-tail`        |         | No       | If debug is enabled, also log tail command output                                                   |
| `--hang-timeout`      | `1.0`   | No       | Time in seconds for the server to hang on initialization before being killed                        |
| `--reconnect-timeout` | `300.0` | No       | Time in seconds for the server to reconnect to Steam before being stopped                           |
| `--stop-timeout`      | `5.0`   | No       | Time in seconds for the server to stop gracefully before being killed                               |
| `--monitor-interval`  | `0.25`  | No       | Interval in seconds for monitoring log line changes; Should be < other timeout values, usually < 1s |
| `--command`           |         | No       | Custom command to run instead of finding and stopping the server process                            |
| `server_log`          |         | Yes      | Server log file                                                                                     |


## License

MIT license. See [LICENSE][license] for more information.


[ets2-dedicated-server]: https://modding.scssoft.com/wiki/Documentation/Tools/Dedicated_Server
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[venv]: https://docs.python.org/3/library/venv.html
[examples]: https://github.com/alexitx/ets2-server-watchdog/tree/master/examples
[license]: https://github.com/alexitx/ets2-server-watchdog/blob/master/LICENSE

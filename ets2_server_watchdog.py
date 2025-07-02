__version__ = '0.2.0'


import argparse
import logging
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil


log = logging.getLogger('ets2-server-watchdog')


def setup_logging(debug=False):
    level = logging.INFO if not debug else logging.NOTSET
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)


def start_tail(log_file):
    log.debug('Starting tail process')
    process = subprocess.Popen(
        ('tail', '-F', '-n', '0', '--retry', '--', str(log_file)),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    os.set_blocking(process.stdout.fileno(), False)
    return process


def stop_tail(tail_process):
    log.debug('Stopping tail process')
    tail_process.terminate()
    tail_process.wait()


def find_server_process(log_file):
    for process in psutil.process_iter():
        if process.info.name() != 'eurotrucks2_server':
            continue

        open_files = process.open_files()
        if open_files is not None and str(log_file) in (of.path for of in open_files):
            log.debug(
                f"Server process found, PID: {process.pid}, Executable: {process.exe()} "
                f"Command line: {process.cmdline()}"
            )
            return process

    return None


def stop_server_process(process, timeout, kill=False):
    log.debug(f'Stopping server process, {timeout=}, {kill=}')
    if kill:
        process.kill()
    else:
        process.terminate()
    try:
        process.wait(timeout)
    except psutil.TimeoutExpired:
        log.warning(f'Server did not stop within {timeout}s, killing process')
        process.kill()
        process.wait()


def find_and_stop_server_process(log_file, timeout, kill=False):
    log.info('Searching for server process')
    process = find_server_process(log_file)
    if process is None:
        log.error('Server process not found')
        return
    log.info(f"{'Killing' if kill else 'Stopping'} server process")
    stop_server_process(process, timeout, kill)


def main():
    if sys.platform != 'linux':
        print('Only Linux platform is supported')
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=f'ets2-server-watchdog {__version__}')
    parser.add_argument('--debug', action='store_true', help='Log debug messages')
    parser.add_argument('--debug-tail', action='store_true', help='If debug is enabled, also log tail command output')
    parser.add_argument('--server-log', required=True, help='Server log file')
    parser.add_argument(
        '--hang-timeout',
        default=1.0,
        type=float,
        help='Time in seconds for the server to hang on initialization before being killed'
    )
    parser.add_argument(
        '--reconnect-timeout',
        default=300.0,
        type=float,
        help='Time in seconds for the server to reconnect to Steam before being stopped'
    )
    parser.add_argument(
        '--stop-timeout',
        default=5.0,
        type=float,
        help='Time in seconds for the server to stop gracefully before being killed'
    )
    parser.add_argument(
        '--monitor-interval',
        default=0.25,
        type=float,
        help='Interval in seconds for monitoring log line changes; Should be < other timeout values, usually < 1s'
    )
    parser.add_argument(
        '--command',
        help='Custom shell command to run instead of finding and stopping the server process'
    )
    args = parser.parse_args()

    if args.hang_timeout < 1.0:
        parser.error('--hang-timeout: Value cannot be lower than 1.0')
    if args.reconnect_timeout < 1.0:
        parser.error('--reconnect-timeout: Value cannot be lower than 1.0')
    if args.stop_timeout < 1.0:
        parser.error('--stop-timeout: Value cannot be lower than 1.0')

    custom_command = args.command is not None
    if custom_command:
        command = args.command.strip()
        if not command:
            parser.error('--command: Invalid value')
        try:
            command_args = shlex.split(command)
        except ValueError as e:
            parser.error(f'--command: Invalid value: {e}')

    setup_logging(args.debug)

    server_log_file = Path(args.server_log).resolve()
    log.info(f"Server log file: '{server_log_file}'")

    server_hanging = False
    server_hang_time = 0
    server_steam_disconnected = False
    server_steam_disconnected_time = 0

    regex_steam_disconnected = re.compile(r'^[\d\:\.]+ : \[MP\] Steam disconnected')

    tail = start_tail(server_log_file)

    signal.signal(signal.SIGINT, lambda *_: stop_tail(tail))
    signal.signal(signal.SIGTERM, lambda *_: stop_tail(tail))

    log.info('Monitoring')

    while tail.poll() is None:
        line = tail.stdout.readline()
        if line:
            if args.debug_tail:
                log.debug(line)

            if line.endswith('[MP] Init steam game server params\n'):
                log.info('Server is initializing')
                server_hanging = True
                server_hang_time = time.time()
            elif line.endswith('[MP] Session running.\n'):
                log.info('Server started')
                server_hanging = False
            elif regex_steam_disconnected.match(line):
                log.info('Server lost connection to Steam')
                server_steam_disconnected = True
                server_steam_disconnected_time = time.time()
            elif line.endswith('[MP] Steam connected\n'):
                log.info('Server connected to Steam')
                server_steam_disconnected = False

            continue

        if server_hanging and time.time() - server_hang_time > args.hang_timeout:
            log.info(f'Server is hanging for longer than {args.hang_timeout}s')
            server_hanging = False

            if custom_command:
                log.info(f"Running '{command}'")
                subprocess.run(command_args)
            else:
                find_and_stop_server_process(server_log_file, args.stop_timeout, True)

        elif server_steam_disconnected and time.time() - server_steam_disconnected_time > args.reconnect_timeout:
            log.info(f'Server did not reconnect to Steam within {args.reconnect_timeout}s')
            server_steam_disconnected = False

            if custom_command:
                log.info(f"Running '{command}'")
                subprocess.run(command_args)
            else:
                find_and_stop_server_process(server_log_file, args.stop_timeout)

        time.sleep(args.monitor_interval)


if __name__ == '__main__':
    main()

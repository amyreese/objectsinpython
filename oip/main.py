# Copyright 2019 John Reese
# Licensed under the MIT license


import sys
from sys import stdin, stdout

from cpgame import start
from supervisor import runtime

from .serial import ALL_COMMANDS, DESCRIPTIONS, VERSION

try:
    from typing import Callable, Dict
except ImportError:
    pass

NIB = "NIB"
NIN = "NIN"
NIF = "NIF"


class OIP:
    def __init__(self):
        self.active = False
        self.rx_data = ""
        self.rx_time = 0
        self.inputs = {}  # type: Dict[str, (int, int)]  # cmd->(channel, fmt)
        self.input_map = {}  # type: Dict[int, List[Callable]]  # channel->function
        self.commands = {
            key: idx for key, idx in enumerate(ALL_COMMANDS, 1)
        }  # type: Dict[str, int]  # cmd->channel

    def execute(self, command):
        # type: (str) -> None
        if command not in self.commands:
            raise ValueError("Command {} not registered".format(command))

        if not self.active:
            pass

        channel = self.commands[command]
        self.send("EXC={}".format(channel))

    def on(self, key, fmt=NIB, fn=None):
        # type: (str, str, Callable) -> None
        def wrapper(fn):
            channel = self.new_input(key, fmt)

            if channel not in self.input_map:
                self.input_map[channel] = [fn]
            else:
                self.input_map[channel].append(fn)

            return fn

        if fn:
            return wrapper(fn)
        else:
            return fn

    def start(self):
        every(0.05, self.read)
        return start()

    def dispatch(self, now, command):
        # type: (float, str) -> None
        if command == "452":
            self.sync()
            return

        self.rx_time = now
        key, _, value = command.partition("=")
        channel, fmt = self.inputs[key]
        fn = self.input_map[key]

        if fmt == NIB:
            fn(now, bool(value))
        elif fmt == NIN:
            fn(now, int(value))
        elif fmt == NIF:
            fn(now, float(value))

    def read(self, now):
        # type: (float) -> None
        """
        Read character by character from stdin when bytes available to prevent blocking.
        When a whole line has been read (current character is newline), run dispatcher.
        """
        while runtime.serial_bytes_available:
            char = stdin.read(1)
            if char == "\r":
                pass
            elif char == "\n":
                command = self.rx_data.strip()
                if command:
                    self.dispatch(now, command)
                self.rx_data = ""
            else:
                self.rx_data += char

    def send(self, command):
        # type: (str) -> None
        if not command.endswith("\n"):
            command += "\n"
        stdout.write(command)

    def sync(self):
        for cmd, (channel, fmt) in self.inputs.items():
            self.send("{}={},{}".format(fmt, cmd, channel))

        for cmd, channel in self.commands.items():
            self.send("CMD={},{}".format(cmd, channel))

        self.send("ACT")
        self.active = True

    def new_input(self, key, fmt):
        # type: (str, int) -> int
        if fmt not in (NIB, NIN, NIF):
            raise ValueError("Invalid fmt, must be NIB/NIN/NIF")

        if key in self.inputs:
            return self.inputs[key][0]

        channel = len(self.inputs) + 1
        self.inputs[key] = (channel, fmt)
        return channel

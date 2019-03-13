# Copyright 2019 John Reese
# Licensed under the MIT license


import gc
import sys
from sys import stdin, stdout
from time import monotonic

from supervisor import runtime

from .serial import ALL_COMMANDS, VERSION

try:
    from typing import Callable, Dict
except ImportError:
    pass

NIB = "NIB"
NIN = "NIN"
NIF = "NIF"


def sort_by_channel(item):
    value, channel = item
    return channel


class OIP:
    def __init__(self):
        self.active = False
        self.rx_data = ""
        self.rx_time = 0
        self.tx_time = 0
        self.inputs = {}  # type: Dict[(str, str), int]  # cmd->(channel, fmt)
        self.input_fmt = {}  # type: Dict[int, str]  # channel->fmt
        self.input_hooks = {}  # type: Dict[int, List[Callable]]
        self.commands = {
            key: idx for idx, key in enumerate(ALL_COMMANDS, 1)
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
        # type: (str, str, Callable) -> Callable
        def wrapper(fn):
            # type: (Callable) -> Callable
            channel = self.new_input(key, fmt)

            if channel not in self.input_hooks:
                self.input_hooks[channel] = [fn]
            else:
                self.input_hooks[channel].append(fn)

            return fn

        if fn:
            return wrapper(fn)
        else:
            return wrapper

    def start(self):
        # type: () -> None
        while True:
            now = monotonic()
            self.read(now)
            if not self.active and now > (self.tx_time + 2):
                self.send("451")
                self.tx_time = now
            gc.collect()

    def dispatch(self, now, command):
        # type: (float, str) -> None
        if command == "452":
            self.sync()
            return

        if command == "GC":
            self.send(
                "DBG=Memory Allocated: {} - Free: {}".format(
                    gc.mem_alloc(), gc.mem_free()  # type: ignore
                )
            )
            return

        self.rx_time = now
        try:
            c, _, value = command.partition("=")
            channel = int(c)

            fmt = self.input_fmt[channel]
            fns = self.input_hooks[channel]

            self.send("DBG=received {} {}={}".format(fmt, channel, value))

            if fmt == NIB:
                value = bool(int(value))  # type: ignore
            elif fmt == NIN:
                value = int(value)  # type: ignore
            elif fmt == NIF:
                value = float(value)  # type: ignore

            for fn in fns:
                self.send("DBG=dispatch {} {}={}".format(fmt, channel, value))
                fn(now, value)

        except Exception as e:
            self.send("DBG=exception on dispatch: {}".format(repr(e)))

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
        # type: () -> None
        self.send("DBG=Objects In Python built for Objects In Space {}".format(VERSION))

        for (cmd, fmt), channel in sorted(self.inputs.items(), key=sort_by_channel):
            self.send("{}={},{}".format(fmt, cmd, channel))

        gc.collect()

        for cmd, channel in sorted(self.commands.items(), key=sort_by_channel):
            self.send("CMD={},{}".format(cmd, channel))

        gc.collect()

        self.send("ACT")
        self.active = True

    def new_input(self, name, fmt):
        # type: (str, str) -> int
        if fmt not in (NIB, NIN, NIF):
            raise ValueError("Invalid fmt, must be NIB/NIN/NIF")

        key = (name, fmt)
        if key in self.inputs:
            return self.inputs[key]

        channel = len(self.inputs) + 1
        self.inputs[key] = channel
        self.input_fmt[channel] = fmt
        return channel

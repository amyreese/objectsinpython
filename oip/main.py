# Copyright 2019 John Reese
# Licensed under the MIT license


import gc
import sys
from sys import stdin, stdout
from time import monotonic

from digitalio import DigitalInOut, Direction, Pull
from supervisor import runtime
from touchio import TouchIn

from .serial import ALL_COMMANDS, VERSION

try:
    from typing import Callable, Dict, List, Tuple
except ImportError:
    pass

NIB = "NIB"
NIN = "NIN"
NIF = "NIF"
DEBOUNCE = 0.02  # how long to wait on up/down changes
REPEAT = object()
INTERVAL = 0.1


class OIP:
    def __init__(self):
        self.active = False
        self.rx_data = ""
        self.rx_time = 0
        self.tx_time = 0
        self.inputs = {}  # type: Dict[int, (DigitalInOut, bool, float)]
        self.input_hooks = {}  # type: Dict[int, List[Callable]] # pin->fn
        self.numerics = {}  # type: Dict[(str, str), int]  # cmd->(channel, fmt)
        self.numeric_fmt = {}  # type: Dict[int, str]  # channel->fmt
        self.numeric_hooks = {}  # type: Dict[int, List[Callable]]
        self.commands = {
            key: idx for idx, key in enumerate(ALL_COMMANDS, 1)
        }  # type: Dict[str, int]  # cmd->channel

    def execute(self, command):
        # type: (str) -> None
        """
        Execute the given command.
        """
        if command not in self.commands:
            raise ValueError("Command {} not registered".format(command))

        if not self.active:
            return

        channel = self.commands[command]
        self.send("EXC={}".format(channel))

    def on(self, key, fmt=NIB, fn=None):
        # type: (str, str, Callable) -> Callable
        """
        Register callback when the given boolean or numeric value changes.
        """

        def wrapper(fn):
            # type: (Callable) -> Callable
            channel = self.new_input(key, fmt)

            if channel not in self.numeric_hooks:
                self.numeric_hooks[channel] = [fn]
            else:
                self.numeric_hooks[channel].append(fn)

            return fn

        if fn:
            return wrapper(fn)
        else:
            return wrapper

    def press(self, button, touch=False, fn=None):
        # type: (DigitalInOut, bool, Callable) -> Callable
        def wrapper(fn):
            # type: (Callable) -> Callable
            btn_id = id(button)
            if btn_id not in self.inputs:
                if touch:
                    dio = TouchIn(button)
                else:
                    dio = DigitalInOut(button)
                    dio.direction = Direction.INPUT
                    dio.pull = Pull.DOWN
                self.inputs[btn_id] = (dio, False, 0)

            if btn_id not in self.input_hooks:
                self.input_hooks[btn_id] = [fn]
            else:
                self.input_hooks[btn_id].append(fn)
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
            self.debounce(now)
            if self.active and now > (self.rx_time + 15):  # timeout, retry handshake
                self.send("DBG=Timeout, retrying handshake")
                self.active = False
            if not self.active and now > (self.tx_time + 2):
                self.send("451")
                self.tx_time = now
            gc.collect()

    def dispatch(self, now, command):
        # type: (float, str) -> None
        self.rx_time = now
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

        try:
            c, _, value = command.partition("=")
            channel = int(c)

            fmt = self.numeric_fmt[channel]
            fns = self.numeric_hooks[channel]

            if fmt == NIB:
                value = bool(int(value))  # type: ignore
            elif fmt == NIN:
                value = int(value)  # type: ignore
            elif fmt == NIF:
                value = float(value)  # type: ignore

            for fn in fns:
                fn(now, value)

        except Exception as e:
            # self.send("DBG=exception on dispatch: {}".format(repr(e)))
            pass

    def debounce(self, now):
        # type: (float) -> None
        for btn_id in list(self.inputs):
            dio, last, ts = self.inputs[btn_id]
            value = dio.value
            if value != last:  # start debouncing
                self.inputs[btn_id] = (dio, value, now)
            elif ts and now > (ts + DEBOUNCE):  # debounce limit reached, trigger action
                self.inputs[btn_id] = (dio, value, 0)
                for fn in self.input_hooks[btn_id]:
                    if fn(now, value) == REPEAT:
                        self.inputs[btn_id] = (dio, value, now + INTERVAL)
                    gc.collect()

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

        for (cmd, fmt), channel in self.numerics.items():
            self.send("{}={},{}".format(fmt, cmd, channel))

        gc.collect()

        for cmd, channel in self.commands.items():
            self.send("CMD={},{}".format(cmd, channel))

        gc.collect()

        self.send("ACT")
        self.active = True

    def new_input(self, name, fmt):
        # type: (str, str) -> int
        if fmt not in (NIB, NIN, NIF):
            raise ValueError("Invalid fmt, must be NIB/NIN/NIF")

        key = (name, fmt)
        if key in self.numerics:
            return self.numerics[key]

        channel = len(self.numerics) + 1
        self.numerics[key] = channel
        self.numeric_fmt[channel] = fmt
        return channel

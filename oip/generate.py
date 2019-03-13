# Copyright 2019 John Reese
# Licensed under the MIT license

"""
Regenerate the command lists from serial_commands.txt

Usage:

    python3 -m oip <serial_commands.txt>

"""

import re
import sys
from pathlib import Path
from pprint import pformat
from typing import Any, Dict

import black

try:
    from typing import Dict, Union, Tuple

    Commands = Dict[str, Dict[str, str]]
except ImportError:
    pass

VERSION_RE = re.compile(r"SERIAL OUTPUT COMMAND LIST - (\S+)")
HEADER_RE = re.compile(r"(.+):$")
COMMAND_RE = re.compile(r"(COMMAND|FUNCTION): (\S+)")
DESCRIPTION_RE = re.compile(r"DESCRIPTION: (.+)")


def generate_metadata(path: Path) -> Tuple[Commands, str]:
    metadata = {
        "numeric": {},
        "boolean": {},
        "command": {},
    }  # type: Dict[str, Dict[str, str]]
    version = ""
    section = ""
    key = ""
    with open(path.as_posix()) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue

            match = VERSION_RE.match(line)
            if match:
                version = match.group(1)
                continue

            match = HEADER_RE.match(line)
            if match:
                word, _, _ = match.group(1).lower().partition(" ")
                section = {
                    "numerical": "numeric",
                    "boolean": "boolean",
                    "ship": "command",
                }[word]
                continue

            match = COMMAND_RE.match(line)
            if match:
                key = match.group(2)
                metadata[section][key] = ""
                continue

            match = DESCRIPTION_RE.match(line)
            if match:
                description = match.group(1)
                metadata[section][key] = description
                continue

            print("Line did not match any patterns: {0}".format(line))

    return metadata, version


def write_metadata(metadata: Commands, version: str, tiny: bool = False) -> None:
    path_in = Path(__file__).parent / ("serial.py.in.tiny" if tiny else "serial.py.in")
    path_out = Path(__file__).parent / "serial.py"

    tpl = '    {0} = "{0}"'
    descriptions = pformat(
        {**metadata["numeric"], **metadata["boolean"], **metadata["command"]}, width=160
    )
    numerics = "\n".join(tpl.format(key) for key in metadata["numeric"])
    booleans = "\n".join(tpl.format(key) for key in metadata["boolean"])
    commands = "\n".join(tpl.format(key) for key in metadata["command"])
    all_commands = pformat(list(metadata["command"]))
    kwargs = {
        "version": version,
        "descriptions": descriptions,
        "numeric": numerics,
        "boolean": booleans,
        "command": commands,
        "all_commands": all_commands,
    }

    with open(path_in.as_posix()) as fh:
        output = fh.read().format(**kwargs)

    output = black.format_str(output, 88)

    with open(path_out.as_posix(), "w") as fh:
        fh.write(output)


if 2 > len(sys.argv) > 3:
    print("Usage: {0} [--tiny] <serial_commands.txt>".format(sys.argv[0]))
    exit(1)


tiny = False
if sys.argv[-2] == "--tiny":
    tiny = True

command_text = Path(sys.argv[-1])
if not command_text.exists():
    print("Serial command list {0} not found".format(command_text))
    exit(1)

metadata, version = generate_metadata(command_text)
write_metadata(metadata, version, tiny=tiny)

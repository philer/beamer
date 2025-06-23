#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple tool for toggling and positioning a second monitor (or projector) on Linux.

Usage:
    beamer [COMMAND]

COMMANDs:
    info   Print details and exit (default)
    clone  Mirror the first monitor to the second
    left | right | above | below
           Display the second monitor beside the first
    off    Only activate the first monitor
    only   Only activate the second monitor
    row [output...]
           Specify a custom row (mostly for more than two monitors)
"""

__title__ = "beamer"
__version__ = "0.2.0"
__license__ = "MIT"
__status__ = "Development"

__author__ = "Philipp Miller"
__email__ = "me@philer.org"
__copyright__ = "Copyright 2019-2024 Philipp Miller"


import os
import re
import subprocess
import sys
from itertools import chain
from math import ceil
from typing import Any, ClassVar, Iterable, Optional, cast
from pydantic import BaseModel


def chunk(iterable, size):
    """Split an iterable into tuples of equal length (last may be shorter)."""
    try:
        for index in range(0, len(iterable), size):
            yield iterable[index:index + size]
    except TypeError:
        it = iter(iterable)
        current_chunk = tuple(next(it) for _ in range(size))
        while current_chunk:
            yield current_chunk
            current_chunk = tuple(next(it) for _ in range(size))


def list_to_columns(strings, *, sep=" ", indent=""):
    """Stringify a sequence into columns fitting into a terminal `ls` style."""
    max_len = max(map(len, strings))
    term_width = os.get_terminal_size().columns
    columns = (term_width - len(indent)) // (max_len + len(sep))
    lines = ceil(len(strings) / columns)
    return "\n".join(indent + sep.join(s.rjust(max_len)
                                       for s in strings[lineno::lines])
                     for lineno in range(lines))


def info(msg):
    """Print an info message."""
    print(f"\033[1;32m{msg}\033[0m")

def error(msg):
    """Print an error message."""
    print(f"\033[1;31m{msg}\033[0m")


def run_cmd(args: tuple[str, ...], echo=True):
    """Execute a command line utility and return the output."""
    if echo:
        info(" ".join(args))
    try:
        result = subprocess.run(args,
                                check=True,
                                universal_newlines=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        error("subprocess '" + " ".join(args) + "' failed:")
        error(cpe.stdout)
        return cpe.stdout
    else:
        if echo:
            print(result.stdout, end="")
        return result.stdout


def _sscanf(string, regex, casts) -> Optional[dict[str, Any]]:
    """Weird sscanf type thing using regex"""
    match = regex.match(string)
    if match is None:
        return None
    result = dict()
    for key, value in match.groupdict().items():
        try:
            result[key] = casts[key](value)
        except TypeError:
            pass
    return result


class Mode(BaseModel, frozen=True):
    """Respresents a single monitor's resolution setting."""
    width: int
    height: int
    frequency: float
    active: bool
    preferred: bool

    _xrandr_regex: ClassVar = re.compile(
        r"""
        \s+(?P<width>\d+)x(?P<height>\d+)
        \s+(?P<frequency>\d+\.\d+)
        (?P<active>\*)?
        (?P<preferred>\+)?
        """,
        flags=re.ASCII|re.VERBOSE
    )

    _xrandr_casts: ClassVar = {
        'width': int,
        'height': int,
        'frequency': float,
        'active': bool,
        'preferred': bool,
    }


class Output(BaseModel, frozen=True):
    """Represents a monitor connection."""
    name: str
    connected: bool
    primary: bool
    width: Optional[int] = None
    height: Optional[int] = None
    xoffset: Optional[int] = None
    yoffset: Optional[int] = None
    info: str
    physical_size: str
    modes: tuple[Mode, ...]

    _xrandr_regex: ClassVar = re.compile(
        r"""
        (?P<name>\S+)
        \ (?P<connected>(?:dis)?connected)
        (?P<primary>\ primary)?
        (?:\ (?P<width>\d+)x(?P<height>\d+)
             (?P<xoffset>[+-]\d+)(?P<yoffset>[+-]\d+)
        )?
        \ \((?P<info>.*?)\)
        (?:\ (?P<physical_size>.*))?
        """,
        flags=re.ASCII|re.VERBOSE,
    )

    _xrandr_casts: ClassVar = {
        'name': str,
        'connected': lambda x: x == "connected",
        'primary': bool,
        'width': int,
        'height': int,
        'xoffset': int,
        'yoffset': int,
        'info': str,
        'physical_size': str,
    }


def scan_xrandr_outputs(echo=True) -> Iterable[Output]:
    """Iterate data of all outputs by parsing `xrandr --query`."""
    lines = run_cmd(("xrandr", "--query"), echo=echo).split("\n")[1:]

    current_output: Optional[dict[str, Any]]
    while (current_output := _sscanf(lines.pop(0), Output._xrandr_regex, Output._xrandr_casts)) is None:
        pass

    modes: list[Mode] = []
    for line in filter(None, lines):
        if new_output := _sscanf(line, Output._xrandr_regex, Output._xrandr_casts):
            yield Output(**current_output, modes=tuple(modes))
            current_output, modes = new_output, []
        elif mode := _sscanf(line, Mode._xrandr_regex, Mode._xrandr_casts):
            modes.append(Mode.model_validate(mode))

    yield Output(**current_output, modes=tuple(modes))


def connected_outputs(echo=False) -> Iterable[Output]:
    """Iterate outputs filtered by connection status."""
    for output in scan_xrandr_outputs(echo=echo):
        if output.connected:
            yield output


def beamer_info():
    for index, output in enumerate(connected_outputs(), start=1):
        info(f"{index}: {output.name}")
        modes = [f"{'*' if m.active else ''}{m.width}x{m.height}" for m in output.modes]
        print(list_to_columns(modes, indent="  "))


def beamer_clone_args() -> Optional[tuple[str, ...]]:
    """xrandr arguments for cloning to all connected outputs."""
    outputs = tuple(connected_outputs())
    print(f"Cloning to {len(outputs)} outputs.")
    resolutions = set[tuple[int, int]].intersection(*({(md.width, md.height) for md in out.modes} for out in outputs))
    try:
        width, height = max(resolutions)
    except ValueError:
        return print("no matching resolution found")
    mode = f"{width}x{height}"
    return ("xrandr", "--output", outputs[0].name, "--mode", mode,
            *chain.from_iterable(("--output", out.name,
                                  "--mode", mode,
                                  "--same-as", outputs[0].name)
                                 for out in outputs[1:])
            )


def beamer_side_args(side) -> Optional[tuple[str, ...]]:
    """xrandr arguments for putting one output next to the other."""
    side_parameters = {
        "left": "--left-of",
        "right": "--right-of",
        "above": "--above",
        "below": "--below",
    }
    outputs = tuple(connected_outputs())
    if len(outputs) != 2:
        return print(f"Which outputs should I use? Found {len(outputs)}")
    return ("xrandr", "--output", outputs[0].name, "--auto",
            "--output", outputs[1].name, "--auto",
            side_parameters[side], outputs[0].name)


def beamer_single_output_args(index=0) -> Optional[tuple[str, ...]]:
    """xrandr arguments for turning off all outputs except one."""
    try:
        activate, *outputs = connected_outputs()
    except ValueError:
        return print(f"No output with index {index} connected")
    return ("xrandr", "--output", activate.name, "--auto",
            *chain.from_iterable(("--output", out.name, "--off")
                                 for out in outputs)
            )


def beamer_row_args(row: list[str]) -> Optional[tuple[str, ...]]:
    """xrandr arguments for arranging multiple outputs."""
    if not row:
        error(f"No outputs specified")
        return None

    outputs = tuple(connected_outputs())
    outputs_by_name = {output.name: output for output in outputs}

    # Using list instead of set so xrandr can display an appropriate error
    # in case of duplicate entries
    row_outputs = list[Output]()
    for entry in row:
        if primary := entry.endswith("!"):
            entry = entry[:-1]
        try:
            output = outputs[int(entry) - 1]
        except IndexError:
            error(f"Could not find output number {int(entry) - 1}")
            return None
        except ValueError:
            try:
                output = outputs_by_name[entry]
            except KeyError:
                error(f"Could not find output '{entry}'")
                return None
        row_outputs.append(output.model_copy(update=dict(primary=primary)))

    row_output_names = {out.name for out in row_outputs}
    return (
        # leftmost for reference - throws IndexError
        "xrandr", "--output", row_outputs[0].name, "--auto",
        # relative positions
        *chain.from_iterable(
            ["--output", out.name, "--auto", "--right-of", left.name]
            + (["--primary"] if out.primary else [])
            for left, out in zip(row_outputs, row_outputs[1:])
        ),
        # turn off unused
        *chain.from_iterable(
            ("--output", out.name, "--off")
            for out in outputs if out.name not in row_output_names
        ),
    )


def main():
    """Run the CLI."""
    cmd: Optional[tuple[str, ...]] = None
    match sys.argv[1:]:
        case ["info"] | []:
            return beamer_info()
        case ["off"]:
            cmd = beamer_single_output_args(index=0)
        case ["only"]:
            cmd = beamer_single_output_args(index=1)
        case ["clone"]:
            cmd = beamer_clone_args()
        case ["left"| "right"| "above"| "below" as command]:
            cmd = beamer_side_args(command)
        case ["row", *row]:
            cmd = beamer_row_args(row)
        case _:
            error(cast(str, __doc__).strip())

    if cmd is None:
        return 1

    print(run_cmd(cmd))


if __name__ == "__main__":
    sys.exit(main())

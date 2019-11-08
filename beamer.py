#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple tool for toggling and positioning a secondary monitor or projector on Linux.

Usage:
    beamer [info|query|clone|left|right|above|below|off|only] [-r|--retry]

Options
    -r --retry    Retry failed commands every second until they succeed.
"""

__title__ = "beamer"
__version__ = "0.2.0"
__license__ = "MIT"
__status__ = "Development"

__author__ = "Philipp Miller"
__email__ = "me@philer.org"
__copyright__ = "Copyright 2019 Philipp Miller"


import sys
import os
import re
import subprocess
from math import ceil
from time import sleep
from itertools import chain


class ObjectDict(dict):
    """Dictionary with dot access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError from None

    def __setattr__(self, key, value):
        self[key] = value


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
    """stringify a sequence into columns fitting into a terminal `ls` style."""
    max_len = max(map(len, strings))
    term_width = os.get_terminal_size().columns
    columns = (term_width - len(indent)) // (max_len + len(sep))
    lines = ceil(len(strings) / columns)
    return "\n".join(indent + sep.join(s.rjust(max_len)
                                       for s in strings[lineno::lines])
                     for lineno in range(lines))


def info(msg):
    """Print an info message and exit."""
    print("\033[1;32m" + str(msg) + "\033[0m")

def error(msg):
    """Print an error message."""
    print("\033[1;31m" + str(msg) + "\033[0m")


def run_cmd(*args, echo=True):
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


def _sscanf(string, regex, casts):
    """Weird sscanf type thing using regex"""
    match = regex.match(string)
    if match is None:
        return None
    result = ObjectDict()
    for key, value in match.groupdict().items():
        try:
            result[key] = casts[key](value)
        except TypeError:
            pass
    return result


xrandr_output_regex = re.compile(r"""
    (?P<name>\S+)
    \ (?P<connected>(?:dis)?connected)
    (?P<primary>\ primary)?
    (?:\ (?P<width>\d+)x(?P<height>\d+)
         (?P<xoffset>[+-]\d+)(?P<yoffset>[+-]\d+)
    )?
    \ \((?P<info>.*?)\)
    (?:\ (?P<physical_size>.*))?
    """, flags=re.ASCII|re.VERBOSE
)
xrandr_output_casts = {
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
xrandr_mode_regex = re.compile(r"""
    \s+(?P<width>\d+)x(?P<height>\d+)
    \s+(?P<frequency>\d+\.\d+)
    (?P<active>\*)?
    (?P<preferred>\+)?
    """, flags=re.ASCII|re.VERBOSE)
xrandr_mode_casts = {
    'width': int,
    'height': int,
    'frequency': float,
    'active': bool,
    'preferred': bool,
}


def scan_xrandr_outputs(echo=True):
    """Iterate data of all outputs by parsing `xrandr --query`."""
    lines = run_cmd("xrandr", "--query", echo=echo).split("\n")[1:]
    current_output = None
    while current_output is None:
        current_output = _sscanf(lines.pop(0), xrandr_output_regex, xrandr_output_casts)
    current_output.modes = []
    for line in filter(None, lines):
        output = _sscanf(line, xrandr_output_regex, xrandr_output_casts)
        if output:
            yield current_output
            current_output = output
            current_output.modes = []
            continue
        mode = _sscanf(line, xrandr_mode_regex, xrandr_mode_casts)
        if mode:
            current_output.modes.append(mode)
            continue
        # print("ignoring line '{}'".format(line))
    yield current_output


def connected_outputs(echo=True):
    """Iterate outputs filtered by connection status."""
    for output in scan_xrandr_outputs(echo=echo):
        if output.connected:
            yield output


def beamer_info():
    for output in connected_outputs(echo=False):
        info(output.name)
        modes = ["{}{}x{}".format("*" if m.active else "", m.width, m.height)
                 for m in output.modes]
        print(list_to_columns(modes, indent="  "))


def beamer_query_args():
    """xrandr arguments for querying current status."""
    return ("xrandr", "--query")


def beamer_clone_args():
    """xrandr arguments for cloning to all connected outputs."""
    outputs = tuple(connected_outputs())
    print("Cloning to {} outputs.".format(len(outputs)))
    resolutions = ({(md.width, md.height) for md in out.modes} for out in outputs)
    try:
        resolution = max(set.intersection(*resolutions))
    except ValueError:
        return print("no matching resolution found")
    mode = "{}x{}".format(*resolution)
    return ("xrandr", "--output", outputs[0].name, "--mode", mode,
            *chain.from_iterable(("--output", out.name,
                                  "--mode", mode,
                                  "--same-as", outputs[0].name)
                                 for out in outputs[1:])
            )


def beamer_side_args(side):
    """xrandr arguments for putting one output next to the other."""
    side_parameters = {
        "left": "--left-of",
        "right": "--right-of",
        "above": "--above",
        "below": "--below",
    }
    outputs = tuple(connected_outputs())
    if len(outputs) != 2:
        return print("Which outputs should I use? Found {}".format(len(outputs)))
    return ("xrandr", "--output", outputs[0].name, "--auto",
            "--output", outputs[1].name, "--auto",
            side_parameters[side], outputs[0].name)


def beamer_single_output_args(index=0):
    """xrandr arguments for turning off all outputs except one."""
    outputs = list(connected_outputs())
    try:
        activate = outputs.pop(index)
    except IndexError:
        return print("No output with index {} connected".format(index))
    return ("xrandr", "--output", activate.name, "--auto",
            *chain.from_iterable(("--output", out.name, "--off")
                                 for out in outputs)
            )

def main():
    """Run the CLI."""
    commands = {"info", "query", "clone", "off", "only",
                "left", "right", "above", "below"}
    switches = {"-r", "--retry"}
    args = set(sys.argv[1:])
    try:
        assert not args - commands - switches
        command, = args & commands or {"info"}
        switches = args & switches
    except:
        print(__doc__.strip())
        return 1

    cmd_args = None
    while cmd_args is None:
        if "off" == command:
            cmd_args = beamer_single_output_args(index=0)
        elif "only" == command:
            cmd_args = beamer_single_output_args(index=1)
        elif "clone" == command:
            cmd_args = beamer_clone_args()
        elif command in {"left", "right", "above", "below"}:
            cmd_args = beamer_side_args(command)
        elif "info" == command:
            return beamer_info()
        else:
            cmd_args = beamer_query_args()

        if cmd_args:
            run_cmd(*cmd_args)
            return
        elif switches & {"-r", "--retry"}:
            sleep(1)
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())

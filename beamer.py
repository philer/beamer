#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplistic CLI for toggling and positioning
a secondary monitor or beamer. May work for
more than 2 connected outputs, but untested.

Usage:
    beamer [info|query|clone|left|right|off|only]
"""

import sys, os
import re
import subprocess
from itertools import chain

from docopt import docopt


class ObjectDict(dict):
    """Dictionary with dot access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError from None

    def __setattr__(self, key, value):
        self[key] = value

# def chunk(iterable, size):
#     it = iter(iterable)
#     current_chunk = tuple(next(it) for _ in range(size))
#     while current_chunk:
#         yield current_chunk
#         current_chunk = tuple(next(it) for _ in range(size))


# def print_list_columns(entries, format=str):
#     entries = tuple(map(format, entries))
#     max_len = max(map(len, entries))
#     term_width = os.get_terminal_size().columns
#     columns = term_width // max_len
#     lines = ceil(len(entries) / columns)
#     for


def error(msg, errno=1):
    """Print an error message and exit."""
    print("\033[1;31m" + str(msg) + "\033[0m")
    sys.exit(errno)


def run_cmd(*args, echo=True):
    """Execute a command line utility and return the output."""
    if echo:
        print("\033[1;32m" + " ".join(args) + "\033[0m")
    result = subprocess.run(args,
                            check=True,
                            universal_newlines=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    # except subprocess.CalledProcessError as cpe:
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
    for number, output in enumerate(connected_outputs(echo=False), start=1):
        # print(number, output)
        print("\033[1;32m{}: {}\033[0m".format(number, output.name))
        # print("\t", *map("{width}x{height}".format_map, output.modes))
        print("\n".join(map("  {width}x{height}".format_map, output.modes)))


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
    outputs = tuple(connected_outputs())
    if len(outputs) != 2:
        return print("Which outputs should I use? Found {}".format(len(outputs)))
    return ("xrandr", "--output", outputs[0].name, "--auto",
            "--output", outputs[1].name, "--auto",
            "--" + side + "-of", outputs[0].name)


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
    args = docopt(__doc__, version="0.0.1")
    cmd_args = None
    if args["off"]:
        cmd_args = beamer_single_output_args(index=0)
    elif args["only"]:
        cmd_args = beamer_single_output_args(index=1)
    elif args["clone"]:
        cmd_args = beamer_clone_args()
    elif args["left"]:
        cmd_args = beamer_side_args("left")
    elif args["right"]:
        cmd_args = beamer_side_args("right")
    elif args["info"]:
        return beamer_info()
    else:
        cmd_args = beamer_query_args()
    if cmd_args:
        run_cmd(*cmd_args)
    else:
        exit(1)


if __name__ == "__main__":
    main()

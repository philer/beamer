`beamer` is a simple command line tool for toggling and positioning a secondary monitor or projector on Linux.  
It is a thin wrapper for `xrandr` to spare you typing out common setups in its verbose syntax. Consequently, it requires `xrandr` to be installed on your system.

## Commands

Commands assume the first output listed by `xrandr` to be the main output (e.g. a laptops monitor).

(See also `beamer -h`)

* `beamer info` Print a short, formatted list of avaliable outputs and modes
* `beamer clone` mirror the main output to a secondary output
* `beamer left|right|above|below` extend the screen to a secondary output next to the main output
* `beamer off` only use main output
* `beamer only` only use secondary output
* `beamer query` show output of `xrandr --query`

## Installation

Run `pip install beamer`

– or –

copy the `beamer.py` file from this repository anywhere on your computer
and run it via `python3 /path/to/beamer.py`.

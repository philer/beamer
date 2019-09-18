# beamer.py

Simplistic CLI for toggling and positioning a secondary monitor or projector.  
This is a thin wrapper for `xrandr` to spare you typing out common setups in its verbose syntax.

## Commands

Commands assume the first output listed by `xrandr` to be the main output (e.g. a laptops monitor).

(See also `beamer.py -h`)

* `beamer.py info` Print a short, formatted list of avaliable outputs and modes
* `beamer.py clone` mirror the main output to a secondary output
* `beamer.py left` extend the screen to a secondary output left of the main output
* `beamer.py right` extend the screen to a secondary output right of the main output
* `beamer.py off` only use main output
* `beamer.py only` only use secondary output
* `beamer.py query` show output of `xrandr --query`

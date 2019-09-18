# beamer.py

Simplistic CLI for toggling and positioning a secondary monitor or projector.  
This is a thin wrapper for `xrandr` to spare you typing out common setups in its verbose syntax.

## Commands

Commands assume the first output listed by `xrandr` to be the main output (e.g. a laptops monitor).

(See also `beamer -h`)

* `beamer info` Print a short, formatted list of avaliable outputs and modes
* `beamer clone` mirror the main output to a secondary output
* `beamer left` extend the screen to a secondary output left of the main output
* `beamer right` extend the screen to a secondary output right of the main output
* `beamer off` only use main output
* `beamer only` only use secondary output
* `beamer query` show output of `xrandr --query`

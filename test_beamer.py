#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run these tests with py.test.
"""

from unittest.mock import patch, call
import beamer


@patch("beamer.run_cmd")
def test_clone(run_cmd):
    run_cmd.return_value = xrandr_output_single
    assert beamer.beamer_clone_args() == ("xrandr",
        "--output", "eDP1", "--mode", "1920x1080")
    assert run_cmd.call_args[0] == ("xrandr", "--query")
    run_cmd.return_value = xrandr_output_with_beamer
    assert beamer.beamer_clone_args() == ("xrandr",
        "--output", "eDP1", "--mode", "1920x1080",
        "--output", "HDMI2", "--mode", "1920x1080",
        "--same-as", "eDP1")
    run_cmd.return_value = xrandr_output_double_monitor
    assert beamer.beamer_clone_args() == ("xrandr",
        "--output", "DVI-D-0", "--mode", "1920x1080",
        "--output", "HDMI-0", "--mode", "1920x1080",
        "--same-as", "DVI-D-0")


@patch("beamer.run_cmd")
def test_sides(run_cmd):
    run_cmd.return_value = xrandr_output_single
    assert beamer.beamer_side_args("left") is None
    run_cmd.return_value = xrandr_output_with_beamer
    assert beamer.beamer_side_args("left") == ("xrandr",
        "--output", "eDP1", "--auto", "--output", "HDMI2", "--auto",
        "--left-of", "eDP1")
    assert beamer.beamer_side_args("right") == ("xrandr",
        "--output", "eDP1", "--auto", "--output", "HDMI2", "--auto",
        "--right-of", "eDP1")
    assert beamer.beamer_side_args("above") == ("xrandr",
        "--output", "eDP1", "--auto", "--output", "HDMI2", "--auto",
        "--above", "eDP1")
    assert beamer.beamer_side_args("below") == ("xrandr",
        "--output", "eDP1", "--auto", "--output", "HDMI2", "--auto",
        "--below", "eDP1")
    run_cmd.return_value = xrandr_output_double_monitor
    assert beamer.beamer_side_args("left") == ("xrandr",
        "--output", "DVI-D-0", "--auto", "--output", "HDMI-0", "--auto",
        "--left-of", "DVI-D-0")
    assert beamer.beamer_side_args("right") == ("xrandr",
        "--output", "DVI-D-0", "--auto", "--output", "HDMI-0", "--auto",
        "--right-of", "DVI-D-0")
    assert beamer.beamer_side_args("above") == ("xrandr",
        "--output", "DVI-D-0", "--auto", "--output", "HDMI-0", "--auto",
        "--above", "DVI-D-0")
    assert beamer.beamer_side_args("below") == ("xrandr",
        "--output", "DVI-D-0", "--auto", "--output", "HDMI-0", "--auto",
        "--below", "DVI-D-0")


@patch("beamer.run_cmd")
def test_single_output(run_cmd):
    run_cmd.return_value = xrandr_output_single
    assert beamer.beamer_single_output_args(0) == ("xrandr",
        "--output", "eDP1", "--auto")
    run_cmd.return_value = xrandr_output_with_beamer
    assert beamer.beamer_single_output_args(0) == ("xrandr",
        "--output", "eDP1", "--auto", "--output", "HDMI2", "--off")
    run_cmd.return_value = xrandr_output_double_monitor
    assert beamer.beamer_single_output_args(0) == ("xrandr",
        "--output", "DVI-D-0", "--auto", "--output", "HDMI-0", "--off")
    ...  # todo "beamer only"

# @patch("beamer.run_cmd")
# def test_info_demo(run_cmd):
#     for query_result in (xrandr_output_single, xrandr_output_double_monitor, xrandr_output_with_beamer):
#       run_cmd.return_value = query_result
#       beamer.beamer_info()


xrandr_output_single = """\
Screen 0: minimum 8 x 8, current 1920 x 1080, maximum 32767 x 32767
eDP1 connected 1920x1080+0+0 (normal left inverted right x axis y axis) 309mm x 173mm
   1920x1080     60.01*+  59.93
   1680x1050     59.95    59.88
   1600x1024     60.17
   1400x1050     59.98
   1600x900      60.00
   1280x1024     60.02
   1440x900      59.89
   1280x960      60.00
   1368x768      60.00
   1360x768      59.80    59.96
   1152x864      60.00
   1280x720      60.00
   1024x768      60.00
   1024x576      60.00
   960x540       60.00
   800x600       60.32    56.25
   864x486       60.00
   640x480       59.94
   720x405       60.00
   640x360       60.00
DP1 disconnected (normal left inverted right x axis y axis)
DP2 disconnected (normal left inverted right x axis y axis)
HDMI1 disconnected (normal left inverted right x axis y axis)
HDMI2 disconnected (normal left inverted right x axis y axis)
VIRTUAL1 disconnected (normal left inverted right x axis y axis)
"""

xrandr_output_with_beamer = """\
Screen 0: minimum 8 x 8, current 1920 x 1080, maximum 32767 x 32767
eDP1 connected 1920x1080+0+0 (normal left inverted right x axis y axis) 309mm x 173mm
   1920x1080     60.01*+  59.93
   1680x1050     59.95    59.88
   1600x1024     60.17
   1400x1050     59.98
   1600x900      60.00
   1280x1024     60.02
   1440x900      59.89
   1280x960      60.00
   1368x768      60.00
   1360x768      59.80    59.96
   1152x864      60.00
   1280x720      60.00
   1024x768      60.00
   1024x576      60.00
   960x540       60.00
   800x600       60.32    56.25
   864x486       60.00
   640x480       59.94
   720x405       60.00
   640x360       60.00
DP1 disconnected (normal left inverted right x axis y axis)
DP2 disconnected (normal left inverted right x axis y axis)
HDMI1 disconnected (normal left inverted right x axis y axis)
HDMI2 connected (normal left inverted right x axis y axis)
   1280x800      59.81 +
   1920x1200     59.95
   1920x1080     60.00    50.00    59.94    30.00    24.00    29.97    23.98
   1920x1080i    60.00    50.00    59.94
   1600x1200     60.00
   1680x1050     59.88
   1400x1050     59.95
   1600x900      60.00
   1280x1024     60.02
   1440x900      59.90
   1280x960      60.00
   1366x768      59.79
   1280x720      60.00    50.00    59.94
   1024x768      60.00
   800x600       60.32
   720x576       50.00
   720x576i      50.00
   720x480       60.00    59.94
   720x480i      60.00    59.94
   640x480       60.00    59.94
VIRTUAL1 disconnected (normal left inverted right x axis y axis)
"""

xrandr_output_double_monitor = """\
Screen 0: minimum 8 x 8, current 3840 x 1080, maximum 32767 x 32767
DVI-D-0 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 531mm x 298mm
   1920x1080     60.00*+
   1680x1050     59.95
   1600x900      60.00
   1280x1024     75.02    60.02
   1280x800      59.81
   1280x720      60.00
   1024x768      75.03    60.00
   800x600       75.00    60.32
   640x480       75.00    59.94
HDMI-0 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 477mm x 268mm
   1920x1080     60.00*+
   1680x1050     59.95
   1600x900      60.00
   1280x1024     75.02    60.02
   1280x960      60.00
   1280x720      60.00
   1152x720      60.00
   1024x768      75.03    60.00
   800x600       75.00    60.32
   640x480       75.00    59.94
DP-0 disconnected (normal left inverted right x axis y axis)
DP-1 disconnected (normal left inverted right x axis y axis)
"""

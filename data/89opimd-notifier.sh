#!/bin/sh
DISPLAY=:0 opimd-notifier &
renice -n 3 $!

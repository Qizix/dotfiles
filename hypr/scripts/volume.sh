#!/bin/bash

# Kill old wob (if any)
pkill -f "wob" 2>/dev/null

# Get volume in 0–65535 range
VOL=$(pamixer --get-volume)
VAL=$(awk "BEGIN { printf \"%d\", $VOL * 65535 / 100 }")

# Pipe to wob and close after 0.5s
echo "$VAL" | (sleep 0.5 && kill $$) | wob

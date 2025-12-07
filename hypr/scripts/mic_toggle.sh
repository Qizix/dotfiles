#!/bin/bash

# Toggle mute
wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle

# Get new status
STATUS=$(wpctl get-volume @DEFAULT_AUDIO_SOURCE@)

# Show notification
if echo "$STATUS" | grep -q MUTED; then
  # Visual notification
  notify-send -u low -t 1000 "Microphone" "Muted 🔇"
  
  # Optional sound (requires `paplay` and a sound file)
  paplay /usr/share/sounds/freedesktop/stereo/audio-volume-change.oga
else
  notify-send -u low -t 1000 "Microphone" "Unmuted 🎙️"
  
  # Optional sound
  paplay /usr/share/sounds/freedesktop/stereo/audio-volume-change.oga
fi

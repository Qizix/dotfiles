#!/bin/bash

action=$1

case "$action" in
    toggle)
        playerctl play-pause
        ;;
    next)
        playerctl next
        ;;
    prev)
        playerctl previous
        ;;
    *)
        status=$(playerctl status 2>/dev/null)
        if [ "$status" = "Playing" ]; then
            artist=$(playerctl metadata artist)
            title=$(playerctl metadata title)
            echo "{\"text\": \"$artist - $title\"}"
        elif [ "$status" = "Paused" ]; then
            echo "{\"text\": \" paused\"}"
        else
            echo "{\"text\": \"\"}"
        fi
        ;;
esac

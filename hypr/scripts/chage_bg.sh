#!/bin/bash

folder="/home/qzx/Pictures/autopapers"

while true; do
  img=$(find "$folder" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) -not -path "*/.git/*" | shuf -n 1)
  swww img "$img" --transition-type any
  sleep 600
done

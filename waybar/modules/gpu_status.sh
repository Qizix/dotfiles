#!/bin/bash

while true; do
  # Get GPU utilization percentage
  GPU_USAGE=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null)
  
  # Get GPU temperature in Celsius
  GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
  
  if [[ -z "$GPU_USAGE" || -z "$GPU_TEMP" ]]; then
    # No NVIDIA GPU or command failed
    echo '{"text": "GPU: N/A", "class": "gpu-off"}'
  else
    echo " ${GPU_USAGE}%  ${GPU_TEMP}°C"
  fi

  sleep 5
done

#!/usr/bin/env ruby

loop do
  status = `wpctl get-volume @DEFAULT_AUDIO_SOURCE@ 2>&1`

  if status.include?('MUTED')
    output = ""
  else
    output = ""
  end

  puts output
  $stdout.flush

  sleep 1
end

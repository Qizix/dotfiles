#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# ---------- Config ----------
WORK_SEC = 25 * 60      # 25:00
CHILL_SEC = 5 * 60      # 05:00

ICON = "󰔛"              # what’s shown on the bar
STATE_DIR = Path(os.path.expanduser("~/.config/waybar/modules/pomodoro"))
STATE_FILE = STATE_DIR / "state.json"

NOTIFY_SUMMARY = "Pomodoro finished"
# A few common long-ish sounds. We'll try them in order.
SOUND_CANDIDATES = [
    ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
    ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
    ["canberra-gtk-play", "-i", "alarm-clock-elapsed"],
    ["canberra-gtk-play", "-i", "complete"],
]

# ---------- Helpers ----------
def now_ts() -> int:
    return int(time.time())

def ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def default_state():
    # paused at Work 25:00 on first run
    return {
        "mode": "work",               # "work" or "chill"
        "paused": True,
        "started_at": None,           # epoch when started (only valid if paused==False)
        "remaining": WORK_SEC,        # remaining seconds when paused
        "work_sec": WORK_SEC,
        "chill_sec": CHILL_SEC,
        "today": current_date(),
        "streak_today": 0,            # number of completed work sessions today
        "last_switch_ts": None,       # for reference
    }

def load_state():
    ensure_state_dir()
    if not STATE_FILE.exists():
        s = default_state()
        save_state(s)
        return s
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
    except Exception:
        s = default_state()

    # Upgrade / sanity
    s.setdefault("work_sec", WORK_SEC)
    s.setdefault("chill_sec", CHILL_SEC)
    s.setdefault("today", current_date())
    s.setdefault("streak_today", 0)
    s.setdefault("last_switch_ts", None)
    return s

def save_state(state):
    ensure_state_dir()
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)

def current_date():
    # store local date (YYYY-MM-DD)
    return datetime.now().strftime("%Y-%m-%d")

def duration_for_mode(state):
    return state["work_sec"] if state["mode"] == "work" else state["chill_sec"]

def compute_remaining(state, tnow=None):
    if tnow is None:
        tnow = now_ts()
    if state["paused"]:
        return max(0, int(state["remaining"]))
    # running
    dur = duration_for_mode(state)
    elapsed = tnow - int(state["started_at"])
    remaining = dur - elapsed
    return max(0, int(remaining))

def set_paused(state, pause=True):
    tnow = now_ts()
    if pause and not state["paused"]:
        # going from running -> paused : freeze remaining
        rem = compute_remaining(state, tnow)
        state["remaining"] = rem
        state["paused"] = True
        state["started_at"] = None
    elif (not pause) and state["paused"]:
        # going from paused -> running : start countdown using remaining
        dur = duration_for_mode(state)
        rem = max(0, int(state["remaining"]))
        elapsed = dur - rem
        state["paused"] = False
        state["started_at"] = tnow - elapsed  # so remaining = dur - (now - started_at)

def reset_current_mode(state):
    state["remaining"] = duration_for_mode(state)
    state["paused"] = True
    state["started_at"] = None

def switch_mode(state, keep_paused=True, after_finish=False):
    prev_mode = state["mode"]
    state["mode"] = "chill" if prev_mode == "work" else "work"
    state["last_switch_ts"] = now_ts()

    # If we just finished a WORK session, increment today's streak
    if after_finish and prev_mode == "work":
        maybe_rollover_streak(state)  # ensure day correct
        state["streak_today"] = int(state["streak_today"]) + 1

    # Start next mode paused with full duration
    state["remaining"] = duration_for_mode(state)
    state["paused"] = True if keep_paused else False
    state["started_at"] = None if keep_paused else now_ts()

def maybe_rollover_streak(state):
    # if date changed, reset today's streak
    today = current_date()
    if state["today"] != today:
        state["today"] = today
        state["streak_today"] = 0

def play_sound():
    for cmd in SOUND_CANDIDATES:
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except FileNotFoundError:
            continue

def notify(title, body):
    try:
        subprocess.Popen(
            ["notify-send", "-u", "normal", "-t", "5000", title, body],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass

def fmt_mmss(sec):
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"

def render_output(state):
    # compute remaining and handle finishing/auto-switch
    tnow = now_ts()
    maybe_rollover_streak(state)
    rem = compute_remaining(state, tnow)

    just_switched = False
    if rem == 0 and not state["paused"]:
        # time is up -> auto switch, ring+notify once
        prev_mode = state["mode"]
        switch_mode(state, keep_paused=True, after_finish=True)
        play_sound()
        notify(
            NOTIFY_SUMMARY,
            f"{prev_mode.capitalize()} finished → {state['mode'].capitalize()} started (paused)"
        )
        just_switched = True
        rem = compute_remaining(state, tnow)

    # Compose tooltip
    paused_flag = "󰐊" if state["paused"] else ""
    mode_label = "Work" if state["mode"] == "work" else "Chill"
    tooltip = (
        f"{mode_label} {paused_flag} {fmt_mmss(rem)}\n"
        f"Today streak: {int(state['streak_today'])}"
    )

    # Classes for CSS theming
    classes = []
    classes.append(state["mode"])  # "work" or "chill"
    if state["paused"]:
        classes.append("paused")

    out = {
        "text": ICON,
        "tooltip": tooltip,
        "class": " ".join(classes),
        "alt": f"{mode_label.lower()}",
    }
    return out, just_switched

# ---------- CLI ----------
def main():
    state = load_state()

    args = sys.argv[1:]
    if not args:
        # Normal "render" path for Waybar
        out, _ = render_output(state)
        save_state(state)
        print(json.dumps(out, ensure_ascii=False))
        return

    # Handle clicks / commands
    cmd = args[0]
    if cmd in ("--toggle",):
        # pause/resume
        set_paused(state, pause=not state["paused"])
    elif cmd in ("--reset",):
        reset_current_mode(state)
    elif cmd in ("--switch-mode", "--switch"):
        # manual user switch (stay paused)
        switch_mode(state, keep_paused=True, after_finish=False)
    elif cmd == "--start":
        set_paused(state, pause=False)
    elif cmd == "--pause":
        set_paused(state, pause=True)
    elif cmd == "--set":
        # optional: set durations (e.g. --set work 50 chill 10)
        # simple parser: pairs (name value)
        pairs = dict(zip(args[1::2], args[2::2]))
        if "work" in pairs:
            try:
                state["work_sec"] = int(pairs["work"]) * 60
            except Exception:
                pass
        if "chill" in pairs:
            try:
                state["chill_sec"] = int(pairs["chill"]) * 60
            except Exception:
                pass
        # reset remaining to new duration for current mode if paused
        if state["paused"]:
            state["remaining"] = duration_for_mode(state)
    else:
        # unknown → no-op
        pass

    # After state change, always print fresh JSON so Waybar updates immediately
    out, _ = render_output(state)
    save_state(state)
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()

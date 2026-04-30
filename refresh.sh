#!/bin/bash
# Kali Refresh - Kill unwanted processes, clear caches, free resources

LOGFILE="/tmp/kali-refresh-$(date +%Y%m%d-%H%M%S).log"

notify() {
    notify-send -i system-run "Kali Refresh" "$1" 2>/dev/null
}

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOGFILE"
}

# --- Unwanted processes to kill ---
# Common resource hogs and background apps not needed for most workflows
UNWANTED_PROCS=(
    # Browsers left running in background
    "chromium"
    "chrome"
    "firefox-esr"
    # Heavy desktop apps
    "libreoffice"
    "gimp"
    "vlc"
    "parole"
    "thunderbird"
    # Misc background bloat
    "evolution-data"
    "tracker-miner"
    "tracker-store"
    "tracker-extract"
    "tumblerd"
    "at-spi-bus-launcher"
    "at-spi2-registryd"
    "gvfsd-trash"
    "gvfsd-metadata"
    "zeitgeist"
    "packagekitd"
    "snapd"
    "update-notifier"
    "polkit-gnome"
)

notify "Starting system refresh..."
log "=== Kali Refresh Started ==="

# --- Kill unwanted processes ---
KILLED=0
for proc in "${UNWANTED_PROCS[@]}"; do
    pids=$(pgrep -f "$proc" 2>/dev/null)
    if [ -n "$pids" ]; then
        kill $pids 2>/dev/null
        log "Killed: $proc (PIDs: $(echo $pids | tr '\n' ' '))"
        ((KILLED++))
    fi
done
log "Killed $KILLED process groups"

# --- Kill zombie processes ---
ZOMBIES=$(ps -eo pid,stat | awk '$2 ~ /Z/ {print $1}')
if [ -n "$ZOMBIES" ]; then
    for z in $ZOMBIES; do
        kill -9 "$z" 2>/dev/null
    done
    log "Killed $(echo "$ZOMBIES" | wc -w) zombie processes"
fi

# --- Clear user caches ---
FREED_BEFORE=$(du -sm ~/.cache 2>/dev/null | cut -f1)

# Thumbnails
rm -rf ~/.cache/thumbnails/* 2>/dev/null
# Browser caches
rm -rf ~/.cache/chromium/*/Cache/* 2>/dev/null
rm -rf ~/.cache/google-chrome/*/Cache/* 2>/dev/null
rm -rf ~/.cache/mozilla/firefox/*/cache2/* 2>/dev/null
# General app caches
rm -rf ~/.cache/pip 2>/dev/null
rm -rf ~/.cache/sessions/* 2>/dev/null
rm -rf ~/.cache/tracker3/* 2>/dev/null
rm -rf ~/.cache/evolution/* 2>/dev/null
rm -rf ~/.cache/fontconfig/* 2>/dev/null
rm -rf ~/.cache/mesa_shader_cache/* 2>/dev/null
# Old temp files
find /tmp -user "$(whoami)" -type f -atime +1 -delete 2>/dev/null

FREED_AFTER=$(du -sm ~/.cache 2>/dev/null | cut -f1)
FREED=$((FREED_BEFORE - FREED_AFTER))
log "Freed ~${FREED}MB from user cache"

# --- Clear system caches (no sudo needed) ---
# Drop page cache via /proc if writable
if [ -w /proc/sys/vm/drop_caches ]; then
    sync && echo 3 > /proc/sys/vm/drop_caches
    log "Dropped kernel page cache"
fi

# --- Clear old journal logs (user-level) ---
journalctl --user --vacuum-time=2d 2>/dev/null
log "Cleaned user journal logs"

# --- Clear recent file history ---
rm -f ~/.local/share/recently-used.xbel 2>/dev/null
log "Cleared recent file history"

# --- Clear bash/zsh history duplicates (compact, don't delete) ---
if [ -f ~/.bash_history ]; then
    sort -u ~/.bash_history -o ~/.bash_history
    log "Compacted bash history"
fi
if [ -f ~/.zsh_history ]; then
    sort -u ~/.zsh_history -o ~/.zsh_history
    log "Compacted zsh history"
fi

# --- Summary ---
MEM_FREE=$(free -m | awk '/Mem:/ {print $4}')
log "=== Refresh Complete === Free RAM: ${MEM_FREE}MB"
notify "Refresh complete! Killed $KILLED process groups, freed ~${FREED}MB cache. Free RAM: ${MEM_FREE}MB"

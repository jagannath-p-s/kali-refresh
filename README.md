# Kali Refresh

A lightweight system refresh tool for Kali Linux (XFCE) that adds a **right-click "Refresh System"** option to your desktop and file manager.

## What it does

- **Kills unwanted processes** - browsers, LibreOffice, tracker services, zombie processes, and other resource hogs
- **Clears user caches** - browser cache, thumbnails, pip cache, font cache, shader cache, old temp files
- **Cleans history** - recent files, journal logs, compacts shell history
- **Frees RAM** - drops kernel page cache if permissions allow
- **Desktop notifications** - shows summary of what was cleaned

## Install

```bash
git clone git@github.com:jagannath-p-s/kali-refresh.git
cd kali-refresh
chmod +x install.sh
./install.sh
```

## Usage

- **Right-click in Thunar** (file manager) → "Refresh System"
- **Desktop shortcut** → double-click "Refresh System" icon
- **Terminal** → `kali-refresh`

## Uninstall

```bash
./uninstall.sh
```

## Customization

Edit `~/.local/bin/kali-refresh` to add/remove processes from the `UNWANTED_PROCS` array.

## License

MIT

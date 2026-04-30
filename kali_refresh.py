#!/usr/bin/env python3
"""Kali Refresh - System cleanup tool with GTK3 GUI showing real-time stats."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, GLib, Gdk, Pango, Notify
import subprocess
import os
import shutil
import signal
import threading
import time
import psutil

UNWANTED_PROCS = [
    "chromium", "chrome", "firefox-esr", "firefox",
    "libreoffice", "soffice", "gimp", "vlc", "parole", "thunderbird",
    "evolution-data", "tracker-miner", "tracker-store", "tracker-extract",
    "tumblerd", "at-spi-bus-launcher", "at-spi2-registryd",
    "gvfsd-trash", "gvfsd-metadata", "zeitgeist",
    "packagekitd", "snapd", "update-notifier",
]

CACHE_DIRS = [
    ("Browser Cache", [
        "~/.cache/chromium/*/Cache",
        "~/.cache/google-chrome/*/Cache",
        "~/.cache/mozilla/firefox/*/cache2",
    ]),
    ("Thumbnails", ["~/.cache/thumbnails"]),
    ("Pip Cache", ["~/.cache/pip"]),
    ("Font Cache", ["~/.cache/fontconfig"]),
    ("Shader Cache", ["~/.cache/mesa_shader_cache"]),
    ("Session Cache", ["~/.cache/sessions"]),
    ("Tracker Cache", ["~/.cache/tracker3"]),
    ("Evolution Cache", ["~/.cache/evolution"]),
]

CSS = """
window {
    background-color: #1a1a2e;
}
.title-label {
    color: #e94560;
    font-size: 22px;
    font-weight: bold;
}
.subtitle-label {
    color: #8a8a9a;
    font-size: 11px;
}
.stat-card {
    background-color: #16213e;
    border-radius: 12px;
    padding: 16px;
}
.stat-value {
    color: #00ff88;
    font-size: 28px;
    font-weight: bold;
}
.stat-value-red {
    color: #e94560;
    font-size: 28px;
    font-weight: bold;
}
.stat-value-blue {
    color: #0f9fff;
    font-size: 28px;
    font-weight: bold;
}
.stat-value-yellow {
    color: #ffc107;
    font-size: 28px;
    font-weight: bold;
}
.stat-label {
    color: #8a8a9a;
    font-size: 11px;
}
.log-view {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: monospace;
    font-size: 11px;
    border-radius: 8px;
    padding: 8px;
}
.refresh-button {
    background-color: #e94560;
    color: white;
    font-size: 14px;
    font-weight: bold;
    border-radius: 8px;
    padding: 12px 32px;
    border: none;
}
.refresh-button:hover {
    background-color: #ff6b81;
}
.refresh-button:disabled {
    background-color: #444;
    color: #888;
}
.section-header {
    color: #e94560;
    font-size: 13px;
    font-weight: bold;
}
.detail-row {
    background-color: #16213e;
    border-radius: 6px;
    padding: 8px 12px;
}
.detail-name {
    color: #c9d1d9;
    font-size: 11px;
}
.detail-value {
    color: #00ff88;
    font-size: 11px;
    font-weight: bold;
}
.progress-bar trough {
    background-color: #16213e;
    border-radius: 4px;
    min-height: 6px;
}
.progress-bar progress {
    background-color: #e94560;
    border-radius: 4px;
    min-height: 6px;
}
"""


def get_dir_size_mb(path):
    expanded = os.path.expanduser(path)
    total = 0
    if '*' in expanded:
        import glob
        for p in glob.glob(expanded):
            if os.path.isdir(p):
                for dirpath, _, filenames in os.walk(p):
                    for f in filenames:
                        try:
                            total += os.path.getsize(os.path.join(dirpath, f))
                        except OSError:
                            pass
    elif os.path.isdir(expanded):
        for dirpath, _, filenames in os.walk(expanded):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
    return total / (1024 * 1024)


def clear_dir(path):
    expanded = os.path.expanduser(path)
    if '*' in expanded:
        import glob
        for p in glob.glob(expanded):
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
    elif os.path.isdir(expanded):
        shutil.rmtree(expanded, ignore_errors=True)


class RefreshApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Kali Refresh")
        self.set_default_size(680, 720)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("view-refresh")
        self.set_resizable(True)

        # Apply CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        Notify.init("Kali Refresh")
        self.stats = {}
        self.build_ui()
        self.collect_before_stats()

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)

        # Header
        title = Gtk.Label(label="Kali Refresh")
        title.get_style_context().add_class("title-label")
        title.set_halign(Gtk.Align.START)
        main_box.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="System cleanup & optimization tool")
        subtitle.get_style_context().add_class("subtitle-label")
        subtitle.set_halign(Gtk.Align.START)
        main_box.pack_start(subtitle, False, False, 4)

        main_box.pack_start(Gtk.Box(spacing=0), False, False, 8)

        # Stats cards row
        stats_grid = Gtk.Grid()
        stats_grid.set_column_spacing(12)
        stats_grid.set_row_spacing(12)
        stats_grid.set_column_homogeneous(True)

        self.ram_before_label = Gtk.Label(label="--")
        self.ram_after_label = Gtk.Label(label="--")
        self.procs_killed_label = Gtk.Label(label="--")
        self.cache_freed_label = Gtk.Label(label="--")

        cards = [
            ("RAM Used", self.ram_before_label, "stat-value-red"),
            ("RAM After", self.ram_after_label, "stat-value"),
            ("Procs Killed", self.procs_killed_label, "stat-value-yellow"),
            ("Cache Freed", self.cache_freed_label, "stat-value-blue"),
        ]

        for i, (label_text, value_widget, css_class) in enumerate(cards):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.get_style_context().add_class("stat-card")
            card.set_margin_top(12)
            card.set_margin_bottom(12)
            card.set_margin_start(12)
            card.set_margin_end(12)

            value_widget.get_style_context().add_class(css_class)
            value_widget.set_halign(Gtk.Align.CENTER)
            card.pack_start(value_widget, False, False, 0)

            lbl = Gtk.Label(label=label_text)
            lbl.get_style_context().add_class("stat-label")
            lbl.set_halign(Gtk.Align.CENTER)
            card.pack_start(lbl, False, False, 0)

            stats_grid.attach(card, i, 0, 1, 1)

        main_box.pack_start(stats_grid, False, False, 0)

        # Progress bar
        self.progress = Gtk.ProgressBar()
        self.progress.get_style_context().add_class("progress-bar")
        self.progress.set_margin_top(8)
        main_box.pack_start(self.progress, False, False, 0)

        self.status_label = Gtk.Label(label="Ready to refresh")
        self.status_label.get_style_context().add_class("subtitle-label")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_margin_top(4)
        main_box.pack_start(self.status_label, False, False, 0)

        main_box.pack_start(Gtk.Box(spacing=0), False, False, 6)

        # Details section with scrollable log
        header = Gtk.Label(label="CLEANUP LOG")
        header.get_style_context().add_class("section-header")
        header.set_halign(Gtk.Align.START)
        main_box.pack_start(header, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(220)

        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.get_style_context().add_class("log-view")
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_left_margin(8)
        self.log_view.set_right_margin(8)
        self.log_view.set_top_margin(8)
        self.log_view.set_bottom_margin(8)
        scroll.add(self.log_view)
        main_box.pack_start(scroll, True, True, 4)

        main_box.pack_start(Gtk.Box(spacing=0), False, False, 6)

        # Button row
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)

        self.refresh_btn = Gtk.Button(label="  Refresh System  ")
        self.refresh_btn.get_style_context().add_class("refresh-button")
        self.refresh_btn.connect("clicked", self.on_refresh)
        btn_box.pack_start(self.refresh_btn, False, False, 0)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda _: self.destroy())
        btn_box.pack_start(close_btn, False, False, 0)

        main_box.pack_start(btn_box, False, False, 0)

    def log(self, msg):
        GLib.idle_add(self._append_log, msg)

    def _append_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        end = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end, f"[{timestamp}] {msg}\n")
        # Auto-scroll
        adj = self.log_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def set_progress(self, fraction, text=""):
        GLib.idle_add(self._update_progress, fraction, text)

    def _update_progress(self, fraction, text):
        self.progress.set_fraction(fraction)
        if text:
            self.status_label.set_text(text)

    def collect_before_stats(self):
        mem = psutil.virtual_memory()
        self.stats['ram_used_before'] = mem.used / (1024**2)
        self.stats['ram_total'] = mem.total / (1024**2)
        self.stats['ram_percent_before'] = mem.percent
        self.ram_before_label.set_text(f"{mem.percent:.0f}%")

        total_cache = 0
        for name, paths in CACHE_DIRS:
            for p in paths:
                total_cache += get_dir_size_mb(p)
        self.stats['cache_before'] = total_cache

    def on_refresh(self, btn):
        self.refresh_btn.set_sensitive(False)
        self.log_buffer.set_text("")
        thread = threading.Thread(target=self.run_refresh, daemon=True)
        thread.start()

    def run_refresh(self):
        total_steps = 5
        step = 0

        # Step 1: Kill unwanted processes
        step += 1
        self.set_progress(step / total_steps, "Killing unwanted processes...")
        self.log("--- Killing Unwanted Processes ---")
        killed = 0
        killed_names = []
        for proc_name in UNWANTED_PROCS:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        pname = proc.info['name'] or ''
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if proc_name.lower() in pname.lower() or proc_name.lower() in cmdline.lower():
                            proc.kill()
                            self.log(f"  Killed: {pname} (PID {proc.info['pid']})")
                            killed += 1
                            if proc_name not in killed_names:
                                killed_names.append(proc_name)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception:
                pass
        if killed == 0:
            self.log("  No unwanted processes found")
        else:
            self.log(f"  Total: {killed} processes killed")

        # Step 2: Kill zombie processes
        step += 1
        self.set_progress(step / total_steps, "Cleaning zombie processes...")
        self.log("--- Cleaning Zombie Processes ---")
        zombies = 0
        for proc in psutil.process_iter(['pid', 'status']):
            try:
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    os.kill(proc.info['pid'], signal.SIGKILL)
                    zombies += 1
            except (ProcessLookupError, PermissionError, psutil.NoSuchProcess):
                pass
        self.log(f"  Zombies killed: {zombies}")

        # Step 3: Clear caches
        step += 1
        self.set_progress(step / total_steps, "Clearing caches...")
        self.log("--- Clearing Caches ---")
        cache_details = {}
        for name, paths in CACHE_DIRS:
            size_before = sum(get_dir_size_mb(p) for p in paths)
            if size_before > 0.1:
                for p in paths:
                    clear_dir(p)
                size_after = sum(get_dir_size_mb(p) for p in paths)
                freed = size_before - size_after
                cache_details[name] = freed
                self.log(f"  {name}: freed {freed:.1f} MB")
            else:
                self.log(f"  {name}: clean")

        # Step 4: Clear misc files
        step += 1
        self.set_progress(step / total_steps, "Cleaning temporary files...")
        self.log("--- Cleaning Misc Files ---")

        # Recent file history
        recent = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(recent):
            os.remove(recent)
            self.log("  Cleared recent file history")

        # Old temp files
        tmp_cleaned = 0
        user = os.getenv("USER", "linux")
        for f in os.listdir("/tmp"):
            fp = os.path.join("/tmp", f)
            try:
                if os.stat(fp).st_uid == os.getuid():
                    age = time.time() - os.stat(fp).st_atime
                    if age > 86400 and os.path.isfile(fp):
                        os.remove(fp)
                        tmp_cleaned += 1
            except OSError:
                pass
        self.log(f"  Temp files cleaned: {tmp_cleaned}")

        # Journal cleanup
        try:
            subprocess.run(
                ["journalctl", "--user", "--vacuum-time=2d"],
                capture_output=True, timeout=10
            )
            self.log("  User journal logs cleaned")
        except Exception:
            pass

        # Step 5: Collect after stats
        step += 1
        self.set_progress(step / total_steps, "Collecting results...")

        time.sleep(0.5)  # Let system settle

        mem_after = psutil.virtual_memory()
        ram_after_pct = mem_after.percent
        ram_freed = self.stats['ram_percent_before'] - ram_after_pct
        total_cache_freed = sum(cache_details.values())

        self.stats['ram_percent_after'] = ram_after_pct
        self.stats['procs_killed'] = killed + zombies
        self.stats['cache_freed'] = total_cache_freed

        self.log("--- Results ---")
        self.log(f"  RAM: {self.stats['ram_percent_before']:.0f}% -> {ram_after_pct:.0f}% ({ram_freed:+.1f}%)")
        self.log(f"  Processes killed: {killed + zombies}")
        self.log(f"  Cache freed: {total_cache_freed:.1f} MB")
        self.log(f"  Free RAM now: {mem_after.available / (1024**2):.0f} MB")

        # Update UI
        GLib.idle_add(self._update_results, ram_after_pct, killed + zombies, total_cache_freed)

        # Desktop notification
        try:
            n = Notify.Notification.new(
                "Kali Refresh Complete",
                f"RAM: {self.stats['ram_percent_before']:.0f}% → {ram_after_pct:.0f}%\n"
                f"Killed {killed + zombies} processes\n"
                f"Freed {total_cache_freed:.1f} MB cache",
                "view-refresh"
            )
            n.show()
        except Exception:
            pass

    def _update_results(self, ram_pct, procs, cache):
        self.ram_after_label.set_text(f"{ram_pct:.0f}%")
        self.procs_killed_label.set_text(str(procs))
        self.cache_freed_label.set_text(f"{cache:.0f}MB")
        self.refresh_btn.set_sensitive(True)
        self.status_label.set_text("Refresh complete!")
        self.progress.set_fraction(1.0)


def main():
    app = RefreshApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

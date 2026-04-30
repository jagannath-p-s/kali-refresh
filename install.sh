#!/bin/bash
# Installer for Kali Refresh - GTK app with XFCE desktop right-click integration

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
DESKTOP_DIR="$HOME/Desktop"

echo "[*] Installing Kali Refresh..."

# Install Python app and launcher
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/kali_refresh.py" "$INSTALL_DIR/kali_refresh.py"
chmod +x "$INSTALL_DIR/kali_refresh.py"

cat > "$INSTALL_DIR/kali-refresh" << 'LAUNCHER'
#!/bin/bash
exec python3 "$HOME/.local/bin/kali_refresh.py" "$@"
LAUNCHER
chmod +x "$INSTALL_DIR/kali-refresh"
echo "[+] Installed app to $INSTALL_DIR/"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "[+] Added $INSTALL_DIR to PATH in .zshrc"
fi

# Create .desktop entry (for app menu and desktop)
mkdir -p "$APP_DIR"
cat > "$APP_DIR/kali-refresh.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Refresh System
Comment=Kill unwanted processes, clear caches, free RAM
Exec=$INSTALL_DIR/kali-refresh
Icon=view-refresh
Terminal=false
Categories=System;Utility;
Keywords=refresh;clean;cache;kill;optimize;
EOF
echo "[+] Created application entry"

# Desktop shortcut
cp "$APP_DIR/kali-refresh.desktop" "$DESKTOP_DIR/kali-refresh.desktop"
chmod +x "$DESKTOP_DIR/kali-refresh.desktop"
echo "[+] Created desktop shortcut"

# Add to Thunar right-click custom actions
XFCE_ACTIONS="$HOME/.config/Thunar/uca.xml"
mkdir -p "$(dirname "$XFCE_ACTIONS")"

if [ -f "$XFCE_ACTIONS" ]; then
    if ! grep -q "kali-refresh" "$XFCE_ACTIONS"; then
        sed -i 's|</actions>|<action>\n\t<icon>view-refresh</icon>\n\t<name>Refresh System</name>\n\t<command>'"$INSTALL_DIR"'/kali-refresh</command>\n\t<description>Kill unwanted processes and clear caches</description>\n\t<patterns>*</patterns>\n\t<directories/>\n\t<audio-files/>\n\t<image-files/>\n\t<other-files/>\n\t<text-files/>\n\t<video-files/>\n</action>\n</actions>|' "$XFCE_ACTIONS"
        echo "[+] Added to Thunar custom actions"
    else
        echo "[=] Already in Thunar custom actions"
    fi
else
    cat > "$XFCE_ACTIONS" << XMLEOF
<?xml version="1.0" encoding="UTF-8"?>
<actions>
<action>
	<icon>view-refresh</icon>
	<name>Refresh System</name>
	<command>$INSTALL_DIR/kali-refresh</command>
	<description>Kill unwanted processes and clear caches</description>
	<patterns>*</patterns>
	<directories/>
	<audio-files/>
	<image-files/>
	<other-files/>
	<text-files/>
	<video-files/>
</action>
</actions>
XMLEOF
    echo "[+] Created Thunar custom actions file"
fi

# Add "Refresh System" to XFCE desktop right-click menu
# This uses xfdesktop's custom actions via .desktop files in the desktop directory
# and by adding to the xfce applications menu
MENU_DIR="$HOME/.config/menus"
MERGE_DIR="$HOME/.local/share/desktop-directories"
mkdir -p "$MENU_DIR" "$MERGE_DIR"

# Create desktop directory entry
cat > "$MERGE_DIR/kali-refresh.directory" << EOF
[Desktop Entry]
Type=Directory
Name=Refresh
Icon=view-refresh
EOF

# The desktop right-click in XFCE shows items from the applications menu
# We ensure our .desktop file is in the right place (already done above)
# Update the desktop database
update-desktop-database "$APP_DIR" 2>/dev/null

echo ""
echo "[*] Installation complete!"
echo "    - Right-click on Desktop -> 'Refresh System' (in Applications menu)"
echo "    - Right-click in Thunar -> 'Refresh System'"
echo "    - Desktop shortcut icon on desktop"
echo "    - Terminal: kali-refresh"
echo ""
echo "[!] You may need to log out and log back in for menu changes to appear."

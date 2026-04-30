#!/bin/bash
# Installer for Kali Refresh - adds right-click desktop action

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
ACTIONS_DIR="$HOME/.local/share/file-manager/actions"
DESKTOP_DIR="$HOME/Desktop"

echo "[*] Installing Kali Refresh..."

# Install main script
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/refresh.sh" "$INSTALL_DIR/kali-refresh"
chmod +x "$INSTALL_DIR/kali-refresh"
echo "[+] Installed script to $INSTALL_DIR/kali-refresh"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "[+] Added $INSTALL_DIR to PATH in .zshrc"
fi

# Create Thunar custom action (XFCE file manager right-click)
mkdir -p "$ACTIONS_DIR"
cat > "$ACTIONS_DIR/kali-refresh.desktop" << 'EOF'
[Desktop Entry]
Type=Action
Name=Refresh System
Tooltip=Kill unwanted processes and clear caches
Icon=view-refresh
Profiles=profile-0;

[X-Action-Profile profile-0]
MimeTypes=*
Exec=bash -c "$HOME/.local/bin/kali-refresh"
Name=Default profile
EOF
echo "[+] Added Thunar custom action"

# Create desktop shortcut
cat > "$DESKTOP_DIR/kali-refresh.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Refresh System
Comment=Kill unwanted processes and clear caches
Exec=$INSTALL_DIR/kali-refresh
Icon=view-refresh
Terminal=false
Categories=System;
EOF
chmod +x "$DESKTOP_DIR/kali-refresh.desktop"
echo "[+] Created desktop shortcut"

# Add to XFCE desktop right-click menu via custom actions XML
XFCE_ACTIONS="$HOME/.config/Thunar/uca.xml"
mkdir -p "$(dirname "$XFCE_ACTIONS")"

if [ -f "$XFCE_ACTIONS" ]; then
    # Check if already added
    if ! grep -q "kali-refresh" "$XFCE_ACTIONS"; then
        # Insert before closing tag
        sed -i 's|</actions>|<action>\n\t<icon>view-refresh</icon>\n\t<name>Refresh System</name>\n\t<command>'"$INSTALL_DIR"'/kali-refresh</command>\n\t<description>Kill unwanted processes and clear caches</description>\n\t<patterns>*</patterns>\n\t<directories/>\n\t<audio-files/>\n\t<image-files/>\n\t<other-files/>\n\t<text-files/>\n\t<video-files/>\n</action>\n</actions>|' "$XFCE_ACTIONS"
        echo "[+] Added to existing Thunar custom actions"
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

echo ""
echo "[*] Installation complete!"
echo "    - Right-click in Thunar file manager -> 'Refresh System'"
echo "    - Desktop shortcut created"
echo "    - Run manually: kali-refresh"

#!/bin/bash
# Uninstaller for Kali Refresh

echo "[*] Uninstalling Kali Refresh..."

rm -f "$HOME/.local/bin/kali-refresh"
rm -f "$HOME/Desktop/kali-refresh.desktop"
rm -f "$HOME/.local/share/file-manager/actions/kali-refresh.desktop"

# Remove from Thunar custom actions
XFCE_ACTIONS="$HOME/.config/Thunar/uca.xml"
if [ -f "$XFCE_ACTIONS" ] && grep -q "kali-refresh" "$XFCE_ACTIONS"; then
    sed -i '/<action>/,/<\/action>/{/kali-refresh/,/<\/action>/d; /kali-refresh/d}' "$XFCE_ACTIONS"
    # Clean approach: remove the action block containing kali-refresh
    python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$XFCE_ACTIONS')
root = tree.getroot()
for action in root.findall('action'):
    cmd = action.find('command')
    if cmd is not None and 'kali-refresh' in (cmd.text or ''):
        root.remove(action)
tree.write('$XFCE_ACTIONS', xml_declaration=True, encoding='UTF-8')
" 2>/dev/null
    echo "[+] Removed from Thunar custom actions"
fi

echo "[*] Uninstall complete."

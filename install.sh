#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Please run this installer with sudo:"
  echo "sudo ./install.sh"
  exit 1
fi

echo "Cleaning up legacy versions..."
# Remove old desktop entries
rm -f /usr/share/applications/usb-guard.desktop
rm -f /usr/share/applications/nana-guard.desktop
# Remove old binary links
rm -f /usr/local/bin/usb-guard
rm -f /usr/local/bin/l3iytool
rm -f /usr/local/bin/nanaguard
# Remove old directories
rm -rf /opt/usb-guard
rm -rf /opt/nana-guard

echo "Installing Nana Blocker..."

# Ensure Tkinter is installed 
apt update && apt install -y python3-tk || {
    echo "Could not install python3-tk automatically. Maybe it is already installed."
}

mkdir -p /opt/nana-guard
cp nana-guard.py /opt/nana-guard/
cp logo3.png /opt/nana-guard/
chmod +x /opt/nana-guard/nana-guard.py

# Create a symlink to easily run from terminal
ln -sf /opt/nana-guard/nana-guard.py /usr/local/bin/nanablocker

# Install desktop shortcut
cp nana-guard.desktop /usr/share/applications/
chmod 644 /usr/share/applications/nana-guard.desktop

echo "Installation complete!"
echo "You can now find 'Nana Blocker' in your application menu, or run 'nanablocker' from the terminal."

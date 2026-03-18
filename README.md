# Nana Blocker 🛡️
**USB Write-Blocking & Forensic Integrity Tool**

Nana Blocker is a lightweight, graphical utility designed for Linux (specifically optimized for Cinnamon/Linux Mint) that allows users to toggle USB write-protection with a single click. It ensures forensic integrity by preventing any accidental writes to connected USB storage devices.

## How it Works (Technical Overview)

The tool operates at the **Linux Kernel** and **udev** levels to enforce write-blocking:

1.  **udev Rule (99-usb-readonly.rules)**: When protection is "ON", the tool creates a high-priority udev rule that monitors the `block` subsystem. Any device identified as `ID_BUS="usb"` triggering an `add` event (plug-in) is intercepted.
2.  **Kernel-level Read-Only (ATTR{ro})**: The udev rule sets the device's `ro` attribute in sysfs to `1`. This tells the kernel that the device is globally read-only.
3.  **Block Layer Lock (blockdev)**: For maximum robustness, the rule also executes the `blockdev --setro` command on the device node (`/dev/sdX`). This locks the block layer, ensuring that even if a mount operation is attempted, it must be read-only.
4.  **Immediate Release Logic**: When protection is turned "OFF", the tool re-scans active USB devices and uses `blockdev --setrw` to "unlock" them instantly, eliminating the need to unplug and replug the device to regain write access.
5.  **Safe Eject Logic**: Integrated right-click functionality allows users to safely unmount all partitions and power down a USB drive using `udisksctl`.
6.  **Secure Elevation**: The GUI runs as a standard user for UI consistency but uses **Polkit (pkexec)** to securely request administrative elevation only for the specific commands that modify system rules.

## Installation

To install Nana Blocker on your system:

1.  Clone this repository or download the ZIP.
 ```bash
    git clone https://github.com/raghu1134/nanablocker.git
 ```
2.  Navigate to the directory in your terminal.
3.  Run the installer:
    ```bash
    sudo bash ./install.sh
    ```

## Manual Verification

On Linux, the lsblk command can show you whether a USB (or any block device) is read-only or writable.
```bash
lsblk -o NAME,RO,RM,SIZE,TYPE,MOUNTPOINT
```
- **NAME** – shows the device name
- **RO** – shows if the device is read-only (`1`) or writable (`0`)
- **RM** – removable (`1 = yes`, `0 = no`)
- **SIZE** – size of the device
- **TYPE** – disk, part, etc.
- **MOUNTPOINT** – where it’s mounted

This helps you see if the device is a USB, its size, and whether it’s read-only.


## Usage

-   **Launch**: Find "Nana Blocker" in your application menu or run `nanablocker` in the terminal.
-   **Protect**: Click **Turn ON** before plugging in your USB.
-   **Release**: Click **Turn OFF** to regain write access (works immediately on connected drives).
-   **Eject**: Right-click any device in the list and select **Safe Eject** to safely unmount and power it down.

## Requirements
-   Linux (Ubuntu, Mint, Debian preferred)
-   `python3-tk` (installed automatically by the script)
-   `udev` and `util-linux` (pre-installed on almost all distros)

---
*Created for secure data handling and forensic workflows.*

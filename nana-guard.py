#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import json

RULE = "/etc/udev/rules.d/99-usb-readonly.rules"
RULE_DISABLED = "/etc/udev/rules.d/99-usb-readonly.rules.disabled"

class USBGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nana Blocker")
        self.root.geometry("640x580")
        self.root.configure(bg="black")
        self.root.resizable(False, False)

        # Style configurations
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        self.create_widgets()
        
        # Load and set application icon
        try:
            self.icon = tk.PhotoImage(file='/opt/nana-guard/logo3.png')
            self.root.iconphoto(False, self.icon)
        except Exception:
            pass # Fallback if icon is missing or wrong format
            
        self.update_status_display()
        self.check_usb_devices()

    def create_widgets(self):
        # Header Frame - Sleek Black
        header_frame = tk.Frame(self.root, bg="black", pady=10)
        header_frame.pack(fill="x")
        
        # Try to show logo in the header
        try:
            # We keep a reference to prevent garbage collection
            orig_logo = tk.PhotoImage(file='/opt/nana-guard/logo3.png')
            self.header_logo = orig_logo.subsample(2, 2)
            logo_label = tk.Label(header_frame, image=self.header_logo, bg="black")
            logo_label.pack(pady=(5, 0))
        except:
            pass

        self.header_label = tk.Label(header_frame, text="Nana Blocker", font=("Arial", 20, "bold"), bg="black", fg="white")
        self.header_label.pack(pady=(0, 5))

        # Status Display
        self.status_label = tk.Label(self.root, text="Checking status...", font=("Arial", 14, "bold"), pady=10, bg="black")
        self.status_label.pack()

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg="black")
        btn_frame.pack(pady=10)

        # Customizing button styles instead of tk.Button for a better modern look
        self.btn_on = tk.Button(btn_frame, text="🔒 Turn ON (Read-Only)", bg="#28a745", fg="white", 
                                font=("Arial", 12, "bold"), width=22, height=2, 
                                relief="flat", highlightbackground="black", highlightthickness=2,
                                command=self.enable_ro)
        self.btn_on.grid(row=0, column=0, padx=15)

        self.btn_off = tk.Button(btn_frame, text="🔓 Turn OFF (Writable)", bg="#dc3545", fg="white", 
                                 font=("Arial", 12, "bold"), width=22, height=2, 
                                 relief="flat", highlightbackground="black", highlightthickness=2,
                                 command=self.disable_ro)
        self.btn_off.grid(row=0, column=1, padx=15)

        # Devices list
        lbl_frame = tk.Frame(self.root, bg="black")
        lbl_frame.pack(fill="x", padx=20, pady=(15, 5))
        tk.Label(lbl_frame, text="Connected USB Devices:", font=("Arial", 11, "bold"), bg="black", fg="white").pack(side="left")

        # Treeview (Table)
        style = ttk.Style()
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        
        columns = ("name", "model", "ro", "mountpoint")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=6)
        
        self.tree.heading("name", text="Device")
        self.tree.heading("model", text="Model")
        self.tree.heading("ro", text="Status")
        self.tree.heading("mountpoint", text="Mountpoint")
        
        self.tree.column("name", width=80, anchor="center")
        self.tree.column("model", width=200, anchor="w")
        self.tree.column("ro", width=120, anchor="center")
        self.tree.column("mountpoint", width=200, anchor="w")
        
        self.tree.pack(padx=20, fill="x")

        # Right-click menu for Eject
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="⏏ Safe Eject", command=self.safe_eject)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Refresh - Footer
        btn_refresh = tk.Button(self.root, text="🔄 Refresh Devices", command=self.check_usb_devices, 
                                font=("Arial", 10), bg="#f8f9fa", relief="groove")
        btn_refresh.pack(pady=(15, 0)) # Closer to the bottom

    def is_enabled(self):
        return os.path.exists(RULE)

    def update_status_display(self):
        if self.is_enabled():
            self.status_label.config(text="🔒 Protection is ENABLED (Read-Only)", fg="#28a745")
        else:
            self.status_label.config(text="🔓 Protection is DISABLED (Writable)", fg="#dc3545")

    def run_root_command(self, cmd_string):
        """Runs a command as root, prompting via polkit if the app itself isn't root."""
        if os.geteuid() == 0:
            final_cmd = cmd_string
        else:
            # Escape single quotes in the command string for polkit
            safe_cmd = cmd_string.replace("'", "'\\''")
            final_cmd = f"pkexec sh -c '{safe_cmd}'"
            
        try:
            subprocess.run(final_cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            messagebox.showerror("Permission Denied", "Action failed. Root permissions are required to modify udev rules.")
            return False

    def enable_ro(self):
        cmds = []
        if os.path.exists(RULE_DISABLED):
            cmds.append(f"mv '{RULE_DISABLED}' '{RULE}'")
        
        # Robust rule: matches any USB block device (disk or partition)
        # We use BOTH ATTR{ro} and blockdev as a hammer to ensure it's read-only
        rule_text = 'ACTION=="add", SUBSYSTEM=="block", ENV{ID_BUS}=="usb", ATTR{ro}="1", RUN+="/usr/sbin/blockdev --setro $tempnode"'
        cmds.append(f"echo '{rule_text}' > '{RULE}'")
        cmds.append("udevadm control --reload-rules")
        
        full_cmd = " && ".join(cmds)
        
        if self.run_root_command(full_cmd):
            self.update_status_display()
            # We don't refresh immediately because the user needs to re-plug
            messagebox.showinfo("Success", "🔒 Nana Blocker ENABLED.\n\n👉 IMPORTANT: If your USB is already plugged in, please UNPLUG it and PLUG it back in now.")
            self.check_usb_devices()
 
    def disable_ro(self):
        cmds = []
        if os.path.exists(RULE):
            cmds.append(f"mv '{RULE}' '{RULE_DISABLED}'")
        
        cmds.append("udevadm control --reload-rules")
        
        # Immediate release: find all USB devices and set them to RW
        # This allows the user to write without unplugging/replugging
        release_cmd = "lsblk -nlo NAME,TRAN | grep usb | awk '{print \"/dev/\"$1}' | xargs -I {} /usr/sbin/blockdev --setrw {}"
        cmds.append(release_cmd)
        
        full_cmd = " && ".join(cmds)
        
        if self.run_root_command(full_cmd):
            self.update_status_display()
            self.check_usb_devices()
            messagebox.showinfo("Success", "🔓 Nana Blocker DISABLED.\n\n✅ USB devices are now Writable immediately.")
        else:
            self.update_status_display()
            self.check_usb_devices()
            messagebox.showinfo("Success", "🔓 Nana Blocker is already DISABLED.")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def safe_eject(self):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        device_name = item['values'][0] # e.g. "sda"
        device_path = f"/dev/{device_name}"
        
        try:
            # 1. Correctly find and unmount all partitions/children of this device
            # We get the 'NAME' of all children that have a mountpoint
            find_parts_cmd = f"lsblk -nlo NAME,MOUNTPOINT {device_path} | grep / | awk '{{print $1}}'"
            parts_res = subprocess.run(find_parts_cmd, shell=True, capture_output=True, text=True)
            
            for part in parts_res.stdout.splitlines():
                part_name = part.strip()
                if part_name:
                    # Unmount each partition using its block device path
                    subprocess.run(["udisksctl", "unmount", "-b", f"/dev/{part_name}"], capture_output=True)
            
            # 2. Power off/Eject the drive
            res = subprocess.run(["udisksctl", "power-off", "-b", device_path], capture_output=True, text=True)
            
            if res.returncode == 0:
                messagebox.showinfo("Success", f"✅ {device_name} has been safely ejected.")
            else:
                # Provide a more helpful message for 'In Use' errors
                error_msg = res.stderr.strip()
                if "in use" in error_msg.lower():
                    messagebox.showwarning("Device In Use", f"Could not eject {device_name} because it is currently in use.\n\n👉 Please close any open folders or files from this USB and try again.")
                else:
                    messagebox.showwarning("Eject Note", f"Device {device_name} unmounted, but could not be powered off.\n\nYou can safely unplug it now.\n\nDetail: {error_msg}")
            
            self.check_usb_devices()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to eject {device_name}: {e}")

    def check_usb_devices(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            result = subprocess.run(["lsblk", "-J", "-o", "NAME,TRAN,RO,MOUNTPOINT,MODEL"], capture_output=True, text=True)
            if not result.stdout.strip():
                return
                
            data = json.loads(result.stdout)
            
            def process_device(dev):
                name = dev.get("name", "")
                model = dev.get("model", "Unknown")
                if model is None: model = "Unknown"
                model = model.strip()
                
                # 'ro' might be boolean (True/False) or "1"/"0"
                ro_val = dev.get("ro")
                is_ro = str(ro_val).lower() in ["1", "true"]
                ro = "🔒 Read-Only" if is_ro else "🔓 Writable"
                
                # Check for mountpoints
                mountpoints = []
                if dev.get("mountpoint"):
                    mountpoints.append(dev.get("mountpoint"))
                    
                for child in dev.get("children", []):
                    if child.get("mountpoint"):
                        mountpoints.append(child.get("mountpoint"))
                        
                mount_str = ", ".join(mountpoints) if mountpoints else "Not Mounted"
                
                self.tree.insert("", "end", values=(name, model, ro, mount_str))

            for dev in data.get("blockdevices", []):
                # Only show USB devices
                if dev.get("tran") == "usb":
                    process_device(dev)
                elif "children" in dev:
                    # Some cases the parent is not marked usb but children are (or weird adapters)
                    is_usb = False
                    for child in dev.get("children", []):
                        if child.get("tran") == "usb":
                            is_usb = True
                    if is_usb:
                        process_device(dev)

        except Exception as e:
            print(f"Error checking devices: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = USBGuardApp(root)
    # Bring window to front
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    root.mainloop()

import os
import sys

# Force AppIndicator backend early for Linux/KDE stability
if sys.platform == 'linux':
    os.environ['PYSTRAY_BACKEND'] = 'appindicator'

import customtkinter as ctk
import socket
import threading
import time
import dashboard
from workout_widget import WorkoutWidget
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

class DashboardClient:
    def __init__(self, start_hidden=False):
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.withdraw()
        self.app = dashboard.Dashboard(self.root, on_protection_change_callback=self.request_toggle)
        self.running = True
        self.status = "INACTIVE"
        self.workout_window = None
        threading.Thread(target=self.poll_status, daemon=True).start()
        threading.Thread(target=self.setup_tray, daemon=True).start()
        if not start_hidden: self.app.show()
        self.root.protocol("WM_DELETE_WINDOW", self.app.hide)
        self.root.mainloop()

    def ensure_autostart(self, active):
        """Creates or removes autostart based on ACTIVE status."""
        autostart_file = os.path.expanduser("~/.config/autostart/breakingbadhabits.desktop")
        if active:
            try:
                if not os.path.exists(os.path.dirname(autostart_file)): os.makedirs(os.path.dirname(autostart_file))
                with open(autostart_file, 'w') as f:
                    f.write(f"[Desktop Entry]\nType=Application\nExec={os.path.abspath('launch.sh')} --background\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=Breaking Bad Habits\n")
            except Exception as e:
                print(f"DEBUG: Failed to ensure autostart: {e}")
        elif os.path.exists(autostart_file):
            try:
                os.remove(autostart_file)
            except Exception as e:
                print(f"DEBUG: Failed to remove autostart: {e}")

    def setup_tray(self):
        self.tray_menu = pystray.Menu(
            item('Show Dashboard', self.on_tray_show, default=True), 
            item('Panic Button', self.on_tray_panic), 
            item('Quit BreakingBadHabits', self.on_tray_quit, enabled=lambda item: self.status != "ACTIVE")
        )
        self.tray_icon = pystray.Icon("BreakingBadHabits", self.create_tray_icon(), "Breaking Bad Habits", self.tray_menu)
        self.tray_icon.run()

    def create_tray_icon(self):
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse((4, 4, 28, 28), fill='#4a90e2', outline='#ffffff', width=2)
        return img

    def on_tray_show(self, icon, item=None): self.root.after(0, self.app.show)
    def on_tray_panic(self, icon, item=None): self.root.after(0, self.app.open_panic)
    def on_tray_quit(self, icon, item=None): 
        if self.status != "ACTIVE": self.root.after(0, self.on_close)

    def send_command(self, cmd):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(60.0) # Increased timeout to allow for pkexec password entry
                s.connect((SERVER_HOST, SERVER_PORT))
                s.sendall(cmd.encode('utf-8'))
                return s.recv(1024).decode('utf-8')
        except (socket.timeout, ConnectionRefusedError, socket.error):
            return None

    def request_toggle(self, target_state, delay_minutes=None):
        print(f"DEBUG: request_toggle called with target_state={target_state}, delay={delay_minutes}")
        if target_state == "CANCEL":
            print("DEBUG: Sending CANCEL_UNLOCK")
            res = self.send_command("CANCEL_UNLOCK")
            if res == "OK_CANCELLED":
                self.app.update_unlock_state(-1)
            return

        cmd = "TOGGLE"
        if target_state and delay_minutes is not None:
            cmd = f"TOGGLE {int(delay_minutes)}"
            
        print(f"DEBUG: Sending command: {cmd}")
        res = self.send_command(cmd)
        print(f"DEBUG: Received response: {res}")
        
        if res == "OK_ACTIVATED": 
            self.app.switch_var.set("on")
            self.ensure_autostart(True)
        elif res == "OK_DEACTIVATED": 
            self.app.switch_var.set("off")
            self.ensure_autostart(False)
            self.app.update_unlock_state(-1)
        elif res and res.startswith("LOCKED"):
            print("DEBUG: Backend returned LOCKED, reverting switch to ON")
            self.app.switch_var.set("on")
        else:
            # If error or cancelled, revert switch to actual status
            expected = "on" if self.status == "ACTIVE" else "off"
            print(f"DEBUG: Reverting switch to {expected} (status={self.status})")
            self.app.switch_var.set(expected)
            
        self.app._update_status_indicator()

    def poll_status(self):
        last_status = None
        while self.running:
            res = self.send_command("STATUS")
            if res:
                parts = res.split(":")
                self.status = parts[0]
                if self.status != last_status:
                    if hasattr(self, 'tray_icon'): self.tray_icon.update_menu()
                    self.ensure_autostart(self.status == "ACTIVE")
                    last_status = self.status
                
                # UI Update logic
                w_text = "Next Workout: --:--"
                u_seconds = -1
                for part in parts[1:]:
                    if part == "WORKOUT": self.root.after(0, self.show_workout_widget)
                    elif part.startswith("W"): 
                        try:
                            secs = int(part[1:])
                            w_text = f"Next Workout: {secs//60:02d}:{secs%60:02d}"
                        except ValueError: pass
                    elif part.startswith("U"): 
                        try: u_seconds = int(part[1:])
                        except ValueError: pass
                    elif part == "SHOW": self.root.after(0, self.app.show)
                
                self.app.workout_timer_label.configure(text=w_text)
                self.app.update_unlock_state(u_seconds)
                
                expected = "on" if self.status == "ACTIVE" else "off"
                if self.app.switch_var.get() != expected:
                    # Don't force revert if we are in the middle of a countdown
                    if u_seconds < 0:
                        self.app.switch_var.set(expected)
                        self.app._update_status_indicator()
            time.sleep(1)

    def show_workout_widget(self):
        if not self.workout_window or not self.workout_window.winfo_exists():
            self.workout_window = WorkoutWidget(self.root)
            self.workout_window.done_button.configure(command=self.on_workout_done)

    def on_workout_done(self):
        self.send_command("WORKOUT_DONE")
        if self.workout_window:
            self.workout_window.destroy()
            self.workout_window = None

    def on_close(self):
        self.running = False; self.send_command("QUIT"); self.root.destroy(); sys.exit(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--background', action='store_true')
    DashboardClient(start_hidden=parser.parse_args().background)

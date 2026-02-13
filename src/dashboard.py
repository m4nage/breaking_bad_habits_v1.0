import customtkinter as ctk
import time
import storage
import blocker
import threading
from panic import QUOTES, PanicWindow
import random

class DelayDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Set Unlock Delay")
        self.geometry("300x200")
        self.attributes("-topmost", True)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self, text="Unlock Delay (minutes):", font=("Arial", 14)).pack(pady=(20, 10))
        
        self.entry = ctk.CTkEntry(self, width=100)
        self.entry.insert(0, "60")
        self.entry.pack(pady=10)
        self.entry.focus_set()

        self.btn_ok = ctk.CTkButton(self, text="Activate", command=self.on_ok)
        self.btn_ok.pack(pady=10)

    def on_ok(self):
        try:
            mins = int(self.entry.get())
            if mins < 1: mins = 1
            self.callback(mins)
            self.destroy()
        except ValueError:
            pass

class Dashboard:
    def __init__(self, root, on_protection_change_callback=None):
        self.root = root
        self.on_protection_change_callback = on_protection_change_callback
        
        self.root.title("Breaking Bad Habits")
        self.root.geometry("350x550") # Match mockup narrow aspect ratio
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        self.data = storage.load_data()
        self.root.grid_columnconfigure(0, weight=1)

        self._setup_ui()
        self._update_timer()

    def _setup_ui(self):
        # Set background color for the root to match custom frames
        bg_color = self.root._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        self.root.configure(fg_color=bg_color)

        # 1. Title
        self.title_label = ctk.CTkLabel(self.root, text="Breaking Bad Habits", font=("Arial", 20, "bold"))
        self.title_label.grid(row=0, column=0, pady=(30, 15))

        # 2. Circular Streak Counter
        self.streak_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.streak_frame.grid(row=1, column=0, pady=10)
        
        # Using a higher width/height and scaling can help with pixelation on some displays
        self.streak_canvas = ctk.CTkCanvas(self.streak_frame, width=140, height=120, bg=bg_color, highlightthickness=0)
        self.streak_canvas.pack()
        
        # Draw base circle
        self.streak_canvas.create_oval(20, 10, 120, 110, outline="#3d3d3d", width=6)
        # Draw progress arc (full circle for now)
        self.streak_canvas.create_oval(20, 10, 120, 110, outline="#4a90e2", width=6)
        
        self.streak_label = ctk.CTkLabel(self.streak_frame, text="0", font=("Arial", 36, "bold"))
        self.streak_label.place(relx=0.5, rely=0.42, anchor="center")
        
        self.streak_sub_label = ctk.CTkLabel(self.streak_frame, text="Days Clean", font=("Arial", 12), text_color="#aaaaaa")
        self.streak_sub_label.place(relx=0.5, rely=0.68, anchor="center")

        # 3. Status Indicator
        self.status_indicator = ctk.CTkLabel(self.root, text="● Protected", font=("Arial", 14), text_color="#4caf50")
        self.status_indicator.grid(row=2, column=0, pady=15)

        # 4. Workout Card
        self.workout_frame = ctk.CTkFrame(self.root, fg_color="#3d3d3d", corner_radius=10)
        self.workout_frame.grid(row=3, column=0, padx=30, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.workout_frame, text="Next Workout In:", font=("Arial", 12), text_color="#aaaaaa").pack(pady=(10, 0), padx=15, anchor="w")
        self.workout_timer_label = ctk.CTkLabel(self.workout_frame, text="--:--", font=("Arial", 20, "bold"))
        self.workout_timer_label.pack(pady=(0, 10), padx=15, anchor="w")

        # 5. Unlock Countdown (Hidden by default)
        self.unlock_timer_label = ctk.CTkLabel(self.root, text="", font=("Arial", 12, "bold"), text_color="#f44336")
        self.unlock_timer_label.grid(row=4, column=0, pady=(10, 0)) # Added top padding
        
        self.btn_abort_unlock = ctk.CTkButton(
            self.root, text="Abort Unlock", 
            fg_color="#555555", width=120, height=28,
            command=self.abort_unlock
        )
        self.btn_abort_unlock.grid(row=5, column=0, pady=(5, 10)) # Moved to row 5 and added padding
        self.btn_abort_unlock.grid_remove() # Hidden by default

        # 6. Controls
        self.controls_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.controls_frame.grid(row=6, column=0, pady=10) # Shifted down to row 6

        self.switch_var = ctk.StringVar(value="on" if self.data.get("protection_active") else "off")
        self.switch_protection = ctk.CTkSwitch(
            self.controls_frame, 
            text="Active Protection", 
            variable=self.switch_var,
            onvalue="on", offvalue="off",
            command=self.toggle_protection,
            progress_color="#d32f2f" # Default to Red when ON
        )
        self.switch_protection.pack(side="left", padx=10)

        self.btn_reset = ctk.CTkButton(self.root, text="Reset Streak", fg_color="#555555", width=100, height=24, command=self.confirm_reset)
        self.btn_reset.grid(row=7, column=0, pady=5) # Shifted down

        # 7. Panic Button
        self.btn_panic = ctk.CTkButton(
            self.root, text="PANIC BUTTON", 
            fg_color="#d32f2f", hover_color="#b71c1c",
            font=("Arial", 16, "bold"), height=45,
            command=self.open_panic
        )
        self.btn_panic.grid(row=8, column=0, padx=30, pady=(20, 10), sticky="ew") # Shifted down

        # 8. Quote
        self.quote_label = ctk.CTkLabel(self.root, text=f'"{random.choice(QUOTES)}"', font=("Arial", 11, "italic"), wraplength=280, text_color="#888888")
        self.quote_label.grid(row=9, column=0, padx=20, pady=10) # Shifted down

        # Sync visual status
        self._update_status_indicator()

    def _update_status_indicator(self, is_pending=False):
        is_active = self.switch_var.get() == "on"
        if is_active:
            if is_pending:
                # Timer is running - Orange or Yellow? User said green when "can turn off"
                # But while counting down, let's keep it red or transition.
                # User: "When the blocker is in locked state the switch should be red"
                # "When the timer has ran out and we can turn off the blocker it should be green"
                self.status_indicator.configure(text="● Unlocking...", text_color="#ff9800")
                self.switch_protection.configure(progress_color="#ff9800")
            else:
                self.status_indicator.configure(text="● Protected", text_color="#4caf50")
                self.switch_protection.configure(progress_color="#d32f2f") # Red for Locked
        else:
            self.status_indicator.configure(text="● Unprotected", text_color="#f44336")
            self.switch_protection.configure(progress_color="#4caf50") # Default green when transitioning TO on

    def update_unlock_state(self, remaining_seconds):
        if remaining_seconds > 0:
            self.unlock_timer_label.configure(text=f"Unlock available in: {remaining_seconds}s")
            self.unlock_timer_label.grid()
            self.btn_abort_unlock.grid()
            self._update_status_indicator(is_pending=True)
        elif remaining_seconds == 0:
            self.unlock_timer_label.configure(text="Unlock Available!", text_color="#4caf50")
            self.unlock_timer_label.grid()
            self.btn_abort_unlock.grid_remove()
            self.switch_protection.configure(progress_color="#4caf50") # Green when ready to turn off
            self.status_indicator.configure(text="● Ready to Deactivate", text_color="#4caf50")
        else:
            self.unlock_timer_label.grid_remove()
            self.btn_abort_unlock.grid_remove()
            self._update_status_indicator(is_pending=False)

    def toggle_protection(self):
        val = self.switch_var.get()
        print(f"DEBUG: toggle_protection called. switch_var={val}")
        target_on = val == "on"
        
        if target_on:
            print("DEBUG: Turning ON - showing DelayDialog")
            # Reverting until password prompt success
            self.switch_var.set("off")
            DelayDialog(self.root, self.activate_with_delay)
        else:
            print("DEBUG: Turning OFF - calling on_protection_change_callback(False)")
            # We are turning it OFF.
            # If timer is NOT running, main.py will start it and return LOCKED.
            # If timer IS running and finished, main.py will perform deactivation.
            if self.on_protection_change_callback:
                self.on_protection_change_callback(False)

    def abort_unlock(self):
        if self.on_protection_change_callback:
            # Special call to cancel
            self.on_protection_change_callback("CANCEL")

    def activate_with_delay(self, mins):
        # We pass the delay to the client, which sends it to the server.
        # The server (main.py) will handle saving the settings.
        if self.on_protection_change_callback:
            self.on_protection_change_callback(True, mins)

    def confirm_reset(self):
        new_start = storage.reset_streak()
        self.data["streak_start"] = new_start
        self.refresh_streak()

    def refresh_streak(self):
        start_time = self.data["streak_start"]
        days, hours, minutes = storage.get_streak_duration(start_time)
        self.streak_label.configure(text=str(days))

    def _update_timer(self):
        if self.root.winfo_exists():
            self.refresh_streak()
            self.root.after(60000, self._update_timer)

    def open_panic(self):
        PanicWindow(self.root)

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.refresh_streak()

    def hide(self):
        self.root.withdraw()

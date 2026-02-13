import customtkinter as ctk

class WorkoutWidget(ctk.CTkToplevel):
    def __init__(self, parent=None, countdown_seconds=300):
        super().__init__(parent)

        self.countdown_seconds = countdown_seconds
        
        # Window setup
        self.title("Workout Reminder")
        self.attributes("-topmost", True)
        self.overrideredirect(True) # Remove title bar for widget-like appearance

        # Frame with border
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, border_width=2, border_color="#4a90e2", fg_color="#2d2d2d")
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Center the window on screen (bottom right)
        width, height = 220, 200
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Offset from bottom right corner
        x = screen_width - width - 20
        y = screen_height - height - 60 
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Content
        self.label_title = ctk.CTkLabel(
            self.main_frame, 
            text="⚠️ Workout Time!", 
            font=("Arial", 16, "bold"), 
            text_color="#ffbd2e"
        )
        self.label_title.pack(pady=(15, 5))

        self.label_desc = ctk.CTkLabel(
            self.main_frame, 
            text="Active for 1 hour.", 
            font=("Arial", 12),
            text_color="#ffffff"
        )
        self.label_desc.pack(pady=2)

        self.exercises = ctk.CTkLabel(
            self.main_frame, 
            text="• 20 Pushups\n• 10 Squats", 
            font=("Arial", 12, "bold"), 
            justify="left",
            text_color="#ffffff"
        )
        self.exercises.pack(pady=10)

        self.label_timer = ctk.CTkLabel(
            self.main_frame, 
            text=self.format_time(self.countdown_seconds), 
            font=("Arial", 14, "bold"),
            text_color="#ffffff"
        )
        self.label_timer.pack(pady=5)

        self.done_button = ctk.CTkButton(
            self.main_frame, 
            text="Done!", 
            height=24, 
            width=80, 
            command=self.destroy, 
            fg_color="#4caf50", 
            hover_color="#45a049"
        )
        self.done_button.pack(pady=(5, 15))

        # Start countdown
        self.update_timer()

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def update_timer(self):
        try:
            if not self.winfo_exists():
                return
                
            if self.countdown_seconds > 0:
                self.countdown_seconds -= 1
                self.label_timer.configure(text=self.format_time(self.countdown_seconds))
                self.after(1000, self.update_timer)
            else:
                self.label_timer.configure(text="Finished!")
                self.label_timer.configure(text_color="#4caf50")
        except Exception:
            pass

if __name__ == "__main__":
    # Test execution
    root = ctk.CTk()
    root.withdraw() # Hide root window
    
    def open_widget():
        widget = WorkoutWidget(countdown_seconds=10)
        
    root.after(100, open_widget)
    root.mainloop()

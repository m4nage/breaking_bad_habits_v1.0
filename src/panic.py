import customtkinter as ctk
import random

QUOTES = [
    "The secret of getting ahead is getting started.",
    "It does not matter how slowly you go as long as you do not stop.",
    "Your future self will thank you for what you do today.",
    "The only way to do great work is to love what you do.",
    "Believe you can and you're halfway there.",
    "The urge is just a feeling, and feelings pass.",
    "You are stronger than your strongest excuse.",
    "Don't give up what you want most for what you want now."
]

class PanicWindow(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.title("Emergency Motivation")
        self.geometry("400x300")
        self.attributes("-topmost", True)
        
        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.label_title = ctk.CTkLabel(
            self.main_frame, 
            text="Take a deep breath...", 
            font=("Arial", 20, "bold"),
            text_color="#d32f2f"
        )
        self.label_title.pack(pady=(20, 10))

        self.quote_text = ctk.CTkLabel(
            self.main_frame, 
            text=f'"{random.choice(QUOTES)}"', 
            font=("Arial", 14, "italic"),
            wraplength=300
        )
        self.quote_text.pack(pady=20)

        # Simple breathing animation (circle scaling)
        self.breathing_canvas = ctk.CTkCanvas(
            self.main_frame, 
            width=100, 
            height=100, 
            bg="#2d2d2d", 
            highlightthickness=0
        )
        self.breathing_canvas.pack(pady=10)
        self.circle = self.breathing_canvas.create_oval(30, 30, 70, 70, fill="#4a90e2", outline="")
        
        self.breathing_state = "inhale"
        self.breathing_size = 40
        self.animate_breathing()

        self.close_button = ctk.CTkButton(
            self.main_frame, 
            text="I'm Okay Now", 
            command=self.destroy,
            fg_color="#3d3d3d",
            hover_color="#555555"
        )
        self.close_button.pack(pady=(20, 10))

    def animate_breathing(self):
        if not self.winfo_exists():
            return

        if self.breathing_state == "inhale":
            self.breathing_size += 1
            if self.breathing_size >= 80:
                self.breathing_state = "exhale"
        else:
            self.breathing_size -= 1
            if self.breathing_size <= 30:
                self.breathing_state = "inhale"

        x0 = 50 - (self.breathing_size // 2)
        y0 = 50 - (self.breathing_size // 2)
        x1 = 50 + (self.breathing_size // 2)
        y1 = 50 + (self.breathing_size // 2)
        self.breathing_canvas.coords(self.circle, x0, y0, x1, y1)
        
        # Change color based on size
        color_val = int(100 + (self.breathing_size * 1.5))
        color = f"#4a{color_val:02x}e2"
        # Wait, that's not quite right for hex. Let's just keep it simple.
        
        self.after(50, self.animate_breathing)

if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    def open_panic():
        p = PanicWindow(root)
    root.after(100, open_panic)
    root.mainloop()
